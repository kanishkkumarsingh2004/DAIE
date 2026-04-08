"""
Pluggable document chunking strategies for the RAG engine.

Provides multiple strategies for splitting documents into chunks:
- FixedSizeChunker: overlap-based character chunking (default)
- SentenceChunker: split on sentence boundaries
- RecursiveChunker: hierarchical split (paragraph → sentence → word)
- SemanticChunker: group sentences by semantic similarity (requires embeddings)
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from daie.rag.document_loader import Document

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A chunk of text extracted from a document."""

    text: str
    """The text content of the chunk."""

    source: str
    """Source file path."""

    chunk_index: int
    """Index of this chunk within the source document."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata for the chunk."""


class ChunkingStrategy(ABC):
    """Abstract base class for document chunking strategies."""

    @abstractmethod
    def chunk(self, document: Document) -> List[Chunk]:
        """
        Split a document into chunks.

        Args:
            document: The document to chunk.

        Returns:
            List of Chunk objects.
        """


class FixedSizeChunker(ChunkingStrategy):
    """
    Fixed-size character chunking with overlap.

    Attempts to break at paragraph or sentence boundaries within the
    chunk size window. Falls back to hard character boundaries.

    This is the default chunking strategy (extracted from original RAGEngine).
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: Document) -> List[Chunk]:
        text = document.content
        doc_meta = getattr(document, "metadata", {}) or {}
        base_meta = {"source": document.source, **doc_meta}

        if len(text) <= self.chunk_size:
            return [Chunk(text=text, source=document.source, chunk_index=0, metadata=base_meta)]

        chunks: List[Chunk] = []
        start = 0
        chunk_idx = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at a sentence or paragraph boundary
            if end < len(text):
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + self.chunk_size // 2:
                    end = para_break + 2
                else:
                    sent_break = text.rfind(". ", start, end)
                    if sent_break > start + self.chunk_size // 2:
                        end = sent_break + 2

            chunk_text = text[start:end].strip()
            if chunk_text:
                meta = {**base_meta, "chunk_index": chunk_idx}
                chunks.append(
                    Chunk(text=chunk_text, source=document.source, chunk_index=chunk_idx, metadata=meta)
                )
                chunk_idx += 1

            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks


class SentenceChunker(ChunkingStrategy):
    """
    Sentence-boundary chunking.

    Splits text into sentences, then groups consecutive sentences
    until the target chunk size is reached.
    """

    # Regex handles abbreviations like Mr., Dr., etc. reasonably well
    _SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

    def __init__(self, chunk_size: int = 500, chunk_overlap_sentences: int = 1):
        self.chunk_size = chunk_size
        self.chunk_overlap_sentences = chunk_overlap_sentences

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = self._SENTENCE_RE.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, document: Document) -> List[Chunk]:
        doc_meta = getattr(document, "metadata", {}) or {}
        base_meta = {"source": document.source, **doc_meta}
        sentences = self._split_sentences(document.content)

        if not sentences:
            return []

        chunks: List[Chunk] = []
        chunk_idx = 0
        i = 0

        while i < len(sentences):
            current_chunk: List[str] = []
            current_len = 0

            while i < len(sentences):
                sent_len = len(sentences[i])
                if current_len + sent_len > self.chunk_size and current_chunk:
                    break
                current_chunk.append(sentences[i])
                current_len += sent_len + 1  # +1 for space
                i += 1

            chunk_text = " ".join(current_chunk)
            if chunk_text:
                meta = {**base_meta, "chunk_index": chunk_idx}
                chunks.append(
                    Chunk(text=chunk_text, source=document.source, chunk_index=chunk_idx, metadata=meta)
                )
                chunk_idx += 1

            # Overlap: back up by overlap_sentences
            i -= self.chunk_overlap_sentences

        return chunks


class RecursiveChunker(ChunkingStrategy):
    """
    Recursive (hierarchical) chunking.

    Tries to split on paragraphs first, then sentences, then words.
    Inspired by LangChain's RecursiveCharacterTextSplitter.
    """

    _SEPARATORS = ["\n\n", "\n", ". ", " "]

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using a hierarchy of separators."""
        if not separators:
            return [text] if text.strip() else []

        sep = separators[0]
        remaining_seps = separators[1:]
        parts = text.split(sep)

        results: List[str] = []
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    results.append(current)
                # If the part itself is too large, recurse with next separator
                if len(part) > self.chunk_size and remaining_seps:
                    sub_parts = self._split_recursive(part, remaining_seps)
                    results.extend(sub_parts)
                    current = ""
                else:
                    current = part

        if current:
            results.append(current)

        return results

    def chunk(self, document: Document) -> List[Chunk]:
        doc_meta = getattr(document, "metadata", {}) or {}
        base_meta = {"source": document.source, **doc_meta}

        raw_chunks = self._split_recursive(document.content, self._SEPARATORS)

        chunks: List[Chunk] = []
        for chunk_idx, text in enumerate(raw_chunks):
            text = text.strip()
            if text:
                meta = {**base_meta, "chunk_index": chunk_idx}
                chunks.append(
                    Chunk(text=text, source=document.source, chunk_index=chunk_idx, metadata=meta)
                )

        return chunks


class SemanticChunker(ChunkingStrategy):
    """
    Semantic chunking using sentence embeddings.

    Groups consecutive sentences whose embeddings are similar
    above a threshold, then splits when similarity drops.

    Requires sentence-transformers (optional dependency).
    """

    def __init__(
        self,
        chunk_size: int = 500,
        similarity_threshold: float = 0.5,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.chunk_size = chunk_size
        self.similarity_threshold = similarity_threshold
        self.embedding_model_name = embedding_model
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.embedding_model_name)
            except ImportError:
                raise ImportError(
                    "SemanticChunker requires sentence-transformers. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, document: Document) -> List[Chunk]:
        import numpy as np

        doc_meta = getattr(document, "metadata", {}) or {}
        base_meta = {"source": document.source, **doc_meta}
        sentences = self._split_sentences(document.content)

        if not sentences:
            return []

        if len(sentences) == 1:
            return [
                Chunk(
                    text=sentences[0],
                    source=document.source,
                    chunk_index=0,
                    metadata=base_meta,
                )
            ]

        model = self._get_model()
        embeddings = model.encode(sentences)

        # Compute cosine similarity between consecutive sentences
        chunks: List[Chunk] = []
        chunk_idx = 0
        current_group: List[str] = [sentences[0]]

        for i in range(1, len(sentences)):
            # Cosine similarity
            sim = np.dot(embeddings[i - 1], embeddings[i]) / (
                np.linalg.norm(embeddings[i - 1]) * np.linalg.norm(embeddings[i]) + 1e-8
            )

            current_text = " ".join(current_group)

            # Split if similarity drops OR chunk size exceeded
            if sim < self.similarity_threshold or len(current_text) + len(sentences[i]) > self.chunk_size:
                if current_text.strip():
                    meta = {**base_meta, "chunk_index": chunk_idx}
                    chunks.append(
                        Chunk(
                            text=current_text.strip(),
                            source=document.source,
                            chunk_index=chunk_idx,
                            metadata=meta,
                        )
                    )
                    chunk_idx += 1
                current_group = [sentences[i]]
            else:
                current_group.append(sentences[i])

        # Final group
        final_text = " ".join(current_group).strip()
        if final_text:
            meta = {**base_meta, "chunk_index": chunk_idx}
            chunks.append(
                Chunk(
                    text=final_text,
                    source=document.source,
                    chunk_index=chunk_idx,
                    metadata=meta,
                )
            )

        return chunks


# ── Factory ───────────────────────────────────────────────────────────────────

_CHUNKER_REGISTRY = {
    "fixed": FixedSizeChunker,
    "sentence": SentenceChunker,
    "recursive": RecursiveChunker,
    "semantic": SemanticChunker,
}


def create_chunker(
    strategy: str = "fixed",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    **kwargs,
) -> ChunkingStrategy:
    """
    Factory function to create a chunking strategy.

    Args:
        strategy: One of "fixed", "sentence", "recursive", "semantic".
        chunk_size: Maximum chunk size in characters.
        chunk_overlap: Overlap between chunks (for strategies that support it).
        **kwargs: Additional arguments passed to the chunker.

    Returns:
        A ChunkingStrategy instance.
    """
    cls = _CHUNKER_REGISTRY.get(strategy)
    if cls is None:
        raise ValueError(
            f"Unknown chunking strategy '{strategy}'. "
            f"Available: {list(_CHUNKER_REGISTRY.keys())}"
        )

    if strategy == "fixed":
        return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    elif strategy == "sentence":
        return cls(chunk_size=chunk_size, chunk_overlap_sentences=kwargs.get("chunk_overlap_sentences", 1))
    elif strategy == "recursive":
        return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    elif strategy == "semantic":
        return cls(
            chunk_size=chunk_size,
            similarity_threshold=kwargs.get("similarity_threshold", 0.5),
            embedding_model=kwargs.get("embedding_model", "all-MiniLM-L6-v2"),
        )
    return cls(chunk_size=chunk_size)
