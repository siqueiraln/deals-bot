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

## 🎮 Comandos do Telegram (Dashboard)

Agora você pode controlar o bot diretamente pelo chat:

- **Colar um Link**: Basta colar um link do ML, Amazon ou Shopee no chat e o bot agendará a postagem.
- **`/status`**: Veja se o bot está online e o resumo de atividade.
- **`/add [link]`**: Adiciona links manuais para processamento imediato.
- **`/hot [termo]`**: Adiciona uma palavra-chave para busca ativa prioritária.
- **`/hot_list`**: Lista todas as palavras-chave de busca ativa.
- **`/remove_hot [termo]`**: Remove um termo da busca ativa.
- **`/block [termo]`**: Adiciona uma palavra à blacklist (filtro de segurança).
- **`/block_list`**: Lista todos os termos na blacklist.
- **`/remove_block [termo]`**: Remove um termo da blacklist.

## 🌟 Outras Funcionalidades

- **Encurtador de Links**: Todos os links são automaticamente encurtados via TinyURL.
- **Categorização Automática**: Identifica produtos e adiciona #hashtags.
- **Manutenção Automática**: Limpa o banco de dados de ofertas com mais de 15 dias para manter a performance.
- **Blacklist**: Filtro de palavras para evitar itens indesejados.

## ✍️ Como adicionar links manualmente

1. Abra o arquivo `manual_links.txt`.
2. Cole o link do Mercado Livre ou Amazon (um por linha).
3. Salve o arquivo.
4. O bot processará esses links no início do próximo ciclo e **limpará o arquivo automaticamente**.

## 📊 Estratégia de Busca

- **Mercado Livre**: Foco total. Busca ativa de todos os termos em `hot_keywords.txt` a cada 30 min.
- **Amazon**: Busca periódica a cada ~1.5h de termos aleatórios da lista.
- **Shopee**: Busca periódica a cada ~2h.
