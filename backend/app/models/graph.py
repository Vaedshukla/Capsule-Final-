import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Relationship(Base):
    """
    Graph-style relationships between entities.
    Prepares Capsule for future knowledge graph functionality.

    Examples:
    - FastAPI USES_DATABASE PostgreSQL
    - JWT USED_IN AuthService
    - pgvector EXTENDS PostgreSQL
    """
    __tablename__ = "entity_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    source_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    # e.g. USES, DEPENDS_ON, EXTENDS, RELATED_TO, CONFLICTS_WITH
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Injection(Base):
    """
    Tracks every time a MemoryCapsule was retrieved and injected
    into an AI conversation. Used for:
    - retrieval optimization
    - importance scoring
    - workflow intelligence
    """
    __tablename__ = "injections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    capsule_id = Column(UUID(as_uuid=True), ForeignKey("memory_capsules.id"),
                        nullable=False, index=True)
    target_source = Column(String(100), nullable=True)   # Where it was injected (Claude, ChatGPT...)
    query_used = Column(Text, nullable=True)             # The search query that triggered retrieval
    injected_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    from sqlalchemy.orm import relationship
    capsule = relationship("MemoryCapsule", back_populates="injections")
