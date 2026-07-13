import sys
import asyncio
import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../backend"))
load_dotenv(os.path.join(backend_dir, ".env"))

sys.path.append(backend_dir)

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        # Check current status
        result = await session.execute(text("SELECT id, email, status FROM users WHERE email = 'charanjeet.s7730@gmail.com'"))
        user = result.fetchone()
        
        if user:
            print(f"User found: {user[1]}, current status: {user[2]}")
            # Update to active
            await session.execute(text("UPDATE users SET status = 'active' WHERE email = 'charanjeet.s7730@gmail.com'"))
            await session.commit()
            print("User successfully reactivated!")
        else:
            print("User not found.")

if __name__ == "__main__":
    asyncio.run(main())
