"""
All Pydantic v2 schemas for API request/response validation.
Completely decoupled from SQLAlchemy models.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import uuid
import json


# ─── Ingestion ────────────────────────────────────────────────────────────────

class IngestMessageIn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None


class IngestConversationIn(BaseModel):
    """Payload sent by the browser extension to ingest a captured conversation."""
    source: str = Field(..., description="Platform slug: chatgpt, claude, gemini, cursor, unknown")
    project_hint: Optional[str] = Field(None, description="Project name hint from the user")
    messages: List[IngestMessageIn]
    url: Optional[str] = None
    title: Optional[str] = None
    captured_at: Optional[str] = None


class IngestConversationOut(BaseModel):
    conversation_id: str
    status: str
    message_count: int
    summary_preview: Optional[str] = None


# ─── Projects ─────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime


# ─── Conversations ─────────────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: Optional[str]
    status: str
    message_count: int
    total_tokens: int
    summary: Optional[str]
    captured_at: Optional[datetime]
    created_at: datetime


# ─── Messages ─────────────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    position: int
    token_count: Optional[int]
    created_at: datetime


# ─── MemoryCapsules ───────────────────────────────────────────────────────────

class CapsuleCreate(BaseModel):
    conversation_id: str
    title: Optional[str] = None


class CapsuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    title: str
    summary: str
    decisions: Optional[List[str]] = None
    insights: Optional[List[str]] = None
    unresolved_issues: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    assumptions: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    importance_score: float
    confidence_score: float = 0.0
    access_count: int
    created_at: datetime
    
    @field_validator(
        'decisions', 'insights', 'unresolved_issues', 'constraints',
        'entities', 'risks', 'assumptions', 'action_items', 'requirements',
        mode='before'
    )
    @classmethod
    def parse_json_strings(cls, v):
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except Exception:
                return []
        return v


# ─── Retrieval ────────────────────────────────────────────────────────────────

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    project_id: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)
    min_similarity: float = Field(0.3, ge=0.0, le=1.0)
    search_type: Literal["capsules", "messages", "all"] = "all"


class SearchResultOut(BaseModel):
    id: str
    type: str
    title: str
    content: str
    similarity_score: float
    rank_score: float = Field(default=0.0)
    importance_score: float = Field(default=0.0)
    recency_score: float = Field(default=0.0)
    access_score: float = Field(default=0.0)
    project_id: Optional[str]
    conversation_id: Optional[str]
    source_slug: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResultOut]
    confidence: float = 1.0


# ─── Injection ────────────────────────────────────────────────────────────────

class InjectionRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    target_source: Optional[str] = None
    limit: int = Field(3, ge=1, le=10)


class InjectionPayload(BaseModel):
    """
    Formatted context payload ready to be injected into an AI conversation.
    This is what the extension receives and prepends to a new conversation.
    """
    context_header: str  # "## Capsule Context"
    capsules: List[CapsuleOut]
    formatted_context: str  # Pre-formatted text ready for injection
    token_estimate: int
