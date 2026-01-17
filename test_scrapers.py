import asyncio
import sys
from scrapers.mercadolivre import MercadoLivreScraper
from scrapers.amazon import AmazonScraper
from scrapers.shopee import ShopeeScraper

async def test_mercadolivre():
    print("\n--- Testing Mercado Livre Scraper ---")
    scraper = MercadoLivreScraper()
    deals = await scraper.fetch_deals()
    for deal in deals[:3]:
        print(f"Title: {deal.title}")
        print(f"Price: R$ {deal.price}")
        print(f"Discount: {deal.discount_percentage}%")
        print(f"URL: {deal.url}")
        print("-" * 20)
    print(f"Total deals found: {len(deals)}")

async def test_amazon():
    print("\n--- Testing Amazon Scraper ---")
    scraper = AmazonScraper()
    deals = await scraper.fetch_deals()
    for deal in deals[:3]:
        print(f"Title: {deal.title}")
        print(f"Price: R$ {deal.price}")
        print(f"Discount: {deal.discount_percentage}%")
        print(f"URL: {deal.url}")
        print("-" * 20)
    print(f"Total deals found: {len(deals)}")

async def test_shopee():
    print("\n--- Testing Shopee Scraper ---")
    scraper = ShopeeScraper()
    deals = await scraper.fetch_deals()
    for deal in deals[:3]:
        print(f"Title: {deal.title}")
        print(f"Price: R$ {deal.price}")
        print(f"Discount: {deal.discount_percentage}%")
        print(f"URL: {deal.url}")
        print("-" * 20)
    print(f"Total deals found: {len(deals)}")

async def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
        if choice == "ml":
            await test_mercadolivre()
        elif choice == "amazon":
            await test_amazon()
        elif choice == "shopee":
            await test_shopee()
        else:
            print("Invalid choice. Use: ml, amazon, or shopee")
    else:
        print("Running all tests...")
        await test_mercadolivre()
        await test_amazon()
        await test_shopee()

if __name__ == "__main__":
    asyncio.run(main())
