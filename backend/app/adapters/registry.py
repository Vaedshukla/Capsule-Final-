"""
Adapter registry — selects the correct adapter for a given source slug.
"""
from app.adapters.base import ConversationAdapter
from app.adapters.chatgpt_adapter import ChatGPTAdapter
from app.adapters.platform_adapters import ClaudeAdapter, GeminiAdapter, GenericAdapter

_ADAPTERS: list[ConversationAdapter] = [
    ChatGPTAdapter(),
    ClaudeAdapter(),
    GeminiAdapter(),
    GenericAdapter(),  # Must be last (catch-all)
]


def get_adapter(source_slug: str) -> ConversationAdapter:
    """
    Returns the first adapter that can handle the given source slug.
    Falls back to GenericAdapter.
    """
    for adapter in _ADAPTERS:
        if adapter.can_handle(source_slug):
            return adapter
    return GenericAdapter()
