import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

load_dotenv()

async def test_telegram():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print(f"--- Teste de Configuração do Telegram ---")
    print(f"Token: {token[:5]}...{token[-5:] if token else ''}")
    print(f"Chat ID: {chat_id}")

    if not token or token == "seu_token_aqui":
        print("ERRO: TELEGRAM_BOT_TOKEN não configurado no arquivo .env")
        return

    if not chat_id or chat_id == "seu_chat_id_aqui":
        print("ERRO: TELEGRAM_CHAT_ID não configurado no arquivo .env")
        return

    bot = Bot(token=token)

    try:
        print("Enviando mensagem de teste...")
        await bot.send_message(
            chat_id=chat_id,
            text="✅ <b>Bot de Promoções Configurado!</b>\n\nSe você recebeu esta mensagem, as suas credenciais do Telegram estão funcionando corretamente.",
            parse_mode=ParseMode.HTML
        )
        print("SUCESSO: Mensagem enviada com sucesso!")
    except Exception as e:
        print(f"ERRO ao enviar mensagem: {e}")
        print("\nDica: Verifique se o Bot foi adicionado ao canal/grupo e se ele tem permissão para enviar mensagens.")

if __name__ == "__main__":
    asyncio.run(test_telegram())
