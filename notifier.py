import os
import asyncio
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

        message = (
            f"🔥 *{deal.title}*\n\n"
            f"💰 *Preço:* R$ {deal.price:.2f}\n"
        )

        if deal.original_price:
            message += f"❌ *De:* ~~R$ {deal.original_price:.2f}~~\n"

        if deal.discount_percentage:
            message += f"📉 *Desconto:* {deal.discount_percentage}% OFF\n"

        message += (
            f"\n🏪 *Loja:* {deal.store}\n\n"
            f"🔗 [COMPRAR AGORA]({deal.affiliate_url})"
        )

        try:
            if deal.image_url:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=deal.image_url,
                    caption=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            print(f"Sent deal to Telegram: {deal.title}")
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
