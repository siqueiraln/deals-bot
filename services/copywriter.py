import os
import google.generativeai as genai
from models.deal import Deal
from dotenv import load_dotenv

load_dotenv()

class Copywriter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY não encontrada. Copywriting desativado.")
            self.model = None
            return

        genai.configure(api_key=self.api_key)
        self.generation_config = genai.GenerationConfig(
            temperature=0.9,
            top_p=0.95,
            top_k=40,
            max_output_tokens=1024,
        )
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config=self.generation_config
        )

    async def generate_caption(self, deal: Deal) -> str:
        """Gera uma legenda persuasiva para a oferta usando IA."""
        if not self.model:
            return f"🔥 <b>{deal.title}</b>"

        prompt = f"""
        Você é um expert em copywriting para notificações curtas.
        
        Produto: {deal.title}
        Preço: R$ {deal.price:.2f}
        
        Sua missão: Escreva APENAS uma headline curta (máximo 50 caracteres) e impactante.
        Use gatilhos de urgência ou curiosidade.
        
        Regras:
        1. APENAS O TEXTO DA HEADLINE. Nada mais.
        2. Sem aspas, sem markdown, sem emojis no início.
        3. Exemplo: "PREÇO DE ERRO! CORRE AGORA" ou "SÓ HOJE: MENOR PREÇO HISTÓRICO"
        """

        try:
            response = await self.model.generate_content_async(prompt)
            print(f"🤖 IA Gerou Texto: {response.text[:50]}...") # Log para confirmar
            return response.text.replace("**", "").strip() # Remove markdown
        except Exception as e:
            print(f"❌ Erro na IA Copywriter: {e}")
            return f"🔥 <b>{deal.title}</b>"

