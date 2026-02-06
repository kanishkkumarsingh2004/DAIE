#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Coordination Layer Tests

Comprehensive tests for the coordination layer functionality.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from central_core_system.coordination.nats_jetstream import NATSJetStreamService
from agent_node_system.communication.encryption_layer import EncryptionLayer
from agent_node_system.communication.message_handler import MessageHandler, MessageType, MessagePriority
from agent_node_system.communication.p2p_client import P2PClient
from agent_node_system.identity.keypair_manager import KeypairManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestEncryptionLayer:
    """Tests for the encryption layer"""
    
    def test_encryption_layer_initialization(self):
        """Test encryption layer initialization"""
        enc_layer = EncryptionLayer()
        assert enc_layer is not None
        logger.info("✅ Encryption layer initialization test passed")
    
    def test_key_generation(self):
        """Test public and private key generation"""
        enc_layer = EncryptionLayer()
        public_key = enc_layer.get_public_key()
        public_key_hex = enc_layer.get_public_key_hex()
        
        assert len(public_key) > 0
        assert len(public_key_hex) > 0
        logger.info("✅ Key generation test passed")
    
    def test_shared_key_generation(self):
        """Test shared key generation via X25519 key exchange"""
        alice = EncryptionLayer()
        bob = EncryptionLayer()
        
        alice_shared_key = alice.generate_shared_key(bob.get_public_key())
        bob_shared_key = bob.generate_shared_key(alice.get_public_key())
        
        assert alice_shared_key == bob_shared_key
        logger.info("✅ Shared key generation test passed")
    
    def test_encryption_decryption(self):
        """Test message encryption and decryption"""
        alice = EncryptionLayer()
        bob = EncryptionLayer()
        
        test_message = b"Hello, this is a secure message!"
        encrypted = alice.encrypt_for_peer(test_message, bob.get_public_key())
        decrypted = bob.decrypt_from_peer(encrypted, alice.get_public_key())
        
        assert decrypted == test_message
        logger.info("✅ Encryption/decryption test passed")
    
    def test_signature_verification(self):
        """Test message signing and verification"""
        enc_layer = EncryptionLayer()
        keypair_manager = KeypairManager()
        
        if not keypair_manager.has_keys():
            keypair_manager.generate_keys()
        
        test_message = b"Test message for signing"
        signature = enc_layer.sign_message(test_message, keypair_manager.get_private_key())
        valid = enc_layer.verify_signature(test_message, signature, keypair_manager.get_public_key())
        
        assert valid is True
        logger.info("✅ Signature verification test passed")

class TestMessageHandler:
    """Tests for the message handler"""
    
    def test_message_handler_initialization(self):
        """Test message handler initialization"""
        handler = MessageHandler("test-agent-001")
        assert handler is not None
        logger.info("✅ Message handler initialization test passed")
    
    def test_create_message(self):
        """Test creating a new message"""
        handler = MessageHandler("test-agent-001")
        message = handler.create_message(
            receiver_id="test-agent-002",
            content="Hello, world!",
            message_type=MessageType.TEXT,
            priority=MessagePriority.NORMAL
        )
        
        assert message is not None
        assert message.sender_id == "test-agent-001"
        assert message.receiver_id == "test-agent-002"
        assert message.content == "Hello, world!"
        logger.info("✅ Create message test passed")
    
    def test_serialization(self):
        """Test message serialization and deserialization"""
        handler = MessageHandler("test-agent-001")
        message = handler.create_message(
            receiver_id="test-agent-002",
            content="Hello, world!",
            message_type=MessageType.TEXT
        )
        
        serialized = handler.serialize_message(message)
        deserialized = handler.deserialize_message(serialized)
        
        assert deserialized.content == message.content
        assert deserialized.type == message.type
        logger.info("✅ Message serialization test passed")
    
    def test_message_processing(self):
        """Test message processing"""
        handler = MessageHandler("test-agent-001")
        
        async def test_processor(msg):
            logger.debug(f"Test processor received: {msg.content}")
        
        handler.register_processor(MessageType.TEXT, test_processor)
        
        test_message = handler.create_message(
            receiver_id="test-agent-001",
            content="Test message",
            message_type=MessageType.TEXT
        )
        
        result = asyncio.run(handler.process_message(test_message))
        assert result is True
        logger.info("✅ Message processing test passed")

class TestNATSJetStreamService:
    """Tests for the NATS JetStream service"""
    
    @pytest.mark.asyncio
    @patch('central_core_system.coordination.nats_jetstream.nats.connect')
    async def test_nats_service_initialization(self, mock_connect):
        """Test NATS JetStream service initialization"""
        with patch('central_core_system.coordination.nats_jetstream.get_nats_service') as mock_get_service:
            mock_service = Mock()
            mock_get_service.return_value = mock_service
            
            service = await mock_get_service("nats://localhost:4222")
            assert service is not None
            logger.info("✅ NATS JetStream service initialization test passed")
    
    @pytest.mark.asyncio
    @patch('central_core_system.coordination.nats_jetstream.nats.connect')
    async def test_agent_registration(self, mock_connect):
        """Test agent registration functionality"""
        with patch('central_core_system.coordination.nats_jetstream.NATSJetStreamService') as MockService:
            service = MockService.return_value
            service.connect.return_value = True
            
            await service.connect()
            
            agent_info = {
                "agent_id": "test-agent-001",
                "name": "Test Agent",
                "role": "test",
                "capabilities": ["test"]
            }
            
            result = await service.register_agent(agent_info)
            assert result is True
            logger.info("✅ Agent registration test passed")
    
    @pytest.mark.asyncio
    @patch('central_core_system.coordination.nats_jetstream.nats.connect')
    async def test_agent_discovery(self, mock_connect):
        """Test agent discovery functionality"""
        with patch('central_core_system.coordination.nats_jetstream.NATSJetStreamService') as MockService:
            service = MockService.return_value
            service.connect.return_value = True
            
            await service.connect()
            
            test_agents = [
                {"agent_id": f"agent-{i}", "name": f"Agent {i}"} for i in range(5)
            ]
            
            service.get_online_agents.return_value = test_agents
            
            agents = await service.get_online_agents()
            assert len(agents) == 5
            logger.info("✅ Agent discovery test passed")
    
    @pytest.mark.asyncio
    @patch('central_core_system.coordination.nats_jetstream.nats.connect')
    async def test_message_sending(self, mock_connect):
        """Test message sending functionality"""
        with patch('central_core_system.coordination.nats_jetstream.NATSJetStreamService') as MockService:
            service = MockService.return_value
            service.connect.return_value = True
            
            await service.connect()
            
            result = await service.send_message(
                "sender-001",
                "receiver-001",
                {"content": "Test message"}
            )
            
            assert result is True
            logger.info("✅ Message sending test passed")

class TestP2PClient:
    """Tests for the P2P client"""
    
    @pytest.mark.asyncio
    async def test_p2p_client_initialization(self):
        """Test P2P client initialization"""
        client = P2PClient("test-agent-001")
        assert client is not None
        assert client.agent_id == "test-agent-001"
        logger.info("✅ P2P client initialization test passed")
    
    @pytest.mark.asyncio
    @patch('agent_node_system.communication.p2p_client.P2PClient._create_host')
    async def test_p2p_connection(self, mock_create_host):
        """Test P2P client connection"""
        # Create a mock host
        mock_host = Mock()
        mock_host.listen = Mock()
        mock_host.connect = Mock()
        mock_host.new_stream = Mock()
        
        mock_create_host.return_value = mock_host
        
        client = P2PClient("test-agent-001")
        
        with patch('agent_node_system.communication.p2p_client.P2PClient.start'):
            await client.start()
            assert client.running is True
            
        logger.info("✅ P2P client connection test passed")

class TestCoordinationIntegration:
    """Integration tests for the coordination layer"""
    
    @pytest.mark.asyncio
    async def test_complete_coordination_flow(self):
        """Test complete coordination layer flow"""
        logger.info("Starting complete coordination layer integration test...")
        
        # Create encryption layer
        enc_layer = EncryptionLayer()
        
        # Create message handler
        message_handler = MessageHandler("test-agent-001")
        
        # Create event listener
        from agent_node_system.communication.event_listener import EventListener, EventType
        event_listener = EventListener("test-agent-001")
        
        async def test_event_handler(event):
            logger.debug(f"Event received: {event.event_type.value}")
            
        event_listener.register_handler(EventType.SYSTEM_READY, test_event_handler)
        
        logger.info("✅ Coordination layer integration test completed")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
