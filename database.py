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

    def is_deal_sent(self, url: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sent_deals WHERE url = ?", (url,))
            return cursor.fetchone() is not None

    def add_sent_deal(self, deal: Deal):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO sent_deals (url, title, price, store, timestamp) VALUES (?, ?, ?, ?, ?)",
                (deal.url, deal.title, deal.price, deal.store, datetime.now())
            )
            conn.commit()

    def clean_old_deals(self, days=7):
        """Optional: remove deals older than X days to keep DB small"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sent_deals WHERE timestamp < datetime('now', ?)", (f'-{days} days',))
            conn.commit()
