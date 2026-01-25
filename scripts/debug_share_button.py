import asyncio
from playwright.async_api import async_playwright
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def debug_product_page():
    """Debug script to inspect ML product page and find Share button"""
    
    # Use a real product URL from the Hub
    test_url = "https://www.mercadolivre.com.br/tenis-masculino-feminino-kappa-park-20-original/p/MLB42858863"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser
        page = await browser.new_page()
        
        print(f"🔍 Navigating to: {test_url}")
        await page.goto(test_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(5)  # Wait for page to fully load
        
        print(f"📄 Page Title: {await page.title()}")
        
        # Try different selectors for Share button
        selectors_to_try = [
            "text=Compartilhar",
            "button:has-text('Compartilhar')",
            "[aria-label*='Compartilhar']",
            "[data-testid*='share']",
            ".andes-button:has-text('Compartilhar')",
            "//button[contains(text(), 'Compartilhar')]",
            "//a[contains(text(), 'Compartilhar')]",
        ]
        
        print("\n🔎 Testing selectors:")
        for selector in selectors_to_try:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    print(f"✅ FOUND: {selector} → '{text}'")
                else:
                    print(f"❌ NOT FOUND: {selector}")
            except Exception as e:
                print(f"❌ ERROR with {selector}: {e}")
        
        # Dump all buttons on the page
        print("\n📋 All buttons on page:")
        buttons = await page.query_selector_all("button")
        for i, btn in enumerate(buttons[:20]):  # Limit to first 20
            try:
                text = await btn.inner_text()
                if text.strip():
                    print(f"  Button {i}: '{text.strip()}'")
            except:
                pass
        
        print("\n⏸️ Browser will stay open for 30 seconds for manual inspection...")
        await asyncio.sleep(30)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_product_page())
