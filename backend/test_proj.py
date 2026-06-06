
import asyncio
from app.db.session import async_session_maker
from app.models.conversation import Conversation
from sqlalchemy.future import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(Conversation).where(Conversation.id=="eeebb8ef-d64a-4298-80f6-71e5eb38d02c"))
        c = res.scalars().first()
        print("Project ID:", getattr(c, "project_id", "NOT FOUND"))

if __name__ == "__main__":
    asyncio.run(main())

