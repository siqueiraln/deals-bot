import sqlite3
import os

def clear_db():
    db_path = "deals.db"
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sent_deals")
        conn.commit()
        print(f"Deleted {cursor.rowcount} rows from sent_deals.")
        conn.close()
    except Exception as e:
        print(f"Error clearing DB: {e}")

if __name__ == "__main__":
    clear_db()
