# Bot de Promoções (Versão: ML Hub 🚀)

Bot focado em automatizar o **Hub de Afiliados do Mercado Livre**, minerando ofertas com alta comissão ("Ganhos Extras") e gerando links de afiliado automaticamente.

## 🚀 Funcionalidades Atuais

- **Mercado Livre Hub**: Acessa sua conta via cookies, encontra ofertas > 10% de comissão.
- **Auto-Link Gen**: Clica automaticamente no botão "Compartilhar" para gerar o link `/sec/`.
- **Filtro de Comissão**: Ignora ofertas com margem baixa.
- **Envio Automático**: Posta ofertas validadas diretamente no Canal do Telegram.
- **Notificação Admin**: Avisa sobre erros, status e comandos.

**Nota:** Os scrapers de Amazon e Shopee foram desativados temporariamente para foco no ML.

## 🛠️ Pré-requisitos

1.  Python 3.10+ e Node.js.
2.  Conta de Afiliado Mercado Livre aprovada.
3.  Extensão **EditThisCookie** (Chrome/Edge) para extrair o arquivo `cookies.json`.

## ⚙️ Instalação e Configuração

1.  **Clone e Instale:**
    ```bash
    git clone [seu-repo]
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    playwright install chromium
    ```

2.  **Configuração de Ambiente (.env):**
    Renomeie `.env.example` para `.env` e preencha:
    - `TELEGRAM_BOT_TOKEN`: Token do BotFather.
    - `TELEGRAM_CHAT_ID`: ID do seu CANAL de ofertas (onde o bot posta).
    - `ADMIN_USER_ID`: Seu ID pessoal (para comandos de controle).

3.  **Cookies do Mercado Livre (CRÍTICO):**
    - Logue no Mercado Livre e acesse o [Hub de Afiliados](https://www.mercadolivre.com.br/afiliados/hub).
    - Use a extensão *EditThisCookie*, exporte os cookies para JSON.
    - Salve como `cookies.json` na raiz do projeto.
    - **Importante:** Se o bot parar de logar, renove este arquivo.

## 🎮 Comandos (Admin Privado)

Fale com o bot no privado para controlar:

- **`/status`**: Resumo de ciclos e ofertas enviadas.
- **`/scan`**: Força uma busca imediata no Hub.
- **`/add [link]`**: Processa um link manual na hora.

## 📊 Estratégia de Busca

- **Modo Atual:** Busca Autenticada (ML Hub).
  - Ignora `hot_keywords.txt` (busca o que o ML recomenda no painel).
  - Ciclos de verificação a cada 30 minutos (ajustável em `ML_FREQUENCY`).

- **Segurança:**
  - `playwright-stealth`: Camuflagem para evitar bloqueios.
  - `cookies.json`: Sessão real de usuário.
  - Rate Limiting e Intervalos Aleatórios.
