#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Knowledge Index

This module provides functionality for managing and querying semantic knowledge
using a local vector database.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import os

from agent_node_system.memory_system.semantic.embedding_engine import get_embedding_engine

logger = logging.getLogger(__name__)

class KnowledgeItem:
    """
    Represents a single knowledge item in the semantic memory
    
    Attributes:
        item_id: Unique identifier
        content: The actual knowledge content
        summary: Summary of the knowledge content
        category: Category or type of knowledge
        source: Source of the knowledge
        confidence: Confidence score (0-1)
        timestamp: When the knowledge was added
        metadata: Additional metadata
    """
    
    def __init__(self, content: str, summary: str = "", category: str = "general",
                 source: str = "unknown", confidence: float = 0.8,
                 metadata: Dict[str, Any] = None):
        self.item_id = str(uuid.uuid4())
        self.content = content
        self.summary = summary
        self.category = category
        self.source = source
        self.confidence = max(0.0, min(1.0, confidence))
        self.timestamp = datetime.now()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage"""
        return {
            "item_id": self.item_id,
            "content": self.content,
            "summary": self.summary,
            "category": self.category,
            "source": self.source,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary format"""
        item = cls(
            content=data["content"],
            summary=data.get("summary", ""),
            category=data.get("category", "general"),
            source=data.get("source", "unknown"),
            confidence=data.get("confidence", 0.8),
            metadata=data.get("metadata", {})
        )
        item.item_id = data.get("item_id", item.item_id)
        if "timestamp" in data:
            item.timestamp = datetime.fromisoformat(data["timestamp"])
        return item

class KnowledgeIndex:
    """
    Semantic Knowledge Index
    
    Provides functionality for managing and querying semantic knowledge using
    a local vector database.
    """
    
    def __init__(self, chroma_client, collection_name: str = "agent_knowledge"):
        """
        Initialize the knowledge index
        
        Args:
            chroma_client: ChromaDB client instance
            collection_name: Name of the collection to use
        """
        self.chroma_client = chroma_client
        self.collection_name = collection_name
        self.embedding_engine = get_embedding_engine()
        
        try:
            # Create or get the collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Agent semantic knowledge base"}
            )
            logger.info(f"Knowledge index initialized with collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge index: {e}")
            raise
    
    def add_knowledge(self, content: str, summary: str = "", category: str = "general",
                     source: str = "unknown", confidence: float = 0.8,
                     metadata: Dict[str, Any] = None) -> str:
        """
        Add a knowledge item to the index
        
        Args:
            content: The actual knowledge content
            summary: Summary of the knowledge content
            category: Category or type of knowledge
            source: Source of the knowledge
            confidence: Confidence score (0-1)
            metadata: Additional metadata
            
        Returns:
            str: ID of the added knowledge item
        """
        try:
            knowledge_item = KnowledgeItem(
                content=content,
                summary=summary,
                category=category,
                source=source,
                confidence=confidence,
                metadata=metadata
            )
            
            # Generate embedding
            embedding = self.embedding_engine.generate_embedding(content)
            if not embedding:
                logger.warning("Failed to generate embedding for knowledge item")
                return ""
                
            # Prepare metadata
            metadata = {
                "summary": knowledge_item.summary,
                "category": knowledge_item.category,
                "source": knowledge_item.source,
                "confidence": knowledge_item.confidence,
                "timestamp": knowledge_item.timestamp.isoformat(),
                **knowledge_item.metadata
            }
            
            # Add to ChromaDB
            self.collection.add(
                ids=[knowledge_item.item_id],
                embeddings=[embedding],
                documents=[knowledge_item.content],
                metadatas=[metadata]
            )
            
            logger.debug(f"Knowledge item added: {knowledge_item.item_id}")
            return knowledge_item.item_id
        except Exception as e:
            logger.error(f"Failed to add knowledge item: {e}")
            return ""
    
    def add_knowledge_batch(self, knowledge_items: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple knowledge items in batch
        
        Args:
            knowledge_items: List of knowledge item dictionaries
            
        Returns:
            list: IDs of added knowledge items
        """
        try:
            items = []
            documents = []
            metadatas = []
            
            for item_data in knowledge_items:
                item = KnowledgeItem(
                    content=item_data["content"],
                    summary=item_data.get("summary", ""),
                    category=item_data.get("category", "general"),
                    source=item_data.get("source", "unknown"),
                    confidence=item_data.get("confidence", 0.8),
                    metadata=item_data.get("metadata", {})
                )
                items.append(item)
                documents.append(item.content)
                metadatas.append({
                    "summary": item.summary,
                    "category": item.category,
                    "source": item.source,
                    "confidence": item.confidence,
                    "timestamp": item.timestamp.isoformat(),
                    **item.metadata
                })
            
            # Generate embeddings
            embeddings = self.embedding_engine.generate_embeddings(documents)
            
            # Filter valid items
            valid_ids = []
            valid_embeddings = []
            valid_documents = []
            valid_metadatas = []
            
            for item, embedding, doc, meta in zip(items, embeddings, documents, metadatas):
                if embedding:
                    valid_ids.append(item.item_id)
                    valid_embeddings.append(embedding)
                    valid_documents.append(doc)
                    valid_metadatas.append(meta)
            
            if valid_ids:
                self.collection.add(
                    ids=valid_ids,
                    embeddings=valid_embeddings,
                    documents=valid_documents,
                    metadatas=valid_metadatas
                )
            
            logger.debug(f"Added {len(valid_ids)} knowledge items out of {len(knowledge_items)}")
            return valid_ids
        except Exception as e:
            logger.error(f"Failed to add knowledge batch: {e}")
            return []
    
    def search_knowledge(self, query: str, category: str = None,
                        min_confidence: float = 0.5, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for relevant knowledge items
        
        Args:
            query: Search query
            category: Filter by category (None for all categories)
            min_confidence: Minimum confidence score (0-1)
            top_k: Number of top results to return
            
        Returns:
            list: List of relevant knowledge items with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_engine.generate_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return []
            
            # Build metadata filter
            if category:
                where = {"$and": [
                    {"confidence": {"$gte": min_confidence}},
                    {"category": category}
                ]}
            else:
                where = {"confidence": {"$gte": min_confidence}}
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            
            # Format results
            formatted_results = []
            for i, (doc, meta, score) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                formatted_results.append({
                    "item_id": results["ids"][0][i],
                    "content": doc,
                    "summary": meta.get("summary", ""),
                    "category": meta.get("category", "general"),
                    "source": meta.get("source", "unknown"),
                    "confidence": meta.get("confidence", 0.8),
                    "timestamp": meta.get("timestamp"),
                    "metadata": {k: v for k, v in meta.items() if k not in [
                        "summary", "category", "source", "confidence", "timestamp"
                    ]},
                    "score": 1 / (1 + score)  # Convert distance to similarity score
                })
            
            logger.debug(f"Found {len(formatted_results)} relevant knowledge items")
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []
    
    def get_knowledge_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific knowledge item by ID
        
        Args:
            item_id: ID of the knowledge item
            
        Returns:
            dict: Knowledge item, or None if not found
        """
        try:
            results = self.collection.get(ids=[item_id])
            if results["ids"]:
                doc = results["documents"][0]
                meta = results["metadatas"][0]
                return {
                    "item_id": results["ids"][0],
                    "content": doc,
                    "summary": meta.get("summary", ""),
                    "category": meta.get("category", "general"),
                    "source": meta.get("source", "unknown"),
                    "confidence": meta.get("confidence", 0.8),
                    "timestamp": meta.get("timestamp"),
                    "metadata": {k: v for k, v in meta.items() if k not in [
                        "summary", "category", "source", "confidence", "timestamp"
                    ]}
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get knowledge item: {e}")
            return None
    
    def remove_knowledge_item(self, item_id: str) -> bool:
        """
        Remove a knowledge item from the index
        
        Args:
            item_id: ID of the knowledge item to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[item_id])
            logger.debug(f"Knowledge item removed: {item_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove knowledge item: {e}")
            return False
    
    def update_knowledge_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a knowledge item
        
        Args:
            item_id: ID of the knowledge item to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            item = self.get_knowledge_item(item_id)
            if not item:
                logger.warning(f"Knowledge item {item_id} not found for update")
                return False
            
            # Apply updates
            updated_item = item.copy()
            updated_item.update(updates)
            
            # Re-generate embedding if content changed
            if "content" in updates:
                embedding = self.embedding_engine.generate_embedding(updated_item["content"])
                if not embedding:
                    logger.warning("Failed to generate embedding for updated content")
                    return False
            else:
                # Get existing embedding
                existing = self.collection.get(ids=[item_id])
                if existing["embeddings"]:
                    embedding = existing["embeddings"][0]
                else:
                    embedding = self.embedding_engine.generate_embedding(updated_item["content"])
            
            # Prepare metadata
            metadata = {
                "summary": updated_item.get("summary", item["summary"]),
                "category": updated_item.get("category", item["category"]),
                "source": updated_item.get("source", item["source"]),
                "confidence": updated_item.get("confidence", item["confidence"]),
                "timestamp": datetime.now().isoformat(),
                **updated_item.get("metadata", item["metadata"])
            }
            
            self.collection.update(
                ids=[item_id],
                embeddings=[embedding],
                documents=[updated_item["content"]],
                metadatas=[metadata]
            )
            
            logger.debug(f"Knowledge item updated: {item_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update knowledge item: {e}")
            return False
    
    def get_category_statistics(self) -> Dict[str, int]:
        """
        Get statistics about knowledge categories
        
        Returns:
            dict: Category names to item counts
        """
        try:
            all_items = self.collection.get()
            categories = {}
            for meta in all_items["metadatas"]:
                category = meta.get("category", "general")
                categories[category] = categories.get(category, 0) + 1
            
            return categories
        except Exception as e:
            logger.error(f"Failed to get category statistics: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall knowledge index statistics
        
        Returns:
            dict: Statistics about the knowledge index
        """
        try:
            all_items = self.collection.get()
            category_stats = self.get_category_statistics()
            
            stats = {
                "total_items": len(all_items["ids"]),
                "categories": len(category_stats),
                "category_distribution": category_stats,
                "total_categories": len(category_stats)
            }
            
            logger.debug(f"Knowledge index statistics: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def clear(self) -> bool:
        """
        Clear all knowledge items from the index
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=self.collection.get()["ids"])
            logger.warning("Knowledge index cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear knowledge index: {e}")
            return False
