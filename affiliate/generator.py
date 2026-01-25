import os
import pyshorteners
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from dotenv import load_dotenv

load_dotenv()

class AffiliateLinkGenerator:
    def __init__(self):
        self.ml_id = os.getenv("ML_AFFILIATE_ID", "your-ml-id")
        self.shortener = pyshorteners.Shortener()

    def generate(self, url: str, store: str, shorten: bool = True) -> str:
        affiliate_url = url
        if "mercadolivre.com.br" in url or store == "Mercado Livre":
            affiliate_url = self._generate_ml(url)

        if shorten:
            return self._shorten_url(affiliate_url)
        return affiliate_url

    def _shorten_url(self, url: str) -> str:
        """Shortens URL using TinyURL (no API key required)"""
        try:
            return self.shortener.tinyurl.short(url)
        except Exception as e:
            print(f"Error shortening URL: {e}")
            return url

    def _generate_ml(self, url: str) -> str:
        """
        Mercado Livre affiliate links usually require a specific structure.
        Commonly: https://www.mercadolivre.com.br/social/afiliados/p/ID
        Or adding a parameter. For simplicity, we'll simulate the parameter approach
        if the user doesn't have the full API integration yet.
        """
        # Note: ML often uses a 'matt_tool' parameter for tracking
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        query['matt_tool'] = [self.ml_id]

        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed_url._replace(query=new_query))
