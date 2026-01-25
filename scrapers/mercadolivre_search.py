
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from models.deal import Deal
import traceback

class MercadoLivreSearchScraper:
    def __init__(self):
        self.base_url = "https://lista.mercadolivre.com.br/"

    async def search_keyword(self, keyword: str, max_results: int = 10) -> list[Deal]:
        """Busca produtos no ML usando uma palavra-chave."""
        deals = []
        search_url = f"{self.base_url}{keyword.replace(' ', '-')}_NoIndex_True#D[A:{keyword},on]"
        
        print(f"🔍 Searching ML for: {keyword}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Use a simple user agent to avoid basic blocks
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                print(f"   Navigating to {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                
                # Check different result container types
                cards = []
                # Type 1: Standard Search
                cards = await page.query_selector_all("li.ui-search-layout__item")
                # Type 2: Grid View
                if not cards:
                    cards = await page.query_selector_all("div.ui-search-result__wrapper")
                # Type 3: Poly Card (Modern)
                if not cards:
                    cards = await page.query_selector_all(".poly-card")
                
                print(f"   Found {len(cards)} potential items")
                
                count = 0
                for card in cards:
                    if count >= max_results: break
                    
                    try:
                        deal = await self._extract_deal_from_card(card, keyword)
                        if deal:
                            deals.append(deal)
                            count += 1
                    except Exception as e:
                        print(f"   Error parsing card: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Error searching for '{keyword}': {e}")
                # traceback.print_exc()
            finally:
                await browser.close()
                
        return deals

    async def scrape_category_url(self, category_url: str, max_results: int = 15) -> list[Deal]:
        """Busca produtos diretamente de uma URL de categoria."""
        deals = []
        print(f"📂 Scraping Category URL: {category_url}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                await page.goto(category_url, wait_until="domcontentloaded", timeout=60000)
                
                # Check different result container types (same as search)
                cards = []
                # Type 1: Standard Search
                cards = await page.query_selector_all("li.ui-search-layout__item")
                # Type 2: Grid View
                if not cards:
                    cards = await page.query_selector_all("div.ui-search-result__wrapper")
                # Type 3: Poly Card (Modern)
                if not cards:
                    cards = await page.query_selector_all(".poly-card")
                
                print(f"   category items found: {len(cards)}")
                
                count = 0
                for card in cards:
                    if count >= max_results: break
                    
                    try:
                        # Extract logic is same
                        deal = await self._extract_deal_from_card(card, "Category Volume")
                        if deal:
                            # Marcar estratégia para scoring
                            deal.strategy = "volume" 
                            deals.append(deal)
                            count += 1
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"❌ Error scraping category: {e}")
            finally:
                await browser.close()
                
        return deals

    async def _extract_deal_from_card(self, card, keyword) -> Deal:
        """Extrai dados de um card de produto usando Playwright."""
        
        # 1. Title
        title_el = await card.query_selector("h2.ui-search-item__title, .poly-component__title")
        if not title_el: return None
        title = await title_el.inner_text()
        
        # 2. URL
        link_el = await card.query_selector("a.ui-search-link, a.poly-component__title")
        if not link_el: return None
        url = await link_el.get_attribute('href')
        
        # 3. Price
        price_el = await card.query_selector("span.andes-money-amount__fraction")
        if not price_el: return None
        price_str = await price_el.inner_text()
        try:
             price = float(price_str.replace('.', '').replace(',', '.'))
        except:
            return None
            
        # 4. Image
        img_el = await card.query_selector("img.ui-search-result-image__element, img.poly-component__picture")
        image_url = None
        if img_el:
            image_url = await img_el.get_attribute('data-src') or await img_el.get_attribute('src')
        
        # Create Deal
        deal = Deal(
            title=title,
            price=price,
            url=url,
            store="Mercado Livre",
            image_url=image_url
        )
        deal.discount_percentage = 0 
        
        return deal
