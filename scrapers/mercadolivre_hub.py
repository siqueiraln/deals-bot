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

                for card in cards:
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
                            store="Mercado Livre Hub",
                            image_url=image_url
                        )
                        deal.discount_percentage = commission_percent if is_extra_commission else 0
                        
                        # Affiliate Link Generation (Automated)
                        # Only generate for valid deals that we are going to use
                        if deal.url.startswith("http"): # Ensure valid URL
                            try:
                                print(f"   Generating affiliate link for: {deal.title[:30]}...")
                                affiliate_link = await self._get_affiliate_link(page, deal.url)
                                if affiliate_link:
                                    deal.url = affiliate_link
                                    print(f"   ✅ Link generated: {deal.url}")
                                else:
                                    print("   ⚠️ Failed to generate link.")
                            except Exception as e:
                                print(f"   ❌ Error generating link: {e}")

                        deals.append(deal)

                    except Exception as e:
                        print(f"Error parsing hub item: {e}")
                        continue

            except Exception as e:
                print(f"Error scraping Hub: {e}")
                import traceback
                traceback.print_exc()

            await browser.close()
        return deals

    async def _get_affiliate_link(self, page, product_url):
        """Navigates to product page and uses the toolbar to generate an affiliate link."""
        try:
            # Open new page or use existing? 
            # We are in a loop, reusing 'page' might lose the Hub context.
            # Best to open a new tab/page.
            new_page = await page.context.new_page()
            
            # Stealth already applied to context? Yes, context has stealth.
            # But let's be safe
            stealth = Stealth()
            await stealth.apply_stealth_async(new_page)

            await new_page.goto(product_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(4) # Wait for toolbar

            # Click "Compartilhar"
            share_btn = await new_page.query_selector("text=Compartilhar")
            if not share_btn:
                print("   ❌ 'Compartilhar' button not found.")
                # Maybe dump page title to see if we are on the right page
                print(f"   Current Title: {await new_page.title()}")
                await new_page.close()
                return None
            
            # Use JS click to bypass overlays/interceptors
            print("   Clicking 'Compartilhar' via JS...")
            await new_page.evaluate("el => el.click()", share_btn)
            
            # Wait for modal input with the link
            try:
                # Wait for ANY text field in a dialog
                await new_page.wait_for_selector("div[role='dialog'] input", timeout=10000)
                print("   Modal dialog detected.")
            except:
                print("   ❌ Modal did not appear after JS click.")
                await new_page.close()
                return None
            
            # Allow time for API to fetch link inside the modal
            await asyncio.sleep(3)
            
            # Try to find input with value containing 'mercadolivre.com/sec/'
            # Strategy 1: Check inputs (failed previously, but keeping as fallback)
            inputs = await new_page.query_selector_all("div[role='dialog'] input")
            for inp in inputs:
                val = await inp.get_attribute("value")
                if val and "/sec/" in val:
                    print(f"   ✨ Found link in INPUT: {val}")
                    await new_page.close()
                    return val

            # Strategy 2: Check Textarea "Texto sugerido" (User suggestion)
            textareas = await new_page.query_selector_all("div[role='dialog'] textarea")
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
                    await new_page.close()
                    return link
            
            # Strategy 3: Check generic text content of the dialog
            dialog = await new_page.query_selector("div[role='dialog']")
            if dialog:
                full_text = await dialog.inner_text()
                match = re.search(r"https://(?:www\.)?mercadolivre\.com(?:\.br)?/sec/[\w]+", full_text)
                if match:
                    link = match.group(0)
                    print(f"   ✨ Found link in DIALOG TEXT: {link}")
                    await new_page.close()
                    return link

            print("   ❌ No SEC link found in modal.")
            await new_page.close()
            return None

        except Exception as e:
            print(f"   ❌ Link generation error: {e}")
            try: await new_page.close()
            except: pass
            return None

        except Exception as e:
            print(f"   Link generation error: {e}")
            try: await new_page.close()
            except: pass
            return None

if __name__ == "__main__":
    scraper = MercadoLivreHubScraper()
    deals = asyncio.run(scraper.fetch_my_deals())
    for d in deals:
        print(f"HUB DEAL: {d.title} | {d.price}")
