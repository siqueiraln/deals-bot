import asyncio
import json
import sys
import os
sys.path.append(os.getcwd())

from datetime import datetime
from typing import List, Optional
import re

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
from models.deal import Deal

class MercadoLivreHubScraper:
    def __init__(self, cookies_path="data/cookies.json"):
        self.cookies_path = cookies_path
        self.hub_url = "https://www.mercadolivre.com.br/afiliados/hub"

    def _load_cookies(self):
        if not os.path.exists(self.cookies_path):
            print(f"Cookie file not found at {self.cookies_path}")
            return []
        try:
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return []

    async def fetch_my_deals(self) -> List[Deal]:
        """Fetches deals specifically recommended in the Affiliate Hub"""
        deals = []
        cookies = self._load_cookies()
        
        if not cookies:
            print("No cookies available to access Affiliate Hub.")
            return []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1366, 'height': 768}
            )
            
            # Add cookies to context
            # Playwright expects 'sameSite' to be valid, sometimes extensions export incompatible values
            clean_cookies = []
            for c in cookies:
                cookie = {
                    'name': c['name'],
                    'value': c['value'],
                    'domain': c['domain'],
                    'path': c['path'],
                    'secure': c.get('secure', False),
                    'httpOnly': c.get('httpOnly', False),
                    'sameSite': 'Lax' if c.get('sameSite') not in ['Strict', 'Lax', 'None'] else c.get('sameSite')
                }
                # Date fields in cookie json might be float, Playwright handles it
                if 'expirationDate' in c:
                    cookie['expires'] = c['expirationDate']
                clean_cookies.append(cookie)
            
            try:
                await context.add_cookies(clean_cookies)
            except Exception as e:
                print(f"Error adding cookies: {e}")

            page = await context.new_page()
            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            print(f"Accessing Affiliate Hub: {self.hub_url}...")
            try:
                await page.goto(self.hub_url, wait_until="networkidle", timeout=60000)
                
                # Check if logged in (url shouldn't redirect to login)
                if "login" in page.url or "sso" in page.url:
                    print("⚠️ Login failed. Cookies might be expired.")
                    await browser.close()
                    return []

                # Wait for cards
                await page.wait_for_selector("div[class*='recommendations']", timeout=15000)

                # Scroll to load more
                await page.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(2)

                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # Identify sections (e.g., "Ganhos extras", "Mais vendidos")
                # The structure in the hub is usually a grid of cards
                # We will look for generic card structures
                
                # Use specific selectors for the Hub's poly-cards
                cards = soup.select(".poly-card")
                print(f"Found {len(cards)} items in Hub.")

                # Hybrid Strategy: Fetch 30 deals, generate affiliate links only for high-score ones
                deal_count = 0
                max_deals = 30

                for card in cards:
                    if deal_count >= max_deals:
                        print(f"⚠️ Limite de {max_deals} ofertas atingido")
                        break
                    try:
                        # Title and Link
                        title_el = card.select_one(".poly-component__title")
                        if not title_el: continue
                        title = title_el.get_text(strip=True)
                        href = title_el.get('href')
                        
                        if href and not href.startswith("http"):
                             url = "https://www.mercadolivre.com.br" + href
                        else:
                             url = href

                        # Price
                        price_el = card.select_one(".andes-money-amount__fraction")
                        if not price_el: continue
                        price_text = price_el.get_text(strip=True).replace('.', '')
                        price = float(price_text)

                        # Image
                        img_el = card.select_one(".poly-component__picture")
                        image_url = img_el['src'] if img_el else None

                        # Check for "Ganhos extras" or commission badge
                        is_extra_commission = False
                        commission_percent = 0
                        chip_el = card.select_one(".poly-component__chip")
                        if chip_el:
                            chip_text = chip_el.get_text(strip=True).lower()
                            # Example text: "ganhos extra 22%"
                            if "extra" in chip_text or "ganhos" in chip_text:
                                is_extra_commission = True
                                # Extract number
                                match = re.search(r"(\d+)", chip_text)
                                if match:
                                    commission_percent = int(match.group(1))

                        # User Request Filter: Only return deals with > 10% extra earnings
                        # If it's just "Mais vendido" without extra earnings, we keep it? 
                        # User said: "traga todos os produtos com ganhos extras acima de 10%"
                        # This implies we should ONLY return those with > 10% IF they are "ganhos extras".
                        # If it is NOT "ganhos extra" (e.g. just Mais Vendido), should we ignore?
                        # Let's be strict: if it has commission, it must be > 10. If it has NO commission info, maybe skip?
                        # The user found value in the "Ganhos extras".
                        
                        if is_extra_commission and commission_percent <= 10:
                            continue # Skip low commission deals

                        # Use the parsed data to create the Deal object
                        deal = Deal(
                            title=title,
                            price=price,
                            url=url,
                            store="Mercado Livre",
                            image_url=image_url
                        )
                        deal.discount_percentage = commission_percent if is_extra_commission else 0
                        
                        # NOTE: Affiliate link generation moved to main.py
                        # Only high-score deals (>= 40) will get affiliate links generated
                        # This saves ~4 seconds per low-score deal

                        deals.append(deal)
                        deal_count += 1  # Increment counter


                    except Exception as e:
                        print(f"Error parsing hub item: {e}")
                        continue

            except Exception as e:
                print(f"Error scraping Hub: {e}")
                import traceback
                traceback.print_exc()

            await browser.close()
        return deals

    async def generate_affiliate_link_for_deal(self, deal: Deal) -> Deal:
        """
        Generates affiliate link for a single deal that has already been scored.
        Updates deal.url, deal.store, and deal.original_price in-place.
        Returns the updated deal.
        
        This is called AFTER scoring to avoid wasting time on low-score deals.
        """
        if not deal.url.startswith("http"):
            return deal
        
        try:
            # Launch browser for this single operation
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                
                # Apply stealth
                stealth = Stealth()
                await stealth.apply_stealth_async(context)
                
                # Load and clean cookies (same as fetch_my_deals)
                if os.path.exists(self.cookies_path):
                    with open(self.cookies_path, 'r') as f:
                        cookies = json.load(f)
                        
                        # Clean cookies to avoid sameSite validation errors
                        clean_cookies = []
                        for c in cookies:
                            cookie = {
                                'name': c['name'],
                                'value': c['value'],
                                'domain': c['domain'],
                                'path': c['path'],
                                'secure': c.get('secure', False),
                                'httpOnly': c.get('httpOnly', False),
                                'sameSite': 'Lax' if c.get('sameSite') not in ['Strict', 'Lax', 'None'] else c.get('sameSite')
                            }
                            clean_cookies.append(cookie)
                        
                        await context.add_cookies(clean_cookies)
                
                page = await context.new_page()
                
                print(f"   🔗 Generating affiliate link for: {deal.title[:40]}...")
                affiliate_link, store_name, original_price = await self._get_affiliate_link(page, deal.url)
                
                if affiliate_link:
                    deal.url = affiliate_link
                    print(f"   ✅ Link generated successfully")
                else:
                    print("   ⚠️ Failed to generate link, using original URL")
                
                # Update store name if found
                if store_name:
                    deal.store = store_name
                
                # Update original price if found
                if original_price:
                    deal.original_price = original_price
                
                await browser.close()
        except Exception as e:
            print(f"   ❌ Error generating affiliate link: {e}")
        
        return deal

    async def _get_affiliate_link(self, page, product_url):
        """Navigates to product page and extracts: affiliate link, store name, and original price.
        Returns: (affiliate_link, store_name, original_price)
        """
        try:
            # IMPORTANT: Reuse the existing page that already has cookies
            # instead of creating a new one
            
            # Navigate to product page
            await page.goto(product_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(4) # Wait for toolbar

            # Extract store name and original price from product page
            store_name = None
            original_price = None
            
            try:
                # Get page content for parsing
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract store name - look for seller info
                # Try multiple selectors
                store_selectors = [
                    "a.ui-pdp-seller__link-trigger",  # Main seller link
                    ".ui-pdp-seller__header__title",   # Seller header
                    "p.ui-pdp-color--BLACK",           # Alternative
                ]
                for selector in store_selectors:
                    store_el = soup.select_one(selector)
                    if store_el:
                        # Use separator=' ' to avoid "Loja oficialBrand" concatenation
                        raw_store = store_el.get_text(separator=' ', strip=True)
                        
                        # Clean up "Loja oficial" prefix (case insensitive)
                        # We want just "CeraVe", not "Loja oficial CeraVe"
                        clean_name = re.sub(r'(?i)^loja\s*oficial\s*', '', raw_store).strip()
                        
                        if clean_name and len(clean_name) > 1:
                            store_name = clean_name.title() # Force Title Case
                            break
                
                # Extract original price (before discount)
                original_price_el = soup.select_one(".andes-money-amount--previous s")
                if original_price_el:
                    price_text = original_price_el.get_text(strip=True)
                    # Extract numbers only
                    price_match = re.search(r"([\d.]+)", price_text.replace('.', ''))
                    if price_match:
                        original_price = float(price_match.group(1))
                        print(f"   📊 Original price found: R$ {original_price:.2f}")
                
                if store_name:
                    print(f"   🏪 Store name found: {store_name}")
            except Exception as e:
                print(f"   ⚠️ Error extracting product details: {e}")

            # Click "Compartilhar"
            share_btn = await page.query_selector("text=Compartilhar")
            if not share_btn:
                print("   ❌ 'Compartilhar' button not found.")
                # Maybe dump page title to see if we are on the right page
                print(f"   Current Title: {await page.title()}")
                await page.close()
                return (None, store_name, original_price)
            
            # Use JS click to bypass overlays/interceptors
            print("   Clicking 'Compartilhar' via JS...")
            await page.evaluate("el => el.click()", share_btn)
            
            # Wait for modal input with the link
            try:
                # Wait for ANY text field in a dialog
                await page.wait_for_selector("div[role='dialog'] input", timeout=10000)
                print("   Modal dialog detected.")
            except:
                print("   ❌ Modal did not appear after JS click.")
                await page.close()
                return (None, store_name, original_price)
            
            # Allow time for API to fetch link inside the modal
            await asyncio.sleep(3)
            
            # Try to find input with value containing 'mercadolivre.com/sec/'
            # Strategy 1: Check inputs (failed previously, but keeping as fallback)
            inputs = await page.query_selector_all("div[role='dialog'] input")
            for inp in inputs:
                val = await inp.get_attribute("value")
                if val and "/sec/" in val:
                    print(f"   ✨ Found link in INPUT: {val}")
                    await page.close()
                    return (val, store_name, original_price)

            # Strategy 2: Check Textarea "Texto sugerido" (User suggestion)
            textareas = await page.query_selector_all("div[role='dialog'] textarea")
            print(f"   Found {len(textareas)} textareas in modal.")
            
            for ta in textareas:
                text = await ta.evaluate("el => el.value") # Textarea value property
                # print(f"   Textarea content: {text[:50]}...") 
                
                # Regex to find https://mercadolivre.com/sec/XXXXX
                # or https://www.mercadolivre.com/sec/XXXXX
                match = re.search(r"https://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[\w]+", text)
                if match:
                    link = match.group(0)
                    print(f"   ✨ Found link in TEXTAREA: {link}")
                    await page.close()
                    return (link, store_name, original_price)
            
            # Strategy 3: Check generic text content of the dialog
            dialog = await page.query_selector("div[role='dialog']")
            if dialog:
                full_text = await dialog.inner_text()
                match = re.search(r"https://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[\w]+", full_text)
                if match:
                    link = match.group(0)
                    print(f"   ✨ Found link in DIALOG TEXT: {link}")
                    await page.close()
                    return (link, store_name, original_price)

            print("   ❌ No SEC link found in modal.")
            await page.close()
            return (None, store_name, original_price)

        except Exception as e:
            print(f"   ❌ Link generation error: {e}")
            # traceback.print_exc()
            try: await page.close()
            except: pass
            return (None, None, None)
            
        return (None, None, None) # Emergency fallback

if __name__ == "__main__":
    scraper = MercadoLivreHubScraper()
    deals = asyncio.run(scraper.fetch_my_deals())
    for d in deals:
        print(f"HUB DEAL: {d.title} | {d.price}")
