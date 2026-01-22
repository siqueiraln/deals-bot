import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
from models.deal import Deal
from typing import List
import re

class MercadoLivreScraper:
    def __init__(self):
        self.base_url = "https://www.mercadolivre.com.br/ofertas"

    async def fetch_deals(self) -> List[Deal]:
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            # Set user agent to avoid basic detection
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            })

            print(f"Fetching deals from {self.base_url}...")
            await page.goto(self.base_url, wait_until="networkidle")

            # Wait for the deals container - using a more robust selector or multiple attempts
            try:
                await page.wait_for_selector(".promotion-item", timeout=10000)
            except:
                print("Primary selector failed, trying secondary selectors...")
                # Try generic selectors if the specific one fails
                selectors = [".poly-component", "[data-testid='poly-card']", ".andes-card"]
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        print(f"Found items with selector: {selector}")
                        break
                    except:
                        continue

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Try different selectors for items based on ML's frequent changes
            items = soup.select(".promotion-item") or soup.select(".poly-card") or soup.select(".poly-component")
            print(f"Found {len(items)} items.")

            for item in items:
                try:
                    # Title
                    title_el = item.select_one(".promotion-item__title") or item.select_one(".poly-component__title") or item.select_one("a")
                    title = title_el.get_text(strip=True) if title_el else "No title"

                    # Price
                    price_container = item.select_one(".andes-money-amount--current") or item.select_one(".poly-price__current")
                    if price_container:
                        fraction = price_container.select_one(".andes-money-amount__fraction")
                        cents = price_container.select_one(".andes-money-amount__cents")

                        if fraction:
                            price_str = fraction.get_text(strip=True).replace(".", "")
                            if cents:
                                price_str += "." + cents.get_text(strip=True)
                            price = float(price_str)
                        else:
                            # Fallback to old method
                            price_text = price_container.get_text(strip=True)
                            clean_text = re.sub(r'[^\d,]', '', price_text)
                            if ',' in clean_text:
                                price = float(clean_text.replace('.', '').replace(',', '.'))
                            else:
                                price = float(clean_text)
                    else:
                        continue

                    # Old Price
                    old_price = None
                    old_price_el = item.select_one(".promotion-item__oldprice") or item.select_one(".poly-price__comparison")
                    if old_price_el:
                        old_price_text = old_price_el.get_text(strip=True)
                        old_price_numbers = re.sub(r'[^\d,]', '', old_price_text).replace(',', '.')
                        if old_price_numbers:
                            old_price = float(old_price_numbers)

                    # Discount
                    discount_el = item.select_one(".promotion-item__discount-text") or item.select_one(".poly-price__discount") or item.select_one(".andes-money-amount__discount")
                    discount = None
                    if discount_el:
                        discount_text = discount_el.get_text(strip=True)
                        discount_match = re.search(r'(\d+)%', discount_text)
                        if discount_match:
                            discount = int(discount_match.group(1))

                    # URL
                    link_el = item.select_one("a.promotion-item__link-container") or item.select_one("a")
                    if not link_el or 'href' not in link_el.attrs:
                        continue
                    url = link_el['href']
                    if not url.startswith("http"):
                        url = "https://www.mercadolivre.com.br" + url

                    # Image
                    img_el = item.select_one("img")
                    image_url = None
                    if img_el:
                        image_url = img_el.get('src') or img_el.get('data-src') or img_el.get('data-lazy')

                    deals.append(Deal(
                        title=title,
                        price=price,
                        original_price=old_price,
                        discount_percentage=discount,
                        url=url,
                        store="Mercado Livre",
                        image_url=image_url
                    ))
                except Exception as e:
                    print(f"Error parsing item: {e}")
                    continue

            await browser.close()
        return deals

    async def fetch_product_details(self, url: str) -> Optional[Deal]:
        """Fetch details for a single product URL"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            })

            try:
                await page.goto(url, wait_until="networkidle")
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                title_el = soup.select_one(".ui-pdp-title")
                title = title_el.get_text(strip=True) if title_el else "No title"

                price_container = soup.select_one(".andes-money-amount--current")
                if price_container:
                    fraction = price_container.select_one(".andes-money-amount__fraction")
                    cents = price_container.select_one(".andes-money-amount__cents")
                    price_str = fraction.get_text(strip=True).replace(".", "") if fraction else "0"
                    if cents:
                        price_str += "." + cents.get_text(strip=True)
                    price = float(price_str)
                else:
                    await browser.close()
                    return None

                discount_el = soup.select_one(".andes-money-amount__discount")
                discount = None
                if discount_el:
                    discount_text = discount_el.get_text(strip=True)
                    discount_match = re.search(r'(\d+)%', discount_text)
                    discount = int(discount_match.group(1)) if discount_match else None

                img_el = soup.select_one(".ui-pdp-gallery__figure img")
                image_url = img_el.get('src') or img_el.get('data-src') if img_el else None

                await browser.close()
                return Deal(
                    title=title,
                    price=price,
                    discount_percentage=discount,
                    url=url,
                    store="Mercado Livre",
                    image_url=image_url
                )
            except Exception as e:
                print(f"Error fetching ML product details: {e}")
                await browser.close()
                return None

    async def search_keyword(self, keyword: str) -> List[Deal]:
        """Search for a specific keyword and return deals (items with discounts)"""
        search_url = f"https://lista.mercadolivre.com.br/{keyword.replace(' ', '-')}_OrderId_PRICE_ASC"
        deals = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            })

            print(f"Searching Mercado Livre for: {keyword}...")
            await page.goto(search_url, wait_until="networkidle")

            try:
                # Wait for items
                await page.wait_for_selector(".ui-search-result", timeout=10000)
            except:
                await browser.close()
                return []

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            items = soup.select(".ui-search-result")

            for item in items:
                try:
                    # Check if it has a discount - look for the discount badge
                    discount_el = item.select_one(".ui-search-price__discount") or item.select_one(".andes-money-amount__discount")
                    if not discount_el:
                        continue # Only take products on sale

                    title_el = item.select_one(".ui-search-item__title")
                    title = title_el.get_text(strip=True) if title_el else "No title"

                    # Price
                    price_container = item.select_one(".andes-money-amount--current")
                    if price_container:
                        fraction = price_container.select_one(".andes-money-amount__fraction")
                        cents = price_container.select_one(".andes-money-amount__cents")
                        price_str = fraction.get_text(strip=True).replace(".", "") if fraction else "0"
                        if cents:
                            price_str += "." + cents.get_text(strip=True)
                        price = float(price_str)
                    else:
                        continue

                    url_el = item.select_one("a.ui-search-link")
                    url = url_el['href'] if url_el else ""
                    if not url.startswith("http"):
                        url = "https://www.mercadolivre.com.br" + url

                    discount_text = discount_el.get_text(strip=True)
                    discount_match = re.search(r'(\d+)%', discount_text)
                    discount = int(discount_match.group(1)) if discount_match else None

                    img_el = item.select_one("img.ui-search-result-image__element")
                    image_url = img_el.get('src') or img_el.get('data-src')

                    deals.append(Deal(
                        title=title,
                        price=price,
                        discount_percentage=discount,
                        url=url,
                        store="Mercado Livre",
                        image_url=image_url
                    ))
                except:
                    continue

            await browser.close()
        return deals
