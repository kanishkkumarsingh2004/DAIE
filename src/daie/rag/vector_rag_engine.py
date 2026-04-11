"""
Vector RAG Engine — Convenience wrapper.

.. deprecated::
    Use ``RAGEngine(backend="chroma")`` instead.
    This class is maintained for backward compatibility.
"""

import logging
import warnings
from typing import Optional

from daie.rag.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class VectorRAGEngine(RAGEngine):
    """
    Vector-based Retrieval-Augmented Generation engine.

    .. deprecated::
        Use ``RAGEngine(backend="chroma")`` instead.

    This is a thin backward-compatible wrapper around the unified
    ``RAGEngine`` with the ChromaDB backend.

    Example:
        >>> engine = VectorRAGEngine("/path/to/docs")
        >>> engine.load()
        >>> context = engine.build_context("What is DAIE?")
    """

    def __init__(
        self,
        document_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
    ):
        warnings.warn(
            "VectorRAGEngine is deprecated. Use RAGEngine(backend='chroma') instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        import os

        if persist_directory is None:
            persist_directory = os.path.join(document_path, ".chroma")
        if collection_name is None:
            collection_name = os.path.basename(os.path.abspath(document_path))

        super().__init__(
            document_path=document_path,
            backend="chroma",
            chunking_strategy="fixed",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=embedding_model,
            collection_name=collection_name,
            persist_directory=persist_directory,
        )

        # Expose for backward compat
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        self.persist_directory = persist_directory
