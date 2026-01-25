# Plano: Otimização de Busca e Qualidade

## Problemas Identificados

### 1. Repetição Excessiva
- ❌ Múltiplos relógios similares
- ❌ Múltiplos fones de ouvido
- ❌ Falta de diversidade de categorias

### 2. Volume Excessivo de Scraping
- ❌ 55+ ofertas por ciclo pode estar causando ban
- ❌ Muitas buscas simultâneas (Hub + 5 Trends + 3 Evergreen)
- ❌ ML detectando padrão de automação

## Soluções Propostas

### A. Deduplicação Inteligente

**Problema**: Bot envia 5 relógios diferentes que são basicamente iguais.

**Solução**: Agrupar por categoria e limitar por tipo:

```python
# Categorias detectadas por palavras-chave no título
CATEGORY_LIMITS = {
    "relógio": 2,      # Máximo 2 relógios por ciclo
    "fone": 2,         # Máximo 2 fones
    "tênis": 2,        # Máximo 2 tênis
    "notebook": 1,     # Máximo 1 notebook
    "celular": 1,      # Máximo 1 celular
}
```

**Implementação**:
1. Após scoring, agrupar ofertas por categoria
2. Pegar apenas as top N de cada categoria
3. Garantir diversidade

### B. Redução de Volume de Busca

**Atual**:
- Hub: 15-30 ofertas
- Trends: 5 termos × 10 produtos = 50 ofertas
- Evergreen: 3 termos × 10 produtos = 30 ofertas
- **Total: ~95 ofertas/ciclo** ❌

**Proposto**:
- Hub: 15 ofertas (manter)
- Trends: **3 termos** × **5 produtos** = 15 ofertas
- Evergreen: **2 termos** × **5 produtos** = 10 ofertas
- **Total: ~40 ofertas/ciclo** ✅

**Benefícios**:
- Menos requisições ao ML (reduz chance de ban)
- Processamento mais rápido
- Foco em qualidade vs quantidade

### C. Rotação de Termos Evergreen

**Problema**: Sempre busca os mesmos 3 primeiros termos (relógio, tênis, fone).

**Solução**: Rotacionar termos a cada ciclo:

```python
# Ciclo 1: relógio, tênis
# Ciclo 2: fone, notebook
# Ciclo 3: celular, tablet
# Ciclo 4: relógio, tênis (volta ao início)
```

**Benefício**: Maior diversidade ao longo do dia.

### D. Filtro de Similaridade

**Problema**: "Relógio Smartwatch W11" e "Relógio Smartwatch W11 Pro" são quase iguais.

**Solução**: Calcular similaridade de títulos e descartar duplicatas:

```python
from difflib import SequenceMatcher

def are_similar(title1, title2, threshold=0.8):
    ratio = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
    return ratio > threshold
```

### E. Delays Inteligentes

**Problema**: Buscas muito rápidas parecem bot.

**Solução**: Aumentar delays entre buscas:

```python
# Atual: 2-4 segundos
await asyncio.sleep(random.uniform(2, 4))

# Proposto: 5-10 segundos
await asyncio.sleep(random.uniform(5, 10))
```

## Configurações Recomendadas

```python
# Reduzir volume
MAX_TRENDS_PER_CYCLE = 3       # Era: 5
MAX_RESULTS_PER_TREND = 5      # Era: 10
MAX_EVERGREEN_PER_CYCLE = 2    # Era: 3
MAX_RESULTS_PER_EVERGREEN = 5  # Era: 10

# Deduplicação
ENABLE_CATEGORY_LIMITS = True
ENABLE_SIMILARITY_FILTER = True
SIMILARITY_THRESHOLD = 0.75

# Anti-ban
MIN_DELAY_BETWEEN_SEARCHES = 5  # segundos
MAX_DELAY_BETWEEN_SEARCHES = 10 # segundos
```

## Prioridades de Implementação

1. **🔴 CRÍTICO**: Reduzir volume de busca (evitar ban)
2. **🟡 IMPORTANTE**: Deduplicação por categoria
3. **🟢 DESEJÁVEL**: Filtro de similaridade
4. **🟢 DESEJÁVEL**: Rotação de termos

## Resultado Esperado

**Antes**:
```
📦 95 ofertas encontradas
🎯 16 ofertas aprovadas
📤 Enviadas: 5 relógios, 4 fones, 3 tênis, 2 notebooks, 2 celulares
```

**Depois**:
```
📦 40 ofertas encontradas
🎯 12 ofertas aprovadas (mais qualidade)
📤 Enviadas: 2 relógios, 2 fones, 2 tênis, 1 notebook, 1 celular, 4 diversos
```

**Benefícios**:
- ✅ Maior diversidade
- ✅ Menos repetição
- ✅ Menor chance de ban
- ✅ Melhor experiência para seguidores

---

**Próximo Passo**: Implementar reduções de volume primeiro (mais urgente).
