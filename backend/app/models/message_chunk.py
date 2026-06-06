import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base
from app.core.config import settings


class MessageChunk(Base):
    """
    A semantic chunk of a Message.

    WHY THIS EXISTS:
      Long messages (2000+ tokens) produce noisy, diluted embeddings when
      embedded whole. Chunking produces focused, high-precision vectors
      that enable accurate sub-message retrieval.

    Each Message has 1..N MessageChunks.
    Short messages (< CHUNK_TARGET_TOKENS) produce exactly 1 chunk.
    Retrieval searches chunks, not raw messages.
    """
    __tablename__ = "message_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)  # 0-indexed within message
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)

    # Text search vector for hybrid BM25 retrieval
    content_tsvector = Column(TSVECTOR)

    # pgvector embedding — the primary retrieval target
    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_message_chunks_content_tsvector", "content_tsvector", postgresql_using="gin"),
    )

    # Relationships
    message = relationship("Message", back_populates="chunks")
