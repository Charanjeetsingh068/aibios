import asyncio

from sqlalchemy import select

from app.core.database import SqliteSessionLocal
from app.models.auth import User


async def main():
    async with SqliteSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == "charanjeet.s7730@gmail.com"))).scalar_one_or_none()
        if user:
            user.status = "active"
            await db.commit()
            print(f"Reactivated user {user.email}")
        else:
            print("User not found.")

if __name__ == "__main__":
    asyncio.run(main())
