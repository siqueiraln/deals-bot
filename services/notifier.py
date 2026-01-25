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
from scrapers.mercadolivre_api import MercadoLivreAPI

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
                target_id = self.chat_id # Fallback
            else:
                target_id = admin_id

        if not self.app or not target_id:
            print(f"Telegram not configured. Deal: {deal.title}")
            return

        if to_admin:
            # --- FORMATO DE REVISÃO (Limpo, sem IA, Link "Clique aqui") ---
            message = f"🕵️ <b>NOVA OFERTA (Aguardando Aprovação)</b>\n\n"
            message += f"<b>{deal.title}</b>\n\n"
            
            # Format Price
            price_str = f"{deal.price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            message += f"💰 R$ {price_str}"
            
            if deal.original_price and deal.original_price > deal.price:
                orig_str = f"{deal.original_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                message += f" (Era R$ {orig_str})"
            
            message += "\n"
            message += f"📦 {deal.store or 'Mercado Livre'}\n\n"
            
            link_url = deal.affiliate_url or deal.url
            message += f"🔗 <a href='{link_url}'>Clique aqui para ver</a>"
            
            # Botões
            keyboard = [[
                InlineKeyboardButton("✅ Aprovar", callback_data="approve"),
                InlineKeyboardButton("❌ Rejeitar", callback_data="reject")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Envio simples para Admin
            try:
                if deal.image_url and deal.image_url.startswith("http"):
                    await self.app.bot.send_photo(
                        chat_id=target_id, photo=deal.image_url, caption=message, 
                        parse_mode=ParseMode.HTML, reply_markup=reply_markup
                    )
                else:
                    await self.app.bot.send_message(
                        chat_id=target_id, text=message, 
                        parse_mode=ParseMode.HTML, reply_markup=reply_markup
                    )
            except Exception as e:
                print(f"Erro envio admin: {e}")

        else:
            # --- FORMATO DO CANAL (Com Copy IA, Layout Final) ---
            # Gera legenda com IA AGORA (Só na hora de postar)
            ai_text = await self.copywriter.generate_caption(deal)
            
            # Formatação Final
            message = f"🔥 <b>{ai_text.upper()}</b>\n\n"
            message += f"{deal.title}\n\n"
            
            # Preços
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

            message += f"📦 <b>{deal.store or 'Oferta Online'}</b>\n"
            link_url = deal.affiliate_url or deal.url
            message += f"🔗 <a href='{link_url}'>VER OFERTA</a>"
            
            # Envio para Canal
            try:
                if deal.image_url and deal.image_url.startswith("http"):
                    await self.app.bot.send_photo(
                        chat_id=target_id, photo=deal.image_url, caption=message, parse_mode=ParseMode.HTML
                    )
                else:
                    await self.app.bot.send_message(
                        chat_id=target_id, text=message, parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                print(f"Erro envio canal: {e}")

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa os cliques nos botões de Aprovar/Rejeitar"""
        query = update.callback_query
        await query.answer()

        data = query.data
        message = query.message
        
        if data == "reject":
            await message.delete()
        
        elif data == "approve":
            text = message.caption or message.text
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            try:
                # Extração
                title = lines[1]
                
                # Extrair Preço e Original
                import re
                prices_line = ""
                for l in lines:
                    if "💰" in l:
                        prices_line = l
                        break
                
                price = 0.0
                original_price = 0.0
                
                # Regex Price:  R$ 1.234,56
                price_match = re.search(r'R\$ ([\d.,]+)', prices_line)
                if price_match:
                    price = float(price_match.group(1).replace(".", "").replace(",", "."))
                
                # Regex Original: (Era R$ 1.234,56)
                orig_match = re.search(r'\(Era R\$ ([\d.,]+)\)', prices_line)
                if orig_match:
                    original_price = float(orig_match.group(1).replace(".", "").replace(",", "."))
                
                # Extrair Link
                url = None
                if message.caption_entities:
                     for entity in message.caption_entities:
                        if entity.type == 'text_link':
                            url = entity.url
                            break
                if not url:
                     link_match = re.search(r"href='([^']+)'", message.caption_html or message.text_html)
                     if link_match: url = link_match.group(1)
                
                # Criar Deal Temporário
                temp_deal = Deal(title=title, price=price, url=url, store="Mercado Livre")
                temp_deal.original_price = original_price
                
                print(f"🔄 Processando Aprovação: {temp_deal.title}")
                print(f"🔗 URL Original: {temp_deal.url}")

                # --- SIMPLIFICAÇÃO MVP: Confiar no link já encurtado ---
                # O main.py já encurtou antes de mandar para aprovação.
                # Não precisamos chamar a API de novo (que estava causando erro).
                
                if temp_deal.url:
                    print(f"✅ Aprovação processada: {temp_deal.url}")
                else:
                    print("⚠️ URL não encontrada na mensagem original.")
                # ---------------------------------------------
                
                # Gerar Copy IA
                await message.edit_caption(caption="⏳ Gerando Copy com IA...")
                ai_copy = await self.copywriter.generate_caption(temp_deal)
                
                # Formatar Mensagem Final
                final_message = f"🔥 <b>{ai_copy.upper()}</b>\n\n"
                final_message += f"{temp_deal.title}\n\n"
                final_message += f"💰 <b>R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "</b>\n\n"
                final_message += f"📦 <b>Mercado Livre</b>\n"
                final_message += f"🔗 <a href='{temp_deal.url}'>VER OFERTA</a>"
                
                # Postar no Canal Oficial
                if message.photo:
                    photo_id = message.photo[-1].file_id
                    await self.app.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo_id,
                        caption=final_message,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await self.app.bot.send_message(
                        chat_id=self.chat_id,
                        text=final_message,
                        parse_mode=ParseMode.HTML
                    )
                
                # Limpar mensagem de admin
                await message.delete()

            except Exception as e:
                print(f"Erro ao aprovar oferta: {e}")
                await message.reply_text(f"Erro ao processar aprovação: {e}")

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
