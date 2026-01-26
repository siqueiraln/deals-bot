import asyncio
import os
import random
import logging
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ContextTypes, Application
from telegram.constants import ParseMode

from scrapers.mercadolivre_search import MercadoLivreSearchScraper
from scrapers.mercadolivre_api import MercadoLivreAPI 

from services.notifier import TelegramNotifier
from core.database import Database
from config.logger import logger
from core.autonomous_mode import AutonomousMode
from utils.category_dedup import deduplicate_by_category

load_dotenv()

# --- Configurações Globais ---
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
REPORT_FREQUENCY = 24   # 1 relatório por dia (ciclos de 1h)
MANUAL_LINKS_FILE = "data/manual_links.txt"
BLACKLIST_FILE = "data/blacklist.txt"

# Filters (Simplificado: apenas evitar spam massivo de 1 coisa só)
CATEGORY_LIMITS = {
    "outros": 10 # Limite alto, deixamos o fluxo controlar
}

# --- CONFIGURAÇÃO SIMPLIFICADA (OFERTAS) ---
# O Bot vai olhar esta lista e cavar até achar 8 itens novos
PRIORITY_URLS = [
    "https://www.mercadolivre.com.br/ofertas#nav-header",
    # Backup caso a principal falhe
    "https://www.mercadolivre.com.br/ofertas?promotion_type=lightning"
]

# Categorias (Volume)
VOLUME_CATEGORY_URLS = [
    "https://lista.mercadolivre.com.br/casa-moveis-decoracao/_NoIndex_True?original_category_landing=true", 
    "https://lista.mercadolivre.com.br/beleza-cuidado-pessoal/_NoIndex_True?original_category_landing=true",
    "https://lista.mercadolivre.com.br/esportes-fitness/_NoIndex_True?original_category_landing=true",
    "https://lista.mercadolivre.com.br/informatica/_NoIndex_True?original_category_landing=true",
    "https://lista.mercadolivre.com.br/joias-relogios/_NoIndex_True?original_category_landing=true",
    "https://lista.mercadolivre.com.br/eletronicos-audio-video/_NoIndex_True?original_category_landing=true"
]

# --- Funções Utilitárias ---

def load_file_lines(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def clear_manual_links():
    with open(MANUAL_LINKS_FILE, "w", encoding="utf-8") as f:
        f.write("# Adicione links aqui (serão limpos após o processamento)\n")

SCAN_EVENT = asyncio.Event()

# --- Handlers do Telegram ---

def is_admin(update: Update):
    if not ADMIN_USER_ID: return True 
    return str(update.effective_user.id) == str(ADMIN_USER_ID)

async def handle_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    await update.message.reply_text("🔎 <b>Forçando nova busca AGORA...</b>", parse_mode=ParseMode.HTML)
    SCAN_EVENT.set()

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    db = Database()
    auto_mode = AutonomousMode().get_status()
    report = (
        "🤖 <b>Bot Online (Hourly Edition)</b>\n\n"
        f"📊 <b>Modo:</b> {auto_mode['mode']}\n"
        f"⏱️ <b>Ciclo:</b> 1 Hora\n"
        f"📉 <b>Total Deals:</b> {db.get_total_count()}\n"
    )
    await update.message.reply_text(report, parse_mode=ParseMode.HTML)

async def handle_direct_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    text = update.message.text
    if text and "http" in text:
        with open(MANUAL_LINKS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{text}\n")
        await update.message.reply_text("📥 Link agendado!")

async def handle_auto_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    new_state = AutonomousMode().toggle()
    mode = "AUTÔNOMO" if new_state else "MANUAL"
    await update.message.reply_text(f"🤖 <b>Modo {mode} Ativado</b>", parse_mode=ParseMode.HTML)

# --- Loop Principal Otimizado ---

async def run_bot():
    logger.info("🔥 Iniciando Deals Bot (Hourly No-Score)...")

    # Inicialização
    notifier = TelegramNotifier()
    db = Database()
    
    # Scrapers & API
    ml_search = MercadoLivreSearchScraper()
    ml_api = MercadoLivreAPI()
    
    auto_mode = AutonomousMode()

    # Telegram Handlers
    telegram_handlers = {
        'scan': handle_scan,
        'status': handle_status,
        'auto': handle_auto_toggle,
        'handle_message': handle_direct_link
    }
    # Inicia listener em background
    asyncio.create_task(notifier.start_listening(telegram_handlers))

    cycle_count = 0

# --- SETUP DE FONTES (Lê do arquivo solicitado) ---
    LINKS_FILE = "docs/links.txt"
    if not os.path.exists(LINKS_FILE):
        logger.error(f"❌ Arquivo {LINKS_FILE} não encontrado! Crie o arquivo com os links.")
        return

    # Loop Principal
    while True:
        try:
            cycle_count += 1
            logger.info(f"--- Ciclo #{cycle_count} [Hora: {datetime.now().strftime('%H:%M')}] ---")

            # 1. Carrega Links Frescos e Separa "Geral" vs "Marca Fixa"
            raw_lines = load_file_lines(LINKS_FILE)
            general_urls = []
            fixed_brand_url = None
            
            for line in raw_lines:
                # Limpa a linha (remove comentários tipo "- Crocs")
                clean_url = line.split(" ")[0].strip()
                if not clean_url.startswith("http"): continue
                
                # Identifica Marca Fixa (Crocs)
                if "crocs" in line.lower() or "MLB1433521" in clean_url:
                    fixed_brand_url = clean_url
                else:
                    general_urls.append(clean_url)

            if not general_urls:
                 logger.warning("⚠️ Nenhum link GERAL encontrado!")
                 await asyncio.sleep(60)
                 continue

            # 2. Estratégia Híbrida (7 + 1)
            target_general = random.choice(general_urls)
            logger.info(f"🎲 Link Geral Sorteado: {target_general}")
            
            if fixed_brand_url:
                logger.info(f"🐊 Link Marca Fixa: {fixed_brand_url}")
            
            # Carrega Blacklist
            blacklist = [w.lower() for w in load_file_lines(BLACKLIST_FILE)]
            scraped_deals = []
            
            # --- FASE 1: BUSCA GERAL (7 Itens) ---
            # Busca 100 itens para garantir variedade
            raw_general = await ml_search.scrape_category_url(target_general, max_results=100)
            random.shuffle(raw_general)
            
            count_general = 0
            for d in raw_general:
                # Blacklist Check
                if any(b in d.title.lower() for b in blacklist): continue
                # DB Check
                if not db.is_deal_sent(d.url, d.price):
                    scraped_deals.append(d)
                    count_general += 1
                    if count_general >= 7: break # Top 7 Gerais
            
            # --- FASE 2: BUSCA MARCA FIXA (1 Item) ---
            if fixed_brand_url:
                # Busca deep também, mas precisamos de apenas 1
                raw_brand = await ml_search.scrape_category_url(fixed_brand_url, max_results=50)
                random.shuffle(raw_brand)
                
                found_brand = False
                for d in raw_brand:
                    # Blacklist Check
                    if any(b in d.title.lower() for b in blacklist): continue
                    # DB Check
                    if not db.is_deal_sent(d.url, d.price):
                        # Tag especial (opcional)
                        # d.title = f"🐊 {d.title}" 
                        scraped_deals.append(d)
                        found_brand = True
                        break # Só 1 item
                
                if not found_brand:
                    logger.warning("⚠️ Nenhum item novo da Marca Fixa encontrado neste ciclo.")
            
            final_selection = scraped_deals
            
            # Links Manuais (Extra bonus)
            manual_links = load_file_lines(MANUAL_LINKS_FILE)
            if manual_links:
                logger.info(f"🔗 Processando {len(manual_links)} links manuais...")
                clear_manual_links()
                # (Lógica manual simplificada - apenas limpa arquivo por enquanto)

            logger.info(f"🚀 Total para Envio: {len(final_selection)}")

            # --- FASE 4: API & PUBLICAÇÃO (Sem Score) ---
            
            if final_selection:
                urls = [d.url for d in final_selection]
                affiliate_links = await ml_api.create_links(urls)
                
                for i, deal in enumerate(final_selection):
                    # Atualizar Link
                    if i < len(affiliate_links) and affiliate_links[i]:
                        deal.affiliate_url = affiliate_links[i] # Guarda no campo correto
                        # NÃO subscreve deal.url, para garantir o check do DB no futuro!
                    
                    # Postar (Modo Autônomo Default)
                    mode = auto_mode.is_autonomous
                    
                    if mode:
                        logger.info(f"📤 Posting: {deal.title[:40]}")
                        await notifier.send_deal(deal, to_admin=False)
                        db.add_sent_deal(deal)
                    else:
                        await notifier.send_deal(deal, to_admin=True)
                        db.add_sent_deal(deal)
                    
                    await asyncio.sleep(10) # Delay para não flooding Telegram

            # --- FASE 5: DORMIR 1 HORA ---
            
            # Relatório Periódico
            if cycle_count % REPORT_FREQUENCY == 0:
                await notifier.send_status_report({"cycles": cycle_count, "db_size": db.get_total_count()})

            wait_time = 3600 # 1 Hora
            logger.info(f"💤 Dormindo por {wait_time/60} minutos... (Próximo ciclo: {(datetime.now().timestamp() + wait_time)})")
            
            try:
                # Permite interromper o sono com comando /scan
                await asyncio.wait_for(SCAN_EVENT.wait(), timeout=wait_time)
                SCAN_EVENT.clear()
                logger.info("⏩ Sono interrompido por comando manual!")
            except asyncio.TimeoutError:
                pass # Acordou naturalmente

        except Exception as e:
            logger.error(f"❌ Erro no loop: {e}", exc_info=True)
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot parado pelo usuário.")
