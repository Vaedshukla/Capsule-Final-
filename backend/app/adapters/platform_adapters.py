from datetime import datetime
from app.adapters.base import ConversationAdapter, NormalizedConversation, NormalizedMessage


class ClaudeAdapter(ConversationAdapter):
    def can_handle(self, source_slug: str) -> bool:
        return source_slug in ("claude", "anthropic")

    def normalize(self, raw_payload: dict) -> NormalizedConversation:
        messages = raw_payload.get("messages", [])
        normalized_messages = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if not content.strip():
                continue

            if role in ("human", "user"):
                role = "user"
            elif role in ("assistant", "claude"):
                role = "assistant"
            else:
                role = "system"

            content = self._clean_content(content)

            ts = msg.get("timestamp")
            message_timestamp = None
            if ts:
                try:
                    message_timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass

            normalized_messages.append(NormalizedMessage(
                role=role,
                content=content,
                position=i,
                token_count=self._estimate_tokens(content),
                message_timestamp=message_timestamp,
            ))

        return NormalizedConversation(
            title=raw_payload.get("title"),
            source_slug="claude",
            source_url=raw_payload.get("url"),
            captured_at=datetime.utcnow(),
            messages=normalized_messages,
        )


class GeminiAdapter(ConversationAdapter):
    def can_handle(self, source_slug: str) -> bool:
        return source_slug in ("gemini", "google")

    def normalize(self, raw_payload: dict) -> NormalizedConversation:
        messages = raw_payload.get("messages", [])
        normalized_messages = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if not content.strip():
                continue

            if role in ("human", "user"):
                role = "user"
            elif role in ("assistant", "model", "gemini"):
                role = "assistant"
            else:
                role = "system"

            content = self._clean_content(content)

            normalized_messages.append(NormalizedMessage(
                role=role,
                content=content,
                position=i,
                token_count=self._estimate_tokens(content),
                message_timestamp=None,
            ))

        return NormalizedConversation(
            title=raw_payload.get("title"),
            source_slug="gemini",
            source_url=raw_payload.get("url"),
            captured_at=datetime.utcnow(),
            messages=normalized_messages,
        )


class GenericAdapter(ConversationAdapter):
    """Fallback adapter for unknown sources."""

    def can_handle(self, source_slug: str) -> bool:
        return True  # Handles anything

    def normalize(self, raw_payload: dict) -> NormalizedConversation:
        messages = raw_payload.get("messages", [])
        normalized_messages = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if not content.strip():
                continue

            role = "user" if role in ("human", "user") else "assistant"
            content = self._clean_content(content)

            normalized_messages.append(NormalizedMessage(
                role=role,
                content=content,
                position=i,
                token_count=self._estimate_tokens(content),
                message_timestamp=None,
            ))

        return NormalizedConversation(
            title=raw_payload.get("title"),
            source_slug=raw_payload.get("source", "unknown"),
            source_url=raw_payload.get("url"),
            captured_at=datetime.utcnow(),
            messages=normalized_messages,
        )
