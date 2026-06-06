import asyncio
from app.db.session import async_session_maker
from sqlalchemy import text

async def inspect_db():
    try:
        async with async_session_maker() as session:
            print("--- TABLE LIST ---")
            tables = await session.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"))
            print([t[0] for t in tables.fetchall()])

            print("\n--- ROW COUNTS ---")
            for table in ['conversations', 'messages', 'message_chunks', 'memory_capsules', 'projects']:
                try:
                    count = await session.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    print(f"{table}: {count.scalar()}")
                except Exception as e:
                    await session.rollback()
                    print(f"{table}: Table missing or error")
            
            print("\n--- PGVECTOR VERIFICATION ---")
            try:
                ext = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
                val = ext.scalar()
                print(f"Extension Active: {val == 'vector'}")
            except Exception as e:
                await session.rollback()
                print(f"Extension Active: Error ({e})")
            
            print("\n--- VECTOR INDEXES ---")
            try:
                indexes = await session.execute(text("SELECT indexname, indexdef FROM pg_indexes WHERE indexdef LIKE '%vector%';"))
                for idx in indexes.fetchall():
                    print(f"Index: {idx[0]} | Def: {idx[1]}")
            except Exception as e:
                await session.rollback()
                
            print("\n--- TIMESTAMPS ---")
            try:
                earliest = await session.execute(text("SELECT MIN(created_at) FROM conversations;"))
                latest = await session.execute(text("SELECT MAX(created_at) FROM conversations;"))
                print(f"Earliest: {earliest.scalar()}")
                print(f"Latest: {latest.scalar()}")
            except Exception:
                await session.rollback()
                
    except Exception as e:
        print(f"Error connecting: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_db())
