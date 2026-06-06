import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base
from app.core.config import settings


class MemoryCapsule(Base):
    """
    THE CORE MODEL.

    A MemoryCapsule is a compressed, semantically searchable, reusable memory unit.
    It is created from one or more conversations and encodes:
      - Key architectural decisions
      - Summarized context
      - Extracted insights
      - Task lists
      - Contextual decisions

    This is what gets injected when a user asks:
      "What did Claude suggest about the auth system?"
    """
    __tablename__ = "memory_capsules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"),
                             nullable=True, index=True)

    # Content
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)       # Compressed summary of the context
    decisions = Column(Text, nullable=True)      # Key decisions extracted (JSON array)
    insights = Column(Text, nullable=True)       # Key insights extracted (JSON array)
    tasks = Column(Text, nullable=True)          # Tasks/TODOs extracted (JSON array)
    raw_context = Column(Text, nullable=True)    # Optional: original relevant segments

    # Semantic
    # The embedding of the full summary for similarity search
    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)

    # --- Phase 2 & 3: Structured Intelligence Fields ---
    entities = Column(JSONB, nullable=True)  # extracted technologies, services, etc.
    unresolved_issues = Column(JSONB, nullable=True)  # open tasks, remaining questions
    constraints = Column(JSONB, nullable=True)  # hard requirements (e.g. "localhost only")
    causal_links = Column(JSONB, nullable=True) # deprecation chains, architectural migrations
    
    risks = Column(JSONB, nullable=True)
    assumptions = Column(JSONB, nullable=True)
    action_items = Column(JSONB, nullable=True)
    requirements = Column(JSONB, nullable=True)
    
    # --- Extraction Versioning ---
    extraction_version = Column(String(50), nullable=True, default="1.0.0")
    extraction_model = Column(String(100), nullable=True)
    extraction_timestamp = Column(DateTime, nullable=True)
    
    # --- Scoring & Usage ---
    importance_score = Column(Float, default=0.5, nullable=False)
    quality_score = Column(Float, nullable=True)  # 1-10 self-assessed extraction quality
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0 LLM confidence
    access_count = Column(Integer, default=0, nullable=False)       # How often retrieved/injected

    # Source tracking
    source_model = Column(String(100), nullable=True)  # Which AI model created this convo

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="capsules")
    conversation = relationship("Conversation", back_populates="capsules")
    injections = relationship("Injection", back_populates="capsule")
