"""
Memory manager for agent memory management

This module provides the MemoryManager class for managing agent memory
with support for multiple storage backends including vector database,
binary files, and JSON files.
"""

import logging
import os
import time
import heapq
from collections import deque, OrderedDict
from typing import Any, Dict, List, Optional

from daie.config import SystemConfig
from daie.memory.storage import (
    MemoryItem,
    StorageBackend,
    VectorDatabaseStorage,
    create_storage_backend,
)
from daie.utils.encryption import uuid7

logger = logging.getLogger(__name__)


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
        
        # Limit the number of agents kept in RAM to prevent memory bloat
        self._max_agents_in_ram = getattr(self.config, "max_agents_in_ram", 20)
        self._agent_memories: OrderedDict[str, Dict[str, deque[MemoryItem]]] = OrderedDict()
        
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
                    "Memory manager started successfully with %s backend (persistent)",
                    self.config.memory_storage_type,
                )
            else:
                self._storage = None
                logger.info("Memory manager started successfully (in-memory only, no persistence)")

            self._is_initialized = True

        except Exception as e:
            logger.error(f"Failed to start memory manager: {e}")
            raise

    def stop(self) -> None:
        """Stop memory manager and flush all pending memory to disk"""
        if not self._is_initialized:
            logger.debug("Memory manager already stopped")
            return

        # Save all agent memories to storage only if persistent memory is enabled
        if self.config.persistent_memory and self._storage:
            for agent_id in list(self._agent_memories.keys()):
                try:
                    self._save_agent_memory(agent_id)
                except Exception as e:
                    logger.error(f"Error saving memory for agent {agent_id} during stop: {e}")

        self._is_initialized = False
        logger.info("Memory manager stopped")

    def _load_agent_memory(self, agent_id: str):
        """Load agent memory from storage"""
        if not self._storage:
            return

        try:
            loaded = self._storage.load_agent_memory(agent_id)
            # Convert loaded lists to deques for performance
            max_items = self.config.max_memory_items or 1000
            self._agent_memories[agent_id] = {
                m_type: deque(items, maxlen=max_items)
                for m_type, items in loaded.items()
            }
            # Move to end (MRU)
            self._agent_memories.move_to_end(agent_id)

            total_items = sum(len(items) for items in self._agent_memories[agent_id].values())
            logger.debug(
                "Loaded memory for agent %s: %d items",
                agent_id,
                total_items,
            )
        except Exception as e:
            logger.error(f"Failed to load memory for agent {agent_id}: {e}")
            # Only initialize empty if not already present
            if agent_id not in self._agent_memories:
                max_items = self.config.max_memory_items or 1000
                self._agent_memories[agent_id] = {
                    "working": deque(maxlen=max_items),
                    "semantic": deque(maxlen=max_items),
                    "episodic": deque(maxlen=max_items),
                    "long_term": deque(maxlen=max_items),
                }
                self._agent_memories.move_to_end(agent_id)

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
        self._agent_memories.clear()

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
            # Try to load from persistent storage first
            if self._storage:
                self._load_agent_memory(agent_id)

            # If still not present (no storage or load returned nothing), init empty
            if agent_id not in self._agent_memories:
                max_items = self.config.max_memory_items or 1000
                self._agent_memories[agent_id] = {
                    "working": deque(maxlen=max_items),
                    "semantic": deque(maxlen=max_items),
                    "episodic": deque(maxlen=max_items),
                    "long_term": deque(maxlen=max_items),
                }
            self._agent_memories.move_to_end(agent_id)
            
            # Maintenance: Evict least recently used agent if we exceed RAM limit
            if len(self._agent_memories) > self._max_agents_in_ram:
                lru_id, _ = self._agent_memories.popitem(last=False)
                logger.debug(f"Evicted agent {lru_id} from RAM cache")

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
            id=uuid7(),
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            metadata=metadata or {},
            tags=tags or [],
        )

        # deque with maxlen handles truncation automatically and efficiently
        self._agent_memories[agent_id][memory_type].append(memory_item)

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

        # Update LRU
        self._agent_memories.move_to_end(agent_id)

        pools = []
        if memory_type:
            if memory_type in self._agent_memories[agent_id]:
                pools.append(self._agent_memories[agent_id][memory_type])
        else:
            pools = list(self._agent_memories[agent_id].values())

        if not pools:
            return []

        # Pools are deques added with append(), so newest is at the end.
        # We use heapq.merge on reversed deques (iterators) to get newest first in O(limit * log(num_pools)).
        # This is significantly faster than combining and sorting O(N log N).
        import itertools
        merged = heapq.merge(
            *[reversed(p) for p in pools],
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        results = list(itertools.islice(merged, limit))

        # Filter by tags if specified (post-merge as tags are rare)
        if tags:
            results = [item for item in results if any(tag in tags for tag in item.tags)]
            
        return results

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

    def log_chat_history(self, agent_id: str, content: str) -> None:
        """
        Log a chat history entry for an agent

        Args:
            agent_id: Agent ID
            content: History content to log
        """
        if not self._is_initialized:
            logger.debug("Memory manager not initialized, skipping history log")
            return

        if self._storage:
            try:
                self._storage.log_history(agent_id, content)
            except Exception as e:
                logger.error(f"Failed to log chat history: {e}")

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
            "total_memories": sum(
                self.get_memory_count(agent_id) for agent_id in self._agent_memories
            ),
        }

    # ── Memory Summarization ──────────────────────────────────────────────────

    def summarize_episodic_memory(
        self,
        agent_id: str,
        llm,
        threshold: int = 50,
    ) -> Optional[str]:
        """
        Summarize old episodic memories using an LLM.

        Retrieves episodic memories, uses the LLM to generate a concise summary,
        stores it as a semantic memory, and clears the summarized episodes.

        Args:
            agent_id: Agent ID
            llm: LLM instance with an invoke() method
            threshold: Minimum number of episodic memories before summarization triggers

        Returns:
            The generated summary string, or None if threshold not met.
        """
        if agent_id not in self._agent_memories:
            return None

        episodic = self._agent_memories[agent_id].get("episodic", deque())
        if len(episodic) < threshold:
            logger.debug(
                f"Agent {agent_id} has {len(episodic)} episodic memories "
                f"(threshold={threshold}), skipping summarization"
            )
            return None

        # Collect all episodic content
        contents = [mem.content for mem in episodic]
        combined = "\n".join(f"- {c}" for c in contents)

        prompt = (
            "You are a concise summarizer. Below are episodic memory entries from an AI agent's history. "
            "Create a brief, factual summary that captures the most important information, decisions, "
            "and outcomes. Be concise but preserve key details.\n\n"
            f"Episodic memories:\n{combined}\n\n"
            "Summary:"
        )

        try:
            summary = llm.invoke(prompt, stream=False, temperature=0.3, max_tokens=500)
            summary = summary.strip()
        except Exception as e:
            logger.error(f"Failed to generate memory summary for agent {agent_id}: {e}")
            return None

        # Store summary as semantic memory
        self.store_memory(
            agent_id,
            f"[Auto-Summary] {summary}",
            memory_type="semantic",
            tags=["auto_summary", "episodic_digest"],
        )

        # Also store in long_term for permanent reference
        self.store_memory(
            agent_id,
            f"[Long-Term Summary] {summary}",
            memory_type="long_term",
            tags=["auto_summary", "long_term"],
        )

        # Clear summarized episodic memories
        self._agent_memories[agent_id]["episodic"] = deque(
            maxlen=self.config.max_memory_items or 1000
        )

        # Persist changes
        if self.config.persistent_memory:
            self._save_agent_memory(agent_id)

        logger.info(
            f"Summarized {len(contents)} episodic memories for agent {agent_id}"
        )
        return summary

    # ── Shared Memory (Cross-Agent in Orchestrator) ───────────────────────────

    def store_shared_memory(
        self,
        namespace: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Store a shared memory accessible by any agent in the namespace.

        Args:
            namespace: Shared memory namespace (e.g., orchestrator name)
            content: Memory content
            metadata: Optional metadata
            tags: Optional tags

        Returns:
            Memory item ID
        """
        shared_agent_id = f"shared_{namespace}"
        return self.store_memory(
            shared_agent_id,
            content,
            memory_type="semantic",
            metadata=metadata,
            tags=tags or ["shared"],
        )

    def retrieve_shared_memory(
        self,
        namespace: str,
        limit: int = 20,
        tags: Optional[List[str]] = None,
    ) -> List["MemoryItem"]:
        """
        Retrieve shared memories from a namespace.

        Args:
            namespace: Shared memory namespace
            limit: Maximum number of memories to return
            tags: Optional tag filter

        Returns:
            List of shared memory items
        """
        shared_agent_id = f"shared_{namespace}"
        if shared_agent_id not in self._agent_memories:
            self.initialize_agent_memory(shared_agent_id)
        return self.retrieve_memories(
            shared_agent_id, memory_type="semantic", tags=tags, limit=limit
        )

    def search_shared_memory(
        self,
        namespace: str,
        query: str,
        limit: int = 10,
    ) -> List["MemoryItem"]:
        """
        Search shared memories semantically.

        Args:
            namespace: Shared memory namespace
            query: Search query
            limit: Maximum results

        Returns:
            List of matching shared memory items
        """
        shared_agent_id = f"shared_{namespace}"
        if shared_agent_id not in self._agent_memories:
            self.initialize_agent_memory(shared_agent_id)
        return self.search_similar(
            shared_agent_id, query, memory_type="semantic", limit=limit
        )
