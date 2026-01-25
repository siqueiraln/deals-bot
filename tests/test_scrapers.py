import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from scrapers.mercadolivre_search import MercadoLivreSearchScraper
from scrapers.mercadolivre_trends import MercadoLivreTrendsScraper

async def test_scrapers():
    keyword = "iphone"
    print(f"🔍 Iniciando teste de scrapers ML-Only...\n")

    # Teste Busca Anônima (Search)
    try:
        print("------- MERCADO LIVRE (BUSCA ANÔNIMA) -------")
        print(f"Buscando por '{keyword}'...")
        ml_search = MercadoLivreSearchScraper()
        deals = await ml_search.search_keyword(keyword, max_results=3)
        print(f"✅ Sucesso! Encontrados: {len(deals)} ofertas.")
        if deals:
            print(f"   Exemplo: {deals[0].title[:50]}... | R$ {deals[0].price}")
            print(f"   URL: {deals[0].url[:60]}...")
    except Exception as e:
        print(f"❌ Falha na Busca Anônima: {e}")

    # Teste Trends
    try:
        print("\n------- MERCADO LIVRE (TRENDS) -------")
        print("Buscando tendências...")
        ml_trends = MercadoLivreTrendsScraper()
        trends = await ml_trends.get_cached_trends()
        print(f"✅ Sucesso! Encontrados: {len(trends)} tendências.")
        if trends:
            print(f"   Top 3: {[t.term for t in trends[:3]]}")
    except Exception as e:
        print(f"❌ Falha nos Trends: {e}")

    # Teste Hub (Opcional)
    # try:
    #     print("\n------- MERCADO LIVRE HUB (Authenticated) -------")
    #     from scrapers.mercadolivre_hub import MercadoLivreHubScraper
    #     # ... (código existente mantido comentado se desejar ou removido para limpeza total)
    # except Exception as e:
    #     pass

if __name__ == "__main__":
    asyncio.run(test_scrapers())
