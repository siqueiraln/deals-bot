import aiohttp
import os
from typing import List
from config.logger import logger

class MercadoLivreAPI:
    """Cliente para API oficial de afiliados do ML"""
    
    API_URL = "https://www.mercadolivre.com.br/affiliate-program/api/v2/affiliates/createLink"
    
    def __init__(self):
        self.tag = os.getenv("ML_AFFILIATE_TAG")
        self.cookies = os.getenv("ML_COOKIES")
        
        if not self.tag or not self.cookies:
            logger.warning("⚠️ ML_AFFILIATE_TAG ou ML_COOKIES não configurados! API oficial não funcionará.")
    
    async def create_links(self, urls: List[str]) -> List[str]:
        """
        Gera links de afiliado em lote usando API oficial.
        
        Args:
            urls: Lista de URLs de produtos
            
        Returns:
            Lista de links de afiliado (mesma ordem)
        """
        if not self.tag or not self.cookies:
            return urls # Retorna URLs originais se não configurado
            
        # Tentar extrair CSRF token dos cookies
        csrf_token = ""
        if "csrf" in self.cookies:
            import re
            match = re.search(r'_csrf=([^;]+)', self.cookies)
            if match:
                csrf_token = match.group(1)

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "cookie": self.cookies,
            "origin": "https://www.mercadolivre.com.br",
            "priority": "u=1, i",
            "referer": "https://www.mercadolivre.com.br/afiliados/linkbuilder",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        
        # O workflow n8n não usa x-csrf-token explícito, apenas os headers acima.
        # Vamos tentar sem o token primeiro se ele não existir, mas manter a lógica de extração se falhar.
        if csrf_token:
            headers["x-csrf-token"] = csrf_token
            headers["x-xsrf-token"] = csrf_token


        
        payload = {
            "urls": urls,
            "tag": self.tag
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # logger.info(f"🔍 API RESPONSE: {data}")
                        
                        if "urls" in data:
                             results = []
                             for url_data, original_url in zip(data["urls"], urls):
                                 short = url_data.get("short_url")
                                 if short:
                                     results.append(short)
                                 else:
                                     # API recusou encurtar (ex: erro 111 - URL not allowed)? Injeta tag manualmente!
                                     if url_data.get("error_code"):
                                         logger.warning(f"⚠️ API Recusou ({url_data.get('error_code')}): {url_data.get('message')} -> Usando Fallback")
                                     results.append(self._inject_tag_fallback(original_url))
                             return results
                        return urls
                    else:
                        logger.error(f"❌ API Error: {response.status} - {await response.text()}")
                        logger.info("⚠️ Usando fallback manual para link de afiliado")
                        return [self._inject_tag_fallback(url) for url in urls]
        except Exception as e:
            logger.error(f"❌ API Exception: {e}")
            return [self._inject_tag_fallback(url) for url in urls]
            
    def _inject_tag_fallback(self, url: str) -> str:
        """Adiciona tag manualmente se a API falhar"""
        if not self.tag: return url
        
        # Garante que não duplique
        if f"tag={self.tag}" in url: return url

        separator = "&" if "?" in url else "?"
        # Para ML, o parâmetro comum de affiliate tag direta é 'tag' ou 'tracking_id'
        # Baseado no payload da API que usa "tag", vamos usar "tag"
        if "mercadolivre.com.br" in url:
             return f"{url}{separator}tag={self.tag}"
        return url
