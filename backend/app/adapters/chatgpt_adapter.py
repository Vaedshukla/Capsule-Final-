from datetime import datetime
from app.adapters.base import ConversationAdapter, NormalizedConversation, NormalizedMessage


class ChatGPTAdapter(ConversationAdapter):
    """
    Normalizes conversation payloads captured from ChatGPT (chatgpt.com).
    Handles the standard extension capture format.
    """

    def can_handle(self, source_slug: str) -> bool:
        return source_slug in ("chatgpt", "openai")

    def normalize(self, raw_payload: dict) -> NormalizedConversation:
        messages = raw_payload.get("messages", [])
        normalized_messages = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if not content.strip():
                continue

            # Normalize role names from ChatGPT variants
            if role in ("human", "user"):
                role = "user"
            elif role in ("assistant", "gpt", "chatgpt"):
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
            source_slug="chatgpt",
            source_url=raw_payload.get("url"),
            captured_at=datetime.utcnow(),
            messages=normalized_messages,
        )
