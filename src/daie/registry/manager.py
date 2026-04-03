"""
Decentralized Registry Module

Provides local/P2P capability discovery so agents can find each other dynamically.
Supports mDNS for local network discovery and DHT for federated discovery.
"""

import asyncio
import json
import logging
import os
import socket
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional imports for mDNS and DHT
try:
    from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf

    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
    logger.warning("zeroconf not installed. mDNS discovery disabled.")

try:
    from kademlia.network import Server

    DHT_AVAILABLE = True
except ImportError:
    DHT_AVAILABLE = False
    logger.warning("kademlia not installed. DHT discovery disabled.")


class NodeRegistry:
    """
    Local file-based or memory-based decentralized registry simulator.
    In a fully P2P system, this would broadcast capabilities via zero-conf or DHT.
    For local network capability testing, it logs capabilities securely.

    Supports:
    - mDNS for local network discovery
    - DHT for federated discovery across networks
    """

    def __init__(
        self,
        registry_file: str = None,
        enable_mdns: bool = True,
        enable_dht: bool = False,
        dht_port: int = 8468,
    ):
        # Use None to disable file persistence by default (in-memory only)
        self.registry_file = registry_file
        self._nodes: Dict[str, Dict[str, Any]] = {}

        # mDNS support
        self._enable_mdns = enable_mdns and MDNS_AVAILABLE
        self._zeroconf = None
        self._mdns_browser = None
        self._mdns_services: Dict[str, ServiceInfo] = {}

        # DHT support
        self._enable_dht = enable_dht and DHT_AVAILABLE
        self._dht_server = None
        self._dht_port = dht_port
        self._background_tasks = set()

        # Initialize memory from file if it exists (for persistent local mesh)
        self._load_registry()

        # Start discovery services if not in an async context
        # In async contexts, use 'await registry.start()'
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                logger.debug("Async loop detected. Deferring discovery startup to start().")
        except RuntimeError:
            if self._enable_mdns:
                # Still sync for now if no loop, but discouraged
                # We'll wrap it in a temporary loop if needed in _start_mdns
                self._start_mdns_sync()
            if self._enable_dht:
                self._start_dht_sync()

    def _load_registry(self):
        if self.registry_file and os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self._nodes = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self._nodes = {}

    def _save_registry(self):
        if not self.registry_file:
            return  # In-memory only, no persistence
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self._nodes, f, indent=4, default=str)
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def _track_task(self, task: asyncio.Task):
        """Track a background task for cleanup"""
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def start(self):
        """Start all enabled discovery services asynchronously"""
        if self._enable_mdns:
            await self._start_mdns()
        if self._enable_dht:
            await self._start_dht()

    async def stop(self):
        """Stop all discovery services asynchronously"""
        # Cancel all background tasks first
        for task in list(self._background_tasks):
            if not task.done():
                task.cancel()
        self._background_tasks.clear()

        if self._enable_mdns:
            await self._stop_mdns()
        if self._enable_dht:
            await self._stop_dht()

    def _start_mdns_sync(self):
        """Synchronous wrapper for starting mDNS"""
        try:
            self._zeroconf = Zeroconf()
            logger.info("mDNS service started (sync)")
        except Exception as e:
            logger.error(f"Failed to start mDNS sync: {e}")
            self._enable_mdns = False

    async def _start_mdns(self):
        """Start mDNS service for local network discovery"""
        if not MDNS_AVAILABLE:
            logger.warning("mDNS not available. Install zeroconf package.")
            return

        if self._zeroconf:
            return

        try:
            # Zeroconf constructor can be blocking, but usually acceptable
            self._zeroconf = Zeroconf()
            logger.info("mDNS service started for local network discovery")
        except Exception as e:
            logger.error(f"Failed to start mDNS: {e}")
            self._enable_mdns = False

    def _start_dht_sync(self):
        """Synchronous wrapper for starting DHT"""
        if not DHT_AVAILABLE: return
        try:
            self._dht_server = Server()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._dht_server.listen(self._dht_port))
            logger.info(f"DHT service started on port {self._dht_port} (sync)")
        except Exception as e:
            logger.error(f"Failed to start DHT sync: {e}")
            self._enable_dht = False

    async def _start_dht(self):
        """Start DHT service for federated discovery"""
        if not DHT_AVAILABLE:
            logger.warning("DHT not available. Install kademlia package.")
            return

        if self._dht_server:
            return

        try:
            self._dht_server = Server()
            await self._dht_server.listen(self._dht_port)
            logger.info(f"DHT service started on port {self._dht_port}")
        except Exception as e:
            logger.error(f"Failed to start DHT: {e}")
            self._enable_dht = False

    async def _stop_mdns(self):
        """Stop mDNS service"""
        if self._zeroconf:
            try:
                # zeroconf.close() can be async in newer versions if it returns a coroutine
                res = self._zeroconf.close()
                if asyncio.iscoroutine(res):
                    await res
                self._zeroconf = None
                logger.info("mDNS service stopped")
            except Exception as e:
                logger.error(f"Error stopping mDNS: {e}")

    def _stop_mdns_sync(self):
        """Sync stop for mDNS"""
        if self._zeroconf:
            try:
                self._zeroconf.close()
                self._zeroconf = None
            except Exception: pass

    async def _stop_dht(self):
        """Stop DHT service"""
        if self._dht_server:
            try:
                await self._dht_server.stop()
                self._dht_server = None
                logger.info("DHT service stopped")
            except Exception as e:
                logger.error(f"Error stopping DHT: {e}")

    def _stop_dht_sync(self):
        """Sync stop for DHT (discouraged, may hang)"""
        if self._dht_server:
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self._dht_server.stop())
                self._dht_server = None
            except Exception: pass

    async def _publish_mdns_service(self, agent_id: str, network_url: str, capabilities: Dict[str, Any]):
        """Publish agent service via mDNS"""
        if not self._enable_mdns or not self._zeroconf:
            return

        try:
            # Parse network URL to get host and port
            from urllib.parse import urlparse

            parsed = urlparse(network_url)
            host = str(parsed.hostname or "localhost")
            port = int(parsed.port or 8000)
            agent_id_str = str(agent_id)

            # Resolve host to IP for mDNS
            try:
                ip_addr = socket.gethostbyname(host)
                addr_bytes = socket.inet_aton(ip_addr)
            except Exception:
                addr_bytes = socket.inet_aton("127.0.0.1")

            # Create service info
            service_type = "_daie-agent._tcp.local."
            service_name = f"{agent_id_str}.{service_type}"

            # Encode capabilities as TXT record
            txt_data = {"capabilities": json.dumps(capabilities, default=str), "agent_id": agent_id_str}

            service_info = ServiceInfo(
                service_type,
                service_name,
                addresses=[addr_bytes],
                port=port,
                properties=txt_data,
                server=f"{agent_id_str}.local.",
            )

            # Use async registration if available
            if hasattr(self._zeroconf, "async_register_service"):
                await self._zeroconf.async_register_service(service_info)
            else:
                self._zeroconf.register_service(service_info)
                
            self._mdns_services[agent_id] = service_info
            logger.info(f"Published mDNS service for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to publish mDNS service for {agent_id}: {e}")

    async def _unpublish_mdns_service(self, agent_id: str):
        """Unpublish agent service from mDNS"""
        if not self._enable_mdns or not self._zeroconf:
            return

        try:
            if agent_id in self._mdns_services:
                info = self._mdns_services[agent_id]
                if hasattr(self._zeroconf, "async_unregister_service"):
                    await self._zeroconf.async_unregister_service(info)
                else:
                    self._zeroconf.unregister_service(info)
                del self._mdns_services[agent_id]
                logger.info(f"Unpublished mDNS service for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to unpublish mDNS service for {agent_id}: {e}")

    async def _publish_dht_node(self, agent_id: str, network_url: str, capabilities: Dict[str, Any]):
        """Publish agent node to DHT"""
        if not self._enable_dht or not self._dht_server:
            return

        try:
            # Store node info in DHT
            node_data = {"network_url": network_url, "capabilities": capabilities, "timestamp": time.time()}

            await self._dht_server.set(agent_id, json.dumps(node_data))
            logger.info(f"Published DHT node for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to publish DHT node for {agent_id}: {e}")

    async def _discover_dht_node(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Discover agent node from DHT"""
        if not self._enable_dht or not self._dht_server:
            return None

        try:
            result = await self._dht_server.get(agent_id)
            if result:
                return json.loads(result)
        except Exception as e:
            logger.error(f"Failed to discover DHT node for {agent_id}: {e}")
        return None

    def register_node(
        self,
        agent_id: str,
        capabilities: Dict[str, Any],
        network_url: Optional[str] = None,
        network_connections: Optional[Dict[str, str]] = None,
    ) -> bool:
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
            "status": "active",
        }
        self._save_registry()

        # Publish to mDNS if enabled and network_url is provided
        if self._enable_mdns and network_url:
            try:
                loop = asyncio.get_running_loop()
                self._track_task(loop.create_task(self._publish_mdns_service(agent_id, network_url, capabilities)))
            except RuntimeError:
                # No running loop, handle sync if needed
                pass

        # Publish to DHT if enabled and network_url is provided
        if self._enable_dht and network_url:
            try:
                loop = asyncio.get_running_loop()
                self._track_task(loop.create_task(self._publish_dht_node(agent_id, network_url, capabilities)))
            except RuntimeError:
                # No running loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._publish_dht_node(agent_id, network_url, capabilities))

        logger.info(
            f"Registered node {agent_id} to decentralized registry (URL: {network_url}, Connections: {len(network_connections or {})})."
        )
        return True

    def deregister_node(self, agent_id: str) -> bool:
        """
        Remove a node from the network pool.
        """
        if agent_id in self._nodes:
            del self._nodes[agent_id]
            self._save_registry()

            # Unpublish from mDNS if enabled
            if self._enable_mdns:
                try:
                    loop = asyncio.get_running_loop()
                    self._track_task(loop.create_task(self._unpublish_mdns_service(agent_id)))
                except RuntimeError: pass

            # Remove from DHT
            if self._enable_dht and self._dht_server:
                try:
                    try:
                        loop = asyncio.get_running_loop()
                        self._track_task(loop.create_task(self._dht_server.set(agent_id, "")))
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._dht_server.set(agent_id, ""))
                except Exception as e:
                    logger.error(f"Failed to remove DHT node for {agent_id}: {e}")

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

    def discover_agents_mdns(self, timeout: float = 2.0) -> List[Dict[str, Any]]:
        """
        Discover agents on the local network using mDNS.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List of discovered agents
        """
        if not self._enable_mdns or not self._zeroconf:
            logger.warning("mDNS discovery not enabled")
            return []

        results = []
        try:
            # Browse for DAIE agent services
            service_type = "_daie-agent._tcp.local."
            browser = ServiceBrowser(self._zeroconf, service_type, handlers=[self._on_mdns_service_added])

            # Wait for discovery
            time.sleep(timeout)

            # Stop browser
            browser.cancel()

            # Return discovered nodes
            for agent_id, service_info in self._mdns_services.items():
                if agent_id in self._nodes:
                    results.append({"agent_id": agent_id, **self._nodes[agent_id]})

            logger.info(f"Discovered {len(results)} agents via mDNS")
        except Exception as e:
            logger.error(f"mDNS discovery failed: {e}")

        return results

    def _on_mdns_service_added(self, zeroconf, service_type, name):
        """Callback for mDNS service discovery"""
        try:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                # Extract agent ID from service name
                agent_id = name.split(".")[0]

                # Extract capabilities from TXT record
                capabilities = {}
                if info.properties:
                    cap_str = info.properties.get(b"capabilities", b"{}").decode("utf-8")
                    capabilities = json.loads(cap_str)

                # Build network URL
                if info.addresses:
                    host = socket.inet_ntoa(info.addresses[0])
                    port = info.port
                    network_url = f"http://{host}:{port}"

                    # Register discovered node
                    if agent_id not in self._nodes:
                        self._nodes[agent_id] = {
                            "capabilities": capabilities,
                            "network_url": network_url,
                            "network_connections": {},
                            "last_seen": time.time(),
                            "status": "active",
                        }
                        logger.info(f"Discovered agent {agent_id} via mDNS at {network_url}")
        except Exception as e:
            logger.error(f"Error processing mDNS service: {e}")

    async def discover_agents_dht(self, agent_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Discover agents from DHT by their IDs.

        Args:
            agent_ids: List of agent IDs to discover

        Returns:
            List of discovered agents
        """
        if not self._enable_dht or not self._dht_server:
            logger.warning("DHT discovery not enabled")
            return []

        results = []
        try:
            for agent_id in agent_ids:
                node_data = await self._discover_dht_node(agent_id)
                if node_data:
                    # Register discovered node
                    if agent_id not in self._nodes:
                        self._nodes[agent_id] = {
                            "capabilities": node_data.get("capabilities", {}),
                            "network_url": node_data.get("network_url"),
                            "network_connections": {},
                            "last_seen": time.time(),
                            "status": "active",
                        }
                        results.append({"agent_id": agent_id, **self._nodes[agent_id]})
                        logger.info(f"Discovered agent {agent_id} via DHT")

            logger.info(f"Discovered {len(results)} agents via DHT")
        except Exception as e:
            logger.error(f"DHT discovery failed: {e}")

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
        topology = {"nodes": {}, "connections": []}

        for agent_id, node_data in self._nodes.items():
            if node_data.get("status") == "active":
                topology["nodes"][agent_id] = {
                    "network_url": node_data.get("network_url"),
                    "capabilities": node_data.get("capabilities", {}),
                    "connections": node_data.get("network_connections", {}),
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

    def cleanup(self):
        """Cleanup resources and stop discovery services (sync)"""
        # Try to use current loop if possible to avoid unawaited coroutines
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # We are in an async loop, but this is a sync cleanup.
                # Just trigger async stop in background if we must.
                self._track_task(loop.create_task(self.stop()))
                return
        except RuntimeError: pass

        self._stop_mdns_sync()
        self._stop_dht_sync()
        logger.info("NodeRegistry cleanup (sync) completed")

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except Exception:
            pass
