import os
import asyncio
from dotenv import load_dotenv
from google import genai

async def list_models():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API Key")
        return

    client = genai.Client(api_key=api_key)
    try:
        # Tenta listar modelos (a API exata pode variar na lib nova, tentando padrão comum)
        # Na nova lib google-genai, pode ser via client.models.list()
        # Na lib google-genai nova, o list retorna uma paginação assíncrona
        pager = await client.aio.models.list(config={'page_size': 100})
        async for model in pager:
             # O objeto model tem atributos como name, display_name
             print(f"Model: {model.name}")
    except Exception as e:
        print(f"Error listing: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
