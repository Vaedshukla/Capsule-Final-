"""
Embedding Service — generates and persists vector embeddings for messages and capsules.
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.embeddings.factory import get_embedding_provider
from app.models.message import Message
from app.models.message_chunk import MessageChunk
from app.models.memory_capsule import MemoryCapsule
from app.models.conversation import Conversation
from app.ingestion.chunker import chunker

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = get_embedding_provider()

    async def embed_conversation(self, conversation_id) -> int:
        """
        Generate and store embeddings for all messages in a conversation.
        Updates conversation status to 'embedded' when done.
        Returns the number of messages embedded.
        """
        log = logger.bind(conversation_id=str(conversation_id))

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.embedding.is_(None))
        )
        messages = result.scalars().all()

        if not messages:
            log.info("no_messages_to_embed")
            return 0

        # Chunking: split all messages into chunks
        all_chunks = []
        for message in messages:
            chunks = chunker.chunk(message.content)
            for c in chunks:
                all_chunks.append((message.id, c))

        if not all_chunks:
            log.info("no_chunks_generated")
            return 0

        # Batch embed all chunk content
        texts = [c.content for _, c in all_chunks]
        log.info("embedding_chunks", count=len(texts))

        try:
            embeddings = await self.provider.embed_batch(texts)
        except Exception as e:
            log.error("embedding_batch_failed", error=str(e))
            raise

        # Persist chunk embeddings
        db_chunks = []
        for (message_id, chunk), embedding in zip(all_chunks, embeddings):
            db_chunk = MessageChunk(
                message_id=message_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                token_count=chunk.token_count,
                embedding=embedding,
            )
            self.db.add(db_chunk)
            db_chunks.append(db_chunk)
            
        # Calculate document-level embedding (mean pooling of chunks)
        for message in messages:
            msg_chunks = [c for c in db_chunks if c.message_id == message.id]
            if msg_chunks:
                import numpy as np
                # Average pooling
                vectors = [np.array(c.embedding) for c in msg_chunks]
                doc_vector = np.mean(vectors, axis=0).tolist()
                message.embedding = doc_vector
            else:
                # Fallback if no chunks generated
                message.embedding = [0.0] * self.provider.dimensions

        # Update conversation status
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalars().first()
        if conversation:
            conversation.status = "embedded"

        await self.db.commit()
        log.info("embedding_complete", embedded_count=len(messages))
        return len(messages)

    async def embed_capsule(self, capsule_id) -> bool:
        """
        Generate and store an embedding for a MemoryCapsule's summary.
        """
        result = await self.db.execute(
            select(MemoryCapsule).where(MemoryCapsule.id == capsule_id)
        )
        capsule = result.scalars().first()
        if not capsule:
            return False

        text_to_embed = f"{capsule.title}\n\n{capsule.summary}"
        embedding = await self.provider.embed(text_to_embed)
        capsule.embedding = embedding

        await self.db.commit()
        logger.info("capsule_embedded", capsule_id=str(capsule_id))
        return True
