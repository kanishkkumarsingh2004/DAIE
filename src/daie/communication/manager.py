"""
Communication manager for agent communication
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from daie.agents.message import AgentMessage
from daie.config import SystemConfig
from daie.core.resilience import CircuitBreaker, RetryPolicy
from daie.core.tracing import TraceContextManager, inject_trace_context, trace_span
from daie.registry.manager import NodeRegistry
from daie.utils.encryption import decrypt_data, encrypt_data, generate_encryption_key

if TYPE_CHECKING:
    from daie.agents import Agent

logger = logging.getLogger(__name__)

# Audit logger for A2A communications
audit_logger = logging.getLogger("daie.audit")


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
    >>> from daie.communication import CommunicationManager
    >>> from daie.config import SystemConfig

    >>> # Create communication manager
    >>> config = SystemConfig()
    >>> comm_manager = CommunicationManager(config=config)

    >>> # Start communication
    >>> comm_manager.start()

    >>> # Register an agent
    >>> comm_manager.register_agent(agent)

    >>> # Send a message
    >>> from daie.agents.agent import AgentMessage
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

        self.registry = NodeRegistry()

        # End-to-end encryption support
        self._encryption_keys: Dict[str, bytes] = {}  # agent_id -> encryption key
        self._enable_encryption = getattr(config, "enable_e2e_encryption", True)

        # Audit logging
        self._enable_audit_logging = getattr(config, "enable_audit_logging", True)
        self._audit_log_file = getattr(config, "audit_log_file", None)

        # Rate limiting
        self._enable_rate_limiting = getattr(config, "enable_rate_limiting", True)
        self._rate_limit_window = getattr(config, "rate_limit_window", 60)  # seconds
        self._rate_limit_max_messages = getattr(config, "rate_limit_max_messages", 100)
        self._message_counts: Dict[str, List[float]] = defaultdict(
            list
        )  # agent_id -> list of timestamps

        # Resilience: Circuit Breakers for remote nodes
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}  # peer_url -> CircuitBreaker

        self._background_tasks = set()

        logger.info("Communication manager initialized")

    @property
    def is_connected(self) -> bool:
        """Check if communication is connected"""
        return self._is_running and self._connection is not None

    def _track_task(self, task: asyncio.Task) -> None:
        """Track background task to ensure it gets cancelled on stop"""
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

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

        # Register Agent capabilities and network config to NodeRegistry
        # network_url: The URL where THIS agent is hosted (others use this to reach it)
        # network_connections: Dict of peer_id -> URL for agents THIS agent can directly reach
        network_url = getattr(agent.config, "network_url", None)
        network_connections = getattr(agent.config, "network_connections", {})
        capabilities = {
            "role": (
                getattr(agent.role, "value", str(agent.role))
                if hasattr(agent, "role")
                else "unknown"
            ),
            "tools": agent.config.capabilities,
        }
        self.registry.register_node(
            agent.id, capabilities, network_url=network_url, network_connections=network_connections
        )

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
                is_connected=True,
            )

        return self

    def get_peer_count(self) -> int:
        """
        Get number of connected peers

        Returns:
            Number of connected peers
        """
        return len([p for p in self._peers.values() if p.is_connected])

    @trace_span("comm_send_message")
    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send a message to another agent with optimized performance

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

            # Rate limiting check
            if self._enable_rate_limiting and not self._check_rate_limit(message.sender_id):
                logger.warning(f"Rate limit exceeded for agent {message.sender_id}")
                self._audit_log("RATE_LIMIT_EXCEEDED", message, "Rate limit exceeded")
                return False

            # Encrypt message content if encryption is enabled
            if self._enable_encryption and message.receiver_id != "*":
                message = self._encrypt_message(message)

            # Audit log for message send
            self._audit_log("MESSAGE_SEND", message)

            # Inject trace context into message metadata for propagation
            message.metadata = inject_trace_context(message.metadata)

            # Handle broadcast messages
            if message.receiver_id == "*":
                await self.broadcast_message(message)
            else:
                # Direct message
                await self._send_message_internal(message)

            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._audit_log("MESSAGE_SEND_ERROR", message, str(e))
            return False

    def _encrypt_message(self, message: AgentMessage) -> AgentMessage:
        """
        Encrypt message content for end-to-end encryption

        Args:
            message: Message to encrypt

        Returns:
            Encrypted message
        """
        try:
            # Get or generate encryption key for receiver
            if message.receiver_id not in self._encryption_keys:
                self._encryption_keys[message.receiver_id] = generate_encryption_key()

            key = self._encryption_keys[message.receiver_id]

            # Encrypt message content
            encrypted_content = encrypt_data(message.content, key)

            # Create encrypted message
            encrypted_msg = AgentMessage(
                id=message.id,
                sender_id=message.sender_id,
                receiver_id=message.receiver_id,
                content=encrypted_content,
                message_type=message.message_type,
                timestamp=message.timestamp,
                metadata={
                    **message.metadata,
                    "encrypted": True,
                    "encryption_key_id": message.receiver_id,
                },
            )

            return encrypted_msg
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return message

    def _decrypt_message(self, message: AgentMessage) -> AgentMessage:
        """
        Decrypt message content for end-to-end encryption

        Args:
            message: Message to decrypt

        Returns:
            Decrypted message
        """
        try:
            # Check if message is encrypted
            if not message.metadata.get("encrypted", False):
                return message

            key_id = message.metadata.get("encryption_key_id")
            if not key_id or key_id not in self._encryption_keys:
                logger.warning(f"No decryption key found for message {message.id}")
                return message

            key = self._encryption_keys[key_id]

            # Decrypt message content
            decrypted_content = decrypt_data(message.content, key)

            # Create decrypted message
            decrypted_msg = AgentMessage(
                id=message.id,
                sender_id=message.sender_id,
                receiver_id=message.receiver_id,
                content=decrypted_content,
                message_type=message.message_type,
                timestamp=message.timestamp,
                metadata={
                    k: v
                    for k, v in message.metadata.items()
                    if k not in ["encrypted", "encryption_key_id"]
                },
            )

            return decrypted_msg
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return message

    def _audit_log(self, event_type: str, message: AgentMessage, details: str = ""):
        """
        Log audit event for A2A communication

        Args:
            event_type: Type of event (e.g., MESSAGE_SEND, MESSAGE_RECEIVE)
            message: Related message
            details: Additional details
        """
        if not self._enable_audit_logging:
            return

        try:
            audit_entry = {
                "timestamp": time.time(),
                "event_type": event_type,
                "message_id": message.id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "message_type": message.message_type,
                "details": details,
            }

            audit_logger.info(json.dumps(audit_entry))
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")

    def _check_rate_limit(self, agent_id: str) -> bool:
        """
        Check if agent has exceeded rate limit

        Args:
            agent_id: Agent ID to check

        Returns:
            True if within rate limit, False otherwise
        """
        if not self._enable_rate_limiting:
            return True

        current_time = time.time()

        # Use config values or system defaults - check both possible keys for compatibility
        window = getattr(self.config, "rate_limit_window", 60)
        max_msgs = getattr(
            self.config, "rate_limit_max_messages", getattr(self.config, "rate_limit_per_peer", 100)
        )

        window_start = current_time - window

        # Clean old timestamps
        self._message_counts[agent_id] = [
            ts for ts in self._message_counts[agent_id] if ts > window_start
        ]

        # Check if within limit
        if len(self._message_counts[agent_id]) >= max_msgs:
            return False

        # Add current timestamp
        self._message_counts[agent_id].append(current_time)
        return True

    async def _send_message_internal(self, message: AgentMessage):
        """Internal message sending implementation with routing support"""
        if message.receiver_id in self._agents:
            # Direct agent-to-agent communication (same process)
            receiver = self._agents[message.receiver_id]

            # --- Authorization Check ---
            allowed = getattr(receiver.config, "allowed_senders", [])
            if allowed and message.sender_id not in allowed:
                logger.warning(
                    f"Blocked message from {message.sender_id} to {message.receiver_id}: sender not in allowed_senders whitelist."
                )
                self._audit_log(
                    "MESSAGE_BLOCKED", message, "Sender not in allowed_senders whitelist"
                )
                return

            # Decrypt message if encrypted
            if self._enable_encryption and message.metadata.get("encrypted", False):
                message = self._decrypt_message(message)

            # Audit log for message receive
            self._audit_log("MESSAGE_RECEIVE", message)

            result = receiver._handle_message(message)
            if asyncio.iscoroutine(result):
                await result
        else:
            # Try to dispatch over the network via P2P HTTP
            sender_node = self.registry.get_node(message.sender_id)
            receiver_node = self.registry.get_node(message.receiver_id)

            if not receiver_node:
                logger.warning(f"Receiver agent {message.receiver_id} not found in registry.")
                return

            # Check for direct connection
            direct_url = None
            if sender_node:
                sender_connections = sender_node.get("network_connections", {})
                if message.receiver_id in sender_connections:
                    direct_url = sender_connections[message.receiver_id]

            if direct_url:
                logger.info(f"Sending message directly to {message.receiver_id} at {direct_url}")
                self._track_task(
                    asyncio.create_task(self._send_remote_message(message, direct_url))
                )
            elif receiver_node.get("network_url"):
                network_url = receiver_node["network_url"]
                logger.info(
                    f"Routing message to remote agent {message.receiver_id} at {network_url}"
                )
                self._track_task(
                    asyncio.create_task(self._send_remote_message(message, network_url))
                )
            else:
                # Try to find a route through intermediate nodes
                route = self.registry.find_route(message.sender_id, message.receiver_id)
                if route and len(route) > 1:
                    next_hop = route[1]
                    next_hop_node = self.registry.get_node(next_hop)
                    if next_hop_node:
                        next_hop_url = None
                        if sender_node:
                            sender_connections = sender_node.get("network_connections", {})
                            next_hop_url = sender_connections.get(next_hop)
                        if not next_hop_url:
                            next_hop_url = next_hop_node.get("network_url")
                        if next_hop_url:
                            logger.info(
                                f"Routing message to {message.receiver_id} via intermediate node {next_hop} at {next_hop_url}"
                            )
                            message.metadata["route"] = route
                            message.metadata["final_destination"] = message.receiver_id
                            message.receiver_id = next_hop
                            self._track_task(
                                asyncio.create_task(
                                    self._send_remote_message(message, next_hop_url)
                                )
                            )
                            return

                logger.warning(f"No route found to receiver agent {message.receiver_id}")

    @trace_span("comm_send_remote_message")
    async def _send_remote_message(self, message: AgentMessage, network_url: str):
        """Send message over the network with circuit breaker and retry support"""
        # Get or create circuit breaker for this endpoint
        if network_url not in self._circuit_breakers:
            self._circuit_breakers[network_url] = CircuitBreaker(
                name=f"remote_{network_url}",
                failure_threshold=getattr(self.config, "circuit_failure_threshold", 5),
                recovery_timeout=getattr(self.config, "circuit_recovery_timeout", 30),
            )

        cb = self._circuit_breakers[network_url]

        # Setup retry policy
        retry_policy = None
        if getattr(self.config, "enable_retries", True):
            retry_policy = RetryPolicy(
                max_retries=getattr(self.config, "max_retries", 3), base_delay=1.0, jitter=True
            )

        async def _do_send():
            import websockets

            sender_agent = self._agents.get(message.sender_id)
            token = getattr(sender_agent.config, "auth_token", "") if sender_agent else ""

            # Convert HTTP URL to WebSocket URL
            ws_url = network_url.replace("http://", "ws://").replace("https://", "wss://")
            endpoint = f"{ws_url.rstrip('/')}/ws/a2a/message"

            async with websockets.connect(endpoint, open_timeout=5) as websocket:
                msg_dict = {
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "metadata": message.metadata,
                    "auth_token": token,
                }
                await websocket.send(json.dumps(msg_dict))

                # Wait for acknowledgment
                response = await websocket.recv()
                response_data = json.loads(response)

                if "error" in response_data:
                    raise RuntimeError(f"Peer error: {response_data['error']}")

                logger.debug(f"Remote message delivered to {endpoint}")
                self._audit_log("MESSAGE_SEND_REMOTE_SUCCESS", message)

        try:
            if retry_policy:
                await cb.call(retry_policy.execute, _do_send)
            else:
                await cb.call(_do_send)
        except Exception as e:
            logger.error(f"Failed to send remote message to {network_url}: {e}")
            self._audit_log("MESSAGE_SEND_REMOTE_ERROR", message, str(e))

    async def broadcast_message(self, message: AgentMessage) -> int:
        """
        Broadcast a message to all registered agents except the sender.

        Args:
            message: Message to broadcast

        Returns:
            Number of agents that received the message
        """
        count = 0

        for agent_id, agent in self._agents.items():
            if agent_id == message.sender_id:
                continue

            broadcast_msg = AgentMessage(
                sender_id=message.sender_id,
                receiver_id=agent_id,
                content=message.content,
                message_type=message.message_type,
                metadata=dict(message.metadata),
            )
            try:
                await self._send_message_internal(broadcast_msg)
                count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to agent {agent_id}: {e}")

        logger.debug(f"Broadcast message sent to {count} agents")
        return count

    def _handle_message(self, agent_id: str, message: AgentMessage):
        """Handle incoming messages with routing support"""
        if agent_id not in self._agents:
            logger.warning(f"Received message for unknown agent: {agent_id}")
            return

        try:
            # Check if this message is being routed through this node
            final_destination = message.metadata.get("final_destination")
            if final_destination and final_destination != agent_id:
                logger.info(
                    f"Forwarding message from {message.sender_id} to final destination {final_destination} via {agent_id}"
                )
                message.receiver_id = final_destination
                message.metadata.pop("final_destination", None)
                message.metadata.pop("route", None)
                self._track_task(asyncio.create_task(self.send_message(message)))
                return

            # Decrypt message if encrypted
            if self._enable_encryption and message.metadata.get("encrypted", False):
                message = self._decrypt_message(message)

            # Audit log for message receive
            self._audit_log("MESSAGE_RECEIVE", message)

            with TraceContextManager(message.metadata):
                agent = self._agents[agent_id]
                # Always schedule via create_task — agent._handle_message is async
                # and handles task vs non-task internally (task messages are awaited
                # directly inside _handle_message to ensure timely reply)
                self._track_task(asyncio.create_task(agent._handle_message(message)))
        except Exception as e:
            logger.error(f"Error handling message for agent {agent_id}: {e}")
            self._audit_log("MESSAGE_RECEIVE_ERROR", message, str(e))

    async def start(self) -> None:
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
            self._loop = asyncio.get_running_loop()

            # Initialize communication connection
            self._connection = await self._initialize_connection()

            # Start registry discovery services
            await self.registry.start()

            # Start message listener
            self._listen_task = self._loop.create_task(self._listen_for_messages())

            # Start peer discovery
            self._discover_task = self._loop.create_task(self._discover_peers())

            self._is_running = True
            logger.info("Communication manager started successfully")

        except Exception as e:
            logger.error(f"Failed to start communication manager: {e}")
            self._is_running = False
            raise

    async def stop(self) -> None:
        """Stop communication manager"""
        if not self._is_running:
            logger.warning("Communication manager already stopped")
            return

        logger.info("Stopping communication manager...")

        try:
            self._is_running = False

            # Cancel background tasks
            for task in list(self._background_tasks):
                task.cancel()
            self._background_tasks.clear()

            if hasattr(self, "_listen_task") and not self._listen_task.done():
                self._listen_task.cancel()
            if hasattr(self, "_discover_task") and not self._discover_task.done():
                self._discover_task.cancel()

            # Close connection
            if self._connection:
                await self._close_connection()

            # Stop registry discovery services
            await self.registry.stop()

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
            "message_handlers": len(self._message_handlers),
        }

    def get_network_topology(self) -> Dict[str, any]:
        """
        Get the complete network topology showing all nodes and their connections.

        Returns:
            Dictionary containing nodes and their connections
        """
        return self.registry.get_network_topology()

    def find_route(self, from_agent: str, to_agent: str) -> Optional[List[str]]:
        """
        Find a route between two agents through the network.

        Args:
            from_agent: Starting agent ID
            to_agent: Destination agent ID

        Returns:
            List of agent IDs forming the route, or None if no route exists
        """
        return self.registry.find_route(from_agent, to_agent)

    def get_connected_peers(self, agent_id: str) -> Dict[str, str]:
        """
        Get all peers directly connected to an agent.

        Args:
            agent_id: Agent ID to get connections for

        Returns:
            Dictionary of peer_id -> network_url for connected peers
        """
        return self.registry.get_connected_peers(agent_id)

    def setup_bidirectional_connection(
        self, agent_a_id: str, agent_b_id: str, url_a: str, url_b: str
    ) -> bool:
        """
        Setup bidirectional connection between two agents.

        Args:
            agent_a_id: First agent ID
            agent_b_id: Second agent ID
            url_a: Network URL for agent A
            url_b: Network URL for agent B

        Returns:
            True if connection setup successfully
        """
        # Update agent A's connections to include B
        node_a = self.registry.get_node(agent_a_id)
        if node_a:
            connections_a = node_a.get("network_connections", {})
            connections_a[agent_b_id] = url_b
            self.registry.update_connections(agent_a_id, connections_a)

        # Update agent B's connections to include A
        node_b = self.registry.get_node(agent_b_id)
        if node_b:
            connections_b = node_b.get("network_connections", {})
            connections_b[agent_a_id] = url_a
            self.registry.update_connections(agent_b_id, connections_b)

        logger.info(f"Setup bidirectional connection between {agent_a_id} and {agent_b_id}")
        return True

    def receive_messages(self, agent_id: str) -> List[AgentMessage]:
        """
        Receive messages for a specific agent (returns empty list — delivery is push-based via _handle_message)

        Args:
            agent_id: Agent ID to receive messages for

        Returns:
            Empty list (messages are delivered directly to agents via _handle_message)
        """
        return []
