"""
RAG (Retrieval-Augmented Generation) module for the Decentralized AI Ecosystem.

Provides document loading, chunking, indexing, and retrieval with pluggable
backends and chunking strategies.

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
    >>> from daie.rag import RAGEngine
    >>> engine = RAGEngine("/path/to/docs")  # uses chroma by default
    >>> engine.load()
    >>> context = engine.build_context("What is DAIE?")

    >>> # Lightweight fallback (no ML dependencies needed)
    >>> engine = RAGEngine("/path/to/docs", backend="tfidf")
    >>> engine.load()
    >>> results = engine.retrieve("query", filters={"source": "*.pdf"})
"""

from daie.rag.backends import (
    ChromaBackend,
    FAISSBackend,
    RAGBackend,
    TFIDFBackend,
    create_backend,
)
from daie.rag.chunking import (
    Chunk,
    ChunkingStrategy,
    FixedSizeChunker,
    RecursiveChunker,
    SemanticChunker,
    SentenceChunker,
    create_chunker,
)
from daie.rag.document_loader import Document, load_directory
from daie.rag.rag_engine import RAGEngine
from daie.rag.vector_rag_engine import VectorRAGEngine

__all__ = [
    # Main engine
    "RAGEngine",
    "VectorRAGEngine",
    # Backends
    "RAGBackend",
    "TFIDFBackend",
    "ChromaBackend",
    "FAISSBackend",
    "create_backend",
    # Chunking
    "Chunk",
    "ChunkingStrategy",
    "FixedSizeChunker",
    "SentenceChunker",
    "RecursiveChunker",
    "SemanticChunker",
    "create_chunker",
    # Document loading
    "Document",
    "load_directory",
]
