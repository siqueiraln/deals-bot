import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from dotenv import load_dotenv

load_dotenv()

class AffiliateLinkGenerator:
    def __init__(self):
        self.amazon_tag = os.getenv("AMAZON_AFFILIATE_TAG", "your-amazon-tag-20")
        self.ml_id = os.getenv("ML_AFFILIATE_ID", "your-ml-id")
        self.shopee_tag = os.getenv("SHOPEE_AFFILIATE_TAG", "your-shopee-tag")

    def generate(self, url: str, store: str) -> str:
        if "mercadolivre.com.br" in url or store == "Mercado Livre":
            return self._generate_ml(url)
        elif "amazon.com.br" in url or store == "Amazon":
            return self._generate_amazon(url)
        elif "shopee.com.br" in url or store == "Shopee":
            return self._generate_shopee(url)
        return url

    def _generate_amazon(self, url: str) -> str:
        """Adds affiliate tag to Amazon URL"""
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        query['tag'] = [self.amazon_tag]

        # Remove existing affiliate tags if any
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed_url._replace(query=new_query))

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

    def _generate_shopee(self, url: str) -> str:
        """
        Shopee links often use deep linking:
        https://shope.ee/ (shortened) or deep_link parameters.
        """
        # This is a simplified version. Real Shopee affiliate links usually
        # go through an API or a specific affiliate subdomain.
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        query['smtt'] = [f"0.0.{self.shopee_tag}"]

        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed_url._replace(query=new_query))
