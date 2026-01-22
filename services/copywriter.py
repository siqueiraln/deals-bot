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
            model_name='gemini-2.0-flash-exp',
            generation_config=self.generation_config
        )

    async def generate_caption(self, deal: Deal) -> str:
        """Gera uma legenda persuasiva para a oferta usando IA."""
        if not self.model:
            return f"🔥 <b>{deal.title}</b>"

        prompt = f"""
        Você é um administrador de um canal de promoções no Telegram. Seu objetivo é fazer o usuário clicar AGORA.
        Seja exagerado, use gírias de internet (TOP, Corre, Insano) e crie senso de urgência.
        
        Produto: {deal.title}
        Preço: R$ {deal.price:.2f}
        Loja: {deal.store}

        Regras Cruciais:
        1. Comece com uma Headline BOMBÁSTICA em Negrito. Ex: <b>🔥 FICOU DE GRAÇA!</b> ou <b>🚨 ERRO DE PREÇO?</b>
        2. Dê uma opinião curta e engraçada/empolgada sobre o produto.
        3. NÃO invente funcionalidades falsas, foque no preço e oportunidade.
        4. NÃO coloque o link, nem hashtags.
        5. Máximo de 3 linhas de texto (sem contar os espaçamentos).
        
        Exemplo de Saída:
        <b>🚨 PREÇO DERRUBADO!</b>
        Galera, o estagiário endoidou! Essa TV tá saindo mais barato que monitor. Imagem 4K absurda pra jogar seu PS5.
        """

        try:
            response = await self.model.generate_content_async(prompt)
            print(f"🤖 IA Gerou Texto: {response.text[:50]}...") # Log para confirmar
            return response.text.replace("**", "").strip() # Remove markdown
        except Exception as e:
            print(f"❌ Erro na IA Copywriter: {e}")
            return f"🔥 <b>{deal.title}</b>"

