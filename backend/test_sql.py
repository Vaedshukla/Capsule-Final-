
import asyncio
from app.db.session import async_session_maker
from app.retrieval.semantic_search import SemanticSearch

async def main():
    async with async_session_maker() as db:
        searcher = SemanticSearch(db)
        chunk_results = await searcher.search_chunks("Why did we choose PostgreSQL?", "b68b3e26-b8f4-47e8-aaab-1508fadc1a81", 10, -1.0)
        print("Chunks found:", len(chunk_results))

if __name__ == "__main__":
    asyncio.run(main())

