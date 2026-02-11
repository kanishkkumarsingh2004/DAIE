"""
Node management module
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Node:
    """
    Represents a node in the decentralized AI network.

    A node is a participating entity that can host agents, process tasks,
    and communicate with other nodes in the network.
    """

    def __init__(self, node_id: str, name: str = "Unknown Node"):
        """
        Initialize a new node instance.

        Args:
            node_id: Unique identifier for the node
            name: Display name for the node
        """
        self.node_id = node_id
        self.name = name
        self._is_active = False
        self._agents: List[str] = []
        self._resources: Dict[str, Any] = {}
        self._connections: List[str] = []

        logger.info(f"Node {self.name} (ID: {self.node_id}) created")

    @property
    def is_active(self) -> bool:
        """Check if the node is active"""
        return self._is_active

    @property
    def agents(self) -> List[str]:
        """Get list of agents on this node"""
        return self._agents.copy()

    @property
    def agent_count(self) -> int:
        """Get number of agents on this node"""
        return len(self._agents)

    @property
    def connections(self) -> List[str]:
        """Get list of connected peer nodes"""
        return self._connections.copy()

    @property
    def connection_count(self) -> int:
        """Get number of connected peer nodes"""
        return len(self._connections)

    def start(self) -> None:
        """Start the node"""
        if self._is_active:
            logger.warning(f"Node {self.name} is already active")
            return

        self._is_active = True
        logger.info(f"Node {self.name} started")

    def stop(self) -> None:
        """Stop the node"""
        if not self._is_active:
            logger.warning(f"Node {self.name} is already stopped")
            return

        self._is_active = False
        logger.info(f"Node {self.name} stopped")

    def add_agent(self, agent_id: str) -> "Node":
        """
        Add an agent to this node

        Args:
            agent_id: Unique identifier of the agent to add

        Returns:
            Self for method chaining
        """
        if agent_id not in self._agents:
            self._agents.append(agent_id)
            logger.debug(f"Agent {agent_id} added to node {self.name}")

        return self

    def remove_agent(self, agent_id: str) -> "Node":
        """
        Remove an agent from this node

        Args:
            agent_id: Unique identifier of the agent to remove

        Returns:
            Self for method chaining
        """
        if agent_id in self._agents:
            self._agents.remove(agent_id)
            logger.debug(f"Agent {agent_id} removed from node {self.name}")

        return self

    def has_agent(self, agent_id: str) -> bool:
        """
        Check if an agent exists on this node

        Args:
            agent_id: Unique identifier of the agent to check

        Returns:
            True if agent exists on this node, False otherwise
        """
        return agent_id in self._agents

    def connect(self, peer_node_id: str) -> "Node":
        """
        Establish a connection to a peer node

        Args:
            peer_node_id: Unique identifier of the peer node to connect to

        Returns:
            Self for method chaining
        """
        if peer_node_id not in self._connections and peer_node_id != self.node_id:
            self._connections.append(peer_node_id)
            logger.debug(f"Connected to peer node {peer_node_id}")

        return self

    def disconnect(self, peer_node_id: str) -> "Node":
        """
        Disconnect from a peer node

        Args:
            peer_node_id: Unique identifier of the peer node to disconnect from

        Returns:
            Self for method chaining
        """
        if peer_node_id in self._connections:
            self._connections.remove(peer_node_id)
            logger.debug(f"Disconnected from peer node {peer_node_id}")

        return self

    def is_connected(self, peer_node_id: str) -> bool:
        """
        Check if connected to a specific peer node

        Args:
            peer_node_id: Unique identifier of the peer node to check

        Returns:
            True if connected to the peer node, False otherwise
        """
        return peer_node_id in self._connections

    def set_resource(self, name: str, value: Any) -> "Node":
        """
        Set a resource value for this node

        Args:
            name: Name of the resource
            value: Value of the resource

        Returns:
            Self for method chaining
        """
        self._resources[name] = value
        logger.debug(f"Resource '{name}' set to '{value}' on node {self.name}")

        return self

    def get_resource(self, name: str, default: Optional[Any] = None) -> Any:
        """
        Get a resource value from this node

        Args:
            name: Name of the resource to get
            default: Default value to return if resource not found

        Returns:
            Value of the resource or default if not found
        """
        return self._resources.get(name, default)

    def get_resource_info(self) -> Dict[str, Any]:
        """
        Get information about all resources on this node

        Returns:
            Dictionary containing all resources and their values
        """
        return self._resources.copy()

    def get_status(self) -> Dict[str, Any]:
        """
        Get node status information

        Returns:
            Dictionary containing node status information
        """
        return {
            "node_id": self.node_id,
            "name": self.name,
            "status": "active" if self._is_active else "inactive",
            "agent_count": self.agent_count,
            "agents": self.agents,
            "connection_count": self.connection_count,
            "connections": self.connections,
            "resources": self.get_resource_info(),
        }

    def __str__(self) -> str:
        """String representation of the node"""
        return f"Node(id={self.node_id}, name={self.name}, status={'active' if self._is_active else 'inactive'})"

    def __repr__(self) -> str:
        """Repr representation of the node"""
        return self.__str__()
