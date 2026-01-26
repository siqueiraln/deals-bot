import sqlite3
from datetime import datetime
from models.deal import Deal

class Database:
    def __init__(self, db_path="data/deals.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_deals (
                    product_id TEXT PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    price REAL,
                    store TEXT,
                    timestamp DATETIME
                )
            """)
            conn.commit()

    def get_last_price(self, product_id: str) -> float:
        """Retorna o último preço registrado para um produto."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT price FROM sent_deals WHERE product_id = ?", (product_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def is_deal_sent(self, product_id: str, current_price: float = None) -> dict:
        """
        Verifica se o deal foi enviado e retorna informações sobre preço.
        
        Returns:
            dict: {
                'sent': bool,           # Se já foi enviado
                'last_price': float,    # Último preço registrado (ou None)
                'price_dropped': bool   # Se o preço atual é menor que o anterior
            }
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT price FROM sent_deals WHERE product_id = ?", (product_id,))
            result = cursor.fetchone()

            if result is None:
                return {
                    'sent': False,
                    'last_price': None,
                    'price_dropped': False
                }

            last_price = result[0]
            price_dropped = current_price < last_price if current_price else False

            return {
                'sent': True,
                'last_price': last_price,
                'price_dropped': price_dropped
            }

    def add_sent_deal(self, deal: Deal):
        """Adiciona ou atualiza um deal no banco."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sent_deals (product_id, url, title, price, store, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (deal.product_id, deal.url, deal.title, deal.price, deal.store, datetime.now())
            )
            conn.commit()

    def get_total_count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sent_deals")
            return cursor.fetchone()[0]

    def clean_old_deals(self, days=7):
        """Optional: remove deals older than X days to keep DB small"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sent_deals WHERE timestamp < datetime('now', ?)", (f'-{days} days',))
            conn.commit()
