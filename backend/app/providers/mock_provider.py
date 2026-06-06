import asyncio
import time
from typing import AsyncGenerator, Dict, Any
from app.providers.base import BaseAIProvider

class MockProvider(BaseAIProvider):
    def __init__(self, name: str = "mock", model: str = "mock-v1"):
        self.name = name
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        await asyncio.sleep(0.5) # Simulate latency
        end_time = time.time()
        
        return {
            "provider": self.name,
            "model": self.model,
            "content": f"Mock response for: {prompt}",
            "tokens_used": len(prompt.split()) + 5,
            "latency_ms": (end_time - start_time) * 1000
        }

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        words = f"Mock streamed response for: {prompt}".split()
        for word in words:
            await asyncio.sleep(0.1) # Simulate stream latency
            yield word + " "

    async def embeddings(self, text: str, **kwargs) -> list[float]:
        await asyncio.sleep(0.1)
        return [0.1, 0.2, 0.3] * 512 # Mock 1536 dim embedding

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "latency": 50.0
        }

    async def estimate_cost(self, prompt: str, **kwargs) -> float:
        return 0.0001
