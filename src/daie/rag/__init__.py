"""
RAG (Retrieval-Augmented Generation) module for the Decentralized AI Ecosystem.

Provides document loading, chunking, indexing, and retrieval with pluggable
backends and chunking strategies.

Backends:
    - ``"tfidf"`` — Pure numpy TF-IDF (default, zero ML deps)
    - ``"chroma"`` — ChromaDB + sentence-transformers
    - ``"faiss"`` — FAISS + sentence-transformers

Chunking strategies:
    - ``"fixed"`` — fixed-size with overlap (default)
    - ``"sentence"`` — sentence-boundary grouping
    - ``"recursive"`` — hierarchical paragraph→sentence→word
    - ``"semantic"`` — embedding-similarity based

Example:
    >>> from daie.rag import RAGEngine
    >>> engine = RAGEngine("/path/to/docs", backend="tfidf")
    >>> engine.load()
    >>> context = engine.build_context("What is DAIE?")

    >>> # With ChromaDB backend and recursive chunking
    >>> engine = RAGEngine("/path/to/docs", backend="chroma", chunking_strategy="recursive")
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
