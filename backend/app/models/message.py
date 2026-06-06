import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base
from app.core.config import settings


class Message(Base):
    """
    An individual message within a conversation.
    Stores the raw content plus a vector embedding for semantic retrieval.
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"),
                             nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)    # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)   # Order within conversation (0-indexed)

    # Token accounting
    token_count = Column(Integer, nullable=True)

    # Temporal metadata (from source, if available)
    message_timestamp = Column(DateTime, nullable=True)

    # Vector embedding (dimensions set by config: 384 for local, 1536 for OpenAI)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    chunks = relationship("MessageChunk", back_populates="message",
                          cascade="all, delete-orphan",
                          order_by="MessageChunk.chunk_index")
