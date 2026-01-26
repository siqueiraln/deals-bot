import os
import re
from google import genai
from models.deal import Deal
from dotenv import load_dotenv

load_dotenv()

class Copywriter:
    # PROMPTS ESPECIALIZADOS (1 agente = 1 função)
    PROMPTS = {
        'calcado': """Você é copywriter de calçados e acessórios para pés.
Produto: {title}
Preço: R$ {price}

Crie APENAS um título curto (máx 5 palavras).
Comece com 🖼
Não explique. Não crie variações.

Exemplos:
🖼 PISANTE NOVO 👟
🖼 CROCS NA PROMO
🖼 CHINELO PRA QUEBRAR O GALHO""",

        'roupa_feminina': """Você é copywriter de moda feminina.
Produto: {title}
Preço: R$ {price}

Crie APENAS um título curto (máx 5 palavras).
Comece com 🖼
Não explique. Não crie variações.

Exemplos:
🖼 PRA ELA 🙋‍♀️
🖼 ESTILO FEMININO
🖼 LOOK DO DIA""",

        'roupa_masculina': """Você é copywriter de moda masculina.
Produto: {title}
Preço: R$ {price}

Crie APENAS um título curto (máx 5 palavras).
Comece com 🖼
Não explique. Não crie variações.

Exemplos:
🖼 PRA ELE 🙋‍♂️
🖼 ESTILO MASCULINO
🖼 BÁSICO QUE FUNCIONA""",

        'perfumaria': """Você é copywriter de perfumes e fragrâncias.
Produto: {title}
Preço: R$ {price}

Crie APENAS um título curto (máx 5 palavras).
Comece com 🖼
Não explique. Não crie variações.

Exemplos:
🖼 CHEIROSO DEMAIS
🖼 CONTRATIPO DO SAUVAGE
🖼 PERFUME DOS MILIONÁRIOS 💸""",

        'eletronico': """Você é copywriter de eletrônicos e tech.
Produto: {title}
Preço: R$ {price}

Crie APENAS um título curto (máx 5 palavras).
Comece com 🖼
Não explique. Não crie variações.

Exemplos:
🖼 TECH NA PROMO
🖼 GADGET DO MOMENTO
🖼 ELETRÔNICO BARATO""",

        'casa': """Você é copywriter de casa e decoração.
Produto: {title}
Preço: R$ {price}

Crie APENAS um título curto (máx 5 palavras).
Comece com 🖼
Não explique. Não crie variações.

Exemplos:
🖼 PRA SUA CASA
🖼 DECORAÇÃO EM CONTA
🖼 ITEM ESSENCIAL""",

        'geral': """Você é copywriter de promoções gerais.
Produto: {title}
Preço: R$ {price}

Crie APENAS um título curto (máx 5 palavras).
Comece com 🖼
Seja criativo mas direto.
Não explique. Não crie variações.

Exemplos:
🖼 OFERTA RELÂMPAGO ⚡
🖼 PREÇO DE BANANA 🍌
🖼 OPORTUNIDADE ÚNICA"""
    }

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY não encontrada. Copywriting desativado.")
            self.client = None
            return

        self.client = genai.Client(api_key=self.api_key)
        # Único modelo que conectou (mesmo com cota limitada)
        self.model_name = 'gemini-2.0-flash-exp' 


    def _clean_title(self, title: str) -> str:
        """Limpa ruídos comuns de títulos de e-commerce."""
        noise_words = [
            "Frete Grátis", "Frete Gratis", "Promoção", "Oferta", 
            "Original", "Envio Imediato", "Full", "Melhor Preço",
            "Pronta Entrega", "Novo", "Lacrado", "Nota Fiscal", "NF"
        ]
        clean_title = title
        for word in noise_words:
            # Case insensitive remove
            clean_title = re.sub(re.escape(word), "", clean_title, flags=re.IGNORECASE)
        
        # Remove caracteres estranhos no inicio
        clean_title = clean_title.strip(" -|[]()")
        # Remove excesso de espaços
        return " ".join(clean_title.split())

    def _classify_product(self, title: str, price: float) -> str:
        """
        Classifica produto SEM criatividade. Só categorização.
        Retorna: 'calcado' | 'roupa_feminina' | 'roupa_masculina' | 'perfumaria' | 'eletronico' | 'casa' | 'geral'
        """
        title_lower = title.lower()
        
        # Calçados (prioridade alta - inclui Crocs)
        if any(word in title_lower for word in ['tênis', 'tenis', 'chinelo', 'sandália', 'sandalia', 'crocs', 'sapato', 'bota']):
            return 'calcado'
        
        # Roupas (detecta gênero)
        roupa_keywords = ['camiseta', 'camisa', 'blusa', 'vestido', 'saia', 'calça', 'calca', 'short', 'bermuda', 'cueca', 'calcinha', 'sutiã', 'sutia']
        if any(word in title_lower for word in roupa_keywords):
            if any(fem in title_lower for fem in ['feminina', 'feminino', 'mulher', 'ela']):
                return 'roupa_feminina'
            elif any(masc in title_lower for masc in ['masculina', 'masculino', 'homem', 'ele']):
                return 'roupa_masculina'
            else:
                # Tenta inferir por palavras específicas
                if any(word in title_lower for word in ['vestido', 'saia', 'calcinha', 'sutiã']):
                    return 'roupa_feminina'
                elif any(word in title_lower for word in ['cueca']):
                    return 'roupa_masculina'
                else:
                    return 'roupa_masculina'  # Default (maioria das ofertas)
        
        # Perfumaria
        if any(word in title_lower for word in ['perfume', 'colônia', 'colonia', 'desodorante', 'deo', 'fragrância', 'fragrancia', 'eau de']):
            return 'perfumaria'
        
        # Eletrônicos
        if any(word in title_lower for word in ['notebook', 'celular', 'smartphone', 'fone', 'headphone', 'tablet', 'tv', 'mouse', 'teclado', 'monitor']):
            return 'eletronico'
        
        # Casa
        if any(word in title_lower for word in ['mesa', 'cadeira', 'sofá', 'sofa', 'cama', 'colchão', 'colchao', 'travesseiro', 'panela', 'frigideira']):
            return 'casa'
        
        # Geral (fallback)
        return 'geral'

    async def generate_caption(self, deal: Deal) -> str:
        """Gera headline estilo 'Promo Out of Context' usando CLASSIFIER PATTERN."""
        if not self.client:
            return f"🖼 OPORTUNIDADE ⚡"

        # ETAPA 1: LIMPEZA (pré-processamento)
        clean_title = self._clean_title(deal.title)

        # ETAPA 2: CLASSIFICAÇÃO (decisão no código, não na IA)
        category = self._classify_product(clean_title, deal.price)

        # ETAPA 3: ESCOLHE PROMPT ESPECIALIZADO
        prompt_template = self.PROMPTS.get(category, self.PROMPTS['geral'])
        prompt = prompt_template.format(title=clean_title, price=f"{deal.price:.2f}")

        # ETAPA 4: IA SÓ EXECUTA (sem decidir papel)
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    'temperature': 0.8,  # Menos criativo = mais consistente
                    'top_p': 0.9,
                    'max_output_tokens': 50,  # Título curto
                }
            )
            text = response.text.replace("**", "").strip()
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1]
            return text
        except Exception as e:
            print(f"❌ Erro na IA Copywriter: {e}")
            # Fallback baseado na categoria
            fallbacks = {
                'calcado': '🖼 PISANTE NOVO 👟',
                'roupa_feminina': '🖼 PRA ELA 🙋‍♀️',
                'roupa_masculina': '🖼 PRA ELE 🙋‍♂️',
                'perfumaria': '🖼 CHEIROSO DEMAIS',
                'eletronico': '� TECH NA PROMO',
                'casa': '🖼 PRA SUA CASA',
                'geral': '🖼 OFERTA RELÂMPAGO ⚡'
            }
            return fallbacks.get(category, '🖼 OFERTA RELÂMPAGO ⚡')

