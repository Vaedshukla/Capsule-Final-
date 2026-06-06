
import asyncio
from app.db.session import async_session_maker
from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker

async def main():
    async with async_session_maker() as db:
        searcher = SemanticSearch(db)
        capsule_results = await searcher.search_capsules("Why did we choose PostgreSQL?", "b68b3e26-b8f4-47e8-aaab-1508fadc1a81", 10, 0.0)
        chunk_results = await searcher.search_chunks("Why did we choose PostgreSQL?", "b68b3e26-b8f4-47e8-aaab-1508fadc1a81", 10, 0.0)
        results = capsule_results + chunk_results
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        ranker = MemoryRanker(db)
        ranked = await ranker.rank(results)
        print("Ranked results:", len(ranked))
        for r in ranked:
            print(f"- {r.type}: {r.content[:50]} (Sim: {r.similarity_score}, Rank: {r.rank_score})")

if __name__ == "__main__":
    asyncio.run(main())

