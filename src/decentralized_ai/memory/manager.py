"""
Memory manager for agent memory management
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import time
from uuid import uuid4

from decentralized_ai.config import SystemConfig
from decentralized_ai.utils.logger import ensure_directory_exists

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


class MemoryManager:
    """
    Memory manager for handling agent memory

    This class manages the memory system for agents, providing persistent
    storage for knowledge, experiences, and context. It supports different
    types of memory including working memory, semantic memory, and episodic
    memory.

    Example:
    >>> from decentralized_ai.memory import MemoryManager
    >>> from decentralized_ai.config import SystemConfig

    >>> # Create memory manager
    >>> config = SystemConfig()
    >>> memory_manager = MemoryManager(config=config)

    >>> # Initialize agent memory
    >>> memory_manager.initialize_agent_memory("agent1")

    >>> # Store memory
    >>> memory_manager.store_memory("agent1", "Test content", "working", tags=["test"])

    >>> # Retrieve memories
    >>> memories = memory_manager.retrieve_memories("agent1", "working")
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
        self._storage = None
        self._root_path = ensure_directory_exists(self.config.memory_root_path)

        logger.info("Memory manager initialized with storage path: %s", self._root_path)

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
            # Initialize storage
            self._initialize_storage()
            
            # Load existing agent memories
            self._load_agent_memories()
            
            self._is_initialized = True
            logger.info("Memory manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start memory manager: {e}")
            raise

    def stop(self) -> None:
        """Stop memory manager"""
        if not self._is_initialized:
            logger.warning("Memory manager already stopped")
            return
            
        # Save all agent memories to file system
        for agent_id in self._agent_memories:
            self._save_agent_memory(agent_id)
            
        self._is_initialized = False
        logger.info("Memory manager stopped")

    def _initialize_storage(self):
        """Initialize storage system based on configuration"""
        if self.config.memory_storage_type == "file":
            logger.info("Using file system storage at: %s", self._root_path)
        elif self.config.memory_storage_type == "in-memory":
            logger.info("Using in-memory storage (non-persistent)")
        else:
            logger.warning("Unsupported storage type: %s, using file system instead", 
                        self.config.memory_storage_type)
            self.config.memory_storage_type = "file"

    def _get_agent_directory(self, agent_id: str) -> str:
        """Get the directory for a specific agent's memory"""
        agent_dir = os.path.join(self._root_path, agent_id)
        ensure_directory_exists(agent_dir)
        return agent_dir

    def _load_agent_memory(self, agent_id: str):
        """Load agent memory from file system"""
        if self.config.memory_storage_type != "file":
            return
            
        agent_dir = self._get_agent_directory(agent_id)
        memory_file = os.path.join(agent_dir, "memory.json")
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._agent_memories[agent_id] = {}
                    for memory_type, items in data.items():
                        self._agent_memories[agent_id][memory_type] = [
                            MemoryItem(**item) for item in items
                        ]
                logger.debug("Loaded memory for agent %s: %d items", 
                           agent_id, 
                           sum(len(items) for items in self._agent_memories[agent_id].values()))
            except Exception as e:
                logger.error(f"Failed to load memory for agent {agent_id}: {e}")
                self._agent_memories[agent_id] = {}
        else:
            self._agent_memories[agent_id] = {}

    def _save_agent_memory(self, agent_id: str):
        """Save agent memory to file system"""
        if self.config.memory_storage_type != "file":
            return
            
        if agent_id not in self._agent_memories:
            return
            
        agent_dir = self._get_agent_directory(agent_id)
        memory_file = os.path.join(agent_dir, "memory.json")
        
        try:
            data = {}
            for memory_type, items in self._agent_memories[agent_id].items():
                data[memory_type] = [
                    {
                        "id": item.id,
                        "content": item.content,
                        "memory_type": item.memory_type,
                        "timestamp": item.timestamp,
                        "metadata": item.metadata,
                        "tags": item.tags
                    } for item in items
                ]
                
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
            logger.debug("Saved memory for agent %s: %d items", 
                       agent_id, 
                       sum(len(items) for items in self._agent_memories[agent_id].values()))
        except Exception as e:
            logger.error(f"Failed to save memory for agent {agent_id}: {e}")

    def _load_agent_memories(self):
        """Load all agent memories from storage"""
        logger.debug("Loading agent memories from storage...")
        self._agent_memories = {}
        
        if self.config.memory_storage_type == "file":
            try:
                # List all directories in the root path
                for agent_dir in os.listdir(self._root_path):
                    agent_dir_path = os.path.join(self._root_path, agent_dir)
                    if os.path.isdir(agent_dir_path):
                        self._load_agent_memory(agent_dir)
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
                    "episodic": []
                }
            logger.info(f"Memory initialized for agent: {agent_id}")
            
        return self

    def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "working",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Store a memory item

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
            id=str(uuid4()),
            content=content,
            memory_type=memory_type,
            timestamp=time.time(),
            metadata=metadata or {},
            tags=tags or []
        )

        # Check if memory type exists
        if memory_type not in self._agent_memories[agent_id]:
            self._agent_memories[agent_id][memory_type] = []

        self._agent_memories[agent_id][memory_type].append(memory_item)

        # Limit memory size
        max_items = self.config.max_memory_items or 1000
        if len(self._agent_memories[agent_id][memory_type]) > max_items:
            # Remove oldest items
            self._agent_memories[agent_id][memory_type] = self._agent_memories[agent_id][memory_type][-max_items:]

        logger.debug(f"Memory stored for agent {agent_id}: {content[:50]}...")
        
        # Save to persistent storage
        self._save_agent_memory(agent_id)
        
        return memory_item.id

    def retrieve_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
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
            all_memories = [
                item for item in all_memories
                if any(tag in tags for tag in item.tags)
            ]

        # Sort by timestamp (newest first) and apply limit
        all_memories.sort(key=lambda x: x.timestamp, reverse=True)
        return all_memories[:limit]

    def clear_agent_memory(self, agent_id: str) -> None:
        """
        Clear all memory for an agent

        Args:
            agent_id: Agent ID
        """
        if agent_id in self._agent_memories:
            del self._agent_memories[agent_id]
            
            if self.config.memory_storage_type == "file":
                agent_dir = self._get_agent_directory(agent_id)
                memory_file = os.path.join(agent_dir, "memory.json")
                if os.path.exists(memory_file):
                    try:
                        os.remove(memory_file)
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
