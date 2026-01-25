# 🚀 Integração de Tendências e Modo Autônomo

Implementamos com sucesso a integração das tendências do Mercado Livre e o novo modo de operação autônomo. O bot agora está muito mais inteligente e capaz de operar sozinho!

## ✨ Novas Funcionalidades

### 1. Busca Inteligente de Tendências
O bot agora monitora diariamente as **50 buscas mais quentes** do Mercado Livre e cruza esses dados com as ofertas do hub.

- **Fonte:** `tendencias.mercadolivre.com.br`
- **Cache:** Atualizado a cada 6 horas (otimizado para baixo uso de recursos)
- **Top Tendências Atuais:** Smartwatch, Luz LED, etc.

### 2. Sistema de Pontuação (Scoring)
Cada oferta recebe uma nota de 0 a 100 baseada em 3 fatores:

| Fator | Peso | Descrição |
|-------|------|-----------|
| **Comissão** | 40% | Valor do ganho extra (>=20% ganha bônus) |
| **Tendência** | 35% | Se o produto está em alta demanda |
| **Desconto** | 25% | Desconto real sobre o preço original |

- **Score > 60:** 🔥 Oferta Quente (Alta conversão)
- **Score < 40:** ❄️ Oferta Fria (Baixa prioridade)

### 3. Modo Autônomo 🤖
Você agora tem controle total sobre a autonomia do bot.

- **Modo Manual (Padrão):** Você aprova TODAS as ofertas.
- **Modo Autônomo:** O bot posta **sozinho** as ofertas com **Score > 60**. As medianas ainda pedem sua aprovação.

## 📖 Como Usar

### Novos Comandos

| Comando | Descrição |
|---------|-----------|
| `/auto` | **Liga/Desliga** o Modo Autônomo. |
| `/status` | Agora mostra qual modo está ativo. |

### Exemplo de Uso

1. **Ativar Modo Autônomo:**
   Envie `/auto` no chat privado com o bot.
   > 🤖 *Modo Autônomo Ativado! O bot postará ofertas quentes automaticamente.*

2. **Verificar Status:**
   Envie `/status`.
   > 📊 *Modo: Autônomo*

## 🛠️ Detalhes Técnicos

- **Arquivos Criados/Modificados:**
  - `scrapers/mercadolivre_trends.py`: Scraper otimizado com cache.
  - `core/autonomous_mode.py`: Gerenciador de estado.
  - `core/scoring.py`: Algoritmo de classificação.
  - `main.py`: Integração completa.
  - `models/trending_term.py`: Modelo de dados.

- **Dependências Instaladas:**
  - `beautifulsoup4`, `lxml`: Para parsing rápido de HTML.
  - `playwright`, `playwright-stealth`: Para acesso seguro à página de tendências.

## ✅ Validação Realizada

Rodamos o script de verificação (`scripts/verify_trends.py`) e confirmamos:
- [x] Scraper coletou 50 tendências reais.
- [x] Sistema de Score classificou corretamente ofertas teste.
- [x] Toggle de modo autônomo funcionou perfeitamente.

O bot está pronto para rodar! 🚀
