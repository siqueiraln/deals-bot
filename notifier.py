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

    async def send_deal(self, deal: Deal):
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
            f"\n🏪 <b>Loja:</b> {deal.store}\n\n"
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
            # If it fails even with HTML, log the error clearly
            if "can't parse" in str(e).lower():
                print("HTML Parsing Error. Check if affiliate_url is valid.")
