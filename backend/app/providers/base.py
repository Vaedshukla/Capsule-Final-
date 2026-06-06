from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.ai_response import AIResponse

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> "AIResponse":
        """
        Generate a single response block.
        Must return normalized AIResponse schema.
        """
        pass
        
    @abstractmethod
    async def generate_structured(self, prompt: str, response_model: type, **kwargs) -> Any:
        """
        Generate a strictly structured response matching the Pydantic response_model.
        """
        pass
        
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream the response block chunk by chunk.
        """
        pass
        
    @abstractmethod
    async def embeddings(self, text: str, **kwargs) -> list[float]:
        """
        Generate embeddings for the given text.
        """
        pass
        
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the provider.
        Returns:
        {
            "status": "HEALTHY" | "DEGRADED" | "OFFLINE",
            "latency": float
        }
        """
        pass
        
    @abstractmethod
    async def estimate_cost(self, prompt: str, **kwargs) -> float:
        """
        Estimate the cost of a request based on provider pricing.
        """
        pass

    @abstractmethod
    async def count_tokens(self, text: str, **kwargs) -> int:
        """
        Count the number of tokens in the given text for this provider/model.
        """
        pass
        
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """
        Validate that the provided API keys/credentials are functional.
        """
        pass
