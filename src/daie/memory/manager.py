"""
Memory manager for agent memory management

This module provides the MemoryManager class for managing agent memory
with support for multiple storage backends including vector database,
binary files, and JSON files.
"""

import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from daie.config import SystemConfig
from daie.memory.storage import (MemoryItem, StorageBackend,
                                 VectorDatabaseStorage, create_storage_backend)

logger = logging.getLogger(__name__)


def uuid7() -> uuid.UUID:
    """Generate a UUID v7 (time-ordered UUID)

    UUID v7 format:
    - 48 bits: timestamp in milliseconds
    - 4 bits: version (0111 for v7)
    - 12 bits: random
    - 2 bits: variant (10)
    - 62 bits: random

    Returns:
        UUID v7 instance
    """
    try:
        # Get current timestamp in milliseconds
        timestamp_ms = int(time.time() * 1000)

        # Generate random bytes using os.urandom for cryptographic randomness
        random_bytes = os.urandom(10)

        # Convert timestamp to 6 bytes (48 bits)
        timestamp_bytes = timestamp_ms.to_bytes(6, byteorder="big")

        # Combine with random bytes
        uuid_bytes = bytearray(timestamp_bytes + random_bytes)

        # Set version bits (bits 4-7 of byte 6 to 0111)
        uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70  # Version 7

        # Set variant bits (bits 6-7 of byte 8 to 10)
        uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80  # Variant 10

        return uuid.UUID(bytes=bytes(uuid_bytes))
    except Exception as e:
        logger.error(f"Failed to generate UUID v7: {e}")
        # Fallback to UUID v4 if v7 generation fails
        return uuid.uuid4()


class MemoryManager:
    """
    Memory manager for handling agent memory

    This class manages the memory system for agents, providing persistent
    storage for knowledge, experiences, and context. It supports different
    types of memory including working memory, semantic memory, and episodic
    memory.

    Storage backends:
    - "vector": Uses ChromaDB for semantic search capabilities (recommended)
    - "binary": Uses pickle for fast binary serialization
    - "json": Uses JSON files (human-readable, slower)

    Example:
    >>> from daie.memory import MemoryManager
    >>> from daie.config import SystemConfig

    >>> # Create memory manager with vector database
    >>> config = SystemConfig(memory_storage_type="vector")
    >>> memory_manager = MemoryManager(config=config)

    >>> # Initialize agent memory
    >>> memory_manager.initialize_agent_memory("agent1")

    >>> # Store memory
    >>> memory_manager.store_memory("agent1", "Test content", "working", tags=["test"])

    >>> # Retrieve memories
    >>> memories = memory_manager.retrieve_memories("agent1", "working")

    >>> # Semantic search (only with vector backend)
    >>> similar = memory_manager.search_similar("agent1", "test query")
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        Initialize memory manager

        Args:
            config: System configuration
        """
        self.config = config or SystemConfig()
        self._is_initialized = False
        self._agent_memories: Dict[str, Dict[str, List[MemoryItem]]] = {}
        self._storage: Optional[StorageBackend] = None
        self._root_path = self.config.memory_root_path

        # Ensure root directory exists
        os.makedirs(self._root_path, exist_ok=True)

        logger.info(
            "Memory manager initialized with storage type: %s at path: %s",
            self.config.memory_storage_type,
            self._root_path,
        )

    @property
    def is_initialized(self) -> bool:
        """Check if memory manager is initialized"""
        return self._is_initialized

    def start(self) -> None:
        """
        Start memory manager

        This method initializes the memory system and connects to storage.
        """
        if self._is_initialized:
            logger.warning("Memory manager already initialized")
            return

        logger.info("Starting memory manager...")

        try:
            # Initialize storage backend only if persistent memory is enabled
            if self.config.persistent_memory:
                self._storage = create_storage_backend(self.config.memory_storage_type)
                self._storage.initialize(self._root_path)

                # Load existing agent memories
                self._load_agent_memories()
                logger.info(
                    "Memory manager started successfully with %s backend (persistent)", self.config.memory_storage_type
                )
            else:
                self._storage = None
                logger.info("Memory manager started successfully (in-memory only, no persistence)")

            self._is_initialized = True

        except Exception as e:
            logger.error(f"Failed to start memory manager: {e}")
            raise

    def stop(self) -> None:
        """Stop memory manager"""
        if not self._is_initialized:
            logger.warning("Memory manager already stopped")
            return

        # Save all agent memories to storage only if persistent memory is enabled
        if self.config.persistent_memory:
            for agent_id in self._agent_memories:
                self._save_agent_memory(agent_id)

        self._is_initialized = False
        logger.info("Memory manager stopped")

    def _load_agent_memory(self, agent_id: str):
        """Load agent memory from storage"""
        if not self._storage:
            return

        try:
            self._agent_memories[agent_id] = self._storage.load_agent_memory(agent_id)

            total_items = sum(len(items) for items in self._agent_memories[agent_id].values())
            logger.debug(
                "Loaded memory for agent %s: %d items",
                agent_id,
                total_items,
            )
        except Exception as e:
            logger.error(f"Failed to load memory for agent {agent_id}: {e}")
            self._agent_memories[agent_id] = {
                "working": [],
                "semantic": [],
                "episodic": [],
            }

    def _save_agent_memory(self, agent_id: str):
        """Save agent memory to storage"""
        if not self._storage:
            return

        if agent_id not in self._agent_memories:
            return

        try:
            self._storage.save_agent_memory(agent_id, self._agent_memories[agent_id])

            total_items = sum(len(items) for items in self._agent_memories[agent_id].values())
            logger.debug(
                "Saved memory for agent %s: %d items",
                agent_id,
                total_items,
            )
        except Exception as e:
            logger.error(f"Failed to save memory for agent {agent_id}: {e}")

    def _load_agent_memories(self):
        """Load all agent memories from storage"""
        logger.debug("Loading agent memories from storage...")
        self._agent_memories = {}

        if not self._storage:
            return

        try:
            agent_ids = self._storage.list_agents()
            for agent_id in agent_ids:
                self._load_agent_memory(agent_id)

            logger.debug("Loaded memories for %d agents", len(self._agent_memories))
        except Exception as e:
            logger.error(f"Failed to load agent memories: {e}")
            self._agent_memories = {}

    def initialize_agent_memory(self, agent_id: str) -> "MemoryManager":
        """
        Initialize memory for an agent

        Args:
            agent_id: Agent ID

        Returns:
            self for method chaining
        """
        if agent_id not in self._agent_memories:
            self._load_agent_memory(agent_id)
            if agent_id not in self._agent_memories:
                self._agent_memories[agent_id] = {
                    "working": [],
                    "semantic": [],
                    "episodic": [],
                }
            logger.info(f"Memory initialized for agent: {agent_id}")

        return self

    def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "working",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store a memory item with optimized performance

        Args:
            agent_id: Agent ID
            content: Memory content
            memory_type: Memory type (working, semantic, episodic)
            metadata: Optional metadata
            tags: Optional tags

        Returns:
            Memory item ID
        """
        if agent_id not in self._agent_memories:
            self.initialize_agent_memory(agent_id)

        memory_item = MemoryItem(
            id=str(uuid7()),
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            metadata=metadata or {},
            tags=tags or [],
        )

        # Check if memory type exists
        if memory_type not in self._agent_memories[agent_id]:
            self._agent_memories[agent_id][memory_type] = []

        self._agent_memories[agent_id][memory_type].append(memory_item)

        # Limit memory size efficiently
        max_items = self.config.max_memory_items or 1000
        current_count = len(self._agent_memories[agent_id][memory_type])
        if current_count > max_items:
            # Remove oldest items in one operation
            self._agent_memories[agent_id][memory_type] = self._agent_memories[agent_id][memory_type][-max_items:]

        # Log only if content is string
        content_preview = str(content)[:50] if content else ""
        logger.debug(f"Memory stored for agent {agent_id}: {content_preview}...")

        # Save to persistent storage only if persistent memory is enabled
        if self.config.persistent_memory:
            self._save_agent_memory(agent_id)

        return memory_item.id

    def retrieve_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[MemoryItem]:
        """
        Retrieve memories for an agent

        Args:
            agent_id: Agent ID
            memory_type: Memory type to retrieve (None for all types)
            tags: Tags to filter memories (None for all)
            limit: Maximum number of memories to return

        Returns:
            List of memory items
        """
        if agent_id not in self._agent_memories:
            return []

        all_memories = []

        if memory_type:
            if memory_type in self._agent_memories[agent_id]:
                all_memories.extend(self._agent_memories[agent_id][memory_type])
        else:
            for memories in self._agent_memories[agent_id].values():
                all_memories.extend(memories)

        # Filter by tags if specified
        if tags:
            all_memories = [item for item in all_memories if any(tag in tags for tag in item.tags)]

        # Sort by timestamp (newest first) and apply limit
        all_memories.sort(key=lambda x: x.timestamp, reverse=True)
        return all_memories[:limit]

    def search_similar(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """
        Search for similar memories using semantic search

        This method is only available when using the vector database backend.
        For other backends, it falls back to tag-based retrieval.

        Args:
            agent_id: Agent ID
            query: Search query
            memory_type: Optional memory type filter
            limit: Maximum number of results

        Returns:
            List of similar memory items
        """
        if not self._is_initialized:
            logger.warning("Memory manager not initialized")
            return []

        # Use vector search if available
        if isinstance(self._storage, VectorDatabaseStorage):
            try:
                return self._storage.search_similar(agent_id, query, memory_type, limit)
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
                return []

        # Fallback: search in memory using simple text matching
        if agent_id not in self._agent_memories:
            return []

        all_memories = []
        if memory_type:
            if memory_type in self._agent_memories[agent_id]:
                all_memories.extend(self._agent_memories[agent_id][memory_type])
        else:
            for memories in self._agent_memories[agent_id].values():
                all_memories.extend(memories)

        # Simple text matching
        query_lower = query.lower()
        matching = [item for item in all_memories if query_lower in item.content.lower()]

        # Sort by timestamp (newest first)
        matching.sort(key=lambda x: x.timestamp, reverse=True)
        return matching[:limit]

    def clear_agent_memory(self, agent_id: str) -> None:
        """
        Clear all memory for an agent

        Args:
            agent_id: Agent ID
        """
        if agent_id in self._agent_memories:
            del self._agent_memories[agent_id]

        if self._storage:
            try:
                self._storage.delete_agent_memory(agent_id)
                logger.debug(f"Cleared memory for agent: {agent_id}")
            except Exception as e:
                logger.error(f"Failed to clear memory for agent {agent_id}: {e}")

    def get_memory_count(self, agent_id: str, memory_type: Optional[str] = None) -> int:
        """
        Get count of memory items for an agent

        Args:
            agent_id: Agent ID
            memory_type: Memory type to count (None for all types)

        Returns:
            Number of memory items
        """
        if agent_id not in self._agent_memories:
            return 0

        if memory_type:
            if memory_type in self._agent_memories[agent_id]:
                return len(self._agent_memories[agent_id][memory_type])
            return 0
        else:
            return sum(len(memories) for memories in self._agent_memories[agent_id].values())

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage backend

        Returns:
            Dictionary with storage information
        """
        return {
            "storage_type": self.config.memory_storage_type,
            "root_path": self._root_path,
            "is_initialized": self._is_initialized,
            "persistent_memory": self.config.persistent_memory,
            "agent_count": len(self._agent_memories),
            "total_memories": sum(self.get_memory_count(agent_id) for agent_id in self._agent_memories),
        }
