
import asyncio
from app.db.session import async_session_maker
from app.services.embeddings.embedding_service import EmbeddingService

async def main():
    async with async_session_maker() as db:
        embedder = EmbeddingService(db)
        try:
            await embedder.embed_capsule("6534f1e2-a82f-4833-b794-6817fe3dc7a6")
            print("Embed Success")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

