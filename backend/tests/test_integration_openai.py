import pytest
import asyncio
from app.providers.openai_provider import OpenAIProvider
from app.compression.capsule_builder import CapsuleExtractionSchema
from app.core.config import settings

@pytest.mark.asyncio
async def test_openai_embeddings():
    # Only run if API key is set
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not set")
        
    provider = OpenAIProvider()
    vector = await provider.embeddings("This is a test sentence for embeddings.")
    
    assert len(vector) == 1536
    assert isinstance(vector[0], float)

@pytest.mark.asyncio
async def test_openai_structured_extraction():
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not set")
        
    provider = OpenAIProvider()
    
    prompt = "We decided to migrate our frontend from React to Vue because of performance issues. We must use TypeScript. This migration relies on the assumption that our team can learn Vue in two weeks. A risk is that third party libraries might not support Vue 3."
    
    extraction = await provider.generate_structured(
        prompt=prompt,
        response_model=CapsuleExtractionSchema
    )
    
    assert isinstance(extraction, CapsuleExtractionSchema)
    assert any("Vue" in d for d in extraction.decisions)
    assert any("TypeScript" in c for c in extraction.constraints)
    assert any("risk" in r.lower() for r in extraction.risks) or len(extraction.risks) > 0
    assert any("assumption" in a.lower() for a in extraction.assumptions) or len(extraction.assumptions) > 0
