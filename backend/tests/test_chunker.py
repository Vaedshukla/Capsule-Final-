import pytest
from app.ingestion.chunker import TextChunker

def test_chunker_short_text():
    chunker = TextChunker(target_tokens=50)
    text = "This is a short sentence."
    chunks = chunker.chunk(text)
    
    assert len(chunks) == 1
    assert chunks[0].content == text
    assert chunks[0].chunk_index == 0

def test_chunker_respects_sentence_boundaries():
    # Target is small enough to force a split
    chunker = TextChunker(target_tokens=10, overlap_tokens=0)
    # 40 chars ~ 10 tokens
    text = "First sentence here. Second sentence here. Third sentence here."
    chunks = chunker.chunk(text)
    
    # Should split near sentences, not mid-word
    assert len(chunks) > 1
    for c in chunks:
        assert not c.content.startswith(" ")
        assert not c.content.endswith(" ")

def test_chunker_overlap():
    chunker = TextChunker(target_tokens=15, overlap_tokens=5)
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    chunks = chunker.chunk(text)
    
    if len(chunks) > 1:
        # Check that some text from chunk 0 appears in chunk 1
        words_0 = set(chunks[0].content.split())
        words_1 = set(chunks[1].content.split())
        assert len(words_0.intersection(words_1)) > 0
