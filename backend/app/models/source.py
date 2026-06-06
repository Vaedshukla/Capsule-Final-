import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Source(Base):
    """
    Represents an AI platform origin.
    e.g. ChatGPT, Claude, Gemini, Cursor, Antigravity, Generic
    """
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    # e.g. "chatgpt", "claude", "gemini", "cursor", "antigravity", "unknown"
    slug = Column(String(50), unique=True, nullable=False, index=True)
    base_url = Column(String(500), nullable=True)
    icon_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversations = relationship("Conversation", back_populates="source")
