import asyncio
import os
from dotenv import load_dotenv
from services.copywriter import Copywriter
from models.deal import Deal

async def test():
    load_dotenv()
    print("--- Diagnostic Start ---")
    key = os.getenv("GEMINI_API_KEY")
    print(f"API Key present: {bool(key)}")
    if key:
        print(f"API Key start: {key[:5]}...")
    
    cw = Copywriter()
    print(f"Model configured: {cw.model_name}")
    
    deal = Deal(
        title="Smartphone Samsung Galaxy S23 Ultra 5G 256GB",
        price=4500.00,
        url="http://example.com/s23",
        store="Mercado Livre"
    )
    
    print("Attempting generation...")
    try:
        result = await cw.generate_caption(deal)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Top Level Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
