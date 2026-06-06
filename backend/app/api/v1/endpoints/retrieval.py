"""
GET /api/v1/retrieval/search — Semantic search across capsules and messages.
"""
import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.schemas import SearchResponse, SearchResultOut
from app.retrieval.semantic_search import SemanticSearch
from app.retrieval.ranker import MemoryRanker

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search across memory capsules and messages",
)
async def semantic_search(
    query: str = Query(..., min_length=1, max_length=1000, description="Natural language search query"),
    project_id: Optional[str] = Query(None, description="Filter by project UUID"),
    top_k: int = Query(10, ge=1, le=50),
    min_confidence: float = Query(0.3, ge=0.0, le=1.0),
    search_type: str = Query("all", description="capsules | chunks | all"),
    db: AsyncSession = Depends(get_db),
):
    searcher = SemanticSearch(db)
    results = []

    if search_type in ("capsules", "all"):
        capsule_results = await searcher.search_capsules(
            query=query,
            project_id=project_id,
            limit=top_k,
            min_similarity=min_confidence,
        )
        results.extend(capsule_results)

    if search_type in ("chunks", "all"):
        message_results = await searcher.search_chunks(
            query=query,
            project_id=project_id,
            limit=top_k,
            min_similarity=min_confidence,
        )
        results.extend(message_results)

    # Sort combined results by similarity descending
    results.sort(key=lambda r: r.similarity_score, reverse=True)
    # Rerank results
    ranker = MemoryRanker(db)
    ranked_results = await ranker.rank(results)

    # Convert to output schemas
    out_results = []
    for r in ranked_results[:top_k]:
        out_results.append(SearchResultOut(
            id=r.id,
            type=r.type,
            title=r.title,
            content=r.content,
            similarity_score=r.similarity_score,
            rank_score=r.rank_score,
            importance_score=r.importance_score,
            recency_score=r.recency_score,
            access_score=r.access_score,
            project_id=r.project_id,
            conversation_id=r.conversation_id,
            source_slug=r.source_slug,
        ))

    overall_confidence = max([r.rank_score for r in out_results]) if out_results else 0.0

    return SearchResponse(
        results=out_results,
        confidence=round(overall_confidence, 2)
    )
