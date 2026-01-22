import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERRO: GEMINI_API_KEY não encontrada no .env")
    exit()

print(f"🔑 Chave encontrada: {api_key[:5]}...{api_key[-5:]}")

genai.configure(api_key=api_key)

print("🔍 Buscando modelos disponíveis para sua chave...")
try:
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Disponível: {m.name}")
            found = True
    
    if not found:
        print("⚠️ Nenhum modelo com suporte a 'generateContent' encontrado. Verifique permissões da chave.")

except Exception as e:
    print(f"❌ Erro de conexão: {e}")
