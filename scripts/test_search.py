
import asyncio
import sys
import os

# Add root dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scrapers.mercadolivre_search import MercadoLivreSearchScraper

async def test_search():
    scraper = MercadoLivreSearchScraper()
    
    keyword = "creatina growth"
    print(f"--- Testando busca por: '{keyword}' ---")
    
    deals = await scraper.search_keyword(keyword, max_results=5)
    
    print(f"\n✅ Encontradas {len(deals)} ofertas:")
    for deal in deals:
        print(f"- {deal.title} | R$ {deal.price:.2f}")
        print(f"  URL: {deal.url[:60]}...")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_search())
