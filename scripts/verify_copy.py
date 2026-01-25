
import asyncio
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.deal import Deal
from services.copywriter import Copywriter

async def test_copy():
    print("--- Testando Copywriter e Formatação ---")
    
    # 1. Mock Deal
    deal = Deal(
        title="Smartphone Samsung Galaxy S23 Ultra 5G 256GB",
        price=4500.00,
        original_price=8000.00,
        url="https://mercadolivre.com.br/s23",
        store="Mercado Livre",
        category="Celulares"
    )
    
    # 2. Testar Copywriter
    copywriter = Copywriter()
    print("Gerando headline...")
    headline = await copywriter.generate_caption(deal)
    print(f"\n[Headline Gerada]: {headline}")
    
    # 3. Simular Formatação do Notifier (Lógica replicada para teste)
    print("\n[Simulação de Mensagem Telegram]:")
    
    def format_currency(value):
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    price_formatted = format_currency(deal.price)
    
    message = ""
    message += f"🔥 <b>{headline.upper()}</b>\n\n"
    message += f"{deal.title}\n\n"
    
    if deal.original_price and deal.original_price > deal.price:
        original_formatted = format_currency(deal.original_price)
        discount = int(((deal.original_price - deal.price) / deal.original_price) * 100)
        message += f"De <s>R$ {original_formatted}</s> por\n"
        message += f"💰 <b>R$ {price_formatted}</b>  <i>({discount}% OFF)</i>\n\n"
    else:
            message += f"💰 <b>R$ {price_formatted}</b>\n\n"

    message += f"📦 <b>{deal.store or 'Oferta Online'}</b>\n"
    
    link_url = deal.affiliate_url or deal.url
    message += f"🔗 <a href='{link_url}'>VER OFERTA</a>"
    
    print("-" * 20)
    print(message)
    print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_copy())
