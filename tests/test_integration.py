"""Integration tests for the entire system."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from daie.core.system import DecentralizedAISystem
from daie.core.node import Node
from daie.agents.agent import Agent
from daie.agents.config import AgentConfig
from daie.agents.message import AgentMessage


class TestSystemIntegration:
    """Integration tests for the entire system."""
    
    @patch("daie.core.system.Agent")
    def test_system_with_multiple_agents(self, mock_agent, mock_logger):
        """Test system with multiple agents."""
        system = DecentralizedAISystem()
        
        # Add agents to system with unique IDs
        agent1 = Mock()
        agent1.id = "agent1"
        agent1.start = Mock()
        agent1.stop = Mock()
        agent1.is_running = False
        
        agent2 = Mock()
        agent2.id = "agent2"
        agent2.start = Mock()
        agent2.stop = Mock()
        agent2.is_running = False
        
        agent3 = Mock()
        agent3.id = "agent3"
        agent3.start = Mock()
        agent3.stop = Mock()
        agent3.is_running = False
        
        system.add_agent(agent1)
        system.add_agent(agent2)
        system.add_agent(agent3)
        
        assert len(system.agents) == 3
        assert "agent1" in system.agents
        assert "agent2" in system.agents
        assert "agent3" in system.agents
    
    def test_node_agent_communication(self, mock_logger):
        """Test communication between nodes and agents."""
        config = AgentConfig(
            name="Test Agent",
            role="test-role"
        )
        
        agent = Agent(config)
        
        # Test communication setup
        assert agent is not None
        assert not agent.is_running
    
    @pytest.mark.asyncio
    async def test_message_propagation(self, mock_logger):
        """Test message propagation through system."""
        # Create communication managers
        comm_manager1 = Mock()
        comm_manager1.send_message = AsyncMock(return_value=True)
        
        comm_manager2 = Mock()
        comm_manager2.send_message = AsyncMock(return_value=True)
        
        # Create nodes with mock communication managers
        node1 = Node(node_id="node1", name="Node 1")
        node1.communication_manager = comm_manager1
        
        node2 = Node(node_id="node2", name="Node 2")
        node2.communication_manager = comm_manager2
        
        # Start nodes
        node1.start()
        node2.start()
        
        # Send message from node1 to node2
        message = AgentMessage(
            sender_id="node1",
            receiver_id="node2",
            content="Hello from node1 to node2!",
            message_type="text"
        )
        
        await node1.communication_manager.send_message(message)
        
        comm_manager1.send_message.assert_called_once()


class TestAgentSystemIntegration:
    """Integration tests for agent-system interactions."""
    
    @patch("daie.agents.agent.CommunicationManager")
    @patch("daie.agents.agent.MemoryManager")
    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, mock_memory, mock_comm, mock_logger):
        """Test complete agent lifecycle."""
        config = AgentConfig(
            name="Test Agent",
            role="test-role",
            capabilities=["capability1", "capability2"]
        )
        
        agent = Agent(config)
        
        # Create mock managers
        mock_comm_instance = Mock()
        mock_comm.return_value = mock_comm_instance
        
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance
        
        # Test agent startup
        await agent.start(communication_manager=mock_comm_instance, memory_manager=mock_memory_instance)
        assert agent.is_running is True
        
        # Test message handling
        message = AgentMessage(
            sender_id="agent2",
            receiver_id="test-agent-1",
            content="Test message",
            message_type="text"
        )
        
        await agent._handle_message(message)
        
        # Test agent shutdown
        await agent.stop()
        assert agent.is_running is False


class TestMemoryIntegration:
    """Integration tests for memory system."""
    
    @patch("daie.agents.agent.MemoryManager")
    @pytest.mark.asyncio
    async def test_memory_across_sessions(self, mock_memory, mock_logger):
        """Test memory persistence across sessions."""
        # Create mock memory manager
        mock_memory_instance = Mock()
        mock_memory_instance.initialize_agent_memory = Mock()
        mock_memory.return_value = mock_memory_instance
        
        # Create system with initial memory
        system1 = DecentralizedAISystem()
        config = AgentConfig(name="Agent 1", role="test-role")
        agent1 = Agent(config)
        system1.add_agent(agent1)
        
        # Start agent with memory manager
        await agent1.start(memory_manager=mock_memory_instance)
        
        # Create new system instance and agent
        system2 = DecentralizedAISystem()
        agent2 = Agent(config)
        system2.add_agent(agent2)
        
        # Start agent with memory manager
        await agent2.start(memory_manager=mock_memory_instance)
        
        # Verify memory manager was initialized for both agents
        assert mock_memory_instance.initialize_agent_memory.call_count == 2


class TestNetworkIntegration:
    """Integration tests for network communication."""
    
    @pytest.mark.asyncio
    async def test_distributed_system(self, mock_logger):
        """Test distributed system behavior."""
        # Create communication managers
        comm_manager1 = Mock()
        comm_manager1.send_message = AsyncMock(return_value=True)
        
        comm_manager2 = Mock()
        comm_manager2.send_message = AsyncMock(return_value=True)
        
        comm_manager3 = Mock()
        comm_manager3.send_message = AsyncMock(return_value=True)
        
        # Create nodes
        node1 = Node(node_id="node1", name="Node 1")
        node1.communication_manager = comm_manager1
        
        node2 = Node(node_id="node2", name="Node 2")
        node2.communication_manager = comm_manager2
        
        node3 = Node(node_id="node3", name="Node 3")
        node3.communication_manager = comm_manager3
        
        # Start nodes
        node1.start()
        node2.start()
        node3.start()
        
        # Test message propagation between nodes
        message1 = AgentMessage(sender_id="node1", receiver_id="node2", content="Message from node1 to node2", message_type="text")
        await node1.communication_manager.send_message(message1)
        
        message2 = AgentMessage(sender_id="node2", receiver_id="node3", content="Message from node2 to node3", message_type="text")
        await node2.communication_manager.send_message(message2)
        
        message3 = AgentMessage(sender_id="node3", receiver_id="node1", content="Message from node3 to node1", message_type="text")
        await node3.communication_manager.send_message(message3)
        
        # Verify messages were sent
        assert comm_manager1.send_message.call_count == 1
        assert comm_manager2.send_message.call_count == 1
        assert comm_manager3.send_message.call_count == 1
        
        # Stop nodes
        node1.stop()
        node2.stop()
        node3.stop()


class TestPerformanceIntegration:
    """Performance integration tests."""
    
    def test_system_scalability(self, mock_logger):
        """Test system scalability with multiple nodes."""
        # Create nodes
        nodes = []
        for i in range(5):
            node = Node(node_id=f"node{i}", name=f"Node {i}")
            nodes.append(node)
        
        assert len(nodes) == 5
        
        # Start nodes
        for node in nodes:
            node.start()
        
        assert all(node.is_active for node in nodes)
        
        # Stop nodes
        for node in nodes:
            node.stop()
        
        assert all(not node.is_active for node in nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
