"""Tests for communication module."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from daie.communication.manager import CommunicationManager
from daie.agents.message import AgentMessage
from daie.config import SystemConfig


class TestCommunicationManager:
    """Tests for CommunicationManager class."""

    @pytest.mark.asyncio
    async def test_communication_manager_creation(self, mock_logger):
        """Test communication manager creation."""
        config = SystemConfig()
        manager = CommunicationManager(config=config)

        assert manager is not None
        assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_communication_manager_start_stop(self, mock_logger):
        """Test communication manager start and stop."""
        config = SystemConfig()
        manager = CommunicationManager(config=config)

        await manager.start()
        assert manager.is_connected is True

        manager.stop()
        # Wait for stop to complete
        await asyncio.sleep(0.1)
        assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_communication_manager_send_message(self, mock_logger):
        """Test sending a message."""
        config = SystemConfig()
        manager = CommunicationManager(config=config)

        await manager.start()

        message = AgentMessage(
            sender_id="agent1",
            receiver_id="agent2",
            content="Test message",
            message_type="text",
        )

        success = await manager.send_message(message)
        assert success is True

    @pytest.mark.asyncio
    async def test_communication_manager_register_agent(self, mock_logger):
        """Test registering an agent."""
        config = SystemConfig()
        manager = CommunicationManager(config=config)

        agent = MagicMock()
        agent.id = "agent1"
        agent.name = "Test Agent"

        manager.register_agent(agent)
        assert manager.get_agent("agent1") == agent

    @pytest.mark.asyncio
    async def test_communication_manager_deregister_agent(self, mock_logger):
        """Test deregistering an agent."""
        config = SystemConfig()
        manager = CommunicationManager(config=config)

        agent = MagicMock()
        agent.id = "agent1"
        agent.name = "Test Agent"

        manager.register_agent(agent)
        assert manager.get_agent("agent1") == agent

        manager.deregister_agent("agent1")
        assert manager.get_agent("agent1") is None

    @pytest.mark.asyncio
    async def test_communication_manager_broadcast_message(self, mock_logger):
        """Test broadcasting a message."""
        config = SystemConfig()
        manager = CommunicationManager(config=config)

        await manager.start()

        message = AgentMessage(
            sender_id="agent1",
            receiver_id="*",
            content="Broadcast message",
            message_type="text",
        )

        count = await manager.broadcast_message(message)
        assert count > 0

    @pytest.mark.asyncio
    async def test_communication_manager_peer_management(self, mock_logger):
        """Test peer management."""
        config = SystemConfig()
        manager = CommunicationManager(config=config)

        manager.update_peer_info(
            "peer1",
            {
                "name": "Peer 1",
                "role": "worker",
                "capabilities": ["compute", "storage"],
            },
        )

        peer_info = manager.get_peer_info("peer1")
        assert peer_info is not None
        assert peer_info.peer_id == "peer1"
        assert peer_info.name == "Peer 1"
        assert peer_info.role == "worker"

        peers = manager.get_peers()
        assert len(peers) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
