import sqlite3

def count_tvs():
    conn = sqlite3.connect('data/deals.db')
    cursor = conn.cursor()
    
    # Query to count TV products
    # Using case-insensitive search for "TV"
    cursor.execute("SELECT COUNT(*) FROM sent_deals WHERE title LIKE '%TV%' OR title LIKE '%Televis%'")
    count = cursor.fetchone()[0]
    
    print(f"Number of TV products sent: {count}")
    
    # Also let's print some sample titles to verify
    print("\nSample TV titles found:")
    cursor.execute("SELECT title FROM sent_deals WHERE title LIKE '%TV%' OR title LIKE '%Televis%' LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"- {row[0]}")

    conn.close()

if __name__ == "__main__":
    count_tvs()
