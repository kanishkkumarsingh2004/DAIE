"""
Tests for the RAG (Retrieval-Augmented Generation) Engine.
"""

import os
import tempfile

import pytest

from daie.rag import RAGEngine


def test_rag_engine_loading_and_retrieval():
    """Test that RAGEngine loads documents and retrieves relevant chunks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test documents
        doc1_path = os.path.join(temp_dir, "test1.txt")
        with open(doc1_path, "w") as f:
            f.write("The capital of France is Paris. It is known for the Eiffel Tower.")

        doc2_path = os.path.join(temp_dir, "test2.txt")
        with open(doc2_path, "w") as f:
            f.write("The capital of Japan is Tokyo. It is known for its sushi and technology.")

        # Initialize engine
        engine = RAGEngine(temp_dir, chunk_size=100, chunk_overlap=10)
        num_chunks = engine.load()

        assert num_chunks >= 2
        assert engine.is_loaded

        # Test retrieval for France
        results = engine.retrieve("What is the capital of France?", top_k=1)
        assert len(results) > 0
        chunk, score = results[0]
        assert "Paris" in chunk.text
        assert "France" in chunk.text

        # Test retrieval for Japan
        results = engine.retrieve("Tell me about Tokyo", top_k=1)
        assert len(results) > 0
        chunk, score = results[0]
        assert "Tokyo" in chunk.text
        assert "Japan" in chunk.text

        # Test context building
        context = engine.build_context("France capital")
        assert "Paris" in context
        assert "[Document 1:" in context


def test_rag_engine_no_docs():
    """Test engine behavior with an empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        engine = RAGEngine(temp_dir)
        num_chunks = engine.load()
        assert num_chunks == 0
        assert engine.is_loaded

        results = engine.retrieve("anything")
        assert len(results) == 0

        context = engine.build_context("anything")
        assert context == ""


def test_rag_engine_tokenization():
    """Test that tokenization works correctly (stop words, etc)."""
    engine = RAGEngine("/tmp")  # path doesn't matter for tokenization test
    tokens = engine._tokenize("The quick brown fox jumps over the lazy dog.")

    # "the", "over" should be removed as stop words
    assert "the" not in tokens
    assert "over" not in tokens
    assert "quick" in tokens
    assert "lazy" in tokens
    assert "dog" in tokens


if __name__ == "__main__":
    pytest.main([__file__])
