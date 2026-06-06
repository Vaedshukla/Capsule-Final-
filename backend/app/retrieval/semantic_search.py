"""
Semantic Search — pgvector-powered similarity retrieval.
"""
from dataclasses import dataclass
from typing import List, Optional
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.services.embeddings.embedding_service import get_embedding_provider
from app.models.memory_capsule import MemoryCapsule
from app.models.message import Message
from app.models.message_chunk import MessageChunk

logger = structlog.get_logger()


@dataclass
class SearchResult:
    id: str
    type: str          # "capsule" | "message"
    title: str
    content: str
    similarity_score: float
    project_id: Optional[str]
    conversation_id: Optional[str]
    source_slug: Optional[str] = None


class SemanticSearch:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = get_embedding_provider()

    async def search_capsules(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.3,
    ) -> List[SearchResult]:
        """
        Search MemoryCapsules by semantic similarity.
        This is the primary retrieval path for context injection.
        """
        query_embedding = await self.provider.embed(query)
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        project_filter = "AND mc.project_id = CAST(:project_id AS uuid)" if project_id else ""
        
        sql = text(f"""
            SELECT
                mc.id,
                mc.title,
                mc.summary,
                mc.project_id,
                mc.conversation_id,
                1 - (mc.embedding <=> :embedding) AS similarity
            FROM memory_capsules mc
            WHERE mc.embedding IS NOT NULL
              {project_filter}
              AND 1 - (mc.embedding <=> :embedding) >= :min_similarity
            ORDER BY similarity DESC
            LIMIT :limit
        """)

        params = {
            "embedding": embedding_str,
            "min_similarity": min_similarity,
            "limit": limit,
        }
        if project_id:
            params["project_id"] = str(project_id)

        result = await self.db.execute(sql, params)

        rows = result.fetchall()
        results = []
        for row in rows:
            results.append(SearchResult(
                id=str(row.id),
                type="capsule",
                title=row.title,
                content=row.summary,
                similarity_score=float(row.similarity),
                project_id=str(row.project_id) if row.project_id else None,
                conversation_id=str(row.conversation_id) if row.conversation_id else None,
            ))

        logger.info("capsule_search_complete", query=query[:50], results=len(results))
        return results

    async def search_chunks(
        self,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 20,
        min_similarity: float = 0.4,
    ) -> List[SearchResult]:
        """
        Search MessageChunks using Hybrid Retrieval (BM25 + pgvector).
        Combines exact technical noun matching with semantic distance
        using Reciprocal Rank Fusion (RRF).
        """
        query_embedding = await self.provider.embed(query)
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        # Reciprocal Rank Fusion (RRF) Constant k
        # https://plg.uwaterloo.ca/~gvcormac/cormackscore.pdf
        rrf_k = 60

        project_filter = "AND c.project_id = CAST(:project_id AS uuid)" if project_id else ""

        sql = text(f"""
            WITH vector_matches AS (
                SELECT
                    mc.id,
                    1 - (mc.embedding <=> :embedding) AS similarity,
                    ROW_NUMBER() OVER (ORDER BY 1 - (mc.embedding <=> :embedding) DESC) AS rank
                FROM message_chunks mc
                JOIN messages m ON mc.message_id = m.id
                JOIN conversations c ON m.conversation_id = c.id
                WHERE mc.embedding IS NOT NULL
                  AND m.role = 'assistant'
                  {project_filter}
                  AND 1 - (mc.embedding <=> :embedding) >= :min_similarity
                ORDER BY similarity DESC
                LIMIT :limit
            ),
            bm25_matches AS (
                SELECT
                    mc.id,
                    ts_rank(mc.content_tsvector, websearch_to_tsquery('english', :query)) AS bm25_score,
                    ROW_NUMBER() OVER (ORDER BY ts_rank(mc.content_tsvector, websearch_to_tsquery('english', :query)) DESC) AS rank
                FROM message_chunks mc
                JOIN messages m ON mc.message_id = m.id
                JOIN conversations c ON m.conversation_id = c.id
                WHERE mc.content_tsvector @@ websearch_to_tsquery('english', :query)
                  AND m.role = 'assistant'
                  {project_filter}
                ORDER BY bm25_score DESC
                LIMIT :limit
            )
            SELECT
                mc.id,
                mc.content,
                m.role,
                m.conversation_id,
                c.title AS conversation_title,
                c.project_id,
                s.slug AS source_slug,
                COALESCE(v.similarity, 0) AS similarity,
                COALESCE(b.bm25_score, 0) AS bm25_score,
                -- Reciprocal Rank Fusion
                (
                    COALESCE(1.0 / (:rrf_k + v.rank), 0.0) +
                    COALESCE(1.0 / (:rrf_k + b.rank), 0.0)
                ) AS rrf_score
            FROM message_chunks mc
            JOIN messages m ON mc.message_id = m.id
            JOIN conversations c ON m.conversation_id = c.id
            LEFT JOIN sources s ON c.source_id = s.id
            LEFT JOIN vector_matches v ON mc.id = v.id
            LEFT JOIN bm25_matches b ON mc.id = b.id
            WHERE v.id IS NOT NULL OR b.id IS NOT NULL
            ORDER BY rrf_score DESC
            LIMIT :limit
        """)

        params = {
            "query": query,
            "embedding": embedding_str,
            "min_similarity": min_similarity,
            "limit": limit,
            "rrf_k": rrf_k,
        }
        if project_id:
            params["project_id"] = str(project_id)

        result = await self.db.execute(sql, params)

        rows = result.fetchall()
        results = []
        for row in rows:
            results.append(SearchResult(
                id=str(row.id),
                type="chunk",
                title=row.conversation_title or "Unknown Conversation",
                content=row.content,
                # We use the raw similarity for the ranker later, or we can use the RRF score.
                # For compatibility with MemoryRanker which expects similarity_score (0-1):
                # RRF score is small (e.g. 0.03). We'll pass the underlying semantic similarity,
                # but we should ideally update MemoryRanker to take rrf_score. 
                # For now, pass similarity and let MemoryRanker do its thing.
                similarity_score=float(row.similarity) if row.similarity > 0 else float(row.rrf_score * 10),
                project_id=str(row.project_id) if row.project_id else None,
                conversation_id=str(row.conversation_id),
                source_slug=row.source_slug,
            ))

        return results
