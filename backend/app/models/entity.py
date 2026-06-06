import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Entity(Base):
    """
    A named entity extracted from conversations.
    Supports future knowledge graph functionality.

    Examples: Redis, FastAPI, PostgreSQL, AgentAuthService, JWT, pgvector
    """
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)
    # e.g. "technology", "framework", "concept", "person", "service", "file"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
