
import asyncio
from app.db.session import async_session_maker
from app.compression.capsule_builder import CapsuleBuilder

async def main():
    async with async_session_maker() as db:
        builder = CapsuleBuilder(db)
        try:
            capsule, metrics = await builder.build_from_conversation("eeebb8ef-d64a-4298-80f6-71e5eb38d02c")
            print("Success:", capsule.id)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

