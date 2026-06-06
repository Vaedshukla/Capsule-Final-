"""
Embedding provider factory.
Selects the correct provider based on settings.EMBEDDING_PROVIDER.
"""
from functools import lru_cache
from app.embeddings.base import EmbeddingProvider
from app.core.config import settings


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """
    Returns a cached singleton embedding provider.
    Configured via EMBEDDING_PROVIDER env var: "local" or "openai"
    """
    if settings.EMBEDDING_PROVIDER == "openai":
        from app.embeddings.openai_provider import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider()
    else:
        from app.embeddings.local_provider import LocalEmbeddingProvider
        return LocalEmbeddingProvider()
