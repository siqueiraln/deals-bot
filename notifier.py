import os
import asyncio
import html
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from models.deal import Deal

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.app = None

        if self.token:
            # Inicializa a aplicação para comandos
            self.app = Application.builder().token(self.token).build()

    async def send_deal(self, deal: Deal, hashtags: str = "", to_admin: bool = False):
        # Define o destino: ID do Admin ou ID do Canal
        target_id = self.chat_id
        if to_admin:
            admin_id = os.getenv("ADMIN_USER_ID")
            if not admin_id:
                print("ADMIN_USER_ID não configurado. Enviando para o canal padrão.")
            else:
                target_id = admin_id

        if not self.app or not target_id:
            print(f"Telegram not configured. Deal: {deal.title}")
            return

        safe_title = html.escape(deal.title)

        # Se for para o admin, adicionamos um cabeçalho de alerta
        header = "🕵️ <b>NOVA OFERTA ENCONTRADA</b>\n\n" if to_admin else ""

        message = (
            f"{header}🔥 <b>{safe_title}</b>\n\n"
            f"💰 <b>Preço:</b> R$ {deal.price:.2f}\n"
        )
        if deal.original_price:
            message += f"❌ <b>De:</b> <s>R$ {deal.original_price:.2f}</s>\n"
        if deal.discount_percentage:
            message += f"📉 <b>Desconto:</b> {deal.discount_percentage}% OFF\n"

        message += (
            f"\n🏪 <b>Loja:</b> {deal.store}\n"
            f"{hashtags}\n\n"
            f"🔗 <a href='{deal.affiliate_url or deal.url}'>LINK DO PRODUTO</a>"
        )

        # Se for para o admin, adicionamos o link do painel para facilitar
        if to_admin and deal.store == "Mercado Livre":
            message += "\n\n🛠 <b>Ação sugerida:</b>\nCrie seu link em: <a href='https://www.mercadolivre.com.br/afiliados'>Painel ML</a>"

        try:
            if deal.image_url:
                await self.app.bot.send_photo(chat_id=target_id, photo=deal.image_url, caption=message, parse_mode=ParseMode.HTML)
            else:
                await self.app.bot.send_message(chat_id=target_id, text=message, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Error sending to Telegram: {e}")

    async def send_status_report(self, stats: dict):
        if not self.app or not self.chat_id: return
        report = (
            "📊 <b>Relatório de Atividade</b>\n\n"
            f"🔄 <b>Ciclos:</b> {stats.get('cycles', 0)}\n"
            f"✅ <b>Enviados:</b> {stats.get('sent', 0)}\n"
            f"🚫 <b>Blacklist:</b> {stats.get('blacklisted', 0)}\n"
            f"📉 <b>Banco de Dados:</b> {stats.get('total_db', 0)}\n"
        )
        try:
            await self.app.bot.send_message(chat_id=self.chat_id, text=report, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Error sending report: {e}")

    # --- Handlers de Comandos ---
    async def start_listening(self, command_handlers: dict):
        """Inicia o bot para ouvir comandos"""
        if not self.app: return

        # Registra os comandos passados pelo main.py
        for cmd, handler in command_handlers.items():
            self.app.add_handler(CommandHandler(cmd, handler))

        # Handler para qualquer mensagem (links diretos)
        if 'handle_message' in command_handlers:
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, command_handlers['handle_message']))

        print("Telegram Bot Listening for commands...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
