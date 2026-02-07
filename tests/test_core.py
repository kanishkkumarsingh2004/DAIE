"""Tests for core module."""

import pytest
from unittest.mock import Mock, patch
from daie.core.node import Node
from daie.core.system import DecentralizedAISystem
from daie.agents.config import AgentConfig


class TestNode:
    """Tests for Node class."""
    
    def test_node_creation(self, mock_logger):
        """Test node creation and initialization."""
        node = Node(node_id="test-node-1", name="Test Node")
        
        assert node.node_id == "test-node-1"
        assert node.name == "Test Node"
        assert node.is_active is False
    
    def test_node_start_stop(self, mock_logger):
        """Test node start and stop operations."""
        node = Node(node_id="test-node-1", name="Test Node")
        
        node.start()
        assert node.is_active is True
        
        node.stop()
        assert node.is_active is False
    
    def test_node_add_remove_agent(self, mock_logger):
        """Test adding and removing agents to/from node."""
        node = Node(node_id="test-node-1", name="Test Node")
        
        node.add_agent("agent1")
        assert "agent1" in node.agents
        assert node.agent_count == 1
        
        node.remove_agent("agent1")
        assert "agent1" not in node.agents
        assert node.agent_count == 0
    
    def test_node_connections(self, mock_logger):
        """Test node connections."""
        node = Node(node_id="test-node-1", name="Test Node")
        
        node.connect("peer-node-2")
        assert node.is_connected("peer-node-2") is True
        assert node.connection_count == 1
        
        node.disconnect("peer-node-2")
        assert node.is_connected("peer-node-2") is False
        assert node.connection_count == 0
    
    def test_node_resources(self, mock_logger):
        """Test node resource management."""
        node = Node(node_id="test-node-1", name="Test Node")
        
        node.set_resource("cpu", 8)
        node.set_resource("memory", 16)
        
        assert node.get_resource("cpu") == 8
        assert node.get_resource("memory") == 16
        assert node.get_resource("disk", 100) == 100
        
        resources = node.get_resource_info()
        assert "cpu" in resources
        assert "memory" in resources
    
    def test_node_status(self, mock_logger):
        """Test getting node status."""
        node = Node(node_id="test-node-1", name="Test Node")
        node.add_agent("agent1")
        node.add_agent("agent2")
        node.connect("peer-node-2")
        node.set_resource("cpu", 8)
        
        status = node.get_status()
        
        assert status["node_id"] == "test-node-1"
        assert status["name"] == "Test Node"
        assert status["status"] == "inactive"
        assert status["agent_count"] == 2
        assert status["agents"] == ["agent1", "agent2"]
        assert status["connection_count"] == 1
        assert status["connections"] == ["peer-node-2"]
        assert status["resources"]["cpu"] == 8


class TestDecentralizedAISystem:
    """Tests for DecentralizedAISystem class."""
    
    def test_system_creation(self, mock_logger):
        """Test system creation and initialization."""
        system = DecentralizedAISystem()
        
        assert system is not None
        assert system.agents == {}
        assert system.is_running is False
    
    @patch("daie.core.system.Agent")
    def test_system_add_agent(self, mock_agent, mock_logger):
        """Test adding agents to system."""
        system = DecentralizedAISystem()
        
        mock_agent_instance = Mock()
        mock_agent_instance.id = "agent1"
        mock_agent.return_value = mock_agent_instance
        
        system.add_agent(mock_agent_instance)
        
        assert len(system.agents) == 1
        assert "agent1" in system.agents
    
    @patch("daie.core.system.Agent")
    def test_system_get_agent(self, mock_agent, mock_logger):
        """Test getting agent from system."""
        system = DecentralizedAISystem()
        
        mock_agent_instance = Mock()
        mock_agent_instance.id = "agent1"
        mock_agent.return_value = mock_agent_instance
        
        system.add_agent(mock_agent_instance)
        
        agent = system.get_agent("agent1")
        assert agent is not None
        assert agent.id == "agent1"
    
    @patch("daie.core.system.Agent")
    def test_system_list_agents(self, mock_agent, mock_logger):
        """Test listing agents in system."""
        system = DecentralizedAISystem()
        
        mock_agent1 = Mock()
        mock_agent1.id = "agent1"
        mock_agent2 = Mock()
        mock_agent2.id = "agent2"
        
        system.add_agent(mock_agent1)
        system.add_agent(mock_agent2)
        
        agents = system.list_agents()
        assert len(agents) == 2
    
    @patch("daie.core.system.CommunicationManager")
    @patch("daie.core.system.MemoryManager")
    @patch("daie.core.system.Agent")
    def test_system_start_stop(self, mock_agent, mock_memory_manager, mock_comm_manager, mock_logger):
        """Test system start and stop operations."""
        system = DecentralizedAISystem()
        
        # Create mock agents
        mock_agent1 = Mock()
        mock_agent1.id = "agent1"
        mock_agent1.start = Mock()
        mock_agent1.stop = Mock()
        
        mock_agent2 = Mock()
        mock_agent2.id = "agent2"
        mock_agent2.start = Mock()
        mock_agent2.stop = Mock()
        
        system.add_agent(mock_agent1)
        system.add_agent(mock_agent2)
        
        # Start system
        with patch.object(system, '_create_pid_file'), \
             patch.object(system, '_run_event_loop'):
            system.start()
            
            assert system.is_running is True
            mock_agent1.start.assert_called_once()
            mock_agent2.start.assert_called_once()
        
        # Stop system
        with patch.object(system, '_remove_pid_file'):
            system.stop()
            assert system.is_running is False
            mock_agent1.stop.assert_called_once()
            mock_agent2.stop.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
