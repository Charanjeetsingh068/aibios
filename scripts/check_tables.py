import sqlite3

try:
    conn = sqlite3.connect('d:/react-website/aibios/backend/aibios.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meta_webhook_logs'")
    print(cursor.fetchall())
except Exception as e:
    print(e)
