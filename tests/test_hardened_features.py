import pytest
import base64
import time
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from daie.utils.encryption.ciphers import (
    generate_x25519_keypair,
    derive_shared_secret,
    encrypt_data,
    decrypt_data
)
from daie.communication.manager import CommunicationManager
from daie.agents.message import AgentMessage
from daie.agents.agent import Agent
from daie.agents.config import AgentConfig
from daie.config import SystemConfig

class TestHardenedFeatures:
    """Integration and unit tests for hardened security and reliability features."""

    def test_x25519_key_exchange(self):
        """Test X25519 keypair generation and shared secret consistency."""
        # Generate two keypairs
        priv1, pub1 = generate_x25519_keypair()
        priv2, pub2 = generate_x25519_keypair()

        # Derive shared secrets
        secret1 = derive_shared_secret(priv1, pub2)
        secret2 = derive_shared_secret(priv2, pub1)

        # They must match
        assert secret1 == secret2
        assert len(secret1) == 32

    @pytest.mark.asyncio
    async def test_e2ee_communication(self):
        """Test End-to-End Encryption between two nodes using CommunicationManager."""
        config = SystemConfig()
        config.enable_e2e_encryption = True
        
        # Mock nats to avoid real network calls
        with patch("daie.communication.manager.NatsProvider") as mock_nats_class:
            mock_nats = mock_nats_class.return_value
            mock_nats.connect = AsyncMock()
            mock_nats.subscribe_agent = AsyncMock()
            mock_nats.unsubscribe_agent = AsyncMock()
            mock_nats.publish = AsyncMock(return_value=True)
            mock_nats.nc = MagicMock()
            mock_nats.nc.is_connected = True
            mock_nats.is_connected = True
            
            manager = CommunicationManager(config=config)
            
            # Setup agents with keypairs
            agent1 = Agent(config=AgentConfig(name="Agent1"))
            agent2 = Agent(config=AgentConfig(name="Agent2"))
            
            manager.register_agent(agent1)
            manager.register_agent(agent2)

            # Registry update with public keys
            manager.registry.register_node(agent1.id, {"role": "test"}, public_key=agent1.config.public_key)
            manager.registry.register_node(agent2.id, {"role": "test"}, public_key=agent2.config.public_key)

            # Mock MetricsServer to avoid port conflicts
            with patch("daie.communication.manager.MetricsServer") as mock_metrics_class:
                mock_metrics = mock_metrics_class.return_value
                mock_metrics.start = AsyncMock()
                mock_metrics.stop = AsyncMock()

                await manager.start()

                # Properly mock the async handler on Agent class for this test
            with patch.object(Agent, "_handle_message", new_callable=AsyncMock) as mock_handle:
                # Send encrypted message
                msg = AgentMessage(sender_id=agent1.id, receiver_id=agent2.id, content="Top secret")

                # The manager will encrypt it
                success = await manager.send_message(msg)
                assert success is True

                # Manually trigger the inbound handler logic (which decrypts)
                manager._handle_message(agent2.id, msg)
                
                # Give a slice to the event loop
                await asyncio.sleep(0.5)

                # Verify agent2 received the content (DECRYPTED)
                assert mock_handle.called
                received_msg = mock_handle.call_args[0][0]
                assert received_msg.content == "Top secret"

            await manager.stop()

    @pytest.mark.asyncio
    async def test_inbound_rate_limiting(self, mock_logger):
        """Test inbound rate limiting in CommunicationManager."""
        config = SystemConfig()
        config.enable_rate_limiting = True
        config.rate_limit_max_messages = 2
        config.rate_limit_window = 1.0
        
        # Mock nats completely
        with patch("daie.communication.manager.NatsProvider") as mock_nats_class:
            mock_nats = mock_nats_class.return_value
            mock_nats.connect = AsyncMock()
            mock_nats.subscribe_agent = AsyncMock()
            mock_nats.publish = AsyncMock(return_value=True)
            mock_nats.nc = MagicMock()
            mock_nats.nc.is_connected = True
            mock_nats.is_connected = True
            
            manager = CommunicationManager(config=config)
            
            agent = Agent(config=AgentConfig(name="Target"))
            manager.register_agent(agent)

            sender_id = "attacker"
            msg = AgentMessage(sender_id=sender_id, receiver_id=agent.id, content="flood")
            
            # Mock MetricsServer
            with patch("daie.communication.manager.MetricsServer") as mock_metrics_class:
                mock_metrics = mock_metrics_class.return_value
                mock_metrics.start = AsyncMock()
                mock_metrics.stop = AsyncMock()
                
                await manager.start()
            
            with patch.object(Agent, "_handle_message", new_callable=AsyncMock) as mock_handle:
                # Message 1 & 2: Success
                manager._handle_message(agent.id, msg)
                manager._handle_message(agent.id, msg)
                
                # Message 3: Should be dropped (rate limited)
                manager._handle_message(agent.id, msg)
                
                await asyncio.sleep(0.5)
                assert mock_handle.call_count == 2
            
            await manager.stop()

    @pytest.mark.asyncio
    async def test_memory_summarization_trigger(self):
        """Test that Agent triggers memory summarization after task execution."""
        config = AgentConfig(
            name="Memo",
            enable_memory_summarization=True,
            memory_summarization_threshold=5,
            stream=False
        )
        agent = Agent(config=config)
        agent.memory_manager = MagicMock()
        
        # Mock LLM and parser to return successfully
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value='{"answer": "Done"}')
        agent._llm = mock_llm
        agent._parse_llm_json = MagicMock(return_value={"answer": "Done"})

        # Mock MetricsServer to avoid port conflicts and hangs
        with patch("daie.communication.manager.MetricsServer") as mock_metrics_server:
            instance = mock_metrics_server.return_value
            instance.start = AsyncMock()
            instance.stop = AsyncMock()
            
            await agent.start()
            
            # Verify _track_task was called for the summarization task
            with patch.object(agent, "_track_task") as mock_track:
                await agent.execute_task("Do something")
                
                assert mock_track.called
                task = mock_track.call_args[0][0]
                # Verify it's a task object (has __await__)
                assert hasattr(task, "__await__") 
            
            await agent.stop()
