#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Message Handler

This module provides message handling capabilities for agents,
including message validation, routing, and processing.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
import json
import time
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages in the decentralized AI ecosystem"""
    TEXT = "text"
    TASK = "task"
    RESPONSE = "response"
    STATUS = "status"
    ERROR = "error"
    DISCOVERY = "discovery"
    HEARTBEAT = "heartbeat"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AgentMessage:
    """Data class representing an agent message"""
    message_id: str
    sender_id: str
    receiver_id: str
    type: MessageType
    content: str
    priority: MessagePriority = field(default=MessagePriority.NORMAL)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)
    signature: Optional[str] = None
    encrypted: bool = False

class MessageHandler:
    """
    Message handler for agent communication
    
    Handles message validation, processing, and dispatch
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize message handler
        
        Args:
            agent_id: Agent identifier
        """
        self.agent_id = agent_id
        self.message_processors: Dict[MessageType, List[Callable]] = {}
        self.sent_messages: Dict[str, AgentMessage] = {}
        self.received_messages: Dict[str, AgentMessage] = {}
        self.message_id_counter = 0
        
        logger.info(f"Message handler initialized for agent: {agent_id}")
    
    def register_processor(self, message_type: MessageType, processor: Callable):
        """
        Register a message processor for a specific message type
        
        Args:
            message_type: Type of message to process
            processor: Callable to handle messages of this type
        """
        if message_type not in self.message_processors:
            self.message_processors[message_type] = []
            
        self.message_processors[message_type].append(processor)
        logger.debug(f"Processor registered for message type: {message_type}")
    
    def create_message(self, receiver_id: str, content: str, 
                      message_type: MessageType = MessageType.TEXT,
                      priority: MessagePriority = MessagePriority.NORMAL,
                      metadata: Dict = None) -> AgentMessage:
        """
        Create a new agent message
        
        Args:
            receiver_id: Receiver agent identifier
            content: Message content
            message_type: Type of message
            priority: Message priority
            metadata: Additional metadata
            
        Returns:
            AgentMessage: Created message
        """
        self.message_id_counter += 1
        message_id = f"{self.agent_id}-{self.message_id_counter}-{int(time.time() * 1000)}"
        
        message = AgentMessage(
            message_id=message_id,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            type=message_type,
            content=content,
            priority=priority,
            metadata=metadata or {},
            timestamp=time.time()
        )
        
        self.sent_messages[message_id] = message
        logger.debug(f"Message created: {message_id}")
        
        return message
    
    async def process_message(self, message: AgentMessage):
        """
        Process an incoming message
        
        Args:
            message: Message to process
        """
        try:
            # Validate message
            if not self._validate_message(message):
                logger.warning(f"Invalid message received: {message.message_id}")
                return False
            
            # Store received message
            self.received_messages[message.message_id] = message
            logger.debug(f"Message received and stored: {message.message_id}")
            
            # Process message based on type
            if message.type in self.message_processors:
                for processor in self.message_processors[message.type]:
                    try:
                        await processor(message)
                    except Exception as e:
                        logger.error(f"Message processor failed: {e}")
                        
            else:
                logger.warning(f"No processor registered for message type: {message.type}")
                await self._handle_unknown_message_type(message)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return False
    
    def _validate_message(self, message: AgentMessage) -> bool:
        """
        Validate an incoming message
        
        Args:
            message: Message to validate
            
        Returns:
            bool: True if message is valid, False otherwise
        """
        # Check required fields
        if not all([message.message_id, message.sender_id, message.receiver_id, 
                   message.type, message.content]):
            logger.warning("Message missing required fields")
            return False
            
        # Check if message is for this agent
        if message.receiver_id != self.agent_id and message.receiver_id != "broadcast":
            logger.warning(f"Message not intended for this agent: {message.receiver_id}")
            return False
            
        # Check if message is already processed
        if message.message_id in self.received_messages:
            logger.warning(f"Message already processed: {message.message_id}")
            return False
            
        # Validate message type
        if not isinstance(message.type, MessageType):
            logger.warning(f"Invalid message type: {message.type}")
            return False
            
        # Validate priority
        if not isinstance(message.priority, MessagePriority):
            logger.warning(f"Invalid message priority: {message.priority}")
            return False
            
        return True
    
    async def _handle_unknown_message_type(self, message: AgentMessage):
        """
        Handle messages of unknown types
        
        Args:
            message: Message to handle
        """
        logger.warning(f"Received unknown message type: {message.type}")
        
        # Create error response
        error_msg = self.create_message(
            receiver_id=message.sender_id,
            content=f"Unknown message type: {message.type}",
            message_type=MessageType.ERROR,
            priority=MessagePriority.NORMAL
        )
        
        logger.debug(f"Error response created: {error_msg.message_id}")
    
    def serialize_message(self, message: AgentMessage) -> str:
        """
        Serialize message to JSON string
        
        Args:
            message: Message to serialize
            
        Returns:
            str: JSON serialized message
        """
        try:
            return json.dumps({
                "message_id": message.message_id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "type": message.type.value,
                "content": message.content,
                "priority": message.priority.value,
                "timestamp": message.timestamp,
                "metadata": message.metadata,
                "signature": message.signature,
                "encrypted": message.encrypted
            })
        except Exception as e:
            logger.error(f"Failed to serialize message: {e}")
            raise
    
    def deserialize_message(self, json_str: str) -> AgentMessage:
        """
        Deserialize JSON string to AgentMessage
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            AgentMessage: Deserialized message
        """
        try:
            data = json.loads(json_str)
            
            return AgentMessage(
                message_id=data["message_id"],
                sender_id=data["sender_id"],
                receiver_id=data["receiver_id"],
                type=MessageType(data["type"]),
                content=data["content"],
                priority=MessagePriority(data["priority"]),
                timestamp=data["timestamp"],
                metadata=data.get("metadata", {}),
                signature=data.get("signature"),
                encrypted=data.get("encrypted", False)
            )
        except Exception as e:
            logger.error(f"Failed to deserialize message: {e}")
            raise
    
    def get_message_by_id(self, message_id: str) -> Optional[AgentMessage]:
        """
        Get message by ID
        
        Args:
            message_id: Message identifier
            
        Returns:
            AgentMessage: Message or None if not found
        """
        return self.received_messages.get(message_id) or self.sent_messages.get(message_id)
    
    def get_sent_messages(self) -> List[AgentMessage]:
        """
        Get list of sent messages
        
        Returns:
            List[AgentMessage]: Sent messages
        """
        return list(self.sent_messages.values())
    
    def get_received_messages(self) -> List[AgentMessage]:
        """
        Get list of received messages
        
        Returns:
            List[AgentMessage]: Received messages
        """
        return list(self.received_messages.values())
    
    def get_messages_by_type(self, message_type: MessageType) -> List[AgentMessage]:
        """
        Get messages by type
        
        Args:
            message_type: Message type to filter
            
        Returns:
            List[AgentMessage]: Messages of the specified type
        """
        all_messages = list(self.sent_messages.values()) + list(self.received_messages.values())
        return [msg for msg in all_messages if msg.type == message_type]
    
    def clear_messages(self, older_than: float = None):
        """
        Clear messages from storage
        
        Args:
            older_than: Clear messages older than this timestamp (optional)
        """
        if older_than is None:
            self.sent_messages.clear()
            self.received_messages.clear()
            logger.info("All messages cleared from storage")
            return
            
        # Clear messages older than specified time
        current_time = time.time()
        for msg_id in list(self.sent_messages.keys()):
            if current_time - self.sent_messages[msg_id].timestamp > older_than:
                del self.sent_messages[msg_id]
                
        for msg_id in list(self.received_messages.keys()):
            if current_time - self.received_messages[msg_id].timestamp > older_than:
                del self.received_messages[msg_id]
                
        logger.info("Old messages cleared from storage")
    
    async def send_heartbeat(self) -> AgentMessage:
        """
        Send heartbeat message
        
        Returns:
            AgentMessage: Heartbeat message
        """
        heartbeat_msg = self.create_message(
            receiver_id="broadcast",
            content="heartbeat",
            message_type=MessageType.HEARTBEAT,
            priority=MessagePriority.LOW,
            metadata={
                "timestamp": time.time(),
                "status": "online"
            }
        )
        
        logger.debug(f"Heartbeat message created: {heartbeat_msg.message_id}")
        return heartbeat_msg
    
    async def send_status_update(self, status: str, metadata: Dict = None) -> AgentMessage:
        """
        Send status update message
        
        Args:
            status: Current status
            metadata: Additional metadata
            
        Returns:
            AgentMessage: Status update message
        """
        status_msg = self.create_message(
            receiver_id="broadcast",
            content=status,
            message_type=MessageType.STATUS,
            priority=MessagePriority.NORMAL,
            metadata=metadata or {}
        )
        
        logger.debug(f"Status update message created: {status_msg.message_id}")
        return status_msg
    
    async def send_error(self, receiver_id: str, error: str, 
                       original_message_id: str = None) -> AgentMessage:
        """
        Send error message
        
        Args:
            receiver_id: Receiver agent identifier
            error: Error message
            original_message_id: Original message ID (optional)
            
        Returns:
            AgentMessage: Error message
        """
        error_msg = self.create_message(
            receiver_id=receiver_id,
            content=error,
            message_type=MessageType.ERROR,
            priority=MessagePriority.HIGH,
            metadata={
                "original_message_id": original_message_id,
                "timestamp": time.time()
            }
        )
        
        logger.debug(f"Error message created: {error_msg.message_id}")
        return error_msg

# Singleton instance for the message handler
_message_handler_instance = None

def get_message_handler(agent_id: str) -> MessageHandler:
    """
    Get the singleton instance of the message handler
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        MessageHandler: Singleton instance
    """
    global _message_handler_instance
    if _message_handler_instance is None:
        _message_handler_instance = MessageHandler(agent_id)
    return _message_handler_instance

if __name__ == "__main__":
    # Test message handler functionality
    logging.basicConfig(level=logging.DEBUG)
    
    async def test_message_handler():
        try:
            # Create message handler
            handler = MessageHandler("test-agent-001")
            
            # Test create message
            test_msg = handler.create_message(
                receiver_id="test-agent-002",
                content="Hello, world!",
                message_type=MessageType.TEXT,
                priority=MessagePriority.NORMAL
            )
            
            logger.info(f"Message created: {test_msg.message_id}")
            
            # Test serialize/deserialize
            serialized = handler.serialize_message(test_msg)
            deserialized = handler.deserialize_message(serialized)
            
            logger.info("Message serialization test passed")
            
            # Test register processor
            async def text_processor(msg):
                logger.info(f"Text message received: {msg.content}")
                
            handler.register_processor(MessageType.TEXT, text_processor)
            
            # Test process message
            await handler.process_message(deserialized)
            
            # Test heartbeats
            heartbeat = await handler.send_heartbeat()
            logger.info(f"Heartbeat created: {heartbeat.message_id}")
            
            # Test status update
            status = await handler.send_status_update("ready", {"load": 0.1})
            logger.info(f"Status update created: {status.message_id}")
            
            # Test message retrieval
            retrieved = handler.get_message_by_id(test_msg.message_id)
            logger.info(f"Message retrieval test passed: {retrieved is not None}")
            
            # Test message filtering
            text_messages = handler.get_messages_by_type(MessageType.TEXT)
            logger.info(f"Text messages found: {len(text_messages)}")
            
            logger.info("✅ Message handler test completed successfully!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    import asyncio
    asyncio.run(test_message_handler())
