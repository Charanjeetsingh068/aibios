import asyncio
import sys

sys.path.append('d:/react-website/aibios/backend')

from app.core.database import postgres_engine, Base
from app.models import enterprise_integrations
from app.models import auth
from app.models import business

async def init_db():
    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
