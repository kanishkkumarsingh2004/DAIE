#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Semantic Vector Store

This module provides functionality for storing and retrieving semantic vectors
for knowledge and context management using ChromaDB as the local vector database.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Semantic Vector Store
    
    Provides functionality for storing and retrieving semantic vectors with
    associated metadata for knowledge management using ChromaDB.
    """
    
    def __init__(self, persist_directory: str = "./local_storage/chroma", dimension: int = 1536):
        """
        Initialize the vector store
        
        Args:
            persist_directory: Directory for persistent storage
            dimension: Dimensionality of the vectors (default: 1536 for OpenAI compatible embeddings)
        """
        self.dimension = dimension
        self.persist_directory = persist_directory
        
        try:
            # Create persistent directory if it doesn't exist
            os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    persist_directory=persist_directory
                )
            )
            
            # Create or get the vector store collection
            self.collection = self.client.get_or_create_collection(
                name="semantic_memory",
                metadata={"dimension": dimension}
            )
            
            logger.info(f"Vector store initialized with {dimension}-dimensional vectors")
            logger.debug(f"ChromaDB persistent storage at: {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def add_vector(self, vector_id: str, vector: list, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a vector to the store
        
        Args:
            vector_id: Unique identifier for the vector
            vector: The vector to store
            metadata: Optional metadata associated with the vector
            
        Returns:
            bool: True if vector added successfully, False otherwise
        """
        try:
            if len(vector) != self.dimension:
                logger.error(f"Vector dimension mismatch. Expected {self.dimension}, got {len(vector)}")
                return False
            
            metadata = metadata or {}
            metadata["timestamp"] = datetime.now().isoformat()
            
            self.collection.add(
                ids=[vector_id],
                embeddings=[vector],
                metadatas=[metadata]
            )
            
            logger.debug(f"Vector {vector_id} added to store")
            return True
        except Exception as e:
            logger.error(f"Failed to add vector: {e}")
            return False
    
    def get_vector(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a vector from the store
        
        Args:
            vector_id: Unique identifier for the vector
            
        Returns:
            dict: Vector and metadata, or None if not found
        """
        try:
            results = self.collection.get(ids=[vector_id], include=["embeddings", "metadatas"])
            if results and results["ids"] and len(results["ids"]) > 0:
                vector = results["embeddings"][0]
                metadata = results["metadatas"][0]
                return {
                    "vector": vector,
                    "metadata": metadata,
                    "timestamp": datetime.fromisoformat(metadata["timestamp"])
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get vector: {e}")
            return None
    
    def remove_vector(self, vector_id: str) -> bool:
        """
        Remove a vector from the store
        
        Args:
            vector_id: Unique identifier for the vector
            
        Returns:
            bool: True if vector removed successfully, False if not found
        """
        try:
            self.collection.delete(ids=[vector_id])
            logger.debug(f"Vector {vector_id} removed from store")
            return True
        except Exception as e:
            logger.error(f"Failed to remove vector: {e}")
            return False
    
    def search_vectors(self, query_vector: list, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query vector
            top_k: Number of top results to return (default: 10)
            
        Returns:
            list: List of most similar vectors with scores
        """
        try:
            if len(query_vector) != self.dimension:
                logger.error(f"Query vector dimension mismatch. Expected {self.dimension}, got {len(query_vector)}")
                return []
            
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["embeddings", "metadatas", "documents", "distances"]
            )
            
            formatted_results = []
            for i, (vector_id, vector, metadata, distance) in enumerate(zip(
                results["ids"][0],
                results["embeddings"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                formatted_results.append({
                    "vector_id": vector_id,
                    "vector": vector,
                    "metadata": metadata,
                    "similarity": 1 / (1 + distance),  # Convert distance to similarity score
                    "timestamp": datetime.fromisoformat(metadata["timestamp"])
                })
            
            # Sort by similarity descending
            formatted_results.sort(key=lambda x: x["similarity"], reverse=True)
            
            logger.debug(f"Found {len(formatted_results)} similar vectors")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            return []
    
    def search_by_metadata(self, metadata_query: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search vectors by metadata
        
        Args:
            metadata_query: Metadata key-value pairs to match
            top_k: Number of top results to return (default: 10)
            
        Returns:
            list: List of matching vectors
        """
        try:
            if not metadata_query:
                logger.warning("Metadata query is empty")
                return []
            
            # Build metadata filter for ChromaDB
            where_clause = {}
            for key, value in metadata_query.items():
                if key == "timestamp":
                    # Handle timestamp comparisons if needed
                    where_clause[key] = value
                else:
                    where_clause[key] = value
            
            results = self.collection.get(where=where_clause, include=["embeddings", "metadatas"])
            
            if not results or not results["ids"]:
                return []
                
            formatted_results = []
            for vector_id, vector, metadata in zip(
                results["ids"],
                results["embeddings"],
                results["metadatas"]
            ):
                formatted_results.append({
                    "vector_id": vector_id,
                    "vector": vector,
                    "metadata": metadata,
                    "timestamp": datetime.fromisoformat(metadata["timestamp"])
                })
            
            # Sort by timestamp descending
            formatted_results.sort(key=lambda x: x["timestamp"], reverse=True)
            
            logger.debug(f"Found {len(formatted_results)} vectors matching metadata query")
            return formatted_results[:top_k]
        except Exception as e:
            logger.error(f"Failed to search by metadata: {e}")
            return []
    
    def update_metadata(self, vector_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update metadata for a vector
        
        Args:
            vector_id: Unique identifier for the vector
            updates: Metadata updates
            
        Returns:
            bool: True if metadata updated successfully, False otherwise
        """
        try:
            existing = self.get_vector(vector_id)
            if not existing:
                logger.warning(f"Vector {vector_id} not found in store")
                return False
            
            # Merge old metadata with updates
            updated_metadata = existing["metadata"].copy()
            updated_metadata.update(updates)
            updated_metadata["timestamp"] = datetime.now().isoformat()
            
            # Get existing vector
            vector = existing["vector"]
            
            self.collection.update(
                ids=[vector_id],
                embeddings=[vector],
                metadatas=[updated_metadata]
            )
            
            logger.debug(f"Metadata updated for vector {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get vector store statistics
        
        Returns:
            dict: Statistics about the vector store
        """
        try:
            all_items = self.collection.get()
            stats = {
                "total_vectors": len(all_items["ids"]),
                "dimension": self.dimension,
                "persist_directory": self.persist_directory
            }
            
            # Get metadata fields
            metadata_fields = set()
            for metadata in all_items["metadatas"]:
                metadata_fields.update(metadata.keys())
            
            # Calculate metadata field statistics
            field_statistics = {}
            for field in metadata_fields:
                if field != "timestamp":
                    field_statistics[field] = set()
                    for metadata in all_items["metadatas"]:
                        if field in metadata:
                            field_statistics[field].add(str(metadata[field]))
            
            stats["metadata_fields"] = list(metadata_fields)
            stats["metadata_field_counts"] = {
                field: len(values) for field, values in field_statistics.items()
            }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def clear(self) -> bool:
        """
        Clear all vectors from the store
        
        Returns:
            bool: True if store cleared successfully
        """
        try:
            self.collection.delete(ids=self.collection.get()["ids"])
            logger.warning("Vector store cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            return False
    
    def save(self, file_path: str = None) -> bool:
        """
        Save vector store to persistent storage
        
        Args:
            file_path: Optional path to specify storage location
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # ChromaDB automatically persists changes, so this is a no-op
            logger.info("Vector store automatically persisted to disk")
            return True
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            return False
    
    def load(self, file_path: str = None) -> bool:
        """
        Load vector store from persistent storage
        
        Args:
            file_path: Optional path to load from
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            # ChromaDB automatically loads from persistent storage on initialization
            logger.info("Vector store loaded from disk")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False

# Singleton instance for the agent node
_vector_store_instance = None

def get_vector_store(persist_directory: str = "./local_storage/chroma", 
                    dimension: int = 1536) -> VectorStore:
    """
    Get a singleton instance of the vector store
    
    Args:
        persist_directory: Directory for persistent storage
        dimension: Dimensionality of the vectors
        
    Returns:
        VectorStore: Singleton instance
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(persist_directory, dimension)
    return _vector_store_instance
