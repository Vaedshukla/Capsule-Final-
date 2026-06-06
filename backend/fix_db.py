
import asyncio
from app.db.session import async_session_maker
from app.models.conversation import Conversation
from app.models.memory_capsule import MemoryCapsule
from sqlalchemy.future import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(Conversation).where(Conversation.id=="eeebb8ef-d64a-4298-80f6-71e5eb38d02c"))
        c = res.scalars().first()
        c.project_id = "b68b3e26-b8f4-47e8-aaab-1508fadc1a81"
        res2 = await db.execute(select(MemoryCapsule).where(MemoryCapsule.conversation_id=="eeebb8ef-d64a-4298-80f6-71e5eb38d02c"))
        cap = res2.scalars().first()
        if cap:
            cap.project_id = "b68b3e26-b8f4-47e8-aaab-1508fadc1a81"
        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())

