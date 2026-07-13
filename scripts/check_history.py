import sqlite3

def check_db(name, path):
    print(f"=== checking {name} database ===")
    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        print("  Tables:", tables)
        if 'users' in tables:
            c.execute("SELECT id, email, status, role_id, organization_id FROM users")
            print("  Users:", c.fetchall())
        if 'organizations' in tables:
            c.execute("SELECT id, name, slug, status FROM organizations")
            print("  Organizations:", c.fetchall())
        if 'login_history' in tables:
            c.execute("PRAGMA table_info(login_history)")
            print("  login_history columns:", [col[1] for col in c.fetchall()])
            c.execute("SELECT * FROM login_history ORDER BY id DESC LIMIT 5")
            print("  Recent login attempts:")
            for row in c.fetchall():
                print("    ", row)
    except Exception as e:
        print("  Error:", e)

check_db("D Drive", "c:/react/aibios/database/postgres/fallback.db")
check_db("C Drive", "c:/react/aibios/database/postgres/fallback.db")
