import sqlite3
import os
from datetime import datetime

"""
Script de migração do banco de dados para adicionar suporte a product_id
"""

DB_PATH = "data/deals.db"
BACKUP_PATH = f"data/deals_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def migrate_database():
    print("🔄 Iniciando migração do banco de dados...")
    
    # 1. Fazer backup do banco atual
    if os.path.exists(DB_PATH):
        print(f"📦 Criando backup em: {BACKUP_PATH}")
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print("✅ Backup criado com sucesso!")
    
    # 2. Conectar ao banco
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 3. Verificar se a coluna product_id já existe
    cursor.execute("PRAGMA table_info(sent_deals)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'product_id' in columns:
        print("✅ Coluna product_id já existe! Nada a fazer.")
        conn.close()
        return
    
    print("🔧 Criando nova estrutura com product_id...")
    
    # 4. Criar nova tabela com a estrutura correta
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_deals_new (
            product_id TEXT PRIMARY KEY,
            url TEXT,
            title TEXT,
            price REAL,
            store TEXT,
            timestamp DATETIME
        )
    """)
    
    # 5. Migrar dados antigos (extraindo product_id da URL)
    print("📊 Migrando dados antigos...")
    cursor.execute("SELECT url, title, price, store, timestamp FROM sent_deals")
    old_data = cursor.fetchall()
    
    import re
    migrated = 0
    skipped = 0
    
    for url, title, price, store, timestamp in old_data:
        # Extrair product_id da URL
        match = re.search(r'(MLB-?\d+)', url)
        if match:
            product_id = match.group(1)
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO sent_deals_new (product_id, url, title, price, store, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (product_id, url, title, price, store, timestamp)
                )
                migrated += 1
            except Exception as e:
                print(f"⚠️ Erro ao migrar {url}: {e}")
                skipped += 1
        else:
            print(f"⚠️ URL sem product_id (ignorado): {url}")
            skipped += 1
    
    # 6. Remover tabela antiga e renomear nova
    cursor.execute("DROP TABLE sent_deals")
    cursor.execute("ALTER TABLE sent_deals_new RENAME TO sent_deals")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migração concluída!")
    print(f"   📈 Registros migrados: {migrated}")
    print(f"   ⚠️ Registros ignorados: {skipped}")
    print(f"   💾 Backup salvo em: {BACKUP_PATH}")

if __name__ == "__main__":
    migrate_database()
