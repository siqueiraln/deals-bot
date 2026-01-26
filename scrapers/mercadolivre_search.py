
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from models.deal import Deal
import traceback
from config.logger import logger

class MercadoLivreSearchScraper:
    def __init__(self):
        self.base_url = "https://lista.mercadolivre.com.br/"

    async def search_keyword(self, keyword: str, max_results: int = 10) -> list[Deal]:
        """Busca produtos no ML usando uma palavra-chave."""
        deals = []
        search_url = f"{self.base_url}{keyword.replace(' ', '-')}_NoIndex_True#D[A:{keyword},on]"
        
        logger.info(f"🔍 Searching ML for: {keyword}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Carregar Cookies e User-Agent
                import os
                cookies_str = os.getenv("ML_COOKIES")
                if cookies_str:
                    cookies_list = []
                    for pair in cookies_str.split(";"):
                        if "=" in pair:
                            name, value = pair.strip().split("=", 1)
                            cookies_list.append({
                                "name": name, 
                                "value": value, 
                                "domain": ".mercadolivre.com.br", 
                                "path": "/"
                            })
                    if cookies_list:
                        await context.add_cookies(cookies_list)
                        logger.info(f"   🍪 Cookies injetados (Search): {len(cookies_list)}")

                # OTIMIZAÇÃO: Bloquear imagens e fontes para tornar o scraping mais leve e rápido
                await page.route("**/*.{png,jpg,jpeg,webp,gif,svg,woff,woff2,ttf,css}", lambda route: route.abort())

                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                logger.info(f"   Navigating to {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                
                # Check different result container types
                cards = []
                cards = await page.query_selector_all("li.ui-search-layout__item")
                if not cards:
                    cards = await page.query_selector_all("div.ui-search-result__wrapper")
                if not cards:
                    cards = await page.query_selector_all(".poly-card")
                
                logger.info(f"   Found {len(cards)} items (Search)")
                
                count = 0
                for card in cards:
                    if count >= max_results: break
                    
                    try:
                        deal = await self._extract_deal_from_card(card, keyword)
                        if deal:
                            deals.append(deal)
                            count += 1
                    except Exception as e:
                        logger.error(f"   Error parsing card: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Error searching for '{keyword}': {e}")
            finally:
                await browser.close()
                
        return deals

    async def scrape_category_url(self, category_url: str, max_results: int = 15) -> list[Deal]:
        """Busca produtos diretamente de uma URL de categoria."""
        deals = []
        logger.info(f"📂 Scraping Category URL: {category_url}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Carregar Cookies do .env
                import os
                cookies_str = os.getenv("ML_COOKIES")
                if cookies_str:
                    cookies_list = []
                    for pair in cookies_str.split(";"):
                        if "=" in pair:
                            name, value = pair.strip().split("=", 1)
                            # Adicionar para o domínio
                            cookies_list.append({
                                "name": name, 
                                "value": value, 
                                "domain": ".mercadolivre.com.br", 
                                "path": "/"
                            })
                    if cookies_list:
                        await context.add_cookies(cookies_list)
                        logger.info(f"   🍪 Cookies injetados: {len(cookies_list)}")

                # OTIMIZAÇÃO: Bloquear imagens e fontes para tornar o scraping mais leve e rápido
                await page.route("**/*.{png,jpg,jpeg,webp,gif,svg,woff,woff2,ttf,css}", lambda route: route.abort())

                # Use a simple user agent to avoid basic blocks
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                logger.info(f"   Navigating to {category_url}")
                await page.goto(category_url, wait_until="domcontentloaded", timeout=60000)
                
                # IMPORTANT: Wait for items to appear (hydration delay)
                try:
                    await page.wait_for_selector(".poly-card, .ui-search-layout__item, .promotion-item", timeout=15000)
                except:
                    logger.warning("   ⚠️ Timeout waiting for items selector (might be empty or slow).")

                # Scroll Logic to Load More Items (Infinite Scroll)
                scroll_cycles = max(5, int(max_results / 10)) # E.g., 100 items -> 10 scrolls
                if scroll_cycles > 25: scroll_cycles = 25 # Safety cap
                
                logger.info(f"   📜 Scrolling {scroll_cycles} times to find {max_results} items...")
                for _ in range(scroll_cycles): 
                    await page.keyboard.press("PageDown")
                    await asyncio.sleep(1.2) # Wait for load
                
                # Check different result container types (same as search)
                cards = []
                # Type 1: Poly Card (Priority)
                cards = await page.query_selector_all(".poly-card")
                # Type 2: Promotion Item (Common in Ofertas)
                if not cards:
                    cards = await page.query_selector_all(".promotion-item")
                # Type 3: Standard Search (Fallback)
                if not cards:
                    cards = await page.query_selector_all("li.ui-search-layout__item")
                # Type 4: Grid View
                if not cards:
                    cards = await page.query_selector_all("div.ui-search-result__wrapper")
                
                logger.info(f"   Items found after scroll: {len(cards)}")
                
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
                        logger.warning(f"   ⚠️ Skipping card due to error: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Error scraping category: {e}")
            finally:
                await browser.close()
                
        return deals

    async def _extract_deal_from_card(self, card, keyword) -> Deal:
        """Extrai dados de um card de produto usando Playwright."""
        
        # 4. Image (Get first to use Alt as Title fallback)
        img_el = await card.query_selector("img.ui-search-result-image__element, img.poly-component__picture, img.promotion-item__img")
        image_url = None
        alt_title = None
        if img_el:
            image_url = await img_el.get_attribute('data-src') or await img_el.get_attribute('src')
            alt_title = await img_el.get_attribute('alt')
        
        # 1. Title
        title = None
        title_el = await card.query_selector("h2.ui-search-item__title, .poly-component__title, .promotion-item__title")
        
        if title_el:
            title = await title_el.inner_text()
        
        # Fallback: Try 'a' tag plain text if specialized class missing
        if not title:
             link_text_el = await card.query_selector("a")
             if link_text_el:
                 text = await link_text_el.inner_text()
                 if len(text) > 10: title = text

        # Fallback 2: Use Image Alt
        if not title and alt_title:
            title = alt_title

        if not title: 
            logger.warning("   ⚠️ Item skipped: No Title found (Text or Alt)")
            return None

        # 2. URL
        link_el = await card.query_selector("a.ui-search-link, a.poly-component__title, a.promotion-item__link-container")
        
        # Fallback: Se o próprio card for um link ou container
        if not link_el:
             link_el = await card.query_selector("h2.ui-search-item__title a") 
        if not link_el:
             link_el = await card.query_selector("div.poly-card__content a")
        if not link_el:
             # Last resort: first 'a' tag in card
             link_el = await card.query_selector("a")

        if not link_el: 
            logger.warning(f"   ⚠️ Item skipped ({title[:15]}...): No Link Element found")
            return None
            
        url = await link_el.get_attribute('href')
        
        # EXTRACT PRODUCT ID (MLB-XXXXXXX)
        import re
        product_id = None
        if url:
            match = re.search(r'(MLB-?\d+)', url)
            if match:
                product_id = match.group(1)
        
        if not product_id:
            logger.warning(f"   ⚠️ Item skipped ({title[:15]}...): No ML Product ID found in URL")
            return None
        
        # CLEAN URL (Critical for DB Dedup)
        # Remove tracking params like ?tracking_id=...
        if url and "?" in url:
            url = url.split("?")[0]
        
        # 3. Price
        price_el = await card.query_selector(".poly-price__current .andes-money-amount__fraction")
        if not price_el:
            price_el = await card.query_selector("span.andes-money-amount__fraction")
            
        if not price_el: 
            logger.warning(f"   ⚠️ Item skipped ({title[:15]}...): No Price Element found")
            return None
            
        price_str = await price_el.inner_text()
        try:
             price = float(price_str.replace('.', '').replace(',', '.'))
        except:
            logger.warning(f"   ⚠️ Item skipped ({title[:15]}...): Price parse error '{price_str}'")
            return None
            
        # Create Deal
        deal = Deal(
            title=title,
            price=price,
            url=url,
            product_id=product_id,
            store="Mercado Livre",
            image_url=image_url
        )
        deal.discount_percentage = 0 
        
        return deal

