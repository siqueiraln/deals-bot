import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup
from models.deal import Deal
from typing import List
import re

class ShopeeScraper:
    def __init__(self):
        # Shopee Brazil flash deals
        self.base_url = "https://shopee.com.br/flash_sale"

    async def fetch_deals(self) -> List[Deal]:
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            await stealth_async(page)

            print(f"Fetching deals from {self.base_url}...")
            try:
                # Shopee is very protective, might require cookies or human-like behavior
                await page.goto(self.base_url, wait_until="networkidle", timeout=60000)

                # Wait for flash sale items to appear
                # Shopee uses obfuscated classes, so we look for structural clues or text
                await page.wait_for_selector(".flash-sale-items", timeout=30000)

                # Scroll to trigger lazy loading
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(1)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # Shopee's DOM is complex. We try to find items inside the flash sale container
                items = soup.select(".flash-sale-item-card")
                print(f"Found {len(items)} items on Shopee.")

                for item in items:
                    try:
                        title_el = item.select_one(".flash-sale-item-card__item-name")
                        title = title_el.get_text(strip=True) if title_el else "No title"

                        # Price is often split into parts
                        price_el = item.select_one(".flash-sale-item-card__current-price")
                        if not price_el:
                            continue

                        price_text = price_el.get_text(strip=True)
                        # R$ 10,90 -> 10.90
                        price = float(re.sub(r'[^\d,]', '', price_text).replace(',', '.'))

                        discount_el = item.select_one(".flash-sale-item-card__discount-label")
                        discount = None
                        if discount_el:
                            discount_text = discount_el.get_text(strip=True)
                            discount_match = re.search(r'(\d+)%', discount_text)
                            if discount_match:
                                discount = int(discount_match.group(1))

                        link_el = item.select_one("a")
                        url = link_el['href'] if link_el else ""
                        if url and not url.startswith("http"):
                            url = "https://shopee.com.br" + url

                        img_el = item.select_one("img")
                        image_url = img_el['src'] if img_el else None

                        deals.append(Deal(
                            title=title,
                            price=price,
                            discount_percentage=discount,
                            url=url,
                            store="Shopee",
                            image_url=image_url
                        ))
                    except Exception as e:
                        print(f"Error parsing Shopee item: {e}")
                        continue

            except Exception as e:
                print(f"Failed to fetch Shopee deals: {e}")

            await browser.close()
        return deals

    async def search_keyword(self, keyword: str) -> List[Deal]:
        """Search for a specific keyword on Shopee and return deals"""
        search_url = f"https://shopee.com.br/search?keyword={keyword.replace(' ', '%20')}"
        deals = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            await stealth_async(page)

            print(f"Searching Shopee for: {keyword}...")
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=60000)

                # Wait for search results
                await page.wait_for_selector(".shopee-search-item-result__item", timeout=30000)

                # Scroll to load items
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(1)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                items = soup.select(".shopee-search-item-result__item")

                for item in items:
                    try:
                        title_el = item.select_one("[data-sqe='name']")
                        title = title_el.get_text(strip=True) if title_el else "No title"

                        # Price
                        price_el = item.select_one(".shopee-item-card__current-price") or item.select_one("span[class*='font-medium text-shopee-primary']")
                        if not price_el:
                            continue

                        price_text = price_el.get_text(strip=True)
                        price = float(re.sub(r'[^\d,]', '', price_text).replace(',', '.'))

                        # Discount
                        discount_el = item.select_one(".shopee-item-card__discount-label")
                        discount = None
                        if discount_el:
                            discount_text = discount_el.get_text(strip=True)
                            discount_match = re.search(r'(\d+)%', discount_text)
                            discount = int(discount_match.group(1)) if discount_match else None

                        link_el = item.select_one("a")
                        url = "https://shopee.com.br" + link_el['href'] if link_el else ""

                        img_el = item.select_one("img")
                        image_url = img_el['src'] if img_el else None

                        deals.append(Deal(
                            title=title,
                            price=price,
                            discount_percentage=discount,
                            url=url,
                            store="Shopee",
                            image_url=image_url
                        ))
                    except:
                        continue
            except Exception as e:
                print(f"Shopee search error for {keyword}: {e}")

            await browser.close()
        return deals

if __name__ == "__main__":
    scraper = ShopeeScraper()
    # Test search
    results = asyncio.run(scraper.search_keyword("cadeira gamer"))
    for d in results[:5]:
        print(f"Found: {d.title} - R${d.price} ({d.discount_percentage}% OFF)")
