import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from models.trending_term import TrendingTerm
import logging

# Configure logger
logger = logging.getLogger(__name__)

class MercadoLivreTrendsScraper:
    def __init__(self, cache_file="data/trends_cache.json"):
        self.trends_url = "https://tendencias.mercadolivre.com.br/"
        self.cache_file = cache_file
        self.cache_ttl_hours = 6
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

    async def get_cached_trends(self) -> List[TrendingTerm]:
        """Returns trends from cache if valid, otherwise scrapes new ones."""
        if self._is_cache_valid():
            logger.info("♻️ Loading trends from cache...")
            return self._load_cache()
        
        logger.info("🔄 Cache expired or missing. Fetching new trends...")
        return await self.fetch_trending_terms()

    async def fetch_trending_terms(self) -> List[TrendingTerm]:
        """Scrapes trending terms from Mercado Livre."""
        trends = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Apply Stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            try:
                logger.info(f"Visiting {self.trends_url}...")
                await page.goto(self.trends_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3) # Wait for dynamic content

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # 1. Scrape Main Page Carousels
                # Carousels: "As buscas que mais cresceram", "As buscas mais desejadas", etc.
                # Structure: h2 (title) -> div (carousel) -> a.ui-search-entry-container
                
                carousels = soup.select(".ui-recommendations-carousel-container")
                if not carousels:
                     # Fallback for different layout or specific selectors found in analysis
                     # Found in analysis: "Ranking/Label", "Trending Term" inside .ui-search-entry-container
                     pass

                # Strategy based on identified selectors:
                # Items are 'a.ui-search-entry-container' or similar.
                # Let's look for specific sections manually if the container class varies.
                
                # "As buscas que mais cresceram" usually usually has a distinctive header/wrapper
                # Let's try a generic approach grabbing all visible trends on main page
                
                trend_items = soup.select("a.ui-search-entry-container")
                if not trend_items:
                    # Retry with the other selector found in analysis or common variations
                    trend_items = soup.select(".andes-carousel-snapped__slide a")
                
                logger.info(f"Found {len(trend_items)} potential trend items on main page.")

                for i, item in enumerate(trend_items):
                    try:
                        # Extract Term
                        term_el = item.select_one("h3") or item.select_one(".ui-search-entry__title")
                        if not term_el: continue
                        term = term_el.get_text(strip=True)
                        
                        # Extract URL
                        url = item.get('href', '')
                        if not url.startswith('http'):
                            url = f"https://lista.mercadolivre.com.br{url}"

                        # Extract Rank (if present)
                        rank = i + 1
                        rank_el = item.select_one(".ui-search-entry__position") # Hypothetical
                        
                        # Simple categorization for now based on page position is hard without strict container context
                        # We will assume "General" for main page items unless we parse headers
                        category = "Geral"
                        trend_type = "Popular" 

                        # Look for section header
                        # This is tricky with flat list, but let's just grab high value terms
                        
                        trends.append(TrendingTerm(
                            term=term,
                            category=category,
                            trend_type=trend_type,
                            rank=rank,
                            url=url
                        ))
                    except Exception as e:
                        logger.warning(f"Error parsing trend item: {e}")

                # 2. Scrape Top Categories (Optional but recommended in plan)
                # Let's stick to main page first to ensure speed, as per request for "low resource usage"
                # If main page yields ~50 items, that's a good start.

                if trends:
                    self._save_cache(trends)
                    logger.info(f"✅ Successfully scraped {len(trends)} trends.")
                else:
                    logger.warning("⚠️ No trends found. Check selectors.")

            except Exception as e:
                logger.error(f"Error scraping trends: {e}")
            finally:
                await browser.close()
        
        return trends

    def _is_cache_valid(self) -> bool:
        if not os.path.exists(self.cache_file):
            return False
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            last_updated = datetime.fromisoformat(data['last_updated'])
            expiration = last_updated + timedelta(hours=self.cache_ttl_hours)
            
            return datetime.now() < expiration
        except Exception:
            return False

    def _load_cache(self) -> List[TrendingTerm]:
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return [TrendingTerm(**t) for t in data['trends']]
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return []

    def _save_cache(self, trends: List[TrendingTerm]):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "trends": [t.__dict__ for t in trends]
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    scraper = MercadoLivreTrendsScraper()
    asyncio.run(scraper.get_cached_trends())
