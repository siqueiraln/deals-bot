import os
import asyncio
import html
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
from models.deal import Deal
from telegram.request import HTTPXRequest
from services.copywriter import Copywriter

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.app = None
        self.copywriter = Copywriter()

        if self.token:
            # Configurando timeouts via HTTPXRequest
            trequest = HTTPXRequest(connection_pool_size=8, read_timeout=30, connect_timeout=30)
            
            self.app = (
                Application.builder()
                .token(self.token)
                .request(trequest)
                .build()
            )

    async def send_deal(self, deal: Deal, to_admin: bool = False):
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

        # Gera legenda com IA
        ai_text = await self.copywriter.generate_caption(deal)
        
        # Se for para o admin, adicionamos um cabeçalho de alerta
        header = "🕵️ <b>NOVA OFERTA (Aguardando Aprovação)</b>\n\n" if to_admin else ""

        # Layout Minimalista
        # 1. Headline (Negrito + Upper)
        # 2. Nome do Produto
        # 3. Preços
        # 4. Loja
        # 5. Link
        
        message = f"{header}"
        message += f"🔥 <b>{ai_text.upper()}</b>\n\n"
        message += f"{deal.title}\n\n"
        
        # Preços (De / Por)
        # Preços (De / Por) com formatação BRL
        def format_currency(value):
            return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        price_formatted = format_currency(deal.price)
        
        if deal.original_price and deal.original_price > deal.price:
            original_formatted = format_currency(deal.original_price)
            discount = int(((deal.original_price - deal.price) / deal.original_price) * 100)
            message += f"De <s>R$ {original_formatted}</s> por\n"
            message += f"💰 <b>R$ {price_formatted}</b>  <i>({discount}% OFF)</i>\n\n"
        else:
             message += f"💰 <b>R$ {price_formatted}</b>\n\n"

        # Loja e Link
        message += f"📦 <b>{deal.store or 'Oferta Online'}</b>\n"
        
        # Link
        link_url = deal.affiliate_url or deal.url
        message += f"🔗 <a href='{link_url}'>VER OFERTA</a>"
        
        if to_admin and deal.store == "Mercado Livre":
             message += f"\n\nLink Original: {deal.url}"
             message += "\n\n🛠 <b>Ação sugerida:</b>\nCrie seu link em: <a href='https://www.mercadolivre.com.br/afiliados'>Painel ML</a>"

        # Botões de Ação (Apenas para Admin)
        reply_markup = None
        if to_admin:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Aprovar", callback_data="approve"),
                    InlineKeyboardButton("❌ Rejeitar", callback_data="reject")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            if deal.image_url and deal.image_url.startswith("http"):
                try:
                    await self.app.bot.send_photo(
                        chat_id=target_id, 
                        photo=deal.image_url, 
                        caption=message, 
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                except Exception as img_err:
                    print(f"Erro ao enviar imagem ({deal.image_url}): {img_err}. Tentando apenas texto.")
                    await self.app.bot.send_message(
                        chat_id=target_id, 
                        text=message, 
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
            else:
                await self.app.bot.send_message(
                    chat_id=target_id, 
                    text=message, 
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
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

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa os cliques nos botões de Aprovar/Rejeitar"""
        query = update.callback_query
        await query.answer()

        data = query.data
        message = query.message
        
        if data == "reject":
            await message.delete()
        
        elif data == "approve":
            caption = message.caption_html if message.caption else message.text_html
            clean_caption = caption.replace("🕵️ <b>NOVA OFERTA (Aguardando Aprovação)</b>\n\n", "")
            
            try:
                if message.photo:
                    photo_id = message.photo[-1].file_id
                    await self.app.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo_id,
                        caption=clean_caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await self.app.bot.send_message(
                        chat_id=self.chat_id,
                        text=clean_caption,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False
                    )
                await message.delete()

            except Exception as e:
                print(f"Erro ao aprovar oferta: {e}")
                await message.reply_text(f"Erro ao enviar: {e}")

    async def start_listening(self, command_handlers: dict):
        if not self.app: return
        for cmd, handler in command_handlers.items():
            self.app.add_handler(CommandHandler(cmd, handler))
        if 'handle_message' in command_handlers:
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, command_handlers['handle_message']))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))

        print("Telegram Bot Listening for commands...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
