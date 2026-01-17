# Bot de Promoções com Links de Afiliado

Este bot monitora promoções no Mercado Livre, Amazon e Shopee, e envia automaticamente para um canal do Telegram com seus links de afiliado.

## 🚀 Funcionalidades

- **Scraping Automático**: Vasculha as seções de ofertas do Mercado Livre, Amazon e Shopee.
- **Gerador de Link de Afiliado**: Converte URLs normais em links de afiliado.
- **Notificação via Telegram**: Envia fotos, títulos, preços e botões de compra para o seu canal.
- **Persistência**: Evita o envio duplicado de promoções já processadas.

## 🛠️ Pré-requisitos

- Python 3.10+
- [Node.js](https://nodejs.org/) (necessário para o Playwright)
- Uma conta de afiliado em cada plataforma.
- Um Bot no Telegram (criado via @BotFather).

## 📦 Instalação

1. Clone ou baixe este repositório.
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
5. Instale os navegadores do Playwright:
   ```bash
   playwright install chromium
   ```

## ⚙️ Configuração

1. Renomeie o arquivo `.env.example` para `.env`.
2. Preencha as informações necessárias:
   - `TELEGRAM_BOT_TOKEN`: Token do seu bot.
   - `TELEGRAM_CHAT_ID`: ID do canal ou grupo (ex: `-100...`).
   - `AMAZON_AFFILIATE_TAG`: Seu ID de associado Amazon (ex: `seu-id-20`).
   - `ML_AFFILIATE_ID`: Seu ID/parâmetro de afiliado do Mercado Livre.
   - `SHOPEE_AFFILIATE_TAG`: Seu ID de afiliado Shopee.

## 🏃 Como usar

Para iniciar o bot, execute:

```bash
python main.py
```

O bot começará a busca e enviará as promoções novas a cada 30 minutos (configurável no `main.py`).

## ⚠️ Notas Importantes

- **Scraping**: Sites como Amazon e Shopee possuem proteções fortes contra robôs. O uso excessivo pode levar ao bloqueio temporário do seu IP. Recomenda-se o uso de Proxies se for rodar em larga escala.
- **Links de Afiliado**: Este bot usa uma substituição simples de parâmetros de URL. Para maior precisão (especialmente na Shopee), recomenda-se usar as APIs oficiais de afiliados para gerar os links.
