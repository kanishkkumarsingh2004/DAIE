"""
RAG (Retrieval-Augmented Generation) Engine.

Provides document chunking, TF-IDF indexing, and cosine-similarity retrieval
using only numpy (no external ML dependencies required).
"""

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from daie.rag.document_loader import Document, load_directory

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


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.

    Loads documents, chunks them, builds a TF-IDF index, and retrieves
    the most relevant chunks for a given query using cosine similarity.

    Uses only numpy — no heavy ML dependencies needed.

    Example:
        >>> engine = RAGEngine("/path/to/docs")
        >>> engine.load()
        >>> context = engine.build_context("What is DAIE?")
    """

    def __init__(
        self,
        document_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Args:
            document_path: Path to directory containing documents.
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of overlapping characters between chunks.
        """
        self.document_path = document_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._chunks: List[Chunk] = []
        self._vocabulary: Dict[str, int] = {}  # word -> index
        self._idf: Optional[np.ndarray] = None  # IDF weights
        self._tfidf_matrix: Optional[np.ndarray] = None  # (num_chunks, vocab_size)
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def num_chunks(self) -> int:
        return len(self._chunks)

    # ── public API ────────────────────────────────────────────────────────

    def load(self) -> int:
        """
        Load documents, chunk them, and build the TF-IDF index.

        Returns:
            Number of chunks created.
        """
        documents = load_directory(self.document_path)
        if not documents:
            logger.warning(f"No documents found in '{self.document_path}'")
            self._loaded = True
            return 0

        self._chunks = self._chunk_documents(documents)
        if not self._chunks:
            logger.warning("No chunks were created from documents")
            self._loaded = True
            return 0

        self._build_index()
        self._loaded = True
        logger.info(
            f"RAG engine loaded: {len(documents)} doc(s), "
            f"{len(self._chunks)} chunk(s), "
            f"{len(self._vocabulary)} unique terms"
        )
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[Chunk, float]]:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: The search query string.
            top_k: Number of top results to return.

        Returns:
            List of (Chunk, similarity_score) tuples, highest score first.
        """
        if not self._loaded or self._tfidf_matrix is None:
            logger.warning("RAG engine not loaded. Call load() first.")
            return []

        if not self._chunks:
            return []

        query_vec = self._text_to_tfidf(query)

        # Cosine similarity: dot(query, chunk) / (||query|| * ||chunk||)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        chunk_norms = np.linalg.norm(self._tfidf_matrix, axis=1)
        # Avoid division by zero
        chunk_norms = np.where(chunk_norms == 0, 1.0, chunk_norms)

        similarities = self._tfidf_matrix.dot(query_vec) / (chunk_norms * query_norm)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.05: # Minimal threshold
                results.append((self._chunks[idx], score))
        return results

    def build_context(self, query: str, top_k: int = 3) -> str:
        """
        Retrieve relevant chunks and format them as a context string
        suitable for injection into an LLM prompt.

        Args:
            query: The user's query.
            top_k: Number of chunks to include.

        Returns:
            Formatted context string, or empty string if no matches.
        """
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return ""

        context_parts = []
        for i, (chunk, score) in enumerate(results, 1):
            context_parts.append(f"--- Document Content ---\n{chunk.text}")

        return "\n\n".join(context_parts)

    # ── chunking ──────────────────────────────────────────────────────────

    def _chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """Split documents into overlapping chunks."""
        chunks: List[Chunk] = []

        for doc in documents:
            text = doc.content
            if len(text) <= self.chunk_size:
                chunks.append(Chunk(text=text, source=doc.source, chunk_index=0))
                continue

            start = 0
            chunk_idx = 0
            while start < len(text):
                end = start + self.chunk_size

                # Try to break at a sentence or paragraph boundary
                if end < len(text):
                    # Look for paragraph break
                    para_break = text.rfind("\n\n", start, end)
                    if para_break > start + self.chunk_size // 2:
                        end = para_break + 2
                    else:
                        # Look for sentence break
                        sent_break = text.rfind(". ", start, end)
                        if sent_break > start + self.chunk_size // 2:
                            end = sent_break + 2

                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append(
                        Chunk(text=chunk_text, source=doc.source, chunk_index=chunk_idx)
                    )
                    chunk_idx += 1

                start = end - self.chunk_overlap
                if start >= len(text):
                    break

        return chunks

    # ── TF-IDF indexing ───────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        text = text.lower()
        # Split on non-alphanumeric characters
        tokens = re.findall(r"[a-z0-9]+", text)
        # Remove very short tokens and common stop words
        stop_words = {
            "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "not", "with", "by", "from", "as",
            "this", "that", "be", "are", "was", "were", "been", "has",
            "have", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "can", "i", "you", "he", "she", "we", "they",
            "over", "under", "again", "further", "then", "once",
            "what", "where", "how", "when", "why", "who", "which",
        }
        return [t for t in tokens if len(t) > 1 and t not in stop_words]

    def _build_index(self) -> None:
        """Build vocabulary and TF-IDF matrix from chunks."""
        # Build vocabulary
        vocab: Dict[str, int] = {}
        chunk_token_lists: List[List[str]] = []

        for chunk in self._chunks:
            tokens = self._tokenize(chunk.text)
            chunk_token_lists.append(tokens)
            for token in set(tokens):  # unique tokens per chunk for DF
                if token not in vocab:
                    vocab[token] = len(vocab)

        self._vocabulary = vocab
        vocab_size = len(vocab)
        num_chunks = len(self._chunks)

        if vocab_size == 0:
            self._tfidf_matrix = np.zeros((num_chunks, 1))
            self._idf = np.zeros(1)
            return

        # Compute IDF: log(N / df) where df = number of chunks containing the term
        df = np.zeros(vocab_size)
        for tokens in chunk_token_lists:
            for token in set(tokens):
                if token in vocab:
                    df[vocab[token]] += 1

        self._idf = np.log((num_chunks + 1) / (df + 1)) + 1  # smoothed IDF

        # Compute TF-IDF matrix
        self._tfidf_matrix = np.zeros((num_chunks, vocab_size))
        for i, tokens in enumerate(chunk_token_lists):
            if not tokens:
                continue
            tf = Counter(tokens)
            for token, count in tf.items():
                if token in vocab:
                    j = vocab[token]
                    # TF: log(1 + count) for sublinear scaling
                    self._tfidf_matrix[i, j] = math.log(1 + count) * self._idf[j]

    def _text_to_tfidf(self, text: str) -> np.ndarray:
        """Convert a text string to a TF-IDF vector using the existing vocabulary."""
        vocab_size = len(self._vocabulary)
        if vocab_size == 0:
            return np.zeros(1)

        vec = np.zeros(vocab_size)
        tokens = self._tokenize(text)
        tf = Counter(tokens)

        for token, count in tf.items():
            if token in self._vocabulary:
                j = self._vocabulary[token]
                vec[j] = math.log(1 + count) * self._idf[j]

        return vec
