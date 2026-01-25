import os
from google import genai
from models.deal import Deal
from dotenv import load_dotenv

load_dotenv()

class Copywriter:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY não encontrada. Copywriting desativado.")
            self.client = None
            return

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-2.0-flash' # Atualizado para modelo mais recente e estável

    async def generate_caption(self, deal: Deal) -> str:
        """Gera uma legenda persuasiva para a oferta usando IA."""
        if not self.client:
            return f"🔥 <b>{deal.title}</b>"

        prompt = f"""
        Você é um expert em copywriting para ofertas no Telegram.
        
        Produto: {deal.title}
        Preço: R$ {deal.price:.2f}
        
        Sua missão: Escreva uma headline CURTA e PROFISSIONAL (máx 50 chars).
        
        Diretrizes:
        - Foco no benefício ou no desconto real.
        - Evite termos apelativos como "PREÇO DE ERRO" ou "CORRE".
        - Use emojis moderados no início (1 apenas).
        - Sem CAPS LOCK excessivo.
        
        Exemplos Bons:
        - "⚡ Creatina Growth Original em Oferta"
        - "📉 Menor preço dos últimos 30 dias"
        - "🔥 iPhone 13 com preço de Black Friday"
        
        Exemplos Ruins:
        - "PREÇO DE ERRO CORRE AGORA"
        - "URGENTE!!! LIQUIDAÇÃO TOTAL"
        """

        try:
            # Nova sintaxe google-genai
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    'temperature': 0.9,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )
            print(f"🤖 IA Gerou Texto: {response.text[:50]}...") 
            text = response.text.replace("**", "").strip()
            # Remove aspas se a IA colocar
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1]
            return text
        except Exception as e:
            print(f"❌ Erro na IA Copywriter: {e}")
            return f"🔥 {deal.title[:40]}..."
        except Exception as e:
            print(f"❌ Erro na IA Copywriter: {e}")
            return f"🔥 {deal.title[:40]}..."

