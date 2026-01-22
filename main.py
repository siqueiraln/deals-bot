import asyncio
import os
import json
import random
import logging
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from scrapers.mercadolivre import MercadoLivreScraper
from scrapers.mercadolivre_hub import MercadoLivreHubScraper
from scrapers.amazon import AmazonScraper
from scrapers.shopee import ShopeeScraper
from affiliate.generator import AffiliateLinkGenerator
from notifier import TelegramNotifier
from database import Database
from logger import logger

load_dotenv()

# --- Configurações ---
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
MIN_DISCOUNT_GENERAL = 20
HOT_KEYWORDS_FILE = "hot_keywords.txt"
MANUAL_LINKS_FILE = "manual_links.txt"
BLACKLIST_FILE = "blacklist.txt"

ML_FREQUENCY = 1
AMZ_FREQUENCY = 3
SHP_FREQUENCY = 4
REPORT_FREQUENCY = 10

CATEGORY_MAP = {
    "Smartphone": ["iphone", "samsung", "galaxy", "celular", "xiaomi", "motorola", "smartphone"],
    "Games": ["ps5", "playstation", "xbox", "nintendo", "switch", "gamer", "jogo", "dualshock", "console"],
    "Informatica": ["notebook", "laptop", "monitor", "teclado", "mouse", "ssd", "ram", "ryzen", "intel", "gpu", "placa de video"],
    "Casa": ["air fryer", "fritadeira", "aspirador", "cafeteira", "alexa", "echo", "smart", "philips", "geladeira", "fogão"],
    "Audio": ["fone", "headset", "bluetooth", "jbl", "caixa de som", "som", "earbuds", "galaxy buds", "airpods"],
    "Moda": ["tenis", "camiseta", "calça", "mochila", "relogio", "apple watch", "casaco"]
}

# --- Funções de Utilitário ---
def load_file_lines(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def clear_manual_links():
    with open(MANUAL_LINKS_FILE, "w", encoding="utf-8") as f:
        f.write("# Adicione links aqui (serão limpos após o processamento)\n")

def get_category_hashtags(title: str) -> str:
    tags = set()
    title_lower = title.lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(k in title_lower for k in keywords):
            tags.add(f"#{category}")
    return " ".join(list(tags)) if tags else "#Oferta"

# --- Evento para Forçar Varredura ---
SCAN_EVENT = asyncio.Event()

# --- Handlers do Telegram ---
def is_admin(update: Update):
    if not ADMIN_USER_ID: return True # Se não configurado, permite todos (para teste inicial)
    return str(update.effective_user.id) == str(ADMIN_USER_ID)

async def handle_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    await update.message.reply_text("🔎 <b>Forçando nova busca...</b>\nO bot vai vasculhar as lojas agora mesmo e te avisar se encontrar algo!", parse_mode=ParseMode.HTML)
    SCAN_EVENT.set() # Acorda o loop principal

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    db = Database()
    report = (
        "🤖 <b>Bot Online & Operante</b>\n\n"
        f"📉 <b>Banco de Dados:</b> {db.get_total_count()} itens\n"
        "✨ <i>Envie um link direto para postar agora!</i>"
    )
    await update.message.reply_text(report, parse_mode=ParseMode.HTML)

async def handle_add_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    link = context.args[0] if context.args else ""
    if "http" in link:
        with open(MANUAL_LINKS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{link}\n")
        await update.message.reply_text("✅ Link agendado para processamento!")
    else:
        await update.message.reply_text("❌ Use: /add [link]")

async def handle_add_hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    keyword = " ".join(context.args)
    if keyword:
        with open(HOT_KEYWORDS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{keyword}\n")
        await update.message.reply_text(f"🔥 '{keyword}' adicionado à busca ativa!")

async def handle_add_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    keyword = " ".join(context.args).lower()
    if keyword:
        with open(BLACKLIST_FILE, "a", encoding="utf-8") as f:
            f.write(f"{keyword}\n")
        await update.message.reply_text(f"🚫 '{keyword}' adicionado à blacklist!")

async def handle_list_hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    keywords = load_file_lines(HOT_KEYWORDS_FILE)
    if keywords:
        text = "🔥 <b>Palavras-chave Ativas:</b>\n\n" + "\n".join([f"• {k}" for k in keywords])
    else:
        text = "Sua lista de busca ativa está vazia."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_list_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    keywords = load_file_lines(BLACKLIST_FILE)
    if keywords:
        text = "🚫 <b>Termos Bloqueados:</b>\n\n" + "\n".join([f"• {k}" for k in keywords])
    else:
        text = "Sua blacklist está vazia."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_remove_hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    keyword = " ".join(context.args).strip()
    keywords = load_file_lines(HOT_KEYWORDS_FILE)
    if keyword in keywords:
        keywords.remove(keyword)
        with open(HOT_KEYWORDS_FILE, "w", encoding="utf-8") as f:
            for k in keywords: f.write(f"{k}\n")
        await update.message.reply_text(f"✅ '{keyword}' removido da busca ativa.")
    else:
        await update.message.reply_text(f"❌ '{keyword}' não encontrado na lista.")

async def handle_remove_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    keyword = " ".join(context.args).strip().lower()
    keywords = load_file_lines(BLACKLIST_FILE)
    if keyword in keywords:
        keywords.remove(keyword)
        with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
            for k in keywords: f.write(f"{k}\n")
        await update.message.reply_text(f"✅ '{keyword}' removido da blacklist.")
    else:
        await update.message.reply_text(f"❌ '{keyword}' não encontrado na blacklist.")

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update): return
    # ...
    help_text = (
        "📖 <b>Guia de Comandos do Bot</b>\n\n"
        "🔗 <b>Links Diretos:</b> Basta colar um link no chat para postar.\n"
        "📊 <b>/status:</b> Resumo de atividade do bot.\n\n"
        "🔥 <b>Busca Ativa (Keywords):</b>\n"
        "• <b>/hot [termo]:</b> Adiciona produto à busca.\n"
        "• <b>/hot_list:</b> Lista termos ativos.\n"
        "• <b>/remove_hot [termo]:</b> Remove termo.\n\n"
        "🚫 <b>Segurança (Blacklist):</b>\n"
        "• <b>/block [termo]:</b> Bloqueia palavras no título.\n"
        "• <b>/block_list:</b> Lista termos bloqueados.\n"
        "• <b>/remove_block [termo]:</b> Desbloqueia termo.\n\n"
        "💡 <i>Dica: Links manuais são limpos automaticamente após o envio!</i>"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def handle_direct_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    text = update.message.text
    if text and "http" in text:
        with open(MANUAL_LINKS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{text}\n")
        await update.message.reply_text("📥 Link recebido e agendado!")

# --- Loop Principal ---
async def run_bot():
    logger.info("Iniciando Bot de Promoções Profissional...")

    notifier = TelegramNotifier()
    db = Database()
    affiliate_gen = AffiliateLinkGenerator()

    ml_scraper = MercadoLivreScraper()
    ml_hub_scraper = MercadoLivreHubScraper()
    # amz_scraper = AmazonScraper()
    # shp_scraper = ShopeeScraper()

    # Iniciar escuta de comandos
    telegram_handlers = {
        'start': handle_help,
        'help': handle_help,
        'scan': handle_scan,
        'status': handle_status,
        'add': handle_add_manual,
        'hot': handle_add_hot,
        'block': handle_add_block,
        'hot_list': handle_list_hot,
        'block_list': handle_list_block,
        'remove_hot': handle_remove_hot,
        'remove_block': handle_remove_block,
        'handle_message': handle_direct_link
    }
    asyncio.create_task(notifier.start_listening(telegram_handlers))

    cycle_count = 0
    total_sent = 0
    total_blacklisted = 0
    last_cleanup = datetime.now().date()

    while True:
      try:
        cycle_count += 1
        current_date = datetime.now().date()

        if current_date > last_cleanup:
            db.clean_old_deals(days=15)
            last_cleanup = current_date

        hot_keywords = load_file_lines(HOT_KEYWORDS_FILE)
        manual_links = load_file_lines(MANUAL_LINKS_FILE)
        blacklist = [w.lower() for w in load_file_lines(BLACKLIST_FILE)]

        all_deals = []
        logger.info(f"--- Ciclo #{cycle_count} ---")

        # 0. Links Manuais (Estes vão para o CANAL PÚBLICO)
        if manual_links:
            logger.info(f"Processando {len(manual_links)} links manuais para o CANAL...")
            for url in manual_links:
                try:
                    deal = None
                    if "mercadolivre" in url: deal = await ml_scraper.fetch_product_details(url)
                    # elif "amazon" in url: deal = await amz_scraper.fetch_product_details(url)
                    # elif "shopee" in url: deal = await shp_scraper.fetch_product_details(url)

                    if deal:
                        # Para links manuais, usamos o link fornecido (que já pode ser de afiliado)
                        # e enviamos para o CANAL (to_admin=False)
                        await notifier.send_deal(deal, get_category_hashtags(deal.title), to_admin=False)
                        db.add_sent_deal(deal)
                except Exception as e:
                    logger.error(f"Erro ao processar link manual {url}: {e}")
            clear_manual_links()

        try:
             # 1-3. Buscas Automáticas
            if hot_keywords:
                      # Mercado Livre (Via Hub de Afiliados - Autenticado)
                if cycle_count % ML_FREQUENCY == 0:
                    try:
                         logger.info(f"Busca ML Hub (Ganhos Extras)...")
                         deals = await ml_hub_scraper.fetch_my_deals()
                         logger.info(f"DEBUG: Scraper retornou {len(deals)} ofertas.")
                         all_deals.extend(deals)
                         logger.info(f"DEBUG: all_deals agora tem {len(all_deals)} itens.")
                    except Exception as e:
                        logger.error(f"Erro no scraper ML Hub: {e}", exc_info=True)

                # Amazon (DISABLED)
                # if cycle_count % AMZ_FREQUENCY == 0:
                #     try:
                #         logger.info("Busca Amazon...")
                #         for kw in hot_keywords:
                #              deals = await amz_scraper.search_keyword(kw)
                #              all_deals.extend(deals)
                #              await asyncio.sleep(random.uniform(5, 15)) # Rate limiting
                #     except Exception as e:
                #          logger.error(f"Erro no scraper Amazon: {e}", exc_info=True)

                # Shopee (DISABLED)
                # if cycle_count % SHP_FREQUENCY == 0:
                #     try:
                #         logger.info("Busca Shopee...")
                #         for kw in hot_keywords:
                #             deals = await shp_scraper.search_keyword(kw)
                #             all_deals.extend(deals)
                #             await asyncio.sleep(random.uniform(5, 15)) # Rate limiting
                #     except Exception as e:
                #         logger.error(f"Erro no scraper Shopee: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Erro crítico no bloco de buscas automáticas: {e}", exc_info=True)
        if all_deals:
            unique_deals = {d.url: d for d in all_deals}.values()
            for deal in unique_deals:
                if any(w in deal.title.lower() for w in blacklist): continue

                if not db.is_deal_sent(deal.url, deal.price):
                    # Enviar direto para o CANAL (to_admin=False)
                    await notifier.send_deal(deal, get_category_hashtags(deal.title), to_admin=False)
                    db.add_sent_deal(deal)
                    await asyncio.sleep(2)

        if cycle_count % REPORT_FREQUENCY == 0:
            await notifier.send_status_report({"cycles": cycle_count, "sent": total_sent, "blacklisted": total_blacklisted, "total_db": db.get_total_count()})

        logger.info(f"Fim do ciclo. Aguardando...")
        try:
            # Espera 30 minutos OU até o SCAN_EVENT ser ativado
            await asyncio.wait_for(SCAN_EVENT.wait(), timeout=1800)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
             logger.error(f"Erro durante a espera do ciclo: {e}")

        SCAN_EVENT.clear() # Reseta o sinal para o próximo ciclo
      except Exception as e:
        logger.error(f"CRASH NO LOOP PRINCIPAL: {e}", exc_info=True)
        await asyncio.sleep(60) # Espera 1 minuto antes de tentar reiniciar para não flodar log

if __name__ == "__main__":
    try: asyncio.run(run_bot())
    except KeyboardInterrupt: logger.info("Bot parado.")
