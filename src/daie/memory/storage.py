"""
Storage backends for agent memory management

This module provides different storage backends for persistent memory storage:
- VectorDatabaseStorage: Uses ChromaDB for semantic search capabilities
- BinaryFileStorage: Uses pickle for fast binary serialization (default)
"""

import json
import logging
import os
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Memory item structure"""

    id: str
    content: str
    memory_type: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def initialize(self, root_path: str) -> None:
        """Initialize the storage backend"""

    @abstractmethod
    def save_agent_memory(self, agent_id: str, memories: Dict[str, List[MemoryItem]]) -> None:
        """Save agent memory to storage"""

    @abstractmethod
    def load_agent_memory(self, agent_id: str) -> Dict[str, List[MemoryItem]]:
        """Load agent memory from storage"""

    @abstractmethod
    def delete_agent_memory(self, agent_id: str) -> None:
        """Delete agent memory from storage"""

    @abstractmethod
    def list_agents(self) -> List[str]:
        """List all agent IDs with stored memories"""

    @abstractmethod
    def log_history(self, agent_id: str, content: str) -> None:
        """Log a chat history entry to a human-readable file"""


class VectorDatabaseStorage(StorageBackend):
    """
    Vector database storage backend using ChromaDB

    This backend provides semantic search capabilities for memories,
    allowing agents to find relevant memories based on content similarity.

    Features:
    - Semantic search using embeddings
    - Fast retrieval with vector indexing
    - Persistent storage
    - Metadata filtering
    """

    def __init__(self):
        self._client = None
        self._collections: Dict[str, Any] = {}
        self._root_path = None

    def initialize(self, root_path: str) -> None:
        """Initialize ChromaDB client"""
        try:
            import chromadb
            from chromadb.config import Settings

            self._root_path = root_path
            chroma_path = os.path.join(root_path, ".chroma")

            # Create persistent client
            self._client = chromadb.PersistentClient(
                path=chroma_path, settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )

            logger.info(f"Vector database storage initialized at: {chroma_path}")

        except ImportError:
            logger.error("ChromaDB not installed. Install with: pip install chromadb")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise

    def _get_collection(self, agent_id: str, memory_type: str):
        """Get or create a collection for agent and memory type"""
        collection_name = f"{agent_id}_{memory_type}"

        if collection_name not in self._collections:
            try:
                self._collections[collection_name] = self._client.get_or_create_collection(
                    name=collection_name, metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                logger.error(f"Failed to get collection {collection_name}: {e}")
                raise

        return self._collections[collection_name]

    def save_agent_memory(self, agent_id: str, memories: Dict[str, List[MemoryItem]]) -> None:
        """Save agent memory to vector database"""
        if not self._client:
            raise RuntimeError("Storage not initialized")

        try:
            for memory_type, items in memories.items():
                if not items:
                    continue

                collection = self._get_collection(agent_id, memory_type)

                # Prepare data for ChromaDB
                ids = [item.id for item in items]
                documents = [item.content for item in items]
                metadatas = [
                    {
                        "memory_type": item.memory_type,
                        "timestamp": item.timestamp,
                        "tags": json.dumps(item.tags),
                        **item.metadata,
                    }
                    for item in items
                ]

                # Upsert documents
                collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

            logger.debug(f"Saved memory for agent {agent_id} to vector database")

        except Exception as e:
            logger.error(f"Failed to save memory for agent {agent_id}: {e}")
            raise

    def load_agent_memory(self, agent_id: str) -> Dict[str, List[MemoryItem]]:
        """Load agent memory from vector database"""
        if not self._client:
            raise RuntimeError("Storage not initialized")

        memories = {}

        try:
            # Load each memory type
            for memory_type in ["working", "semantic", "episodic"]:
                collection_name = f"{agent_id}_{memory_type}"

                try:
                    collection = self._client.get_collection(collection_name)
                    results = collection.get()

                    items = []
                    if results and results["ids"]:
                        for i, doc_id in enumerate(results["ids"]):
                            metadata = results["metadatas"][i] if results["metadatas"] else {}

                            # Parse tags from JSON string
                            tags_str = metadata.get("tags", "[]")
                            try:
                                tags = json.loads(tags_str)
                            except (json.JSONDecodeError, TypeError):
                                tags = []

                            item = MemoryItem(
                                id=doc_id,
                                content=results["documents"][i] if results["documents"] else "",
                                memory_type=memory_type,
                                timestamp=metadata.get("timestamp", time.time()),
                                metadata={
                                    k: v for k, v in metadata.items() if k not in ["memory_type", "timestamp", "tags"]
                                },
                                tags=tags,
                            )
                            items.append(item)

                    memories[memory_type] = items

                except Exception:
                    # Collection doesn't exist yet
                    memories[memory_type] = []

            logger.debug(f"Loaded memory for agent {agent_id} from vector database")
            return memories

        except Exception as e:
            logger.error(f"Failed to load memory for agent {agent_id}: {e}")
            return {"working": [], "semantic": [], "episodic": []}

    def delete_agent_memory(self, agent_id: str) -> None:
        """Delete agent memory from vector database"""
        if not self._client:
            raise RuntimeError("Storage not initialized")

        try:
            for memory_type in ["working", "semantic", "episodic"]:
                collection_name = f"{agent_id}_{memory_type}"
                try:
                    self._client.delete_collection(collection_name)
                    if collection_name in self._collections:
                        del self._collections[collection_name]
                except Exception:
                    pass  # Collection doesn't exist

            logger.debug(f"Deleted memory for agent {agent_id} from vector database")

        except Exception as e:
            logger.error(f"Failed to delete memory for agent {agent_id}: {e}")
            raise

    def list_agents(self) -> List[str]:
        """List all agent IDs with stored memories"""
        if not self._client:
            return []

        try:
            collections = self._client.list_collections()
            agent_ids = set()

            for collection in collections:
                # Collection name format: {agent_id}_{memory_type}
                parts = collection.name.rsplit("_", 1)
                if len(parts) == 2:
                    agent_ids.add(parts[0])

            return list(agent_ids)

        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    def log_history(self, agent_id: str, content: str) -> None:
        """Log to vector database (no-op for history.txt)"""
        pass

    def search_similar(
        self, agent_id: str, query: str, memory_type: Optional[str] = None, limit: int = 10
    ) -> List[MemoryItem]:
        """
        Search for similar memories using semantic search

        Args:
            agent_id: Agent ID
            query: Search query
            memory_type: Optional memory type filter
            limit: Maximum number of results

        Returns:
            List of similar memory items
        """
        if not self._client:
            raise RuntimeError("Storage not initialized")

        try:
            results = []

            # Search in specified memory type or all types
            memory_types = [memory_type] if memory_type else ["working", "semantic", "episodic"]

            for m_type in memory_types:
                collection_name = f"{agent_id}_{m_type}"

                try:
                    collection = self._client.get_collection(collection_name)
                    search_results = collection.query(query_texts=[query], n_results=limit)

                    if search_results and search_results["ids"]:
                        for i, doc_id in enumerate(search_results["ids"][0]):
                            metadata = search_results["metadatas"][0][i] if search_results["metadatas"] else {}

                            tags_str = metadata.get("tags", "[]")
                            try:
                                tags = json.loads(tags_str)
                            except (json.JSONDecodeError, TypeError):
                                tags = []

                            item = MemoryItem(
                                id=doc_id,
                                content=search_results["documents"][0][i] if search_results["documents"] else "",
                                memory_type=m_type,
                                timestamp=metadata.get("timestamp", time.time()),
                                metadata={
                                    k: v for k, v in metadata.items() if k not in ["memory_type", "timestamp", "tags"]
                                },
                                tags=tags,
                            )
                            results.append(item)

                except Exception:
                    continue

            # Sort by relevance (ChromaDB returns in order of relevance)
            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to search similar memories: {e}")
            return []


class BinaryFileStorage(StorageBackend):
    """
    Binary file storage backend using pickle

    This backend provides fast serialization and deserialization
    of memory data using Python's pickle format.

    Features:
    - Fast read/write operations
    - Compact file size
    - Native Python object support
    - Simple implementation
    """

    def __init__(self):
        self._root_path = None

    def initialize(self, root_path: str) -> None:
        """Initialize binary file storage"""
        self._root_path = root_path
        logger.info(f"Binary file storage initialized at: {root_path}")

    def _get_agent_directory(self, agent_id: str) -> str:
        """Get the directory for a specific agent's memory"""
        agent_dir = os.path.join(self._root_path, agent_id)
        os.makedirs(agent_dir, exist_ok=True)
        return agent_dir

    def _get_memory_file(self, agent_id: str) -> str:
        """Get the memory file path for an agent"""
        agent_dir = self._get_agent_directory(agent_id)
        return os.path.join(agent_dir, "memory.pkl")

    def save_agent_memory(self, agent_id: str, memories: Dict[str, List[MemoryItem]]) -> None:
        """Save agent memory to binary file using atomic write to prevent corruption"""
        try:
            memory_file = self._get_memory_file(agent_id)
            tmp_file = memory_file + ".tmp"

            # Convert MemoryItem objects to dictionaries for pickling
            data = {}
            for memory_type, items in memories.items():
                data[memory_type] = [
                    {
                        "id": item.id,
                        "content": item.content,
                        "memory_type": item.memory_type,
                        "timestamp": item.timestamp,
                        "metadata": item.metadata,
                        "tags": item.tags,
                    }
                    for item in items
                ]

            # Write to temp file first, then atomically rename
            with open(tmp_file, "wb") as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_file, memory_file)
            logger.debug(f"Saved memory for agent {agent_id} to binary file: {memory_file}")

        except Exception as e:
            logger.error(f"Failed to save memory for agent {agent_id}: {e}")
            # Clean up temp file if it exists
            tmp_file = self._get_memory_file(agent_id) + ".tmp"
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except OSError:
                    pass
            raise

    def load_agent_memory(self, agent_id: str) -> Dict[str, List[MemoryItem]]:
        """Load agent memory from binary file"""
        memory_file = self._get_memory_file(agent_id)

        if not os.path.exists(memory_file):
            return {"working": [], "semantic": [], "episodic": []}

        try:
            with open(memory_file, "rb") as f:
                data = pickle.load(f)

            memories = {}
            for memory_type, items in data.items():
                memories[memory_type] = [MemoryItem(**item) for item in items]

            logger.debug(f"Loaded memory for agent {agent_id} from binary file")
            return memories

        except Exception as e:
            logger.error(f"Failed to load memory for agent {agent_id}: {e}")
            return {"working": [], "semantic": [], "episodic": []}

    def delete_agent_memory(self, agent_id: str) -> None:
        """Delete agent memory binary file"""
        try:
            memory_file = self._get_memory_file(agent_id)
            if os.path.exists(memory_file):
                os.remove(memory_file)
                logger.debug(f"Deleted memory for agent {agent_id} from binary file")
        except Exception as e:
            logger.error(f"Failed to delete memory for agent {agent_id}: {e}")
            raise

    def list_agents(self) -> List[str]:
        """List all agent IDs with stored memories"""
        if not self._root_path or not os.path.exists(self._root_path):
            return []

        try:
            agent_ids = []
            for item in os.listdir(self._root_path):
                agent_dir = os.path.join(self._root_path, item)
                if os.path.isdir(agent_dir):
                    memory_file = os.path.join(agent_dir, "memory.pkl")
                    if os.path.exists(memory_file):
                        agent_ids.append(item)

            return agent_ids

        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []

    def log_history(self, agent_id: str, content: str) -> None:
        """Log a chat history entry to history.txt"""
        try:
            agent_dir = self._get_agent_directory(agent_id)
            history_file = os.path.join(agent_dir, "history.txt")
            
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {content}\n")
                
            logger.debug(f"Logged history for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to log history for agent {agent_id}: {e}")


def create_storage_backend(storage_type: str) -> StorageBackend:
    """
    Factory function to create storage backend

    Args:
        storage_type: Type of storage backend ("vector", "binary")

    Returns:
        StorageBackend instance
    """
    if storage_type == "vector":
        return VectorDatabaseStorage()
    elif storage_type == "binary":
        return BinaryFileStorage()
    elif storage_type == "json":
        # Fallback to binary for now as JSON backend is not yet implemented
        logger.warning("JSON storage backend not yet implemented, falling back to binary")
        return BinaryFileStorage()
    else:
        logger.warning(f"Unknown storage type: {storage_type}, using binary as fallback")
        return BinaryFileStorage()
