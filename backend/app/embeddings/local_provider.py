"""
Local embedding provider using sentence-transformers.
Fully offline. Privacy-preserving. No API key required.

Recommended model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)

Install: uv pip install capsule-backend[local-embeddings]
"""
from typing import List
import structlog
from app.embeddings.base import EmbeddingProvider
from app.core.config import settings

logger = structlog.get_logger()


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self._model = None
        self._model_name = settings.EMBEDDING_MODEL_LOCAL

    def _load_model(self):
        """Lazy-load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("loading_local_embedding_model", model=self._model_name)
                self._model = SentenceTransformer(self._model_name)
                logger.info("local_embedding_model_ready", model=self._model_name)
            except ImportError:
                raise RuntimeError(
                    "sentence-transformers is not installed. "
                    "Run: uv pip install 'capsule-backend[local-embeddings]'"
                )

    @property
    def dimensions(self) -> int:
        return 384  # all-MiniLM-L6-v2 output size

    async def embed(self, text: str) -> List[float]:
        self._load_model()
        import asyncio
        loop = asyncio.get_event_loop()
        # Run in thread pool to avoid blocking the event loop
        embedding = await loop.run_in_executor(
            None, lambda: self._model.encode(text, normalize_embeddings=True).tolist()
        )
        return embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        import asyncio
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: self._model.encode(texts, normalize_embeddings=True).tolist()
        )
        return embeddings

    async def health_check(self) -> bool:
        try:
            self._load_model()
            return self._model is not None
        except Exception:
            return False
