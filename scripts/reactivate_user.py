import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://aibios_admin:aibios_secure_password_2026@localhost/aibios_db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

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
