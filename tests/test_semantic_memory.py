#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Semantic Memory Tests

This module contains tests for the semantic memory system.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import pytest
import tempfile
import os
from datetime import datetime

from agent_node_system.memory_system.semantic.embedding_engine import EmbeddingEngine, get_embedding_engine
from agent_node_system.memory_system.semantic.vector_store import VectorStore, get_vector_store
from agent_node_system.memory_system.semantic.knowledge_index import KnowledgeIndex, KnowledgeItem

def test_embedding_engine_initialization():
    """Test embedding engine initialization"""
    engine = get_embedding_engine()
    assert isinstance(engine, EmbeddingEngine)
    assert engine.is_available() == True
    
def test_embedding_generation():
    """Test embedding generation"""
    engine = get_embedding_engine()
    
    # Test single embedding
    embedding = engine.generate_embedding("Hello, world!")
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, float) for x in embedding)
    
    # Test batch embedding
    texts = ["First text", "Second text", "Third text"]
    embeddings = engine.generate_embeddings(texts)
    assert len(embeddings) == 3
    assert all(embedding is not None and isinstance(embedding, list) for embedding in embeddings)
    
    # Test dimension consistency
    dim1 = len(embedding)
    dim2 = len(embeddings[0])
    assert dim1 == dim2
    
def test_vector_store_basic_operations(tmp_path):
    """Test vector store basic operations"""
    persist_dir = str(tmp_path / "chroma_db")
    vector_store = VectorStore(persist_directory=persist_dir, dimension=1536)
    
    # Test add vector
    vector_id = "test_vector_1"
    vector = [0.1] * 1536
    metadata = {"key": "value", "category": "test"}
    assert vector_store.add_vector(vector_id, vector, metadata) == True

    # Test get vector
    retrieved = vector_store.get_vector(vector_id)
    assert retrieved is not None
    assert retrieved["metadata"]["key"] == "value"

    # Test search vectors
    similar_vector = [0.15] * 1536
    results = vector_store.search_vectors(similar_vector, top_k=1)
    assert len(results) == 1
    assert results[0]["vector_id"] == vector_id
    
    # Test metadata search
    metadata_results = vector_store.search_by_metadata({"category": "test"})
    assert len(metadata_results) == 1
    assert metadata_results[0]["vector_id"] == vector_id
    
    # Test statistics
    stats = vector_store.get_statistics()
    assert stats["total_vectors"] == 1
    assert stats["dimension"] == 1536
    
    # Test remove vector
    assert vector_store.remove_vector(vector_id) == True
    assert vector_store.get_vector(vector_id) is None

def test_knowledge_index(tmp_path):
    """Test knowledge index operations"""
    from chromadb import PersistentClient
    
    # Initialize ChromaDB client
    persist_dir = str(tmp_path / "chroma_db")
    chroma_client = PersistentClient(path=persist_dir)
    
    # Create knowledge index
    index = KnowledgeIndex(chroma_client)
    
    # Test add knowledge
    content = "The capital of France is Paris"
    item_id = index.add_knowledge(
        content=content,
        summary="Paris is the capital of France",
        category="geography",
        source="wikipedia",
        confidence=0.95
    )
    assert len(item_id) > 0
    
    # Test get knowledge item
    item = index.get_knowledge_item(item_id)
    assert item is not None
    assert item["content"] == content
    assert item["category"] == "geography"
    
    # Test search knowledge
    search_results = index.search_knowledge("France capital", category="geography")
    assert len(search_results) > 0
    assert item_id in [result["item_id"] for result in search_results]
    
    # Test statistics
    stats = index.get_statistics()
    assert stats["total_items"] == 1
    assert stats["categories"] == 1
    
    # Test update knowledge
    assert index.update_knowledge_item(item_id, {"confidence": 0.98}) == True
    updated_item = index.get_knowledge_item(item_id)
    assert updated_item["confidence"] == 0.98
    
    # Test remove knowledge
    assert index.remove_knowledge_item(item_id) == True
    assert index.get_knowledge_item(item_id) is None
    
    # Test clear knowledge index
    item_id2 = index.add_knowledge(
        content="Python is a programming language",
        category="programming",
        source="official",
        confidence=0.99
    )
    assert index.get_statistics()["total_items"] == 1
    index.clear()
    assert index.get_statistics()["total_items"] == 0

def test_semantic_memory_integration(tmp_path):
    """Test integration of all semantic memory components"""
    from chromadb import PersistentClient
    
    # Initialize all components with persistent storage
    persist_dir = str(tmp_path / "chroma_db")
    
    # Test embedding engine
    engine = get_embedding_engine()
    embedding = engine.generate_embedding("Test integration")
    dim = len(embedding)
    
    # Test vector store
    vector_store = get_vector_store(persist_directory=persist_dir, dimension=dim)
    vector_id = "test_integration_vector"
    assert vector_store.add_vector(vector_id, embedding, {"purpose": "integration_test"})
    
    # Test retrieval from vector store
    retrieved = vector_store.get_vector(vector_id)
    assert retrieved is not None
    
    # Test search
    search_results = vector_store.search_vectors([0.05]*dim)
    assert len(search_results) == 1
    
    # Test knowledge index
    knowledge_index = KnowledgeIndex(vector_store.client, collection_name="integration_test")
    
    # Add knowledge
    knowledge_id = knowledge_index.add_knowledge(
        content="Machine learning uses algorithms to learn from data",
        summary="Machine learning is about learning from data",
        category="ai",
        source="course",
        confidence=0.9
    )
    
    # Test search in knowledge index
    search_results = knowledge_index.search_knowledge("machine learning")
    assert len(search_results) > 0
    assert any("learning" in result["content"].lower() for result in search_results)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
