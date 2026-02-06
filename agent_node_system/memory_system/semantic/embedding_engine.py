#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Embedding Engine

This module provides functionality for generating semantic embeddings for text
content using local embedding models.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
from typing import List, Optional
import os
from langchain_community.embeddings import OllamaEmbeddings

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    """
    Semantic Embedding Engine
    
    Provides functionality for generating semantic embeddings from text content
    using local embedding models.
    """
    
    def __init__(self, model_name: str = "nomic-embed-text", model_source: str = "ollama"):
        """
        Initialize the embedding engine
        
        Args:
            model_name: Name of the embedding model to use
            model_source: Source of the embedding model (ollama)
        """
        self.model_name = model_name
        self.model_source = model_source
        self.embeddings = None
        
        try:
            if model_source == "ollama":
                logger.info(f"Initializing OllamaEmbeddings with model: {model_name}")
                self.embeddings = OllamaEmbeddings(model=model_name)
            else:
                raise ValueError(f"Unsupported model source: {model_source}")
                
            logger.info("Embedding engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embedding engine: {e}")
            raise
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate a semantic embedding for a single text
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            list: Embedding vector, or None if generation fails
        """
        try:
            if not text or not isinstance(text, str):
                logger.warning("Invalid text input for embedding generation")
                return None
                
            embedding = self.embeddings.embed_query(text.strip())
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def generate_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate semantic embeddings for multiple texts
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            list: List of embedding vectors
        """
        try:
            valid_texts = [text.strip() for text in texts if text and isinstance(text, str)]
            if not valid_texts:
                logger.warning("No valid texts for embedding generation")
                return []
                
            embeddings = self.embeddings.embed_documents(valid_texts)
            logger.debug(f"Generated {len(embeddings)} embeddings for {len(texts)} texts")
            
            results = []
            idx = 0
            for text in texts:
                if text and isinstance(text, str):
                    results.append(embeddings[idx])
                    idx += 1
                else:
                    results.append(None)
                    
            return results
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return [None] * len(texts)
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimensionality of the generated embeddings
        
        Returns:
            int: Embedding dimension
        """
        try:
            test_embedding = self.generate_embedding("test")
            if test_embedding:
                return len(test_embedding)
            logger.warning("Could not determine embedding dimension")
            return 1536  # Default to OpenAI compatible dimension
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}")
            return 1536
    
    def is_available(self) -> bool:
        """
        Check if the embedding engine is available and operational
        
        Returns:
            bool: True if engine is available, False otherwise
        """
        try:
            test_embedding = self.generate_embedding("availability test")
            return test_embedding is not None
        except Exception as e:
            logger.error(f"Embedding engine not available: {e}")
            return False


# Singleton instance for the agent node
_embedding_engine_instance = None

def get_embedding_engine(model_name: str = "nomic-embed-text", 
                       model_source: str = "ollama") -> EmbeddingEngine:
    """
    Get a singleton instance of the embedding engine
    
    Args:
        model_name: Name of the embedding model to use
        model_source: Source of the embedding model (ollama)
        
    Returns:
        EmbeddingEngine: Singleton instance
    """
    global _embedding_engine_instance
    if _embedding_engine_instance is None:
        _embedding_engine_instance = EmbeddingEngine(model_name, model_source)
    return _embedding_engine_instance
