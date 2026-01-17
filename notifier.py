import os
import asyncio
import html
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv
from models.deal import Deal

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.bot = Bot(token=self.token) if self.token else None

    async def send_deal(self, deal: Deal, hashtags: str = ""):
        if not self.bot or not self.chat_id:
            print(f"Telegram not configured. Deal: {deal.title} - {deal.affiliate_url}")
            return

        # Escape HTML characters to prevent parsing errors
        safe_title = html.escape(deal.title)

        message = (
            f"🔥 <b>{safe_title}</b>\n\n"
            f"💰 <b>Preço:</b> R$ {deal.price:.2f}\n"
        )

        if deal.original_price:
            message += f"❌ <b>De:</b> <s>R$ {deal.original_price:.2f}</s>\n"

        if deal.discount_percentage:
            message += f"📉 <b>Desconto:</b> {deal.discount_percentage}% OFF\n"

        message += (
            f"\n🏪 <b>Loja:</b> {deal.store}\n"
            f"{hashtags}\n\n"
            f"🔗 <a href='{deal.affiliate_url}'>COMPRAR AGORA</a>"
        )

        try:
            if deal.image_url:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=deal.image_url,
                    caption=message,
                    parse_mode=ParseMode.HTML
                )
            else:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
            print(f"Sent deal to Telegram: {deal.title}")
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
    async def send_status_report(self, stats: dict):
        if not self.bot or not self.chat_id:
            return

        report = (
            "📊 <b>Relatório de Atividade do Bot</b>\n\n"
            f"🔄 <b>Ciclos executados:</b> {stats.get('cycles', 0)}\n"
            f"✅ <b>Ofertas enviadas:</b> {stats.get('sent', 0)}\n"
            f"🚫 <b>Produtos ignorados (Blacklist):</b> {stats.get('blacklisted', 0)}\n"
            f"📉 <b>Preços monitorados:</b> {stats.get('total_db', 0)}\n\n"
            "🚀 <i>O bot continua operando normalmente.</i>"
        )

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=report,
                parse_mode=ParseMode.HTML
            )
            print("Status report sent to Telegram.")
        except Exception as e:
            print(f"Error sending report: {e}")
