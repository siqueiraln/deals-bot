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

# --- ESTRATÉGIA FINAL (OFERTAS HOURLY) ---
# Alvo: 8 itens daqui
PRIORITY_URLS = [
    "https://www.mercadolivre.com.br/ofertas#nav-header",
    "https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&promotion_type=lightning#filter_applied=promotion_type&filter_position=2&is_recommended_domain=false&origin=scut"
]

# Alvo: 2 itens daqui
VOLUME_CATEGORY_URLS = [
    "https://lista.mercadolivre.com.br/casa-moveis-decoracao/_NoIndex_True?original_category_landing=true", # Cozinha/Casa
    "https://lista.mercadolivre.com.br/beleza-cuidado-pessoal/_NoIndex_True?original_category_landing=true",
    "https://lista.mercadolivre.com.br/esportes-fitness/_NoIndex_True?original_category_landing=true",
    "https://lista.mercadolivre.com.br/informatica/_NoIndex_True?original_category_landing=true",
    "https://lista.mercadolivre.com.br/joias-relogios/_NoIndex_True?original_category_landing=true"
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

    while True:
        try:
            cycle_count += 1
            logger.info(f"--- Ciclo #{cycle_count} [Hora: {datetime.now().strftime('%H:%M')}] ---")

            # Listas de controle
            blacklist = [w.lower() for w in load_file_lines(BLACKLIST_FILE)]
            
            scraped_deals = []
            
            # --- FASE 1: BUSCA NAS URLs PRIORITÁRIAS (Meta: 8 itens únicos) ---
            
            # Pega MUITOS (50) para filtrar duplicados e chegar nos 8 novos
            logger.info("⚡ Buscando Ofertas Gerais (com scroll)...")
            # Usamos a primeira URL principal (Ofertas)
            deals_prio = await ml_search.scrape_category_url(PRIORITY_URLS[0], max_results=50)
            scraped_deals.extend(deals_prio)
            
            # Se precisar, busca na Lightning também
            if len(deals_prio) < 20:
                 deals_light = await ml_search.scrape_category_url(PRIORITY_URLS[1], max_results=30)
                 scraped_deals.extend(deals_light)

            # Separa os candidatos ÚNICOS e NÃO-ENVIADOS da Prioridade
            priority_candidates = []
            for d in scraped_deals:
                # Blacklist Check
                if any(b in d.title.lower() for b in blacklist): continue
                # DB Check (Essencial para não repetir)
                if not db.is_deal_sent(d.url, d.price):
                    priority_candidates.append(d)
                    if len(priority_candidates) >= 8: # Meta atingida
                        break
            
            logger.info(f"   ✅ Candidatos Ofertas: {len(priority_candidates)}")

            # --- FASE 2: CATEGORIA SECUNDÁRIA (Meta: 2 itens únicos) ---
            
            category_idx = cycle_count % len(VOLUME_CATEGORY_URLS)
            target_category_url = VOLUME_CATEGORY_URLS[category_idx]
            logger.info(f"📂 Buscando Categoria: {target_category_url.split('/')[-2]}...")
            
            cat_raw_deals = await ml_search.scrape_category_url(target_category_url, max_results=20)
            
            category_candidates = []
            for d in cat_raw_deals:
                if any(b in d.title.lower() for b in blacklist): continue
                # Evita duplicar se já pegou na priority (raro mas possível)
                if any(p.url == d.url for p in priority_candidates): continue
                
                if not db.is_deal_sent(d.url, d.price):
                    category_candidates.append(d)
                    if len(category_candidates) >= 2: # Meta atingida
                        break
            
            logger.info(f"   ✅ Candidatos Categoria: {len(category_candidates)}")

            # --- FASE 3: CONSOLIDAÇÃO ---
            
            final_selection = priority_candidates + category_candidates
            
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
                        deal.url = affiliate_links[i]
                    
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
