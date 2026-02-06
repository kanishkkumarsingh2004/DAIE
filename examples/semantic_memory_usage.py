#!/usr/bin/env python3
"""
Examples of using the semantic memory system
"""

import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def example_knowledge_management():
    """Example of managing and querying knowledge"""
    logger = logging.getLogger(__name__)
    logger.info("=== Semantic Memory Usage Example ===\n")
    
    try:
        # Initialize components
        from agent_node_system.memory_system.semantic.embedding_engine import get_embedding_engine
        from agent_node_system.memory_system.semantic.knowledge_index import KnowledgeIndex
        from agent_node_system.memory_system.semantic.vector_store import get_vector_store
        
        logger.info("Initializing components...")
        engine = get_embedding_engine()
        vector_store = get_vector_store(persist_directory="./local_storage/chroma", dimension=768)
        knowledge_index = KnowledgeIndex(vector_store.client)
        
        logger.info("✓ Components initialized successfully\n")
        
        # Add knowledge items
        logger.info("Adding knowledge items...")
        
        # Add single item
        item1_id = knowledge_index.add_knowledge(
            content="Quantum computing uses quantum mechanics to solve problems faster than classical computers",
            summary="Quantum computing basics",
            category="quantum_computing",
            source="wikipedia",
            confidence=0.95,
            metadata={"difficulty": "advanced", "year": 2024}
        )
        
        # Add multiple items at once
        items = [
            {
                "content": "Machine learning is a subset of artificial intelligence that enables systems to learn without explicit programming",
                "summary": "Machine learning definition",
                "category": "artificial_intelligence",
                "source": "tech_blog",
                "confidence": 0.98,
                "metadata": {"difficulty": "intermediate"}
            },
            {
                "content": "Natural Language Processing (NLP) allows computers to understand and generate human language",
                "summary": "NLP basics",
                "category": "artificial_intelligence",
                "source": "academic_paper",
                "confidence": 0.96,
                "metadata": {"difficulty": "intermediate"}
            },
            {
                "content": "Docker containers provide isolated environments for running applications",
                "summary": "Docker containers",
                "category": "devops",
                "source": "documentation",
                "confidence": 0.99,
                "metadata": {"difficulty": "beginner"}
            }
        ]
        
        item_ids = knowledge_index.add_knowledge_batch(items)
        
        logger.info(f"✓ Added {1 + len(item_ids)} knowledge items\n")
        
        # Search knowledge
        logger.info("=== Searching for 'quantum computing' ===")
        quantum_results = knowledge_index.search_knowledge("quantum computing")
        
        for i, result in enumerate(quantum_results, 1):
            logger.info(f"{i}. {result['summary']}")
            logger.info(f"   Source: {result['source']}")
            logger.info(f"   Confidence: {result['confidence']:.2f}")
            logger.info(f"   Category: {result['category']}\n")
        
        logger.info("=== Searching for 'artificial intelligence' ===")
        ai_results = knowledge_index.search_knowledge("artificial intelligence")
        
        for i, result in enumerate(ai_results, 1):
            logger.info(f"{i}. {result['summary']}")
            logger.info(f"   Source: {result['source']}")
            logger.info(f"   Confidence: {result['confidence']:.2f}")
            logger.info(f"   Category: {result['category']}\n")
        
        logger.info("=== Searching for 'containers' with confidence ≥ 0.95 ===")
        container_results = knowledge_index.search_knowledge(
            "containers", min_confidence=0.95
        )
        
        for i, result in enumerate(container_results, 1):
            logger.info(f"{i}. {result['summary']}")
            logger.info(f"   Source: {result['source']}")
            logger.info(f"   Confidence: {result['confidence']:.2f}")
            logger.info(f"   Category: {result['category']}\n")
        
        # Category search
        logger.info("=== Searching in 'devops' category ===")
        devops_results = knowledge_index.search_knowledge(
            "docker", category="devops"
        )
        
        for i, result in enumerate(devops_results, 1):
            logger.info(f"{i}. {result['summary']}")
            logger.info(f"   Source: {result['source']}")
            logger.info(f"   Confidence: {result['confidence']:.2f}")
            logger.info(f"   Category: {result['category']}\n")
        
        # Get statistics
        stats = knowledge_index.get_statistics()
        logger.info("=== Knowledge Base Statistics ===")
        logger.info(f"Total items: {stats['total_items']}")
        logger.info(f"Categories: {stats['total_categories']}")
        logger.info("Category distribution:")
        for category, count in stats['category_distribution'].items():
            logger.info(f"  {category}: {count} items")
        
        logger.info("\n=== Vector Store Statistics ===")
        vs_stats = vector_store.get_statistics()
        logger.info(f"Total vectors: {vs_stats['total_vectors']}")
        logger.info(f"Vector dimension: {vs_stats['dimension']}")
        
        logger.info("\n=== All operations completed successfully ===")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

def example_vector_store_usage():
    """Example of using the vector store directly"""
    logger = logging.getLogger(__name__)
    logger.info("\n=== Vector Store Direct Usage Example ===\n")
    
    try:
        from agent_node_system.memory_system.semantic.vector_store import get_vector_store
        from agent_node_system.memory_system.semantic.embedding_engine import get_embedding_engine
        
        engine = get_embedding_engine()
        vector_store = get_vector_store(persist_directory="./local_storage/chroma", dimension=768)
        
        logger.info("Adding vectors...")
        
        # Add text with embeddings
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Machine learning models require training data",
            "Web development involves frontend and backend"
        ]
        
        for i, text in enumerate(texts):
            embedding = engine.generate_embedding(text)
            vector_store.add_vector(
                f"vector_{i}",
                embedding,
                {"text": text, "category": "test", "timestamp": datetime.now().isoformat()}
            )
        
        logger.info(f"✓ Added {len(texts)} vectors\n")
        
        # Search similar vectors
        logger.info("=== Searching for 'quick brown fox' ===")
        query = "quick brown fox"
        query_embedding = engine.generate_embedding(query)
        results = vector_store.search_vectors(query_embedding)
        
        logger.info(f"Found {len(results)} similar vectors:")
        for i, result in enumerate(results, 1):
            logger.info(f"{i}. Text: {result['metadata']['text']}")
            logger.info(f"   Similarity: {result['similarity']:.3f}")
            logger.info(f"   Vector ID: {result['vector_id']}")
            logger.info("")
        
        # Metadata search
        logger.info("=== Searching by category 'test' ===")
        metadata_results = vector_store.search_by_metadata({"category": "test"})
        logger.info(f"Found {len(metadata_results)} vectors in 'test' category")
        
        logger.info("\n=== Vector store statistics ===")
        stats = vector_store.get_statistics()
        logger.info(f"Total vectors: {stats['total_vectors']}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Create storage directory if needed
    os.makedirs("./local_storage/chroma", exist_ok=True)
    
    example_knowledge_management()
    example_vector_store_usage()
