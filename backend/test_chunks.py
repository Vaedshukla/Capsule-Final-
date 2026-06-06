
import asyncio
from app.db.session import async_session_maker
from app.models.message import Message
from app.models.message_chunk import MessageChunk
from sqlalchemy.future import select

async def main():
    async with async_session_maker() as db:
        res = await db.execute(select(MessageChunk).limit(5))
        chunks = res.scalars().all()
        print("Chunks:", len(chunks))
        for c in chunks:
            print("-", c.content, c.embedding is not None)

if __name__ == "__main__":
    asyncio.run(main())

