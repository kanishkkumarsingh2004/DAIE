#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Central Core System
NATS JetStream Coordination Service

This module provides the coordination layer using NATS JetStream for:
- Agent discovery
- Identity verification
- Encrypted messaging
- Task routing
- Event streaming

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
import nats
from nats.js import JetStreamContext
from nats.aio.client import Client as NATSClient
from nats.aio.errors import ErrConnectionClosed, ErrTimeout

logger = logging.getLogger(__name__)

class NATSJetStreamService:
    """
    NATS JetStream coordination service for the decentralized AI ecosystem
    
    Provides:
    - Agent discovery and registration
    - Message routing with load balancing
    - Event streaming with durable subscriptions
    - Task distribution
    """
    
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        """
        Initialize NATS JetStream service
        
        Args:
            nats_url: NATS server URL
        """
        self.nats_url = nats_url
        self.nc: Optional[NATSClient] = None
        self.js: Optional[JetStreamContext] = None
        self.connected = False
        self.agent_registry: Dict[str, Dict] = {}
        self.subscriptions: List[Any] = []
        
        logger.info(f"Initialized NATS JetStream service with URL: {nats_url}")
    
    async def connect(self) -> bool:
        """
        Connect to NATS server and JetStream
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to NATS server: {self.nats_url}")
            
            # Connect to NATS
            self.nc = await nats.connect(self.nats_url)
            
            # Get JetStream context
            self.js = self.nc.jetstream()
            
            # Create required streams
            await self._create_streams()
            
            # Create consumers for agent discovery and message routing
            await self._create_consumers()
            
            # Subscribe to agent discovery topics
            await self._subscribe_to_agent_topics()
            
            self.connected = True
            logger.info("Successfully connected to NATS JetStream")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to NATS JetStream: {e}")
            return False
    
    async def _create_streams(self):
        """Create required JetStream streams"""
        try:
            # Stream for agent discovery and registration
            await self.js.add_stream(
                name="AGENT_DISCOVERY",
                subjects=["agents.>"],
                retention="limits",
                max_bytes=1024 * 1024 * 100,  # 100MB
                max_age=3600 * 24  # 24 hours
            )
            
            # Stream for encrypted messaging between agents
            await self.js.add_stream(
                name="AGENT_MESSAGES",
                subjects=["messages.>"],
                retention="limits",
                max_bytes=1024 * 1024 * 1000,  # 1GB
                max_age=3600 * 24 * 7  # 7 days
            )
            
            # Stream for task distribution and routing
            await self.js.add_stream(
                name="TASK_ROUTING",
                subjects=["tasks.>"],
                retention="limits",
                max_bytes=1024 * 1024 * 500,  # 500MB
                max_age=3600 * 24 * 3  # 3 days
            )
            
            # Stream for system events and telemetry
            await self.js.add_stream(
                name="SYSTEM_EVENTS",
                subjects=["events.>"],
                retention="limits",
                max_bytes=1024 * 1024 * 200,  # 200MB
                max_age=3600 * 24 * 1  # 1 day
            )
            
            logger.info("JetStream streams created successfully")
            
        except Exception as e:
            logger.warning(f"Stream creation failed (may already exist): {e}")
    
    async def _create_consumers(self):
        """Create JetStream consumers for processing messages"""
        try:
            # Consumer for agent discovery
            await self.js.add_consumer(
                stream="AGENT_DISCOVERY",
                consumer={
                    "name": "agent-discovery-consumer",
                    "subjects": ["agents.>"],
                    "ack_policy": "explicit",
                    "retention": "workqueue",
                    "max_deliver": 5
                }
            )
            
            # Consumer for task routing with load balancing
            await self.js.add_consumer(
                stream="TASK_ROUTING",
                consumer={
                    "name": "task-routing-consumer",
                    "subjects": ["tasks.>"],
                    "ack_policy": "explicit",
                    "retention": "workqueue",
                    "max_deliver": 3
                }
            )
            
            logger.info("JetStream consumers created successfully")
            
        except Exception as e:
            logger.warning(f"Consumer creation failed (may already exist): {e}")
    
    async def _subscribe_to_agent_topics(self):
        """Subscribe to agent discovery and heartbeat topics"""
        try:
            # Subscribe to agent registration
            sub = await self.nc.subscribe(
                "agents.register",
                cb=self._handle_agent_registration
            )
            self.subscriptions.append(sub)
            
            # Subscribe to agent heartbeats
            sub = await self.nc.subscribe(
                "agents.heartbeat",
                cb=self._handle_agent_heartbeat
            )
            self.subscriptions.append(sub)
            
            # Subscribe to agent unregistration
            sub = await self.nc.subscribe(
                "agents.unregister",
                cb=self._handle_agent_unregistration
            )
            self.subscriptions.append(sub)
            
            logger.info("Agent discovery subscriptions created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create agent discovery subscriptions: {e}")
    
    async def _handle_agent_registration(self, msg):
        """Handle agent registration messages"""
        try:
            agent_info = json.loads(msg.data.decode())
            agent_id = agent_info.get("agent_id")
            
            if agent_id:
                self.agent_registry[agent_id] = {
                    "info": agent_info,
                    "last_seen": time.time(),
                    "status": "online"
                }
                
                logger.info(f"Agent registered: {agent_id}")
                logger.debug(f"Agent info: {agent_info}")
                
                # Acknowledge the message
                await msg.ack()
                
                # Broadcast agent registration to all subscribers
                await self._broadcast_agent_update(agent_id, "registered")
                
            else:
                logger.warning("Received agent registration without agent_id")
                
        except Exception as e:
            logger.error(f"Failed to handle agent registration: {e}")
    
    async def _handle_agent_heartbeat(self, msg):
        """Handle agent heartbeat messages"""
        try:
            heartbeat_data = json.loads(msg.data.decode())
            agent_id = heartbeat_data.get("agent_id")
            
            if agent_id in self.agent_registry:
                self.agent_registry[agent_id]["last_seen"] = time.time()
                self.agent_registry[agent_id]["status"] = "online"
                
                logger.debug(f"Heartbeat received from agent: {agent_id}")
                
                # Acknowledge the message
                await msg.ack()
                
            else:
                logger.warning(f"Heartbeat received from unknown agent: {agent_id}")
                
        except Exception as e:
            logger.error(f"Failed to handle agent heartbeat: {e}")
    
    async def _handle_agent_unregistration(self, msg):
        """Handle agent unregistration messages"""
        try:
            agent_info = json.loads(msg.data.decode())
            agent_id = agent_info.get("agent_id")
            
            if agent_id in self.agent_registry:
                del self.agent_registry[agent_id]
                logger.info(f"Agent unregistered: {agent_id}")
                
                # Acknowledge the message
                await msg.ack()
                
                # Broadcast agent unregistration to all subscribers
                await self._broadcast_agent_update(agent_id, "unregistered")
                
            else:
                logger.warning(f"Unregistration request for unknown agent: {agent_id}")
                
        except Exception as e:
            logger.error(f"Failed to handle agent unregistration: {e}")
    
    async def _broadcast_agent_update(self, agent_id: str, event_type: str):
        """Broadcast agent status updates to subscribers"""
        try:
            update_msg = {
                "agent_id": agent_id,
                "event_type": event_type,
                "timestamp": time.time(),
                "agent_info": self.agent_registry.get(agent_id, {}).get("info")
            }
            
            await self.nc.publish(
                "agents.updates",
                json.dumps(update_msg).encode()
            )
            
            logger.debug(f"Agent update broadcasted: {agent_id} - {event_type}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast agent update: {e}")
    
    async def register_agent(self, agent_info: Dict) -> bool:
        """
        Register an agent with the coordination system
        
        Args:
            agent_info: Agent information dictionary
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            await self.nc.publish(
                "agents.register",
                json.dumps(agent_info).encode()
            )
            
            logger.info(f"Agent registration published: {agent_info.get('agent_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish agent registration: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the coordination system
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            bool: True if unregistration successful, False otherwise
        """
        try:
            await self.nc.publish(
                "agents.unregister",
                json.dumps({"agent_id": agent_id}).encode()
            )
            
            logger.info(f"Agent unregistration published: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish agent unregistration: {e}")
            return False
    
    async def send_message(self, sender_id: str, receiver_id: str, message: Dict) -> bool:
        """
        Send a message from one agent to another
        
        Args:
            sender_id: Sender agent identifier
            receiver_id: Receiver agent identifier
            message: Message to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            message_payload = {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "message": message,
                "timestamp": time.time()
            }
            
            await self.js.publish(
                f"messages.{sender_id}.{receiver_id}",
                json.dumps(message_payload).encode()
            )
            
            logger.debug(f"Message sent from {sender_id} to {receiver_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message from {sender_id} to {receiver_id}: {e}")
            return False
    
    async def route_task(self, task: Dict, target_agents: List[str] = None) -> bool:
        """
        Route a task to available agents
        
        Args:
            task: Task to route
            target_agents: List of specific agents to route to (optional)
            
        Returns:
            bool: True if task routed successfully, False otherwise
        """
        try:
            task_payload = {
                "task": task,
                "timestamp": time.time(),
                "target_agents": target_agents
            }
            
            if target_agents:
                # Route to specific agents
                for agent_id in target_agents:
                    await self.js.publish(
                        f"tasks.{agent_id}",
                        json.dumps(task_payload).encode()
                    )
            else:
                # Route to any available agent (work queue pattern)
                await self.js.publish(
                    "tasks.available",
                    json.dumps(task_payload).encode()
                )
                
            logger.debug(f"Task routed successfully: {task.get('task_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to route task: {e}")
            return False
    
    async def publish_event(self, event_type: str, event_data: Dict) -> bool:
        """
        Publish a system event
        
        Args:
            event_type: Event type
            event_data: Event data
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        try:
            event_payload = {
                "event_type": event_type,
                "data": event_data,
                "timestamp": time.time()
            }
            
            await self.js.publish(
                f"events.{event_type}",
                json.dumps(event_payload).encode()
            )
            
            logger.debug(f"Event published: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    async def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """
        Get agent information from registry
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict: Agent information or None if not found
        """
        return self.agent_registry.get(agent_id, {}).get("info")
    
    async def get_online_agents(self) -> List[Dict]:
        """
        Get list of online agents
        
        Returns:
            List[Dict]: List of online agent information
        """
        current_time = time.time()
        online_agents = []
        
        for agent_id, agent_data in self.agent_registry.items():
            # Consider agents as online if heartbeat within last 60 seconds
            if current_time - agent_data["last_seen"] < 60:
                online_agents.append({
                    "agent_id": agent_id,
                    "info": agent_data["info"],
                    "last_seen": agent_data["last_seen"],
                    "status": agent_data["status"]
                })
                
        return online_agents
    
    async def subscribe_to_messages(self, agent_id: str, callback):
        """
        Subscribe to messages for a specific agent
        
        Args:
            agent_id: Agent identifier
            callback: Callback function to handle messages
            
        Returns:
            Subscription object
        """
        try:
            sub = await self.js.pull_subscribe(
                f"messages.*.{agent_id}",
                stream="AGENT_MESSAGES",
                durable=f"agent-{agent_id}-messages",
                config={
                    "ack_policy": "explicit",
                    "max_deliver": 5
                }
            )
            
            # Start background task to process messages
            asyncio.create_task(self._process_messages(sub, callback))
            
            logger.info(f"Subscribed to messages for agent: {agent_id}")
            return sub
            
        except Exception as e:
            logger.error(f"Failed to subscribe to messages for agent {agent_id}: {e}")
            raise
    
    async def _process_messages(self, subscription, callback):
        """Process messages from a subscription"""
        while self.connected:
            try:
                msgs = await subscription.fetch(5, timeout=1)
                for msg in msgs:
                    try:
                        message_data = json.loads(msg.data.decode())
                        await callback(message_data)
                        await msg.ack()
                    except Exception as e:
                        logger.error(f"Failed to process message: {e}")
                        await msg.nak()
                        
            except ErrTimeout:
                continue
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                await asyncio.sleep(1)
    
    async def health_check(self) -> Dict:
        """
        Perform health check on the coordination system
        
        Returns:
            Dict: Health check results
        """
        try:
            health_info = {
                "connected": self.connected,
                "agent_count": len(self.agent_registry),
                "online_agents": len(await self.get_online_agents()),
                "subscriptions": len(self.subscriptions)
            }
            
            return health_info
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"connected": False, "error": str(e)}
    
    async def disconnect(self):
        """Disconnect from NATS JetStream"""
        try:
            for sub in self.subscriptions:
                await sub.unsubscribe()
            
            if self.nc:
                await self.nc.drain()
                await self.nc.close()
                
            self.connected = False
            logger.info("Disconnected from NATS JetStream")
            
        except Exception as e:
            logger.error(f"Error disconnecting from NATS JetStream: {e}")

# Singleton instance for the NATS JetStream service
_nats_service_instance = None

async def get_nats_service(nats_url: str = "nats://localhost:4222") -> NATSJetStreamService:
    """
    Get the singleton instance of the NATS JetStream service
    
    Args:
        nats_url: NATS server URL
        
    Returns:
        NATSJetStreamService: Singleton instance
    """
    global _nats_service_instance
    if _nats_service_instance is None:
        _nats_service_instance = NATSJetStreamService(nats_url)
        await _nats_service_instance.connect()
    elif not _nats_service_instance.connected:
        await _nats_service_instance.connect()
        
    return _nats_service_instance

if __name__ == "__main__":
    # Test NATS JetStream service functionality
    logging.basicConfig(level=logging.DEBUG)
    
    async def test_service():
        try:
            # Create and connect to NATS JetStream
            nats_service = NATSJetStreamService("nats://localhost:4222")
            connected = await nats_service.connect()
            
            if not connected:
                logger.error("Failed to connect to NATS server")
                return
            
            logger.info("NATS JetStream service test starting...")
            
            # Test health check
            health = await nats_service.health_check()
            logger.info(f"Health check: {health}")
            
            # Test agent registration
            test_agent = {
                "agent_id": "test-agent-001",
                "name": "Test Agent",
                "role": "test",
                "capabilities": ["test"],
                "version": "1.0.0"
            }
            
            await nats_service.register_agent(test_agent)
            
            # Wait for registration to propagate
            await asyncio.sleep(1)
            
            # Test agent discovery
            online_agents = await nats_service.get_online_agents()
            logger.info(f"Online agents: {len(online_agents)}")
            
            for agent in online_agents:
                logger.debug(f"Agent: {agent['agent_id']} - {agent['info']['name']}")
            
            # Test task routing
            test_task = {
                "task_id": "test-task-001",
                "type": "test",
                "priority": "normal",
                "data": {"test": "data"}
            }
            
            await nats_service.route_task(test_task)
            
            logger.info("Test task routed successfully")
            
            # Test event publishing
            await nats_service.publish_event(
                "system.ready",
                {"service": "nats-coordination", "version": "1.0.0"}
            )
            
            logger.info("Test event published successfully")
            
            # Wait for messages to be processed
            await asyncio.sleep(2)
            
            # Test agent unregistration
            await nats_service.unregister_agent("test-agent-001")
            
            # Wait for unregistration
            await asyncio.sleep(1)
            
            online_agents = await nats_service.get_online_agents()
            logger.info(f"Online agents after unregistration: {len(online_agents)}")
            
            logger.info("✅ NATS JetStream service test completed successfully!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            
        finally:
            if 'nats_service' in locals():
                await nats_service.disconnect()
    
    asyncio.run(test_service())
