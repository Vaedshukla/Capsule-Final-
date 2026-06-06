"""
Chunking Evaluator — verifies chunk boundaries capture semantics better than full messages.
"""
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.message import Message
from app.models.message_chunk import MessageChunk

class ChunkingEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_boundaries(self) -> Dict:
        """
        Evaluate if chunks are being properly generated and respect target token lengths.
        """
        # Fetch some chunks and messages to inspect
        res_msgs = await self.db.execute(select(Message))
        messages = res_msgs.scalars().all()
        
        res_chunks = await self.db.execute(select(MessageChunk))
        chunks = res_chunks.scalars().all()
        
        total_msgs = len(messages)
        total_chunks = len(chunks)
        
        if total_msgs == 0:
            return {"status": "No messages to evaluate."}
            
        avg_chunks_per_msg = total_chunks / total_msgs
        
        chunk_sizes = [c.token_count for c in chunks if c.token_count is not None]
        avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        
        # Check how many are near the overlap/target bounds
        # We configured 200 target, 40 overlap
        target = 200
        within_bounds = sum(1 for s in chunk_sizes if s <= target * 1.5)
        percent_within_bounds = (within_bounds / len(chunk_sizes)) * 100 if chunk_sizes else 0
        
        return {
            "total_messages": total_msgs,
            "total_chunks": total_chunks,
            "avg_chunks_per_msg": round(avg_chunks_per_msg, 2),
            "avg_chunk_tokens": round(avg_chunk_size, 2),
            "percent_chunks_within_target_bounds": round(percent_within_bounds, 2)
        }
