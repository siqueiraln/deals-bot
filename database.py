import sqlite3
from datetime import datetime
from models.deal import Deal

class Database:
    def __init__(self, db_path="deals.db"):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_deals (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    price REAL,
                    store TEXT,
                    timestamp DATETIME
                )
            """)
            conn.commit()

    def get_last_price(self, url: str) -> float:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT price FROM sent_deals WHERE url = ?", (url,))
            result = cursor.fetchone()
            return result[0] if result else None

    def is_deal_sent(self, url: str, current_price: float = None) -> bool:
        """
        Checks if deal was sent.
        If current_price is provided, returns True only if the price is the same.
        Returns False if the price changed (indicating a new opportunity).
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT price FROM sent_deals WHERE url = ?", (url,))
            result = cursor.fetchone()

            if result is None:
                return False

            if current_price is not None:
                last_price = result[0]
                # If price is the same, we don't want to send it again
                return abs(last_price - current_price) < 0.01

            return True

    def add_sent_deal(self, deal: Deal):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sent_deals (url, title, price, store, timestamp) VALUES (?, ?, ?, ?, ?)",
                (deal.url, deal.title, deal.price, deal.store, datetime.now())
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
