import asyncio
import json
import sys
import os
sys.path.append(os.getcwd())

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

async def debug_product():
    cookies_path = "cookies.json"
    # An example product URL (can be any active ML product)
    # Using one found in previous logs or a generic one. 
    # Let's use the one from the log:
    url = "https://www.mercadolivre.com.br/impressora-multifuncional-cor-epson-ecotank-l3250/p/MLB34229008"
    
    if not os.path.exists(cookies_path):
        print("Cookies not found")
        return

    with open(cookies_path, 'r', encoding='utf-8') as f:
        cookies = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Load cookies
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
            if 'expirationDate' in c:
                cookie['expires'] = c['expirationDate']
            clean_cookies.append(cookie)
        
        await context.add_cookies(clean_cookies)
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        print(f"Accessing product page: {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Navigation warning: {e}")

        # Wait a bit for potential toolbar dynamic load
        await asyncio.sleep(8)

        # Helper to find the toolbar
        print("\n--- TOOLBAR / HEADER HTML ---\n")
        # The affiliate toolbar usually sits at the top or bottom
        # Let's dump the body to a file? No, too big.
        # Let's search for "Compartilhar" text
        
        element = await page.query_selector("text=Compartilhar")
        if element:
            print("Found 'Compartilhar' element!")
            html = await element.evaluate("el => el.parentElement.outerHTML")
            print(html)
            
            # Try to click it to see the modal
            try:
                await element.click()
                print("Clicked 'Compartilhar'. Waiting for modal...")
                await asyncio.sleep(3)
                
                # Dump modal content
                # Look for "Link do produto" or the input
                modal_input = await page.query_selector("input[value*='mercadolivre.com/sec/']")
                if modal_input:
                    val = await modal_input.get_attribute("value")
                    print(f"FOUND LINK: {val}")
                else:
                     print("Could not find input with /sec/ link.")
                     # Dump general modal content
                     dialog = await page.query_selector("div[role='dialog']")
                     if dialog:
                         print(await dialog.inner_html())
            except Exception as e:
                print(f"Error interacting: {e}")
        else:
            print("'Compartilhar' button not found.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_product())
