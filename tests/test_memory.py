"""Tests for memory module - Agent Memory Management System.

Use Case Description:
This test file validates the memory management system in the Decentralized AI Ecosystem (DAIE), which enables agents to store, retrieve, and manage memories. Key functionalities tested include:

1. **Memory Manager**: Core memory orchestrator
   - Memory manager creation and initialization
   - Starting and stopping memory services
   - Agent memory initialization

2. **Memory Operations**: Basic memory management
   - Storing memories with different types and metadata
   - Retrieving memories by agent ID
   - Filtering memories by type and tags
   - Limiting retrieval results

3. **Memory Types**: Different memory categories
   - Working memory (temporary storage)
   - Semantic memory (knowledge storage)
   - Episodic memory (event storage)

4. **Memory Management**: Advanced operations
   - Clearing agent memory
   - Counting memories by type
   - Memory persistence across sessions

5. **Storage Backends**: Different storage options
   - Binary file storage (pickle) - Primary
   - Vector database storage (ChromaDB) - Optional

These tests ensure that agents can effectively manage their memories, enabling them to learn from experiences, recall information, and maintain context across interactions in the decentralized environment.
"""

import pytest
import tempfile
import shutil
from daie.memory.manager import MemoryManager, MemoryItem
from daie.config import SystemConfig


class TestMemoryManager:
    """Tests for MemoryManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def memory_manager(self, temp_dir):
        """Create a new memory manager instance with binary storage for each test."""
        config = SystemConfig()
        config.memory_storage_type = "binary"
        config.memory_root_path = temp_dir
        manager = MemoryManager(config=config)
        manager.start()
        return manager

    def test_memory_manager_creation(self, mock_logger, memory_manager):
        """Test memory manager creation with binary storage."""
        assert memory_manager is not None
        assert memory_manager.is_initialized is True
        assert hasattr(memory_manager, "_agent_memories")
        assert memory_manager.config.memory_storage_type == "binary"

    def test_memory_manager_agent_memory_operations(self, mock_logger, memory_manager):
        """Test agent memory initialization, storage, and retrieval with binary storage."""
        # Initialize agent memory
        memory_manager.initialize_agent_memory("agent1")
        assert "agent1" in memory_manager._agent_memories

        # Store memory
        memory_id = memory_manager.store_memory(
            "agent1",
            "Test content",
            "working",
            metadata={"key": "value"},
            tags=["test"],
        )

        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

        # Retrieve memories
        memories = memory_manager.retrieve_memories("agent1")
        assert len(memories) == 1
        assert isinstance(memories[0], MemoryItem)
        assert "Test content" in memories[0].content
        assert memories[0].memory_type == "working"
        assert memories[0].tags == ["test"]
        assert memories[0].metadata == {"key": "value"}

    def test_memory_manager_retrieve_filtered(self, mock_logger, memory_manager):
        """Test retrieving memories with filters using binary storage."""
        memory_manager.initialize_agent_memory("agent1")

        # Store different types of memories
        memory_manager.store_memory(
            "agent1", "Working memory 1", "working", tags=["test", "important"]
        )
        memory_manager.store_memory(
            "agent1", "Semantic memory 1", "semantic", tags=["knowledge"]
        )
        memory_manager.store_memory(
            "agent1", "Episodic memory 1", "episodic", tags=["event"]
        )
        memory_manager.store_memory(
            "agent1", "Working memory 2", "working", tags=["test"]
        )

        # Test retrieving working memory
        working_memories = memory_manager.retrieve_memories("agent1", "working")
        assert len(working_memories) == 2

        # Test retrieving by tags
        test_memories = memory_manager.retrieve_memories("agent1", tags=["test"])
        assert len(test_memories) == 2

        # Test limit parameter
        limited_memories = memory_manager.retrieve_memories("agent1", limit=1)
        assert len(limited_memories) == 1

    def test_memory_manager_clear_memory(self, mock_logger, memory_manager):
        """Test clearing agent memory with binary storage."""
        memory_manager.initialize_agent_memory("agent1")
        memory_manager.store_memory("agent1", "Test content", "working")

        assert memory_manager.get_memory_count("agent1") == 1

        memory_manager.clear_agent_memory("agent1")
        assert memory_manager.get_memory_count("agent1") == 0

    def test_memory_manager_count_operations(self, mock_logger, memory_manager):
        """Test memory count operations with binary storage."""
        memory_manager.initialize_agent_memory("agent1")
        memory_manager.store_memory("agent1", "Memory 1", "working")
        memory_manager.store_memory("agent1", "Memory 2", "working")
        memory_manager.store_memory("agent1", "Memory 3", "semantic")

        assert memory_manager.get_memory_count("agent1") == 3
        assert memory_manager.get_memory_count("agent1", "working") == 2
        assert memory_manager.get_memory_count("agent1", "semantic") == 1
        assert memory_manager.get_memory_count("agent1", "episodic") == 0

    def test_memory_manager_stop_start(self, mock_logger, temp_dir):
        """Test memory manager start and stop operations with binary storage."""
        config = SystemConfig()
        config.memory_storage_type = "binary"
        config.memory_root_path = temp_dir
        manager = MemoryManager(config=config)

        manager.start()
        assert manager.is_initialized is True

        manager.stop()
        assert manager.is_initialized is False

    def test_memory_persistence(self, mock_logger, temp_dir):
        """Test memory persistence across sessions with binary storage."""
        # First session
        config1 = SystemConfig()
        config1.memory_storage_type = "binary"
        config1.memory_root_path = temp_dir
        manager1 = MemoryManager(config=config1)
        manager1.start()
        
        manager1.initialize_agent_memory("agent1")
        manager1.store_memory("agent1", "Persistent memory", "working", tags=["test"])
        manager1.stop()

        # Second session - should load from disk
        config2 = SystemConfig()
        config2.memory_storage_type = "binary"
        config2.memory_root_path = temp_dir
        manager2 = MemoryManager(config=config2)
        manager2.start()
        
        memories = manager2.retrieve_memories("agent1")
        assert len(memories) == 1
        assert memories[0].content == "Persistent memory"
        manager2.stop()

    def test_search_similar(self, mock_logger, memory_manager):
        """Test search_similar with binary storage (text matching fallback)."""
        memory_manager.initialize_agent_memory("agent1")
        
        memory_manager.store_memory(
            "agent1", "Python programming language", "semantic", tags=["programming"]
        )
        memory_manager.store_memory(
            "agent1", "Java programming language", "semantic", tags=["programming"]
        )
        memory_manager.store_memory(
            "agent1", "Cooking recipes", "semantic", tags=["cooking"]
        )

        # Search for programming-related memories
        results = memory_manager.search_similar("agent1", "programming")
        assert len(results) >= 2

    def test_get_storage_info(self, mock_logger, memory_manager):
        """Test get_storage_info with binary storage."""
        info = memory_manager.get_storage_info()
        assert info["storage_type"] == "binary"
        assert info["is_initialized"] is True
        assert "root_path" in info
        assert "agent_count" in info
        assert "total_memories" in info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
