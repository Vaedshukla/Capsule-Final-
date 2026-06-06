from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Abstract base class for all embedding providers.
    Capsule treats embeddings as pluggable — local or cloud-based.
    """

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Number of dimensions in the output embedding vector."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text string."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of texts (more efficient)."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is functional."""
        ...
