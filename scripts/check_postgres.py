import os
import asyncio
import asyncpg
from dotenv import load_dotenv
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../backend"))
load_dotenv(os.path.join(backend_dir, ".env"))

async def run():
    # Load postgres connection string
    db_url = os.environ.get("POSTGRES_SERVER")
    if not db_url:
        print("No POSTGRES_SERVER found in .env")
        return
        
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    try:
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        print("Tables:")
        for t in tables:
            print("-", t['table_name'])
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(run())
