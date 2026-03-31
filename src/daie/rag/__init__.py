"""
RAG (Retrieval-Augmented Generation) module for the Decentralized AI Ecosystem.

Provides document loading, chunking, TF-IDF indexing, and cosine-similarity
retrieval so that agents can answer questions from loaded documents.

Example:
    >>> from daie.rag import RAGEngine
    >>> engine = RAGEngine("/path/to/docs")
    >>> engine.load()
    >>> context = engine.build_context("What is DAIE?")
"""

from daie.rag.document_loader import Document, load_directory
from daie.rag.rag_engine import RAGEngine
from daie.rag.vector_rag_engine import VectorRAGEngine

__all__ = ["RAGEngine", "VectorRAGEngine", "Document", "load_directory"]
