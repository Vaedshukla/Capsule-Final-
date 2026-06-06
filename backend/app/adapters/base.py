"""
Backend-side Platform Adapters.
These handle parsing of conversation exports/payloads from different AI sources.
Each adapter normalizes a raw payload into a list of normalized messages.

Note: DOM extraction happens in the browser extension.
These adapters handle the server-side parsing and normalization of what the extension sends.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class NormalizedMessage:
    role: str               # "user" | "assistant" | "system"
    content: str
    position: int           # 0-indexed order
    token_count: Optional[int] = None
    message_timestamp: Optional[datetime] = None


@dataclass
class NormalizedConversation:
    title: Optional[str]
    source_slug: str        # "chatgpt" | "claude" | "gemini" | "cursor" | "unknown"
    source_url: Optional[str]
    captured_at: datetime
    messages: List[NormalizedMessage]


class ConversationAdapter(ABC):
    """
    Abstract adapter for normalizing raw conversation payloads
    from different AI platform sources.
    """

    @abstractmethod
    def can_handle(self, source_slug: str) -> bool:
        """Return True if this adapter handles the given source slug."""
        ...

    @abstractmethod
    def normalize(self, raw_payload: dict) -> NormalizedConversation:
        """
        Parse the raw ingestion payload into a NormalizedConversation.
        The raw_payload matches the CapturePayload structure from the extension.
        """
        ...

    def _clean_content(self, content: str) -> str:
        """Strip excessive whitespace from message content."""
        return " ".join(content.split()).strip()

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)
