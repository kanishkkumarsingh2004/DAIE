"""
Decentralized Registry Module

Provides local/P2P capability discovery so agents can find each other dynamically.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import os
import time

logger = logging.getLogger(__name__)

class NodeRegistry:
    """
    Local file-based or memory-based decentralized registry simulator.
    In a fully P2P system, this would broadcast capabilities via zero-conf or DHT.
    For local network capability testing, it logs capabilities securely.
    """

    def __init__(self, registry_file: str = "node_registry.json"):
        # We can store the registry in the same config path if available
        self.registry_file = registry_file
        self._nodes: Dict[str, Dict[str, Any]] = {}
        
        # Initialize memory from file if it exists (for persistent local mesh)
        self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self._nodes = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self._nodes = {}

    def _save_registry(self):
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self._nodes, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def register_node(self, agent_id: str, capabilities: Dict[str, Any], network_url: Optional[str] = None, network_connections: Optional[Dict[str, str]] = None) -> bool:
        """
        Register a new node (agent) with its capabilities into the network pool.
        Capabilities should include role, goals, and exposed tools.
        
        Args:
            agent_id: Unique identifier for the agent
            capabilities: Dictionary of agent capabilities
            network_url: Base URL where THIS agent is hosted (others use this to reach it)
            network_connections: Dictionary of peer_id -> network_url for agents THIS agent can directly reach
        """
        self._nodes[agent_id] = {
            "capabilities": capabilities,
            "network_url": network_url,
            "network_connections": network_connections or {},
            "last_seen": time.time(),
            "status": "active"
        }
        self._save_registry()
        logger.info(f"Registered node {agent_id} to decentralized registry (URL: {network_url}, Connections: {len(network_connections or {})}).")
        return True

    def deregister_node(self, agent_id: str) -> bool:
        """
        Remove a node from the network pool.
        """
        if agent_id in self._nodes:
            # Mark inactive rather than deleting immediately for P2P eventual consistency
            self._nodes[agent_id]["status"] = "inactive"
            self._nodes[agent_id]["last_seen"] = time.time()
            self._save_registry()
            logger.info(f"Deregistered node {agent_id} from decentralized registry.")
            return True
        return False

    def discover_agents(self, capability_query: str = None) -> List[Dict[str, Any]]:
        """
        Find actively registered agents on the network matching a specific capability profile or role.
        """
        results = []
        # Filter for active nodes
        active_nodes = {k: v for k, v in self._nodes.items() if v.get("status") == "active"}
        
        if not capability_query:
            # Return all active nodes if no specific query
            for k, v in active_nodes.items():
                results.append({"agent_id": k, **v})
            return results

        # Simple keyword matching search for capability discovery
        query_lower = capability_query.lower()
        for k, v in active_nodes.items():
            cap_str = json.dumps(v.get("capabilities", {})).lower()
            if query_lower in cap_str:
                results.append({"agent_id": k, **v})
                
        return results

    def get_node(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific node's metadata."""
        return self._nodes.get(agent_id)

    def get_network_topology(self) -> Dict[str, Any]:
        """
        Get the complete network topology showing all nodes and their connections.
        
        Returns:
            Dictionary containing nodes and their connections
        """
        topology = {
            "nodes": {},
            "connections": []
        }
        
        for agent_id, node_data in self._nodes.items():
            if node_data.get("status") == "active":
                topology["nodes"][agent_id] = {
                    "network_url": node_data.get("network_url"),
                    "capabilities": node_data.get("capabilities", {}),
                    "connections": node_data.get("network_connections", {})
                }
                # Add bidirectional connections
                for peer_id, peer_url in node_data.get("network_connections", {}).items():
                    connection = {"from": agent_id, "to": peer_id, "url": peer_url}
                    if connection not in topology["connections"]:
                        topology["connections"].append(connection)
        
        return topology

    def find_route(self, from_agent: str, to_agent: str) -> Optional[List[str]]:
        """
        Find a route between two agents through the network.
        Uses BFS to find the shortest path.
        
        Args:
            from_agent: Starting agent ID
            to_agent: Destination agent ID
            
        Returns:
            List of agent IDs forming the route, or None if no route exists
        """
        if from_agent == to_agent:
            return [from_agent]
        
        # Build adjacency list from network connections
        graph = {}
        for agent_id, node_data in self._nodes.items():
            if node_data.get("status") == "active":
                graph[agent_id] = list(node_data.get("network_connections", {}).keys())
        
        # BFS to find shortest path
        from collections import deque
        queue = deque([(from_agent, [from_agent])])
        visited = {from_agent}
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in graph.get(current, []):
                if neighbor == to_agent:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None

    def get_connected_peers(self, agent_id: str) -> Dict[str, str]:
        """
        Get all peers directly connected to an agent.
        
        Args:
            agent_id: Agent ID to get connections for
            
        Returns:
            Dictionary of peer_id -> network_url for connected peers
        """
        node = self._nodes.get(agent_id)
        if not node:
            return {}
        return node.get("network_connections", {})

    def update_connections(self, agent_id: str, connections: Dict[str, str]) -> bool:
        """
        Update network connections for an agent.
        
        Args:
            agent_id: Agent ID to update
            connections: New connections dictionary
            
        Returns:
            True if updated successfully
        """
        if agent_id not in self._nodes:
            return False
        
        self._nodes[agent_id]["network_connections"] = connections
        self._nodes[agent_id]["last_seen"] = time.time()
        self._save_registry()
        logger.info(f"Updated connections for node {agent_id}: {len(connections)} connections")
        return True
