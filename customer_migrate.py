"""Run once: python customer_migrate.py. Safe to run again."""
from database.db import get_db_connection
conn = get_db_connection()
try:
    conn.execute('''CREATE TABLE IF NOT EXISTS customer_order_links (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_customer_order_user ON customer_order_links(user_id)')
    conn.commit()
    print('OK: customer_order_links is ready. Old guest orders remain unlinked.')
finally:
    conn.close()
