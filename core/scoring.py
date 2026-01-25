from typing import List
from models.deal import Deal
from models.trending_term import TrendingTerm

def calculate_deal_score(deal: Deal, trending_terms: List[TrendingTerm]) -> float:
    score = 0
    
    # --- FATOR 1: BASE SCORE (20 pts) ---
    # Só por existir e ser válido, já ganha 20 pontos.
    score += 20

    # --- FATOR 2: TENDÊNCIA / ESTRATÉGIA (45 pts) ---
    # Se é o que o povo quer, tem peso MUITO alto.
    is_trending = False
    
    # Se for da estratégia de volume (Categoria Específica), ganha bonus forte
    # O usuário pediu para priorizar volume em categorias quentes
    if hasattr(deal, 'strategy') and deal.strategy == 'volume':
        score += 30 # Bonus de Categoria Volume
        
    deal_title_lower = deal.title.lower()
    
    for trend in trending_terms:
        if trend.term.lower() in deal_title_lower:
            is_trending = True
            break
            
    if is_trending:
        score += 45
    
    # --- FATOR 3: COMISSÃO / DESCONTO (30 pts) ---
    # Comissão (Hub) ou Desconto Real (Search)
    commission = deal.discount_percentage or 0
    
    real_discount = 0
    if deal.original_price and deal.original_price > deal.price:
        real_discount = ((deal.original_price - deal.price) / deal.original_price) * 100
    
    # Usa o maior entre comissão e desconto real
    best_value_metric = max(commission, real_discount)
    
    # Cap em 30 pontos (se tiver 50% off, ganha 15pts. Se tiver 80% off, ganha 24pts)
    score += min(best_value_metric * 0.5, 30)

    # --- FATOR 4: PREÇO PSICOLÓGICO (15 pts) ---
    # Produtos baratos (< R$ 100) convertem por impulso.
    if deal.price < 50:
        score += 15
    elif deal.price < 100:
        score += 10
    elif deal.price < 250:
        score += 5

    return round(score, 2)
