"""
RAG (Retrieval-Augmented Generation) Engine.

Unified entry point for document chunking, indexing, and retrieval.
Supports pluggable backends (chroma, faiss, tfidf) and chunking
strategies (fixed, sentence, recursive, semantic).

Example:
    >>> engine = RAGEngine("/path/to/docs")  # default: chroma + fixed
    >>> engine.load()
    >>> context = engine.build_context("What is DAIE?")

    >>> engine = RAGEngine("/path/to/docs", backend="tfidf")  # lightweight fallback
    >>> engine.load()
    >>> results = engine.retrieve("query", top_k=5, filters={"source": "*.pdf"})
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from daie.rag.backends import RAGBackend, create_backend
from daie.rag.chunking import Chunk, ChunkingStrategy, create_chunker
from daie.rag.document_loader import load_directory

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.

    Loads documents, chunks them using a configurable strategy, indexes
    them with a pluggable backend, and retrieves the most relevant
    chunks for a given query.

    Backends:
        - ``"chroma"`` — ChromaDB + sentence-transformers (default)
        - ``"faiss"`` — FAISS + sentence-transformers
        - ``"tfidf"`` — Pure numpy TF-IDF (lightweight fallback, zero ML deps)

    Chunking strategies:
        - ``"fixed"`` — fixed-size with overlap (default)
        - ``"sentence"`` — sentence-boundary grouping
        - ``"recursive"`` — hierarchical paragraph→sentence→word
        - ``"semantic"`` — embedding-similarity based

    Example:
        >>> engine = RAGEngine("/path/to/docs")  # uses chroma by default
        >>> engine.load()
        >>> context = engine.build_context("What is DAIE?")
    """

    def __init__(
        self,
        document_path: str,
        backend: str = "chroma",
        chunking_strategy: str = "fixed",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        recursive: bool = False,
        **kwargs,
    ):
        """
        Args:
            document_path: Path to directory containing documents.
            backend: Backend engine — ``"chroma"`` (default), ``"faiss"``, or ``"tfidf"``.
            chunking_strategy: Chunking strategy — ``"fixed"``, ``"sentence"``,
                ``"recursive"``, or ``"semantic"``.
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of overlapping characters between chunks.
            recursive: If True, load documents from subdirectories too.
            **kwargs: Additional backend/chunker-specific options:
                - ``embedding_model``: Model name for vector backends (default: ``"all-MiniLM-L6-v2"``)
                - ``collection_name``: ChromaDB collection name
                - ``persist_directory``: ChromaDB persistence directory
                - ``index_type``: FAISS index type (``"flat"`` or ``"ivf"``)
                - ``similarity_threshold``: For semantic chunking (default: 0.5)
        """
        self.document_path = document_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.recursive = recursive

        self._backend: RAGBackend = create_backend(backend, **kwargs)
        self._chunker: ChunkingStrategy = create_chunker(
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        )
        self._chunks: List[Chunk] = []
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
        Load documents, chunk them, and build the search index.

        Returns:
            Number of chunks created.
        """
        documents = load_directory(self.document_path, recursive=self.recursive)
        if not documents:
            logger.warning(f"No documents found in '{self.document_path}'")
            self._loaded = True
            return 0

        # Chunk all documents
        self._chunks = []
        for doc in documents:
            self._chunks.extend(self._chunker.chunk(doc))

        if not self._chunks:
            logger.warning("No chunks were created from documents")
            self._loaded = True
            return 0

        # Index chunks with the backend
        self._backend.index(self._chunks)
        self._loaded = True

        logger.info(
            f"RAG engine loaded: {len(documents)} doc(s), "
            f"{len(self._chunks)} chunk(s), "
            f"backend={type(self._backend).__name__}"
        )
        return len(self._chunks)

    async def aload(self) -> int:
        """Async variant of load() — runs in a thread to avoid blocking."""
        return await asyncio.to_thread(self.load)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query: The search query string.
            top_k: Number of top results to return.
            filters: Optional metadata filters, e.g. ``{"source": "*.pdf"}``.

        Returns:
            List of (Chunk, similarity_score) tuples, highest score first.
        """
        if not self._loaded:
            logger.warning("RAG engine not loaded. Call load() first.")
            return []

        if not self._chunks:
            return []

        return self._backend.search(query, top_k=top_k, filters=filters)

    async def aretrieve(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        """Async variant of retrieve()."""
        return await asyncio.to_thread(self.retrieve, query, top_k, filters)

    def build_context(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Retrieve relevant chunks and format them as a context string
        suitable for injection into an LLM prompt.

        Args:
            query: The user's query.
            top_k: Number of chunks to include.
            filters: Optional metadata filters.

        Returns:
            Formatted context string, or empty string if no matches.
        """
        results = self.retrieve(query, top_k=top_k, filters=filters)
        if not results:
            return ""

        context_parts = []
        for i, (chunk, score) in enumerate(results, 1):
            context_parts.append(f"[Document {i}: {chunk.source}]\n{chunk.text}")

        return "\n\n".join(context_parts)

    async def abuild_context(
        self,
        query: str,
        top_k: int = 3,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Async variant of build_context()."""
        return await asyncio.to_thread(self.build_context, query, top_k, filters)

    def clear(self) -> None:
        """Clear all indexed data."""
        self._backend.clear()
        self._chunks = []
        self._loaded = False
