import asyncio
import os
import sys

# Ensure backend directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine
from app.models.auth import Base as AuthBase
from app.models.business import Base as BizBase

async def init_db():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(AuthBase.metadata.create_all)
        await conn.run_sync(BizBase.metadata.create_all)
    print("Done")

if __name__ == "__main__":
    asyncio.run(init_db())
