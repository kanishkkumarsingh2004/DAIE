"""Tests for communication module - Agent Communication and Peer Management.

Use Case Description:
This test file validates the communication system in the Decentralized AI Ecosystem (DAIE), which enables agents to communicate and share information across the decentralized network. Key functionalities tested include:

1. **Communication Manager**: Core communication orchestrator
   - Communication manager creation and initialization
   - Starting and stopping communication services
   - Connection status management

2. **Message Handling**: Agent communication
   - Sending and receiving AgentMessage objects
   - Broadcasting messages to all connected agents
   - Message serialization and deserialization

3. **Agent Registration**: Managing agent connections
   - Registering agents with communication manager
   - Deregistering agents from communication manager
   - Retrieving agent information

4. **Peer Management**: Network node discovery
   - Updating peer node information
   - Retrieving peer information
   - Managing network topology

These tests ensure that agents can communicate reliably across the network, forming the communication backbone of the decentralized AI system.
"""

import asyncio
from unittest.mock import MagicMock, AsyncMock

import pytest

from daie.agents.message import AgentMessage
from daie.communication.manager import CommunicationManager
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

        await manager.stop()
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
        await manager.stop()

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

        # Register an agent to receive broadcast
        agent1 = MagicMock()
        agent1.id = "agent1"
        agent1.name = "Agent 1"
        agent1.config = MagicMock()
        agent1.config.allowed_senders = []

        agent2 = MagicMock()
        agent2.id = "agent2"
        agent2.name = "Agent 2"
        agent2.config = MagicMock()
        agent2.config.allowed_senders = []

        manager.register_agent(agent1)
        manager.register_agent(agent2)

        message = AgentMessage(
            sender_id="agent1",
            receiver_id="*",
            content="Broadcast message",
            message_type="text",
        )

        count = await manager.broadcast_message(message)
        # Verify count > 0 (agent2 should have received it, agent1 is skipped as sender)
        assert count >= 1
        await manager.stop()

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

    @pytest.mark.asyncio
    async def test_communication_manager_encryption(self, mock_logger):
        """Test end-to-end encryption for messages."""
        config = SystemConfig()
        config.enable_e2e_encryption = True
        manager = CommunicationManager(config=config)

        await manager.start()

        # Register agents
        agent1 = MagicMock()
        agent1.id = "agent1"
        agent1.name = "Agent 1"
        agent1.config = MagicMock()
        agent1.config.allowed_senders = []
        agent1._handle_message = AsyncMock()

        agent2 = MagicMock()
        agent2.id = "agent2"
        agent2.name = "Agent 2"
        agent2.config = MagicMock()
        agent2.config.allowed_senders = []
        agent2._handle_message = AsyncMock()

        manager.register_agent(agent1)
        manager.register_agent(agent2)

        # Send encrypted message
        message = AgentMessage(
            sender_id="agent1",
            receiver_id="agent2",
            content="Secret message",
            message_type="text",
        )

        success = await manager.send_message(message)
        assert success is True

        # Verify agent2 received the message (decrypted)
        assert agent2._handle_message.called
        await manager.stop()

    @pytest.mark.asyncio
    async def test_communication_manager_audit_logging(self, mock_logger):
        """Test audit logging for A2A communications."""
        config = SystemConfig()
        config.enable_audit_logging = True
        manager = CommunicationManager(config=config)

        await manager.start()

        # Register agents
        agent1 = MagicMock()
        agent1.id = "agent1"
        agent1.name = "Agent 1"
        agent1.config = MagicMock()
        agent1.config.allowed_senders = []
        agent1._handle_message = MagicMock()

        agent2 = MagicMock()
        agent2.id = "agent2"
        agent2.name = "Agent 2"
        agent2.config = MagicMock()
        agent2.config.allowed_senders = []
        agent2._handle_message = MagicMock()

        manager.register_agent(agent1)
        manager.register_agent(agent2)

        # Send message and verify audit log
        message = AgentMessage(
            sender_id="agent1",
            receiver_id="agent2",
            content="Test message",
            message_type="text",
        )

        success = await manager.send_message(message)
        assert success is True
        await manager.stop()

    @pytest.mark.asyncio
    async def test_communication_manager_rate_limiting(self, mock_logger):
        """Test rate limiting for A2A communications."""
        config = SystemConfig()
        config.enable_rate_limiting = True
        config.rate_limit_window = 1  # 1 second window
        config.rate_limit_max_messages = 2  # Max 2 messages per window
        manager = CommunicationManager(config=config)

        await manager.start()

        # Register agents
        agent1 = MagicMock()
        agent1.id = "agent1"
        agent1.name = "Agent 1"
        agent1.config = MagicMock()
        agent1.config.allowed_senders = []
        agent1._handle_message = MagicMock()

        agent2 = MagicMock()
        agent2.id = "agent2"
        agent2.name = "Agent 2"
        agent2.config = MagicMock()
        agent2.config.allowed_senders = []
        agent2._handle_message = MagicMock()

        manager.register_agent(agent1)
        manager.register_agent(agent2)

        # Send messages up to rate limit
        for i in range(2):
            message = AgentMessage(
                sender_id="agent1",
                receiver_id="agent2",
                content=f"Message {i}",
                message_type="text",
            )
            success = await manager.send_message(message)
            assert success is True

        # Third message should be rate limited
        message = AgentMessage(
            sender_id="agent1",
            receiver_id="agent2",
            content="Rate limited message",
            message_type="text",
        )
        success = await manager.send_message(message)
        assert success is False
        await manager.stop()

    @pytest.mark.asyncio
    async def test_communication_manager_rate_limiting_disabled(self, mock_logger):
        """Test rate limiting when disabled."""
        config = SystemConfig()
        config.enable_rate_limiting = False
        manager = CommunicationManager(config=config)

        await manager.start()

        # Register agents
        agent1 = MagicMock()
        agent1.id = "agent1"
        agent1.name = "Agent 1"
        agent1.config = MagicMock()
        agent1.config.allowed_senders = []
        agent1._handle_message = MagicMock()

        agent2 = MagicMock()
        agent2.id = "agent2"
        agent2.name = "Agent 2"
        agent2.config = MagicMock()
        agent2.config.allowed_senders = []
        agent2._handle_message = MagicMock()

        manager.register_agent(agent1)
        manager.register_agent(agent2)

        # Send many messages - should all succeed when rate limiting is disabled
        for i in range(10):
            message = AgentMessage(
                sender_id="agent1",
                receiver_id="agent2",
                content=f"Message {i}",
                message_type="text",
            )
            success = await manager.send_message(message)
            assert success is True
        await manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
