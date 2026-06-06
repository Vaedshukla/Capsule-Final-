import asyncio
from app.db.session import async_session_maker
from sqlalchemy import text

async def verify_pgvector():
    try:
        async with async_session_maker() as session:
            # Attempt to create the extension
            print("Attempting to create vector extension...")
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            await session.commit()
            
            # Verify if the extension exists
            print("Checking if vector extension is active...")
            result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
            ext = result.scalar()
            
            if ext == 'vector':
                print("✅ Success: pgvector extension is installed and active in the database!")
            else:
                print("❌ Failed: The extension was not found in pg_extension.")
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_pgvector())
