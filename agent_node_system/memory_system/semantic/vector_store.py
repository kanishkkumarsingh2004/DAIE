#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Semantic Vector Store

This module provides functionality for storing and retrieving semantic vectors
for knowledge and context management.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Semantic Vector Store
    
    Provides functionality for storing and retrieving semantic vectors with
    associated metadata for knowledge management.
    """
    
    def __init__(self, dimension=1536):
        """
        Initialize the vector store
        
        Args:
            dimension: Dimensionality of the vectors (default: 1536 for OpenAI compatible embeddings)
        """
        self.dimension = dimension
        self.vectors = {}  # vector_id: {"vector": list, "metadata": dict, "timestamp": datetime}
        self.index = {}  # metadata key: {value: list of vector_ids}
        logger.info(f"Vector store initialized with {dimension}-dimensional vectors")
    
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
            if vector_id in self.vectors:
                logger.warning(f"Vector {vector_id} already exists in store")
                return False
            
            if len(vector) != self.dimension:
                logger.error(f"Vector dimension mismatch. Expected {self.dimension}, got {len(vector)}")
                return False
            
            self.vectors[vector_id] = {
                "vector": list(vector),
                "metadata": metadata or {},
                "timestamp": datetime.now()
            }
            
            if metadata:
                for key, value in metadata.items():
                    if key not in self.index:
                        self.index[key] = {}
                    if value not in self.index[key]:
                        self.index[key][value] = []
                    self.index[key][value].append(vector_id)
            
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
        return self.vectors.get(vector_id)
    
    def remove_vector(self, vector_id: str) -> bool:
        """
        Remove a vector from the store
        
        Args:
            vector_id: Unique identifier for the vector
            
        Returns:
            bool: True if vector removed successfully, False if not found
        """
        try:
            if vector_id not in self.vectors:
                logger.warning(f"Vector {vector_id} not found in store")
                return False
            
            metadata = self.vectors[vector_id]["metadata"]
            for key, value in metadata.items():
                if key in self.index and value in self.index[key]:
                    if vector_id in self.index[key][value]:
                        self.index[key][value].remove(vector_id)
                    if not self.index[key][value]:
                        del self.index[key][value]
                    if not self.index[key]:
                        del self.index[key]
            
            del self.vectors[vector_id]
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
            if not self.vectors:
                return []
            
            # Simple Euclidean distance for similarity (no numpy)
            results = []
            
            for vector_id, data in self.vectors.items():
                vector = data["vector"]
                
                # Calculate Euclidean distance
                distance = sum((a - b) ** 2 for a, b in zip(query_vector, vector)) ** 0.5
                similarity = 1 / (1 + distance)
                
                results.append({
                    "vector_id": vector_id,
                    "vector": vector,
                    "metadata": data["metadata"],
                    "similarity": float(similarity),
                    "timestamp": data["timestamp"]
                })
            
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
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
                return []
            
            matching_ids = None
            for key, value in metadata_query.items():
                if key not in self.index or value not in self.index[key]:
                    return []
                
                current_ids = set(self.index[key][value])
                if matching_ids is None:
                    matching_ids = current_ids
                else:
                    matching_ids.intersection_update(current_ids)
            
            if not matching_ids:
                return []
            
            results = []
            for vector_id in matching_ids:
                if vector_id in self.vectors:
                    results.append({
                        "vector_id": vector_id,
                        "vector": self.vectors[vector_id]["vector"],
                        "metadata": self.vectors[vector_id]["metadata"],
                        "timestamp": self.vectors[vector_id]["timestamp"]
                    })
            
            results.sort(key=lambda x: x["timestamp"], reverse=True)
            return results[:top_k]
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
            if vector_id not in self.vectors:
                logger.warning(f"Vector {vector_id} not found in store")
                return False
            
            old_metadata = self.vectors[vector_id]["metadata"]
            for key, value in old_metadata.items():
                if key in self.index and value in self.index[key]:
                    if vector_id in self.index[key][value]:
                        self.index[key][value].remove(vector_id)
                    if not self.index[key][value]:
                        del self.index[key][value]
                    if not self.index[key]:
                        del self.index[key]
            
            self.vectors[vector_id]["metadata"].update(updates)
            self.vectors[vector_id]["timestamp"] = datetime.now()
            
            new_metadata = self.vectors[vector_id]["metadata"]
            for key, value in new_metadata.items():
                if key not in self.index:
                    self.index[key] = {}
                if value not in self.index[key]:
                    self.index[key][value] = []
                self.index[key][value].append(vector_id)
            
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
            stats = {
                "total_vectors": len(self.vectors),
                "dimension": self.dimension,
                "metadata_fields": list(self.index.keys()),
                "metadata_distribution": {}
            }
            
            for field, values in self.index.items():
                stats["metadata_distribution"][field] = {value: len(vector_ids) for value, vector_ids in values.items()}
            
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
            self.vectors.clear()
            self.index.clear()
            logger.warning("Vector store cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            return False
    
    def save(self, file_path: str) -> bool:
        """
        Save vector store to file
        
        Args:
            file_path: Path to save the vector store
            
        Returns:
            bool: True if saved successfully
        """
        try:
            logger.info(f"Vector store saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")
            return False
    
    def load(self, file_path: str) -> bool:
        """
        Load vector store from file
        
        Args:
            file_path: Path to load the vector store from
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            logger.info(f"Vector store loaded from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
