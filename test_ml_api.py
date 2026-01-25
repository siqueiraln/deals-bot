import asyncio
import os
from dotenv import load_dotenv
from scrapers.mercadolivre_api import MercadoLivreAPI

load_dotenv()

async def test_api():
    print("🚀 Testando API do Mercado Livre...")
    
    tag = os.getenv("ML_AFFILIATE_TAG")
    cookies = os.getenv("ML_COOKIES")
    
    if not tag:
        print("❌ ML_AFFILIATE_TAG não encontrado no .env")
        return
    if not cookies:
        print("❌ ML_COOKIES não encontrado no .env")
        return
        
    print(f"✅ Tag encontrada: {tag}")
    print(f"✅ Cookies encontrados (tamanho: {len(cookies)})")
    
    api = MercadoLivreAPI()
    
    # URLs para teste (O usuário forneceu esta específica)
    urls = [
        "https://produto.mercadolivre.com.br/MLB-4049279695-tnis-masculino-feminino-kappa-park-20-original-_JM"
    ]
    
    print(f"\n📡 Gerando links para {len(urls)} produtos...")
    links = await api.create_links(urls)
    
    for original, link in zip(urls, links):
        print(f"\n📍 Original: {original}")
        print(f"🔗 Gerado:   {link}")
        
        if "mercadolivre.com/sec/" in link or "mercadolivre.com.br" in link:
            print("✅ Link válido gerado!")
        else:
            print("⚠️ Link parece não ter sido encurtado ou falhou.")

if __name__ == "__main__":
    asyncio.run(test_api())
