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

class AIProvider:
    async def generate_structured(self, prompt: str, response_model: type) -> any:
        import instructor
        from google import genai
        from app.core.config import settings
        
        # Instructor's from_genai wrapper uses the new google-genai SDK
        client = instructor.from_genai(genai.Client(api_key=settings.OPENAI_API_KEY))
        
        import asyncio
        return await asyncio.to_thread(
            client.chat.completions.create,
            model="gemini-2.5-flash",
            response_model=response_model,
            messages=[{"role": "user", "content": prompt}],
        )

@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    return AIProvider()
