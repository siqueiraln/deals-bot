import asyncio
import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv

from scrapers.mercadolivre import MercadoLivreScraper
from scrapers.amazon import AmazonScraper
from scrapers.shopee import ShopeeScraper
from affiliate.generator import AffiliateLinkGenerator
from notifier import TelegramNotifier
from database import Database
from logger import logger

load_dotenv()

# Configurações de Filtro
MIN_DISCOUNT_GENERAL = 20  # % mínimo para produtos gerais
HOT_KEYWORDS_FILE = "hot_keywords.txt"
MANUAL_LINKS_FILE = "manual_links.txt"
BLACKLIST_FILE = "blacklist.txt"

# Configurações de Frequência (Ciclos de ~30 min cada)
ML_FREQUENCY = 1
AMZ_FREQUENCY = 3
SHP_FREQUENCY = 4
REPORT_FREQUENCY = 10 # Envia relatório de status a cada 10 ciclos

# Mapeamento de Categorias por Keywords para Hashtags
CATEGORY_MAP = {
    "Smartphone": ["iphone", "samsung", "galaxy", "celular", "xiaomi", "motorola", "smartphone"],
    "Games": ["ps5", "playstation", "xbox", "nintendo", "switch", "gamer", "jogo", "dualshock", "console"],
    "Informatica": ["notebook", "laptop", "monitor", "teclado", "mouse", "ssd", "ram", "ryzen", "intel", "gpu", "placa de video"],
    "Casa": ["air fryer", "fritadeira", "aspirador", "cafeteira", "alexa", "echo", "smart", "philips", "geladeira", "fogão"],
    "Audio": ["fone", "headset", "bluetooth", "jbl", "caixa de som", "som", "earbuds", "galaxy buds", "airpods"],
    "Moda": ["tenis", "camiseta", "calça", "mochila", "relogio", "apple watch", "casaco"]
}

def load_hot_keywords():
    if os.path.exists(HOT_KEYWORDS_FILE):
        with open(HOT_KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def load_manual_links():
    if os.path.exists(MANUAL_LINKS_FILE):
        with open(MANUAL_LINKS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def clear_manual_links():
    """Limpa o arquivo de links manuais após a leitura para evitar reprocessamento"""
    if os.path.exists(MANUAL_LINKS_FILE):
        with open(MANUAL_LINKS_FILE, "w", encoding="utf-8") as f:
            f.write("# Adicione links aqui (serão limpos após o processamento)\n")

def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]
    return []

def is_blacklisted(title: str, blacklist: list) -> bool:
    title_lower = title.lower()
    return any(word in title_lower for word in blacklist)

def get_category_hashtags(title: str) -> str:
    tags = set()
    title_lower = title.lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(k in title_lower for k in keywords):
            tags.add(f"#{category}")

    if not tags:
        tags.add("#Oferta")

    return " ".join(list(tags))

async def run_bot():
    logger.info("Iniciando Bot de Promoções Profissional...")

    ml_scraper = MercadoLivreScraper()
    amz_scraper = AmazonScraper()
    shp_scraper = ShopeeScraper()

    affiliate_gen = AffiliateLinkGenerator()
    notifier = TelegramNotifier()
    db = Database()

    cycle_count = 0
    total_sent_session = 0
    total_blacklisted_session = 0

    while True:
        cycle_count += 1
        hot_keywords = load_hot_keywords()
        manual_links = load_manual_links()
        blacklist = load_blacklist()
        all_deals = []

        logger.info(f"--- Iniciando Ciclo #{cycle_count} (Total Enviado: {total_sent_session}) ---")

        # 0. PROCESSAR LINKS MANUAIS
        if manual_links:
            logger.info(f"Processando {len(manual_links)} links manuais...")
            for url in manual_links:
                try:
                    deal = None
                    if "mercadolivre.com.br" in url:
                        deal = await ml_scraper.fetch_product_details(url)
                    elif "amazon.com.br" in url:
                        deal = await amz_scraper.fetch_product_details(url)

                    if deal:
                        all_deals.append(deal)
                except Exception as e:
                    logger.error(f"Erro ao processar link manual {url}: {e}")
            clear_manual_links()

        # 1. MERCADO LIVRE (Prioridade Máxima)
        if cycle_count % ML_FREQUENCY == 0:
            logger.info("Busca no Mercado Livre...")
            try:
                deals = await ml_scraper.fetch_deals()
                all_deals.extend([d for d in deals if (d.discount_percentage or 0) >= MIN_DISCOUNT_GENERAL])
                for keyword in hot_keywords:
                    priority_deals = await ml_scraper.search_keyword(keyword)
                    all_deals.extend(priority_deals)
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Erro no ML: {e}")

        # 2. AMAZON
        if cycle_count % AMZ_FREQUENCY == 0:
            logger.info("Busca na Amazon...")
            try:
                deals = await amz_scraper.fetch_deals()
                all_deals.extend([d for d in deals if (d.discount_percentage or 0) >= MIN_DISCOUNT_GENERAL])
                if hot_keywords:
                    keyword = random.choice(hot_keywords)
                    priority_deals = await amz_scraper.search_keyword(keyword)
                    all_deals.extend(priority_deals)
            except Exception as e:
                logger.error(f"Erro na Amazon: {e}")

        # 3. SHOPEE
        if cycle_count % SHP_FREQUENCY == 0:
            logger.info("Busca na Shopee...")
            try:
                deals = await shp_scraper.fetch_deals()
                all_deals.extend([d for d in deals if (d.discount_percentage or 0) >= MIN_DISCOUNT_GENERAL])
            except Exception as e:
                logger.error(f"Erro na Shopee: {e}")

        # 4. Processar e Notificar
        if all_deals:
            unique_deals = {}
            for d in all_deals:
                if d.url not in unique_deals or (d.discount_percentage or 0) > (unique_deals[d.url].discount_percentage or 0):
                    unique_deals[d.url] = d

            final_list = list(unique_deals.values())

            # Ordenação de prioridade
            def priority_score(d):
                is_hot = any(k.lower() in d.title.lower() for k in hot_keywords)
                discount = d.discount_percentage or 0
                return (is_hot, discount)

            final_list.sort(key=priority_score, reverse=True)

            new_deals_count = 0
            for deal in final_list:
                # FILTRO 1: Blacklist
                if is_blacklisted(deal.title, blacklist):
                    logger.info(f"Produto ignorado (Blacklist): {deal.title}")
                    total_blacklisted_session += 1
                    continue

                # FILTRO 2: Validação de Preço / Duplicidade
                if db.is_deal_sent(deal.url, deal.price):
                    continue

                # Gerar link e tags
                deal.affiliate_url = affiliate_gen.generate(deal.url, deal.store)
                hashtags = get_category_hashtags(deal.title)

                await notifier.send_deal(deal, hashtags)
                db.add_sent_deal(deal)
                new_deals_count += 1
                total_sent_session += 1
                await asyncio.sleep(5)

            logger.info(f"Ciclo finalizado. {new_deals_count} novas ofertas enviadas.")

        # 5. Relatório de Status Periódico
        if cycle_count % REPORT_FREQUENCY == 0:
            stats = {
                "cycles": cycle_count,
                "sent": total_sent_session,
                "blacklisted": total_blacklisted_session,
                "total_db": db.get_total_count()
            }
            await notifier.send_status_report(stats)

        logger.info("Aguardando 30 minutos para o próximo ciclo...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot parado pelo usuário.")
