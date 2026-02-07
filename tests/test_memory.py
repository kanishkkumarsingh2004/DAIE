"""Tests for memory module."""

import pytest
from unittest.mock import Mock, patch
from daie.memory.manager import MemoryManager, MemoryItem
from daie.config import SystemConfig


class TestMemoryManager:
    """Tests for MemoryManager class."""
    
    @pytest.fixture
    def memory_manager(self):
        """Create a new memory manager instance with in-memory storage for each test."""
        config = SystemConfig()
        config.memory_storage_type = "in-memory"
        manager = MemoryManager(config=config)
        manager.start()
        return manager
    
    def test_memory_manager_creation(self, mock_logger, memory_manager):
        """Test memory manager creation."""
        assert memory_manager is not None
        assert memory_manager.is_initialized is True
        assert hasattr(memory_manager, "_agent_memories")
    
    def test_memory_manager_agent_memory_operations(self, mock_logger, memory_manager):
        """Test agent memory initialization, storage, and retrieval."""
        # Initialize agent memory
        memory_manager.initialize_agent_memory("agent1")
        assert "agent1" in memory_manager._agent_memories
        
        # Store memory
        memory_id = memory_manager.store_memory(
            "agent1", 
            "Test content", 
            "working", 
            metadata={"key": "value"}, 
            tags=["test"]
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
        """Test retrieving memories with filters."""
        memory_manager.initialize_agent_memory("agent1")
        
        # Store different types of memories
        memory_manager.store_memory("agent1", "Working memory 1", "working", tags=["test", "important"])
        memory_manager.store_memory("agent1", "Semantic memory 1", "semantic", tags=["knowledge"])
        memory_manager.store_memory("agent1", "Episodic memory 1", "episodic", tags=["event"])
        memory_manager.store_memory("agent1", "Working memory 2", "working", tags=["test"])
        
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
        """Test clearing agent memory."""
        memory_manager.initialize_agent_memory("agent1")
        memory_manager.store_memory("agent1", "Test content", "working")
        
        assert memory_manager.get_memory_count("agent1") == 1
        
        memory_manager.clear_agent_memory("agent1")
        assert memory_manager.get_memory_count("agent1") == 0
    
    def test_memory_manager_count_operations(self, mock_logger, memory_manager):
        """Test memory count operations."""
        memory_manager.initialize_agent_memory("agent1")
        memory_manager.store_memory("agent1", "Memory 1", "working")
        memory_manager.store_memory("agent1", "Memory 2", "working")
        memory_manager.store_memory("agent1", "Memory 3", "semantic")
        
        assert memory_manager.get_memory_count("agent1") == 3
        assert memory_manager.get_memory_count("agent1", "working") == 2
        assert memory_manager.get_memory_count("agent1", "semantic") == 1
        assert memory_manager.get_memory_count("agent1", "episodic") == 0
    
    def test_memory_manager_stop_start(self, mock_logger):
        """Test memory manager start and stop operations."""
        config = SystemConfig()
        config.memory_storage_type = "in-memory"
        manager = MemoryManager(config=config)
        
        manager.start()
        assert manager.is_initialized is True
        
        manager.stop()
        assert manager.is_initialized is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
