#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Event Listener

This module provides event handling capabilities for agents,
listening to and processing events from the coordination layer.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of events in the decentralized AI ecosystem"""
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    AGENT_STATUS_UPDATED = "agent_status_updated"
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    MESSAGE_RECEIVED = "message_received"
    SYSTEM_READY = "system_ready"
    SYSTEM_SHUTDOWN = "system_shutdown"
    ERROR_OCCURRED = "error_occurred"
    RESOURCE_LOW = "resource_low"

@dataclass
class SystemEvent:
    """Data class representing a system event"""
    event_id: str
    event_type: EventType
    timestamp: float
    source: str
    data: Dict
    priority: str = "normal"
    correlation_id: Optional[str] = None

class EventListener:
    """
    Event listener for the agent node system
    
    Handles listening to and processing events from the coordination layer
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize event listener
        
        Args:
            agent_id: Agent identifier
        """
        self.agent_id = agent_id
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[SystemEvent] = []
        self.event_id_counter = 0
        self.running = False
        self._listener_task = None
        
        logger.info(f"Event listener initialized for agent: {agent_id}")
    
    async def start(self):
        """Start the event listener"""
        try:
            logger.info("Starting event listener...")
            
            # Connect to coordination layer
            self.running = True
            
            # Start listening for events
            await self._connect_to_coordination()
            
            logger.info("Event listener started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start event listener: {e}")
            raise
    
    async def _connect_to_coordination(self):
        """Connect to the coordination layer and subscribe to events"""
        try:
            # Initialize NATS connection
            from central_core_system.coordination.nats_jetstream import get_nats_service
            self.nats_service = await get_nats_service()
            
            # Subscribe to relevant events
            await self._subscribe_to_events()
            
            logger.debug("Successfully connected to coordination layer")
            
        except Exception as e:
            logger.error(f"Failed to connect to coordination layer: {e}")
            raise
    
    async def _subscribe_to_events(self):
        """Subscribe to relevant event streams"""
        try:
            # Subscribe to agent discovery events
            await self.nats_service.subscribe_to_messages(
                self.agent_id,
                self._handle_nats_message
            )
            
            logger.debug("Subscribed to agent discovery events")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            raise
    
    async def _handle_nats_message(self, message_data: Dict):
        """Handle messages from NATS JetStream"""
        try:
            logger.debug(f"Received NATS message: {message_data}")
            
            # Convert to SystemEvent
            event = self._create_system_event(
                event_type=self._map_message_type(message_data),
                source=message_data.get("sender_id", "unknown"),
                data=message_data.get("message", {}),
                correlation_id=message_data.get("correlation_id")
            )
            
            # Process event
            await self._process_event(event)
            
        except Exception as e:
            logger.error(f"Failed to handle NATS message: {e}")
    
    def _map_message_type(self, message_data: Dict) -> EventType:
        """Map message type to event type"""
        msg_type = message_data.get("message_type")
        
        type_mapping = {
            "text": EventType.MESSAGE_RECEIVED,
            "task": EventType.TASK_CREATED,
            "response": EventType.TASK_COMPLETED,
            "status": EventType.AGENT_STATUS_UPDATED,
            "error": EventType.ERROR_OCCURRED
        }
        
        return type_mapping.get(msg_type, EventType.MESSAGE_RECEIVED)
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """
        Register an event handler
        
        Args:
            event_type: Type of event to handle
            handler: Callback function to handle events of this type
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Handler registered for event type: {event_type}")
    
    def register_global_handler(self, handler: Callable):
        """
        Register a global event handler that receives all events
        
        Args:
            handler: Callback function to handle all events
        """
        self.register_handler("*", handler)
        logger.debug("Global event handler registered")
    
    async def _process_event(self, event: SystemEvent):
        """Process a received event"""
        try:
            # Store event in history
            self.event_history.append(event)
            
            logger.debug(f"Event received: {event.event_type.value} from {event.source}")
            
            # Call type-specific handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Event handler failed: {e}")
            
            # Call global handlers
            if "*" in self.event_handlers:
                for handler in self.event_handlers["*"]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Global event handler failed: {e}")
                        
            # Clean up old events
            self._cleanup_event_history()
            
        except Exception as e:
            logger.error(f"Failed to process event: {e}")
    
    def _cleanup_event_history(self, max_events: int = 1000):
        """Clean up old events from history"""
        if len(self.event_history) > max_events:
            self.event_history = self.event_history[-max_events:]
            logger.debug("Event history truncated")
    
    def _create_system_event(self, event_type: EventType, source: str, 
                            data: Dict, correlation_id: str = None) -> SystemEvent:
        """Create a system event instance"""
        self.event_id_counter += 1
        event_id = f"{self.agent_id}-event-{self.event_id_counter}-{int(time.time() * 1000)}"
        
        event = SystemEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=time.time(),
            source=source,
            data=data,
            correlation_id=correlation_id
        )
        
        return event
    
    async def publish_event(self, event_type: EventType, data: Dict, 
                          correlation_id: str = None) -> bool:
        """
        Publish an event to the coordination layer
        
        Args:
            event_type: Type of event to publish
            data: Event data
            correlation_id: Correlation ID for tracking
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        try:
            event = self._create_system_event(
                event_type=event_type,
                source=self.agent_id,
                data=data,
                correlation_id=correlation_id
            )
            
            # Publish to NATS JetStream
            await self.nats_service.publish_event(
                event_type.value,
                {
                    "event_id": event.event_id,
                    "event_type": event_type.value,
                    "timestamp": event.timestamp,
                    "source": event.source,
                    "data": event.data,
                    "correlation_id": event.correlation_id
                }
            )
            
            logger.debug(f"Event published: {event_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    async def publish_error(self, error_message: str, error_data: Dict = None, 
                          correlation_id: str = None) -> bool:
        """
        Publish an error event
        
        Args:
            error_message: Error message
            error_data: Additional error details
            correlation_id: Correlation ID for tracking
            
        Returns:
            bool: True if error published successfully, False otherwise
        """
        error_event_data = {
            "message": error_message,
            "details": error_data or {}
        }
        
        return await self.publish_event(
            EventType.ERROR_OCCURRED,
            error_event_data,
            correlation_id
        )
    
    def get_event_history(self, event_type: EventType = None, 
                         limit: int = 100) -> List[SystemEvent]:
        """
        Get event history
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List[SystemEvent]: Event history
        """
        filtered = self.event_history
        
        if event_type:
            filtered = [event for event in filtered if event.event_type == event_type]
            
        return filtered[-limit:]
    
    def get_event_count(self, event_type: EventType = None) -> int:
        """
        Get count of events
        
        Args:
            event_type: Filter by event type (optional)
            
        Returns:
            int: Number of events
        """
        if event_type:
            return sum(1 for event in self.event_history if event.event_type == event_type)
        else:
            return len(self.event_history)
    
    async def stop(self):
        """Stop the event listener"""
        logger.info("Stopping event listener...")
        
        self.running = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event listener stopped")

# Singleton instance for the event listener
_event_listener_instance = None

def get_event_listener(agent_id: str) -> EventListener:
    """
    Get the singleton instance of the event listener
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        EventListener: Singleton instance
    """
    global _event_listener_instance
    if _event_listener_instance is None:
        _event_listener_instance = EventListener(agent_id)
    return _event_listener_instance

if __name__ == "__main__":
    # Test event listener functionality
    logging.basicConfig(level=logging.DEBUG)
    
    async def test_event_listener():
        try:
            # Create event listener
            listener = EventListener("test-agent-001")
            
            # Test handler registration
            async def agent_registered_handler(event):
                logger.info(f"Agent registered: {event.data}")
                
            listener.register_handler(EventType.AGENT_REGISTERED, agent_registered_handler)
            
            async def global_handler(event):
                logger.debug(f"Global handler received: {event.event_type.value}")
                
            listener.register_global_handler(global_handler)
            
            # Test event creation
            test_event = listener._create_system_event(
                EventType.TASK_CREATED,
                "system",
                {"task_id": "test-task-001", "description": "Test task"}
            )
            
            # Test event processing
            await listener._process_event(test_event)
            
            # Test event history
            history = listener.get_event_history()
            logger.info(f"Event history contains: {len(history)} events")
            
            # Test event count
            count = listener.get_event_count(EventType.TASK_CREATED)
            logger.info(f"Task created events: {count}")
            
            logger.info("✅ Event listener test completed successfully!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    import asyncio
    import time
    from dataclasses import dataclass
    asyncio.run(test_event_listener())
