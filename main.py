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
from scrapers.amazon import AmazonScraper
from scrapers.shopee import ShopeeScraper
from affiliate.generator import AffiliateLinkGenerator
from notifier import TelegramNotifier
from database import Database
from logger import logger

load_dotenv()

# --- Configurações ---
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

# --- Handlers do Telegram ---
async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database()
    report = (
        "🤖 <b>Bot Online & Operante</b>\n\n"
        f"📉 <b>Banco de Dados:</b> {db.get_total_count()} itens\n"
        "✨ <i>Envie um link direto para postar agora!</i>"
    )
    await update.message.reply_text(report, parse_mode=ParseMode.HTML)

async def handle_add_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = context.args[0] if context.args else ""
    if "http" in link:
        with open(MANUAL_LINKS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{link}\n")
        await update.message.reply_text("✅ Link agendado para processamento!")
    else:
        await update.message.reply_text("❌ Use: /add [link]")

async def handle_add_hot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args)
    if keyword:
        with open(HOT_KEYWORDS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{keyword}\n")
        await update.message.reply_text(f"🔥 '{keyword}' adicionado à busca ativa!")

async def handle_add_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args)
    if keyword:
        with open(BLACKLIST_FILE, "a", encoding="utf-8") as f:
            f.write(f"{keyword}\n")
        await update.message.reply_text(f"🚫 '{keyword}' adicionado à blacklist!")

async def handle_direct_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    amz_scraper = AmazonScraper()
    shp_scraper = ShopeeScraper()

    # Iniciar escuta de comandos
    telegram_handlers = {
        'status': handle_status,
        'add': handle_add_manual,
        'hot': handle_add_hot,
        'block': handle_add_block,
        'handle_message': handle_direct_link
    }
    asyncio.create_task(notifier.start_listening(telegram_handlers))

    cycle_count = 0
    total_sent = 0
    total_blacklisted = 0
    last_cleanup = datetime.now().date()

    while True:
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

        # 0. Links Manuais
        if manual_links:
            for url in manual_links:
                try:
                    deal = await ml_scraper.fetch_product_details(url) if "mercadolivre" in url else await amz_scraper.fetch_product_details(url)
                    if deal: all_deals.append(deal)
                except: pass
            clear_manual_links()

        # 1. Mercado Livre
        if cycle_count % ML_FREQUENCY == 0:
            try:
                deals = await ml_scraper.fetch_deals()
                all_deals.extend([d for d in deals if (d.discount_percentage or 0) >= MIN_DISCOUNT_GENERAL])
                for kw in hot_keywords:
                    all_deals.extend(await ml_scraper.search_keyword(kw))
                    await asyncio.sleep(2)
            except Exception as e: logger.error(f"Erro ML: {e}")

        # 2. Amazon
        if cycle_count % AMZ_FREQUENCY == 0:
            try:
                deals = await amz_scraper.fetch_deals()
                all_deals.extend([d for d in deals if (d.discount_percentage or 0) >= MIN_DISCOUNT_GENERAL])
                if hot_keywords: all_deals.extend(await amz_scraper.search_keyword(random.choice(hot_keywords)))
            except Exception as e: logger.error(f"Erro Amazon: {e}")

        # 3. Shopee
        if cycle_count % SHP_FREQUENCY == 0:
            try:
                deals = await shp_scraper.fetch_deals()
                all_deals.extend([d for d in deals if (d.discount_percentage or 0) >= MIN_DISCOUNT_GENERAL])
            except Exception as e: logger.error(f"Erro Shopee: {e}")

        # 4. Processar
        if all_deals:
            unique_deals = {d.url: d for d in all_deals}.values()
            for deal in unique_deals:
                if any(w in deal.title.lower() for w in blacklist):
                    total_blacklisted += 1
                    continue

                if not db.is_deal_sent(deal.url, deal.price):
                    deal.affiliate_url = affiliate_gen.generate(deal.url, deal.store)
                    await notifier.send_deal(deal, get_category_hashtags(deal.title))
                    db.add_sent_deal(deal)
                    total_sent += 1
                    await asyncio.sleep(5)

        if cycle_count % REPORT_FREQUENCY == 0:
            await notifier.send_status_report({"cycles": cycle_count, "sent": total_sent, "blacklisted": total_blacklisted, "total_db": db.get_total_count()})

        logger.info(f"Fim do ciclo. Aguardando...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    try: asyncio.run(run_bot())
    except KeyboardInterrupt: logger.info("Bot parado.")
