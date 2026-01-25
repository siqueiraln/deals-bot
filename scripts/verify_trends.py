import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from scrapers.mercadolivre_trends import MercadoLivreTrendsScraper
from core.scoring import calculate_deal_score
from core.autonomous_mode import AutonomousMode
from models.deal import Deal

async def verify_trends():
    print("🚀 Iniciando Verificação de Tendências...")
    
    # 1. Testar Trends Scraper
    scraper = MercadoLivreTrendsScraper()
    print("\n📊 Buscando tendências (pode demorar alguns segundos)...")
    trends = await scraper.get_cached_trends()
    
    if trends:
        print(f"✅ Encontradas {len(trends)} tendências!")
        print(f"Top 3: {[t.term for t in trends[:3]]}")
    else:
        print("❌ Nenhuma tendência encontrada.")
        return

    # 2. Testar Scoring
    print("\n🧮 Testando Sistema de Scoring...")
    
    # Caso 1: Deal com tendência e comissão alta
    deal_hot = Deal(
        title=f"Promoção Incrível {trends[0].term} Pro Max",
        price=1000.0,
        original_price=1500.0,
        url="http://teste.com",
        store="Test Store",
        discount_percentage=25 # Comissão alta
    )
    score_hot = calculate_deal_score(deal_hot, trends)
    print(f"Deal 'HOT' ({deal_hot.title}): Score {score_hot:.2f} (Esperado > 60)")

    # Caso 2: Deal comum sem tendência
    deal_cold = Deal(
        title="Ventilador Genérico",
        price=100.0,
        url="http://teste.com",
        store="Test Store",
        discount_percentage=5 # Comissão baixa
    )
    score_cold = calculate_deal_score(deal_cold, trends)
    print(f"Deal 'COLD' ({deal_cold.title}): Score {score_cold:.2f} (Esperado < 40)")

    # 3. Testar Autonomous Mode
    print("\n🤖 Testando Modo Autônomo...")
    auto_mode = AutonomousMode()
    status = auto_mode.get_status()
    print(f"Status Inicial: {status}")
    
    print("Alternando modo...")
    auto_mode.toggle()
    print(f"Novo Status: {auto_mode.get_status()}")
    
    # Revertendo
    auto_mode.toggle()
    print("Modo revertido.")

    print("\n✅ Verificação Concluída com Sucesso!")

if __name__ == "__main__":
    asyncio.run(verify_trends())
