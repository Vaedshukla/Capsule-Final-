import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Conversation(Base):
    """
    Metadata for a captured AI conversation.
    Each conversation belongs to a Source (ChatGPT, Claude...) and optionally a Project.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=True, index=True)

    # Metadata from capture
    title = Column(String(500), nullable=True)
    source_url = Column(Text, nullable=True)  # Original URL of the conversation
    captured_at = Column(DateTime, nullable=True)  # When the extension captured it

    # Computed
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    summary = Column(Text, nullable=True)  # Brief auto-generated summary

    # Status
    # "raw" = stored but not embedded
    # "embedded" = vectors generated for all messages
    # "compressed" = at least one MemoryCapsule created
    status = Column(String(50), default="raw", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="conversations")
    source = relationship("Source", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan",
                            order_by="Message.position")
    capsules = relationship("MemoryCapsule", back_populates="conversation")
