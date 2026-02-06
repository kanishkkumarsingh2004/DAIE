"""
Communication manager for agent communication
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

from decentralized_ai.config import SystemConfig
from decentralized_ai.agents.message import AgentMessage

if TYPE_CHECKING:
    from decentralized_ai.agents import Agent

logger = logging.getLogger(__name__)


@dataclass
class PeerInfo:
    """Peer information"""
    peer_id: str
    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    last_seen: float = 0.0
    is_connected: bool = True


class CommunicationManager:
    """
    Communication manager for handling agent communication

    This class manages communication between agents using NATS JetStream and
    peer-to-peer communication protocols. It provides methods for sending and
    receiving messages, managing connections, and event handling.

    Example:
    >>> from decentralized_ai.communication import CommunicationManager
    >>> from decentralized_ai.config import SystemConfig

    >>> # Create communication manager
    >>> config = SystemConfig()
    >>> comm_manager = CommunicationManager(config=config)

    >>> # Start communication
    >>> comm_manager.start()

    >>> # Register an agent
    >>> comm_manager.register_agent(agent)

    >>> # Send a message
    >>> from decentralized_ai.agents.agent import AgentMessage
    >>> message = AgentMessage(
    ...     sender_id="agent1",
    ...     receiver_id="agent2",
    ...     content="Hello, world!",
    ...     message_type="text"
    ... )
    >>> await comm_manager.send_message(message)
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        Initialize communication manager

        Args:
            config: System configuration
        """
        self.config = config or SystemConfig()
        self._is_running = False
        self._agents: Dict[str, "Agent"] = {}
        self._peers: Dict[str, PeerInfo] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._connection: Optional[any] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info("Communication manager initialized")

    @property
    def is_connected(self) -> bool:
        """Check if communication is connected"""
        return self._is_running and self._connection is not None

    @property
    def peer_count(self) -> int:
        """Get number of connected peers"""
        return sum(1 for peer in self._peers.values() if peer.is_connected)

    def register_agent(self, agent: "Agent") -> "CommunicationManager":
        """
        Register an agent for communication

        Args:
            agent: Agent instance to register

        Returns:
            self for method chaining
        """
        if agent.id in self._agents:
            logger.warning(f"Agent {agent.id} already registered")
            return self

        self._agents[agent.id] = agent
        logger.info(f"Agent {agent.name} (ID: {agent.id}) registered for communication")
        
        # Create a message handler for the agent
        self._message_handlers[agent.id] = lambda msg: self._handle_message(agent.id, msg)
        
        return self

    def deregister_agent(self, agent_id: str) -> "CommunicationManager":
        """
        Deregister an agent from communication

        Args:
            agent_id: ID of agent to deregister

        Returns:
            self for method chaining
        """
        if agent_id not in self._agents:
            logger.warning(f"Agent {agent_id} not found for deregistration")
            return self

        agent = self._agents.pop(agent_id)
        if agent_id in self._message_handlers:
            del self._message_handlers[agent_id]
            
        logger.info(f"Agent {agent.name} (ID: {agent_id}) deregistered from communication")
        
        return self

    def get_agent(self, agent_id: str) -> Optional["Agent"]:
        """
        Get registered agent by ID

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_id)

    def get_peers(self) -> List[PeerInfo]:
        """
        Get list of connected peers

        Returns:
            List of peer information
        """
        return list(self._peers.values())

    def get_peer_info(self, peer_id: str) -> Optional[PeerInfo]:
        """
        Get peer information

        Args:
            peer_id: Peer ID

        Returns:
            Peer information or None if not found
        """
        return self._peers.get(peer_id)

    def update_peer_info(self, peer_id: str, info: Dict) -> "CommunicationManager":
        """
        Update peer information

        Args:
            peer_id: Peer ID
            info: Dictionary with updated information

        Returns:
            self for method chaining
        """
        import time
        
        if peer_id in self._peers:
            for key, value in info.items():
                if hasattr(self._peers[peer_id], key):
                    setattr(self._peers[peer_id], key, value)
            self._peers[peer_id].last_seen = time.time()
        else:
            self._peers[peer_id] = PeerInfo(
                peer_id=peer_id,
                name=info.get("name", "Unknown"),
                role=info.get("role", "unknown"),
                capabilities=info.get("capabilities", []),
                last_seen=time.time(),
                is_connected=True
            )
            
        return self

    def get_peer_count(self) -> int:
        """
        Get number of connected peers

        Returns:
            Number of connected peers
        """
        return len([p for p in self._peers.values() if p.is_connected])

    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send a message to another agent

        Args:
            message: Message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self._is_running:
            logger.error("Communication manager not running")
            return False

        try:
            logger.debug(f"Sending message from {message.sender_id} to {message.receiver_id}")
            
            # In real implementation, this would use NATS JetStream or P2P
            await self._send_message_internal(message)
            
            logger.debug(f"Message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def _send_message_internal(self, message: AgentMessage):
        """Internal message sending implementation"""
        # For development and testing, use a simple in-memory communication
        if message.receiver_id in self._agents:
            # Direct agent-to-agent communication
            receiver = self._agents[message.receiver_id]
            await receiver._handle_message(message)
        else:
            logger.warning(f"Receiver agent {message.receiver_id} not found")

    async def broadcast_message(self, message: AgentMessage) -> int:
        """
        Broadcast a message to all connected agents

        Args:
            message: Message to broadcast

        Returns:
            Number of agents that received the message
        """
        count = 0
        
        for agent_id in self._agents:
            if agent_id != message.sender_id:
                broadcast_msg = AgentMessage(
                    sender_id=message.sender_id,
                    receiver_id=agent_id,
                    content=message.content,
                    message_type=message.message_type,
                    metadata=message.metadata
                )
                await self.send_message(broadcast_msg)
                count += 1
                
        logger.debug(f"Broadcast message sent to {count} agents")
        return count

    def _handle_message(self, agent_id: str, message: AgentMessage):
        """Handle incoming messages"""
        if agent_id not in self._agents:
            logger.warning(f"Received message for unknown agent: {agent_id}")
            return

        try:
            agent = self._agents[agent_id]
            asyncio.create_task(agent._handle_message(message))
        except Exception as e:
            logger.error(f"Error handling message for agent {agent_id}: {e}")

    def start(self) -> None:
        """
        Start communication manager

        This method initializes the communication system and starts listening
        for incoming messages and connections.
        """
        if self._is_running:
            logger.warning("Communication manager already running")
            return

        logger.info("Starting communication manager...")
        
        try:
            self._loop = asyncio.get_event_loop()
            
            # Initialize communication connection
            self._connection = self._loop.run_until_complete(self._initialize_connection())
            
            # Start message listener
            self._loop.create_task(self._listen_for_messages())
            
            # Start peer discovery
            self._loop.create_task(self._discover_peers())
            
            self._is_running = True
            logger.info("Communication manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start communication manager: {e}")
            self._is_running = False
            raise

    def stop(self) -> None:
        """Stop communication manager"""
        if not self._is_running:
            logger.warning("Communication manager already stopped")
            return

        logger.info("Stopping communication manager...")
        
        try:
            self._is_running = False
            
            # Close connection
            if self._connection:
                self._loop.run_until_complete(self._close_connection())
                
            logger.info("Communication manager stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping communication manager: {e}")

    async def _initialize_connection(self):
        """Initialize communication connection (mock implementation)"""
        logger.debug("Initializing communication connection...")
        await asyncio.sleep(0.1)  # Simulate connection delay
        return True

    async def _close_connection(self):
        """Close communication connection (mock implementation)"""
        logger.debug("Closing communication connection...")
        await asyncio.sleep(0.1)

    async def _listen_for_messages(self):
        """Listen for incoming messages (mock implementation)"""
        while self._is_running:
            await asyncio.sleep(0.5)  # Check for messages periodically

    async def _discover_peers(self):
        """Discover peers (mock implementation)"""
        while self._is_running:
            await asyncio.sleep(10)  # Discover peers every 10 seconds
            logger.debug("Discovering peers...")

    def on_message_received(self, agent_id: str, handler: Callable[[AgentMessage], None]):
        """
        Register a message handler for an agent

        Args:
            agent_id: Agent ID
            handler: Handler function to call

        Returns:
            self for method chaining
        """
        self._message_handlers[agent_id] = handler
        return self

    def get_communication_stats(self) -> Dict[str, any]:
        """
        Get communication statistics

        Returns:
            Dictionary with communication statistics
        """
        return {
            "connected": self.is_connected,
            "agents_registered": len(self._agents),
            "peers_connected": self.get_peer_count(),
            "total_peers": len(self._peers),
            "message_handlers": len(self._message_handlers)
        }
