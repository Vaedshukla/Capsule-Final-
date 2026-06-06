"""
Text Chunker — splits message content into semantically coherent chunks.

WHY CHUNKING IS CRITICAL:
  A single assistant message may be 2,000+ tokens (code explanations, architecture
  docs, debugging sessions). Embedding the entire message as ONE vector creates:
    - Noisy, diluted embeddings (average of many different topics)
    - Poor retrieval precision (entire message matches or nothing does)
    - Wasted token budget on irrelevant content during injection

  By chunking into ~200-token segments with 40-token overlap:
    - Each chunk has a focused, coherent semantic meaning
    - Retrieval returns the SPECIFIC relevant passage, not the whole message
    - Context assembly can pick targeted excerpts

CHUNKING STRATEGY:
  1. Split on paragraph boundaries first (double newlines)
  2. If a paragraph > target_tokens, split further on sentence boundaries
  3. If a sentence > target_tokens, split on clause boundaries (semicolon, comma)
  4. Maintain overlap between adjacent chunks for context continuity
  5. Never split mid-word
"""
import re
from dataclasses import dataclass
from typing import List
import structlog

from app.core.config import settings

logger = structlog.get_logger()


from abc import ABC, abstractmethod

@dataclass
class TextChunk:
    content: str
    chunk_index: int
    token_count: int
    char_start: int
    char_end: int


class BaseChunker(ABC):
    """
    Abstract interface for extensible, language-aware chunking strategies.
    """
    def __init__(
        self,
        target_tokens: int | None = None,
        overlap_tokens: int | None = None,
    ):
        self.target_tokens = target_tokens or settings.CHUNK_TARGET_TOKENS
        self.overlap_tokens = overlap_tokens or settings.CHUNK_OVERLAP_TOKENS
        self._chars_per_token = 4

    @property
    def target_chars(self) -> int:
        return self.target_tokens * self._chars_per_token

    @property
    def overlap_chars(self) -> int:
        return self.overlap_tokens * self._chars_per_token

    @abstractmethod
    def chunk(self, text: str) -> List[TextChunk]:
        """Split text into chunks."""
        pass
        
    def _make_chunk(self, content: str, index: int, original: str) -> TextChunk:
        """Create a TextChunk with positional metadata."""
        start = original.find(content[:min(50, len(content))])
        if start == -1:
            start = 0
        return TextChunk(
            content=content,
            chunk_index=index,
            token_count=max(1, len(content) // self._chars_per_token),
            char_start=start,
            char_end=start + len(content),
        )


class MarkdownChunker(BaseChunker):

    @property
    def target_chars(self) -> int:
        return self.target_tokens * self._chars_per_token

    @property
    def overlap_chars(self) -> int:
        return self.overlap_tokens * self._chars_per_token

    def chunk(self, text: str) -> List[TextChunk]:
        """
        Split text into overlapping chunks respecting sentence boundaries.
        Returns list of TextChunk objects with positional metadata.
        """
        if not text or not text.strip():
            return []

        # Estimate token count: if short enough, return as single chunk
        estimated_tokens = len(text) // self._chars_per_token
        if estimated_tokens <= self.target_tokens:
            return [TextChunk(
                content=text.strip(),
                chunk_index=0,
                token_count=estimated_tokens,
                char_start=0,
                char_end=len(text),
            )]

        # Build sentence list
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks: List[TextChunk] = []
        current_sentences: List[str] = []
        current_chars = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_chars = len(sentence)

            # If adding this sentence exceeds target, flush current chunk
            if current_chars + sentence_chars > self.target_chars and current_sentences:
                chunk_content = " ".join(current_sentences).strip()
                if chunk_content:
                    chunks.append(self._make_chunk(chunk_content, chunk_index, text))
                    chunk_index += 1

                # Carry overlap: keep last N sentences for context continuity
                overlap_sentences = self._get_overlap_sentences(current_sentences)
                current_sentences = overlap_sentences
                current_chars = sum(len(s) for s in current_sentences)

            current_sentences.append(sentence)
            current_chars += sentence_chars

        # Flush remainder
        if current_sentences:
            chunk_content = " ".join(current_sentences).strip()
            if chunk_content:
                chunks.append(self._make_chunk(chunk_content, chunk_index, text))

        logger.debug(
            "text_chunked",
            original_tokens=estimated_tokens,
            chunk_count=len(chunks),
            target_tokens=self.target_tokens,
        )
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using a hierarchy of delimiters:
        indivisible blocks → paragraphs → sentences → clauses
        """
        sentences: List[str] = []

        # Phase 2: Identify indivisible markdown blocks (code blocks)
        # We replace them temporarily to prevent them from being split
        code_blocks = []
        
        def _preserve_block(match):
            block_content = match.group(0)
            idx = len(code_blocks)
            code_blocks.append(block_content)
            return f"\n\n__INDIVISIBLE_BLOCK_{idx}__\n\n"
            
        # Protect ``` blocks
        text = re.sub(r"```.*?```", _preserve_block, text, flags=re.DOTALL)

        # First split on paragraph breaks
        paragraphs = re.split(r'\n{2,}', text)

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # Restore indivisible blocks before measuring size
            restored_para = para
            for i, block in enumerate(code_blocks):
                placeholder = f"__INDIVISIBLE_BLOCK_{i}__"
                if placeholder in restored_para:
                    restored_para = restored_para.replace(placeholder, block)
                    
            para_chars = len(restored_para)
            
            if para_chars <= self.target_chars or "__INDIVISIBLE_BLOCK_" in para:
                # Paragraph fits in one chunk OR it contains an indivisible block
                # We NEVER split indivisible blocks, even if they exceed target size.
                sentences.append(restored_para)
            else:
                # Split normal paragraph into sentences
                raw_sentences = re.split(r'(?<=[.!?])\s+', restored_para)
                for sent in raw_sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(sent) <= self.target_chars:
                        sentences.append(sent)
                    else:
                        # Sentence too long — split on clause boundaries
                        clauses = re.split(r'(?<=[;,])\s+', sent)
                        for clause in clauses:
                            clause = clause.strip()
                            if clause:
                                sentences.append(clause)

        return [s for s in sentences if s.strip()]

    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """
        Return the last N sentences that fit within overlap budget.
        """
        overlap: List[str] = []
        total_chars = 0
        for sent in reversed(sentences):
            if total_chars + len(sent) > self.overlap_chars:
                break
            overlap.insert(0, sent)
            total_chars += len(sent)
        return overlap

    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """
        Return the last N sentences that fit within overlap budget.
        """
        overlap: List[str] = []
        total_chars = 0
        for sent in reversed(sentences):
            if total_chars + len(sent) > self.overlap_chars:
                break
            overlap.insert(0, sent)
            total_chars += len(sent)
        return overlap


# Default singleton instance (for backward compatibility / general use)
chunker = MarkdownChunker()
