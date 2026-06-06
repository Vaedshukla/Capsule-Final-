"""
Context Assembler — intelligently packs retrieval results into a token budget.

Features:
  - Token budget enforcement (prevents injecting 10k tokens of history)
  - Deduplication: prevents including two chunks that say the same thing
  - Section formatting: adds clear attribution to the AI prompt
"""
import numpy as np
from typing import List, Dict, Optional
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.retrieval.ranker import RankedResult
from app.models.memory_capsule import MemoryCapsule
from app.models.message_chunk import MessageChunk

logger = structlog.get_logger()


class ContextAssembler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.budget = settings.CONTEXT_TOKEN_BUDGET
        self.dedup_threshold = settings.CONTEXT_DEDUP_THRESHOLD

    async def assemble(
        self,
        ranked_results: List[RankedResult],
        query: str,
    ) -> tuple[str, int]:
        """
        Assembles ranked results into a formatted string, staying under budget.
        Returns: (formatted_string, estimated_token_count)
        """
        if not ranked_results:
            return "No relevant memory found for this query.", 10

        # Fetch full DB objects for the top N results
        capsule_ids = [r.id for r in ranked_results if r.type == "capsule"]
        chunk_ids = [r.id for r in ranked_results if r.type == "chunk"]

        capsules: Dict[str, MemoryCapsule] = {}
        if capsule_ids:
            res = await self.db.execute(select(MemoryCapsule).where(MemoryCapsule.id.in_(capsule_ids)))
            for c in res.scalars():
                capsules[str(c.id)] = c

        chunks: Dict[str, MessageChunk] = {}
        if chunk_ids:
            res = await self.db.execute(select(MessageChunk).where(MessageChunk.id.in_(chunk_ids)))
            for c in res.scalars():
                chunks[str(c.id)] = c

        included_texts: List[str] = []
        included_embeddings: List[np.ndarray] = []
        total_tokens = 0
        
        # Header tokens (~20)
        total_tokens += 20
        
        context_parts = ["## Capsule Context\n"]
        context_parts.append(f"*Retrieved from Capsule memory for query: \"{query}\"*\n")

        for r in ranked_results:
            if total_tokens >= self.budget:
                break

            text_to_add = ""
            est_tokens = 0
            embedding = None

            if r.type == "capsule" and r.id in capsules:
                cap = capsules[r.id]
                text_to_add = f"\n### Capsule: {cap.title}\n{cap.summary}"
                if cap.decisions:
                    import json
                    try:
                        decs = json.loads(cap.decisions)
                        if decs:
                            text_to_add += "\n**Key Decisions:**\n" + "\n".join(f"- {d}" for d in decs[:3])
                    except Exception:
                        pass
                # Rough token estimation
                est_tokens = len(text_to_add) // 4
                embedding = np.array(cap.embedding) if cap.embedding else None

            elif r.type == "chunk" and r.id in chunks:
                chunk = chunks[r.id]
                text_to_add = f"\n### Excerpt from: {r.title}\n{chunk.content}"
                est_tokens = chunk.token_count or (len(chunk.content) // 4)
                embedding = np.array(chunk.embedding) if chunk.embedding else None

            if not text_to_add:
                continue

            # Deduplication check
            if embedding is not None and included_embeddings:
                is_duplicate = False
                for inc_emb in included_embeddings:
                    if inc_emb is not None:
                        # Cosine similarity
                        sim = np.dot(embedding, inc_emb) / (np.linalg.norm(embedding) * np.linalg.norm(inc_emb))
                        if sim > self.dedup_threshold:
                            is_duplicate = True
                            break
                if is_duplicate:
                    logger.debug("context_assembler_deduped", id=r.id, type=r.type)
                    continue

            # Budget check
            if total_tokens + est_tokens > self.budget:
                continue

            # Add to context
            context_parts.append(text_to_add)
            included_texts.append(text_to_add)
            included_embeddings.append(embedding)
            total_tokens += est_tokens

        formatted_context = "\n".join(context_parts)
        
        logger.info(
            "context_assembled", 
            items_included=len(included_texts),
            tokens=total_tokens,
            budget=self.budget
        )
        
        return formatted_context, total_tokens
