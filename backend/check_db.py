
import asyncio
from app.db.session import async_session_maker
from app.models.memory_capsule import MemoryCapsule
from sqlalchemy.future import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(MemoryCapsule).where(MemoryCapsule.project_id=="b68b3e26-b8f4-47e8-aaab-1508fadc1a81"))
        caps = res.scalars().all()
        print([(c.id, c.title, c.decisions, c.summary) for c in caps])

if __name__ == "__main__":
    asyncio.run(main())

