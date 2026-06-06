"""
OpenAI embedding provider.
Uses text-embedding-3-small (1536 dimensions).
Requires OPENAI_API_KEY in environment.
Configured via EMBEDDING_PROVIDER=openai in .env
"""
from typing import List
import structlog
from app.embeddings.base import EmbeddingProvider
from app.core.config import settings

logger = structlog.get_logger()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set to use OpenAI embeddings.")
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.EMBEDDING_MODEL_OPENAI

    @property
    def dimensions(self) -> int:
        return 1536  # text-embedding-3-small

    async def embed(self, text: str) -> List[float]:
        response = await self._client.embeddings.create(
            input=[text],
            model=self._model,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = await self._client.embeddings.create(
            input=texts,
            model=self._model,
        )
        # Return in the same order
        return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    async def health_check(self) -> bool:
        try:
            await self.embed("health check")
            return True
        except Exception as e:
            logger.warning("openai_embedding_health_check_failed", error=str(e))
            return False
