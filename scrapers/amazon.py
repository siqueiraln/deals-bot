import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth
from bs4 import BeautifulSoup
from models.deal import Deal
from typing import List
import re

class AmazonScraper:
    def __init__(self):
        # Amazon Brazil deals page
        self.base_url = "https://www.amazon.com.br/gp/goldbox"

    async def fetch_deals(self) -> List[Deal]:
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Use a realistic context
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            await stealth(page)

            print(f"Fetching deals from {self.base_url}...")
            try:
                # Use a more stealthy approach
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)

                # Wait for some content to appear, doesn't have to be the full grid yet
                try:
                    await page.wait_for_selector("[data-testid='grid-deals-container']", timeout=15000)
                except:
                    # Fallback: maybe it's a different version of the page
                    await page.wait_for_selector(".s-result-item, .octopus-dlp-asin-section", timeout=10000)

                # Human-like scrolling
                for _ in range(5):
                    await page.mouse.wheel(0, 500)
                    await asyncio.sleep(0.5)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # Amazon deals are often in cards with specific data attributes
                items = soup.select("[data-testid='deal-card']")
                print(f"Found {len(items)} items on Amazon.")

                for item in items:
                    try:
                        title_el = item.select_one("[data-testid='deal-card-title']")
                        title = title_el.get_text(strip=True) if title_el else "No title"

                        # Amazon price structure can be complex (deal price vs list price)
                        price_el = item.select_one(".a-price-whole")
                        fraction_el = item.select_one(".a-price-fraction")

                        if price_el:
                            price_str = price_el.get_text(strip=True).replace('.', '')
                            fraction_str = fraction_el.get_text(strip=True) if fraction_el else "00"
                            price = float(f"{price_str}.{fraction_str}")
                        else:
                            continue # Skip if no price found

                        # Extract discount
                        discount_el = item.select_one(".a-badge-text") # e.g., "20% de desconto"
                        discount = None
                        if discount_el:
                            discount_text = discount_el.get_text(strip=True)
                            discount_match = re.search(r'(\d+)%', discount_text)
                            if discount_match:
                                discount = int(discount_match.group(1))

                        link_el = item.select_one("a.a-link-normal")
                        url = link_el['href'] if link_el else ""
                        if url and not url.startswith("http"):
                            url = "https://www.amazon.com.br" + url

                        img_el = item.select_one("img")
                        image_url = img_el['src'] if img_el else None

                        deals.append(Deal(
                            title=title,
                            price=price,
                            discount_percentage=discount,
                            url=url,
                            store="Amazon",
                            image_url=image_url
                        ))
                    except Exception as e:
                        print(f"Error parsing Amazon item: {e}")
                        continue

            except Exception as e:
                print(f"Failed to fetch Amazon deals: {e}")

            await browser.close()
        return deals

    async def fetch_product_details(self, url: str) -> Optional[Deal]:
        """Fetch details for a single Amazon product URL"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await stealth(page)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector("#productTitle", timeout=15000)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                title_el = soup.select_one("#productTitle")
                title = title_el.get_text(strip=True) if title_el else "No title"

                price_whole = soup.select_one(".a-price-whole")
                price_fraction = soup.select_one(".a-price-fraction")
                if price_whole:
                    price_str = price_whole.get_text(strip=True).replace('.', '').replace(',', '.')
                    if price_fraction:
                        price_str += price_fraction.get_text(strip=True)
                    price = float(re.sub(r'[^\d.]', '', price_str))
                else:
                    await browser.close()
                    return None

                img_el = soup.select_one("#landingImage")
                image_url = img_el['src'] if img_el else None

                await browser.close()
                return Deal(
                    title=title,
                    price=price,
                    url=url,
                    store="Amazon",
                    image_url=image_url
                )
            except Exception as e:
                print(f"Error fetching Amazon product details: {e}")
                await browser.close()
                return None

    async def search_keyword(self, keyword: str) -> List[Deal]:
        """Search for a specific keyword on Amazon and return deals"""
        search_url = f"https://www.amazon.com.br/s?k={keyword.replace(' ', '+')}"
        deals = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await stealth(page)

            print(f"Searching Amazon for: {keyword}...")
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_selector(".s-result-item", timeout=15000)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                items = soup.select(".s-result-item[data-component-type='s-search-result']")

                for item in items:
                    try:
                        # Amazon search results often have a "Oferta do Dia" or price drop
                        # Check for discount indicators
                        discount_el = item.select_one(".a-badge-text") or item.select_one(".a-letter-space + span")

                        title_el = item.select_one("h2 a span")
                        title = title_el.get_text(strip=True) if title_el else "No title"

                        price_whole = item.select_one(".a-price-whole")
                        if not price_whole:
                            continue

                        price_str = price_whole.get_text(strip=True).replace('.', '').replace(',', '.')
                        price = float(re.sub(r'[^\d.]', '', price_str))

                        link_el = item.select_one("h2 a")
                        url = "https://www.amazon.com.br" + link_el['href'] if link_el else ""

                        img_el = item.select_one("img.s-image")
                        image_url = img_el['src'] if img_el else None

                        # Only add if it's likely a deal (Amazon doesn't always show % in search results)
                        # but we can filter by keyword match
                        deals.append(Deal(
                            title=title,
                            price=price,
                            url=url,
                            store="Amazon",
                            image_url=image_url
                        ))
                    except:
                        continue
            except Exception as e:
                print(f"Amazon search error for {keyword}: {e}")

            await browser.close()
        return deals
