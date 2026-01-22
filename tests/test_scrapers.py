import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from scrapers.mercadolivre import MercadoLivreScraper
from scrapers.amazon import AmazonScraper
from scrapers.shopee import ShopeeScraper

async def test_scrapers():
    keyword = "iphone"
    print(f"🔍 Iniciando teste de scrapers para o termo: '{keyword}'\n")

    # teste Mercado Livre
    try:
        print("------- MERCADO LIVRE -------")
        print("Inicializando scraper com Stealth...")
        ml = MercadoLivreScraper()
        deals = await ml.search_keyword(keyword)
        print(f"✅ Sucesso! Encontrados: {len(deals)} ofertas.")
        if deals:
            print(f"   Exemplo: {deals[0].title[:50]}... | R$ {deals[0].price}")
    except Exception as e:
        print(f"❌ Falha no Mercado Livre: {e}")

    # teste Amazon
    try:
        print("\n------- AMAZON -------")
        print("Inicializando scraper...")
        amz = AmazonScraper()
        deals = await amz.search_keyword(keyword)
        print(f"✅ Sucesso! Encontrados: {len(deals)} ofertas.")
        if deals:
             print(f"   Exemplo: {deals[0].title[:50]}... | R$ {deals[0].price}")
    except Exception as e:
         print(f"❌ Falha na Amazon: {e}")

    # Teste Shopee
    try:
        print("\n------- SHOPEE -------")
        print("Inicializando scraper...")
        shp = ShopeeScraper()
        deals = await shp.search_keyword(keyword)
        print(f"✅ Sucesso! Encontrados: {len(deals)} ofertas.")
        if deals:
             print(f"   Exemplo: {deals[0].title[:50]}... | R$ {deals[0].price}")
    except Exception as e:
        print(f"❌ Falha na Shopee: {e}")

    # Teste Mercado Livre Hub (Authenticated)
    try:
        print("\n------- MERCADO LIVRE HUB (Authenticated) -------")
        from scrapers.mercadolivre_hub import MercadoLivreHubScraper
        if os.path.exists("cookies.json"):
            print("Inicializando scraper do Hub com cookies...")
            ml_hub = MercadoLivreHubScraper()
            deals = await ml_hub.fetch_my_deals()
            print(f"✅ Sucesso! Encontrados: {len(deals)} ofertas no Hub.")
            if deals:
                print(f"   Exemplo: {deals[0].title[:50]}... | R$ {deals[0].price}")
        else:
            print("⚠️ cookies.json não encontrado. Pulando teste do Hub.")
    except Exception as e:
        print(f"❌ Falha no Mercado Livre Hub: {e}")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
