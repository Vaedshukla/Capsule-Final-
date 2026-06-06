"""
Memory Ranker — scores and orders retrieval results based on composite factors.

Pure vector similarity is insufficient for production retrieval.
A result might match semantically but be old, rarely used, or low-importance.

Rank equation:
  rank = (w_sim * similarity)
       + (w_imp * importance)
       + (w_rec * recency)
       + (w_acc * access)
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.retrieval.semantic_search import SearchResult
from app.models.memory_capsule import MemoryCapsule

logger = structlog.get_logger()


@dataclass
class RankedResult:
    search_result: SearchResult
    rank_score: float
    raw_similarity: float
    importance_score: float
    recency_score: float
    access_score: float

    # So we can duck-type as a SearchResult in serialization
    @property
    def id(self) -> str: return self.search_result.id
    @property
    def type(self) -> str: return self.search_result.type
    @property
    def title(self) -> str: return self.search_result.title
    @property
    def content(self) -> str: return self.search_result.content
    @property
    def similarity_score(self) -> float: return self.raw_similarity
    @property
    def project_id(self) -> Optional[str]: return self.search_result.project_id
    @property
    def conversation_id(self) -> Optional[str]: return self.search_result.conversation_id
    @property
    def source_slug(self) -> Optional[str]: return self.search_result.source_slug


class MemoryRanker:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.w_sim = settings.RANK_WEIGHT_SIMILARITY
        self.w_imp = settings.RANK_WEIGHT_IMPORTANCE
        self.w_rec = settings.RANK_WEIGHT_RECENCY
        self.w_acc = settings.RANK_WEIGHT_ACCESS
        self.half_life_days = settings.RANK_RECENCY_HALF_LIFE_DAYS

    async def rank(self, results: List[SearchResult]) -> List[RankedResult]:
        """Rank a mixed list of capsules and chunks."""
        if not results:
            return []

        # 1. Fetch metadata for capsules
        capsule_ids = [r.id for r in results if r.type == "capsule"]
        # For chunks, we'd normally fetch message/conv metadata.
        # For now, we'll assign baseline scores for chunks.
        
        capsule_metadata: Dict[str, MemoryCapsule] = {}
        if capsule_ids:
            res = await self.db.execute(
                select(MemoryCapsule).where(MemoryCapsule.id.in_(capsule_ids))
            )
            for c in res.scalars():
                capsule_metadata[str(c.id)] = c

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        ranked: List[RankedResult] = []
        max_access = max([c.access_count for c in capsule_metadata.values()] + [1])

        for r in results:
            sim = r.similarity_score
            
            if r.type == "capsule" and r.id in capsule_metadata:
                cap = capsule_metadata[r.id]
                imp = float(cap.importance_score)
                
                # Confidence score (Phase 2 LLM quality extraction)
                conf = float(cap.confidence_score) if cap.confidence_score is not None else 1.0
                
                # Recency decay: 1 / (1 + (days / half_life))
                days_old = max(0, (now - cap.created_at).total_seconds() / 86400)
                rec = 1.0 / (1.0 + (days_old / self.half_life_days))
                
                # Access affinity: log scale or simple normalize
                acc = cap.access_count / max_access
                
            else:
                # Baseline for chunks (or missing capsules)
                imp = 0.5
                rec = 0.8  # Assume relatively recent
                acc = 0.1
                conf = 1.0

            rank_score = ((self.w_sim * sim) + (self.w_imp * imp) + (self.w_rec * rec) + (self.w_acc * acc)) * conf
            
            ranked.append(RankedResult(
                search_result=r,
                rank_score=round(rank_score, 4),
                raw_similarity=sim,
                importance_score=imp,
                recency_score=round(rec, 4),
                access_score=round(acc, 4)
            ))

        # Sort by composite rank descending
        ranked.sort(key=lambda x: x.rank_score, reverse=True)
        return ranked
