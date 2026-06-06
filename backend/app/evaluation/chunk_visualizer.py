"""
Chunk Visualizer — prints out chunk splits and overlap windows to debug semantic fragmentation.
"""
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.message import Message

class ChunkVisualizer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def visualize_message_chunks(self, message_id: str) -> Dict:
        """
        Returns a structured view of how a specific message was chunked.
        Shows exact overlap windows to diagnose boundary fragmentation.
        """
        # Fetch message and its chunks
        result = await self.db.execute(
            select(Message)
            .options(selectinload(Message.chunks))
            .where(Message.id == message_id)
        )
        msg = result.scalars().first()
        
        if not msg:
            return {"error": "Message not found."}
            
        if not msg.chunks:
            return {"error": "Message has no chunks."}
            
        chunks = sorted(msg.chunks, key=lambda c: c.chunk_index)
        
        visualization = []
        for i in range(len(chunks)):
            c = chunks[i]
            
            # Highlight overlap with previous chunk
            overlap_text = ""
            if i > 0:
                prev_c = chunks[i-1]
                # Simple logic to find overlapping tail/head
                # Assuming the chunker overlapped exact text
                words_prev = prev_c.content.split()
                words_curr = c.content.split()
                
                # Find overlap length by checking tail of prev vs head of curr
                overlap_len = 0
                for j in range(1, min(len(words_prev), len(words_curr))):
                    if words_prev[-j:] == words_curr[:j]:
                        overlap_len = j
                
                if overlap_len > 0:
                    overlap_text = " ".join(words_curr[:overlap_len])
            
            visualization.append({
                "chunk_index": c.chunk_index,
                "token_count": c.token_count,
                "overlap_with_previous": overlap_text if overlap_text else "None",
                "content_preview": c.content[:150] + "...",
                "full_content": c.content
            })
            
        return {
            "message_id": msg.id,
            "role": msg.role,
            "original_length": len(msg.content),
            "chunk_count": len(chunks),
            "chunk_details": visualization
        }
