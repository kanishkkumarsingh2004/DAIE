"""
Communication manager for agent communication
"""

import asyncio
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from daie.config import SystemConfig
    from daie.agents import Agent

from daie.agents.message import AgentMessage
from daie.config import SystemConfig
from daie.core.resilience import CircuitBreaker, RetryPolicy
from daie.core.tracing import TraceContextManager, inject_trace_context, trace_span, extract_trace_context
from daie.utils.encryption import encrypt_data, decrypt_data, generate_encryption_key
from daie.utils.encryption.ciphers import derive_shared_secret
import base64
from daie.registry.manager import NodeRegistry
from daie.communication.nats_provider import NatsProvider
from daie.core.metrics import metrics, MetricsServer

if TYPE_CHECKING:
    from daie.agents import Agent

from daie.core.tracing import get_logger
logger = get_logger(__name__)

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
        self._listen_task: Optional[asyncio.Task] = None
        self._discover_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._last_heartbeat_sent: float = 0
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._agents: Dict[str, "Agent"] = {}
        self._peers: Dict[str, PeerInfo] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._connection: Optional[any] = None

        self.registry = NodeRegistry(config=self.config)

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
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._last_heartbeat_sent: float = 0.0
        
        # Metrics server
        self.metrics_server = None
        self._enable_metrics = getattr(self.config, "enable_metrics", True)
        self._metrics_port = getattr(self.config, "prometheus_port", 9090)

        # NATS provider for P2P and Group messaging
        self.nats = NatsProvider(config=self.config)

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
        public_key = getattr(agent.config, "public_key", None)
        self.registry.register_node(
            agent.id,
            capabilities,
            network_url=network_url,
            network_connections=network_connections,
            public_key=public_key,
        )

        # Subscribe to NATS if connected
        if self.nats and self.nats.nc:
            self._track_task(
                asyncio.create_task(
                    self.nats.subscribe_agent(agent.id, self._handle_message)
                )
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

    async def join_group(self, agent_id: str, group_id: str):
        """Join an agent to a group for swarm messaging"""
        if agent_id not in self._agents:
            return False
        
        if self.nats and self.nats.nc:
            await self.nats.subscribe_group(
                group_id,
                agent_id,
                lambda msg: self._handle_message(agent_id, msg)
            )
            logger.info(f"Agent {agent_id} joined group {group_id}")
            return True
        return False

    async def leave_group(self, agent_id: str, group_id: str):
        """Remove an agent from a group"""
        if self.nats and self.nats.nc:
            await self.nats.unsubscribe_group(group_id, agent_id)
            logger.info(f"Agent {agent_id} left group {group_id}")
            return True
        return False

    async def send_group_message(self, group_id: str, message: AgentMessage):
        """Send a message to all agents in a group"""
        message.receiver_id = f"group:{group_id}"
        await self.send_message(message)

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

            # Try NATS first if available (provides queuing and persistence)
            if self.nats and self.nats.is_connected:
                start_time = time.time()
                success = await self.nats.publish(message)
                if success:
                    latency = time.time() - start_time
                    metrics.observe("daie_comm_p2p_latency_seconds", latency, labels={"method": "nats"})
                    metrics.increment("daie_comm_messages_sent_total", labels={"agent_id": message.sender_id})
                    return True
                logger.warning("NATS publish failed, falling back to direct communication")

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

    def _get_shared_key(self, sender_private_key_b64: str, receiver_id: str) -> Optional[bytes]:
        """Derive or retrieve shared key for E2EE"""
        try:
            # Check cache first
            cache_key = f"{receiver_id}_shared"
            if cache_key in self._encryption_keys:
                return self._encryption_keys[cache_key]

            # Get receiver's public key from registry
            topology = self.registry.get_network_topology()
            receiver_data = topology.get("nodes", {}).get(receiver_id)
            if not receiver_data or not receiver_data.get("public_key"):
                logger.warning(f"No public key found for receiver {receiver_id}")
                return None

            # Derive shared secret
            priv = base64.b64decode(sender_private_key_b64)
            pub = base64.b64decode(receiver_data["public_key"])
            shared_key = derive_shared_secret(priv, pub)
            
            # Cache for future use
            self._encryption_keys[cache_key] = shared_key
            return shared_key
        except Exception as e:
            logger.error(f"Failed to derive shared key for {receiver_id}: {e}")
            return None

    def _encrypt_message(self, message: AgentMessage) -> AgentMessage:
        """
        Encrypt message content for end-to-end encryption using X25519

        Args:
            message: Message to encrypt

        Returns:
            Encrypted message
        """
        try:
            # Get sender agent to access its private key
            sender = self._agents.get(message.sender_id)
            if not sender or not sender.config.private_key:
                logger.warning(f"Sender {message.sender_id} has no private key for E2EE")
                return message

            # Derive shared key
            key = self._get_shared_key(sender.config.private_key, message.receiver_id)
            if not key:
                return message

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
        Decrypt message content for end-to-end encryption using X25519

        Args:
            message: Message to decrypt

        Returns:
            Decrypted message
        """
        try:
            # Check if message is encrypted
            if not message.metadata.get("encrypted", False):
                return message

            # Get self (receiver) to access private key
            receiver = self._agents.get(message.receiver_id)
            if not receiver or not receiver.config.private_key:
                logger.warning(f"Receiver {message.receiver_id} has no private key for decryption")
                return message

            # Derive shared key (using sender's public key)
            # For simplicity, we use the same cache mechanism but reverse roles
            key = self._get_shared_key(receiver.config.private_key, message.sender_id)
            if not key:
                logger.warning(f"Failed to derive decryption key for message from {message.sender_id}")
                return message

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
            metrics.increment("daie_comm_messages_received_total", labels={"agent_id": message.receiver_id})

            with TraceContextManager(message.metadata):
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

            # Use timeout for the entire connection and message exchange
            # getattr for flexibility in config
            timeout = getattr(self.config, "comm_timeout", 10.0)

            async with websockets.connect(
                endpoint, open_timeout=timeout, close_timeout=2.0
            ) as websocket:
                msg_dict = {
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "metadata": message.metadata,
                    "auth_token": token,
                }
                
                # Send with timeout
                await asyncio.wait_for(websocket.send(json.dumps(msg_dict)), timeout=timeout)

                # Wait for acknowledgment with timeout
                response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
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
        """
        # If NATS is available, use it for efficient broadcasting
        if self.nats and self.nats.nc and self.nats.nc.is_connected:
            message.receiver_id = "*"
            if await self.nats.publish(message):
                # We consider all agents reached via NATS broadcast
                return len(self._agents) - 1

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
        """
        Handle an incoming message for a specific agent.
        This includes decryption and routing.
        """
        try:
            # Incoming Rate Limiting: Prevent DoS from specific peers
            if not self._check_rate_limit(message.sender_id):
                logger.warning(f"Rate limit exceeded for sender {message.sender_id}. Dropping message.")
                return

            # Check if agent exists locally
            if agent_id not in self._agents:
                logger.warning(f"Received message for unknown agent: {agent_id}")
                return

            # Update last seen for the sender if it's a known peer
            if message.sender_id in self._peers:
                self._peers[message.sender_id].last_seen = time.time()
                self._peers[message.sender_id].is_connected = True

            # Special handling for heartbeats
            if message.message_type == "heartbeat":
                logger.debug(f"Received heartbeat from {message.sender_id}")
                return

            # Decrypt message if encrypted
            if self._enable_encryption and message.metadata.get("encrypted", False):
                message = self._decrypt_message(message)

            # Audit log for message receive
            self._audit_log("MESSAGE_RECEIVE", message)

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

            with TraceContextManager(message.metadata):
                agent = self._agents[agent_id]
                # Always schedule via create_task — agent._handle_message is async
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

            # Connect to NATS if URL is provided
            if self.config.nats_url:
                try:
                    await self.nats.connect()
                except Exception as e:
                    logger.warning(f"NATS connection failed (offline mode): {e}")

            # Start heartbeat loop if enabled
            heartbeat_interval = getattr(self.config, "heartbeat_interval", 10)
            if heartbeat_interval > 0:
                self._heartbeat_task = self._loop.create_task(self._heartbeat_loop())

            # Start reconnection monitor loop
            self._reconnect_task = self._loop.create_task(self._reconnect_loop())

            # Start metrics server if enabled
            if self._enable_metrics:
                self.metrics_server = MetricsServer(metrics, self._metrics_port)
                self._track_task(self._loop.create_task(self.metrics_server.start()))

            self._is_running = True
            logger.info(f"Communication manager started successfully (Metrics: {self._metrics_port if self._enable_metrics else 'Off'})")

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
            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()

            # Disconnect NATS
            if self.nats:
                await self.nats.disconnect()

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
            await asyncio.sleep(getattr(self.config, "discovery_interval", 60))
            logger.debug("Discovering peers...")

    async def _reconnect_loop(self):
        """Monitor NATS connection and reconnect with exponential backoff if lost"""
        if not self.config.nats_url:
            return

        retry_delay = 2
        max_delay = 60

        while self._is_running:
            try:
                if not self.nats.is_connected:
                    logger.warning(
                        f"NATS connection lost, attempting to reconnect in {retry_delay}s..."
                    )
                    try:
                        await self.nats.connect()
                        logger.info("Successfully reconnected to NATS")
                        retry_delay = 2  # Reset delay on success
                    except Exception as e:
                        logger.error(f"Reconnection attempt failed: {e}")
                        retry_delay = min(retry_delay * 2, max_delay)
                else:
                    # Connection is healthy, check again in 30s
                    retry_delay = 2
            except Exception as e:
                logger.error(f"Error in reconnection loop: {e}")

            # Ensure we don't crash the loop if self.nats is missing (though it shouldn't be)
            connected = False
            if hasattr(self, "nats") and self.nats:
                connected = self.nats.is_connected

            await asyncio.sleep(30 if connected else retry_delay)

    async def _heartbeat_loop(self):
        """Periodically send heartbeats to all connected peers"""
        interval = getattr(self.config, "heartbeat_interval", 10)
        while self._is_running:
            try:
                await self._send_heartbeats()
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
            await asyncio.sleep(interval)

    async def _send_heartbeats(self):
        """Send heartbeats to all registered agents and connected peers"""
        self._last_heartbeat_sent = time.time()
        
        # In a real P2P system, we'd broadcast this or send to known neighbor nodes
        # For now, we'll mark this node as active in the registry
        for agent_id, agent in self._agents.items():
            heartbeat_msg = AgentMessage(
                sender_id=agent_id,
                receiver_id="*",  # Broadcast heartbeat
                content="hb",
                message_type="heartbeat"
            )
            # We don't use broadcast_message here to avoid recursion,
            # we just want to notify the registry and peers.
            self.registry.register_node(
                agent_id,
                {"role": str(getattr(agent, "role", "unknown")), "tools": agent.config.capabilities},
                network_url=getattr(agent.config, "network_url", None)
            )
        
        logger.debug(f"Sent heartbeats for {len(self._agents)} agents")

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
