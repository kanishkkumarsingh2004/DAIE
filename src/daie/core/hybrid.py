"""
Hybrid Orchestrator Node module for combining Node and Orchestrator architectures.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from daie.communication.manager import CommunicationManager
from daie.core.node import Node

if TYPE_CHECKING:
    from daie.agents.agent import Agent
    from daie.core.orchestrator import Orchestrator
    from daie.agents.router import AgentRouter

logger = logging.getLogger(__name__)


class HybridOrchestratorNode:
    """
    A hybrid system that combines Node and Orchestrator architectures.

    This class provides a simple, batteries-included approach to building
    enterprise-scale multi-agent systems with both infrastructure management
    (Node) and workflow coordination (Orchestrator).

    Key Features:
        - Automatic Node creation and management
        - Automatic Orchestrator setup with configurable context
        - Built-in CommunicationManager for P2P and A2A messaging
        - Optional intelligent AgentRouter for message routing
        - Resource management per node
        - Cross-node communication support
        - Simple API for task execution

    Example:
        ```python
        from daie import Agent, AgentConfig, set_llm
        from daie.agents import AgentRole
        from daie.core.hybrid import HybridOrchestratorNode

        # Configure LLM
        set_llm(ollama_llm="llama3.2:1b", stream=True)

        # Create hybrid system
        hybrid = HybridOrchestratorNode(
            node_id="research-lab",
            node_name="Research Lab",
            context_name="Research Lab",
            main_role="Professor",
            sub_role="Researcher"
        )

        # Add main agent (orchestrator)
        professor = Agent(config=AgentConfig(
            name="Professor",
            role=AgentRole.COORDINATOR,
            system_prompt="You coordinate research projects."
        ))
        hybrid.set_main_agent(professor)

        # Add sub-agents
        researcher = Agent(config=AgentConfig(
            name="Researcher",
            role=AgentRole.SPECIALIZED,
            system_prompt="You conduct research and gather information."
        ))
        analyst = Agent(config=AgentConfig(
            name="Analyst",
            role=AgentRole.SPECIALIZED,
            system_prompt="You analyze data and identify trends."
        ))
        hybrid.add_sub_agent(researcher)
        hybrid.add_sub_agent(analyst)

        # Start the hybrid system
        await hybrid.start()

        # Execute tasks
        result = await hybrid.execute_task("Research AI trends")

        # Cleanup
        await hybrid.stop()
        ```
    """

    def __init__(
        self,
        node_id: str,
        node_name: str = "Hybrid Node",
        context_name: str = "Hybrid System",
        main_role: str = "Coordinator",
        sub_role: str = "Specialist",
        enable_router: bool = True,
        comm_manager: Optional[CommunicationManager] = None,
        resources: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Hybrid Orchestrator Node.

        Args:
            node_id: Unique identifier for the node
            node_name: Display name for the node
            context_name: Name of the orchestration context (e.g., "Research Lab")
            main_role: Role name for the main agent (e.g., "Professor")
            sub_role: Role name for sub-agents (e.g., "Researcher")
            enable_router: Whether to enable intelligent AgentRouter for message routing
            comm_manager: Optional CommunicationManager instance (creates new one if not provided)
            resources: Optional dictionary of initial node resources
        """
        self.node_id = node_id
        self.node_name = node_name
        self.context_name = context_name
        self.main_role = main_role
        self.sub_role = sub_role
        self.enable_router = enable_router

        # Initialize core components
        self.node = Node(node_id=node_id, name=node_name)
        self.comm_manager = comm_manager or CommunicationManager()

        # Agent management
        self.main_agent: Optional[Agent] = None
        self.sub_agents: List[Agent] = []
        self.all_agents: List[Agent] = []

        # Orchestrator (created when main agent is set)
        self.orchestrator: Optional[Orchestrator] = None

        # Router (created when started if enable_router is True)
        self.router: Optional[AgentRouter] = None

        # State tracking
        self._is_running = False
        self._is_initialized = False

        # Nested node management
        self._parent_hybrid_node_id: Optional[str] = None
        self._child_hybrid_node_ids: List[str] = []

        # Set initial resources if provided
        if resources:
            for name, value in resources.items():
                self.node.set_resource(name, value)

        logger.info(f"HybridOrchestratorNode '{node_name}' (ID: {node_id}) created")

    def set_main_agent(self, agent: Agent) -> "HybridOrchestratorNode":
        """
        Set the main agent (orchestrator) for the hybrid system.

        Args:
            agent: The main agent that will coordinate sub-agents

        Returns:
            Self for method chaining
        """
        if self._is_running:
            raise RuntimeError("Cannot set main agent while system is running")

        self.main_agent = agent
        self.all_agents.append(agent)
        self.node.add_agent(agent.id)

        # Create orchestrator with the main agent
        from daie.core.orchestrator import Orchestrator

        self.orchestrator = Orchestrator(
            main_agent=agent,
            sub_agents=[],  # Sub-agents added separately
            context_name=self.context_name,
            main_role=self.main_role,
            sub_role=self.sub_role,
            comm_manager=self.comm_manager,
        )

        logger.info(f"Main agent '{agent.name}' set for hybrid node '{self.node_name}'")
        return self

    def add_sub_agent(self, agent: Agent) -> "HybridOrchestratorNode":
        """
        Add a sub-agent to the hybrid system.

        Args:
            agent: The sub-agent to add

        Returns:
            Self for method chaining
        """
        if self._is_running:
            raise RuntimeError("Cannot add sub-agent while system is running")

        if not self.main_agent:
            raise RuntimeError("Must set main agent before adding sub-agents")

        self.sub_agents.append(agent)
        self.all_agents.append(agent)
        self.node.add_agent(agent.id)

        # Update orchestrator's sub-agents
        if self.orchestrator:
            self.orchestrator.sub_agents = self.sub_agents

        logger.info(f"Sub-agent '{agent.name}' added to hybrid node '{self.node_name}'")
        return self

    def add_resource(self, name: str, value: Any) -> "HybridOrchestratorNode":
        """
        Add a resource to the node.

        Args:
            name: Name of the resource
            value: Value of the resource

        Returns:
            Self for method chaining
        """
        self.node.set_resource(name, value)
        logger.debug(f"Resource '{name}' set to '{value}' on node '{self.node_name}'")
        return self

    def connect_to_node(
        self, peer_node_id: str, peer_connections: Optional[Dict[str, str]] = None
    ) -> "HybridOrchestratorNode":
        """
        Connect this node to another peer node.

        Args:
            peer_node_id: Unique identifier of the peer node to connect to
            peer_connections: Optional mapping of peer agent IDs to network URLs

        Returns:
            Self for method chaining
        """
        self.node.connect(peer_node_id)
        logger.info(f"Hybrid node '{self.node_name}' connected to peer node '{peer_node_id}'")

        if peer_connections:
            for agent in self.all_agents:
                agent.config.network_connections.update(peer_connections)
                if hasattr(agent, "communication_manager") and agent.communication_manager:
                    agent.communication_manager.registry.update_connections(
                        agent.id, agent.config.network_connections
                    )

        return self

    def set_parent_hybrid_node(self, parent_node_id: str) -> "HybridOrchestratorNode":
        """
        Set a parent hybrid node for this node.

        Args:
            parent_node_id: Unique identifier of the parent hybrid node

        Returns:
            Self for method chaining
        """
        if parent_node_id == self.node_id:
            logger.warning(f"Hybrid node '{self.node_name}' cannot be its own parent")
            return self

        self._parent_hybrid_node_id = parent_node_id
        self.node.set_parent(parent_node_id)
        logger.info(f"Hybrid node '{self.node_name}' set parent to '{parent_node_id}'")
        return self

    def add_child_hybrid_node(self, child_node_id: str) -> "HybridOrchestratorNode":
        """
        Add a child hybrid node to this node.

        Args:
            child_node_id: Unique identifier of the child hybrid node

        Returns:
            Self for method chaining
        """
        if child_node_id == self.node_id:
            logger.warning(f"Hybrid node '{self.node_name}' cannot be its own child")
            return self

        if child_node_id not in self._child_hybrid_node_ids:
            self._child_hybrid_node_ids.append(child_node_id)
            self.node.add_child(child_node_id)
            logger.info(f"Hybrid node '{self.node_name}' added child node '{child_node_id}'")
        return self

    def remove_child_hybrid_node(self, child_node_id: str) -> "HybridOrchestratorNode":
        """
        Remove a child hybrid node from this node.

        Args:
            child_node_id: Unique identifier of the child hybrid node to remove

        Returns:
            Self for method chaining
        """
        if child_node_id in self._child_hybrid_node_ids:
            self._child_hybrid_node_ids.remove(child_node_id)
            self.node.remove_child(child_node_id)
            logger.info(f"Hybrid node '{self.node_name}' removed child node '{child_node_id}'")
        return self

    @property
    def parent_hybrid_node_id(self) -> Optional[str]:
        """Get the parent hybrid node ID"""
        return self._parent_hybrid_node_id

    @property
    def child_hybrid_node_ids(self) -> List[str]:
        """Get list of child hybrid node IDs"""
        return self._child_hybrid_node_ids.copy()

    @property
    def child_hybrid_node_count(self) -> int:
        """Get number of child hybrid nodes"""
        return len(self._child_hybrid_node_ids)

    async def start(self) -> None:
        """
        Start the hybrid system.

        This initializes the communication manager, starts all agents,
        creates the orchestrator, and optionally sets up the intelligent router.
        """
        if self._is_running:
            logger.warning(f"Hybrid node '{self.node_name}' is already running")
            return

        if not self.main_agent:
            raise RuntimeError("Must set main agent before starting")

        if not self.sub_agents:
            logger.warning(f"No sub-agents added to hybrid node '{self.node_name}'")

        logger.info(f"Starting hybrid node '{self.node_name}'...")

        # Start communication manager if not already running
        if not self.comm_manager._is_running:
            await self.comm_manager.start()

        # Start the node
        await self.node.start()

        # Start the orchestrator (which starts main_agent + sub_agents internally)
        if self.orchestrator:
            await self.orchestrator.start()
        else:
            # Fallback: start all agents directly if no orchestrator
            for agent in self.all_agents:
                await agent.start(communication_manager=self.comm_manager)

        # Create intelligent router if enabled
        if self.enable_router and self.all_agents:
            from daie.agents.router import AgentRouter

            self.router = AgentRouter.from_agents(self.all_agents)
            logger.info(f"Intelligent router created with {len(self.all_agents)} agents")

        self._is_running = True
        self._is_initialized = True

        logger.info(f"Hybrid node '{self.node_name}' started successfully")
        logger.info(f"  - Node ID: {self.node_id}")
        logger.info(f"  - Agents: {len(self.all_agents)} ({len(self.sub_agents)} sub-agents)")
        logger.info(f"  - Orchestrator: {self.context_name}")
        logger.info(f"  - Router: {'enabled' if self.router else 'disabled'}")

    async def execute_task(self, task: str) -> Any:
        """
        Execute a task using the orchestrator.

        Args:
            task: The task to execute

        Returns:
            The result of the task execution
        """
        if not self._is_running:
            await self.start()

        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")

        logger.info(f"Executing task on hybrid node '{self.node_name}': {task}")
        return await self.orchestrator.execute_task(task)

    async def route_message(self, message: str) -> str:
        """
        Route a message to the most appropriate agent using the intelligent router.

        Args:
            message: The message to route

        Returns:
            The response from the selected agent
        """
        if not self._is_running:
            await self.start()

        if not self.router:
            raise RuntimeError("Router not enabled. Set enable_router=True to use routing.")

        # Route to the best agent
        agent_type = await self.router.route(message)

        # Find the agent by type
        agent = None
        for a in self.all_agents:
            if a.name.lower() == agent_type.lower():
                agent = a
                break

        if not agent:
            # Fallback to main agent
            agent = self.main_agent

        logger.info(f"Message routed to agent '{agent.name}'")
        return await agent.send_message(message)

    async def execute_collaborative_task(self, task: str) -> str:
        """
        Execute a task that requires collaboration between all agents.

        Args:
            task: The collaborative task to execute

        Returns:
            Combined response from all agents
        """
        if not self._is_running:
            await self.start()

        logger.info(f"Executing collaborative task on hybrid node '{self.node_name}': {task}")

        results = []
        for agent in self.all_agents:
            prompt = f"As a {agent.name}, contribute your expertise to this task: {task}"
            response = await agent.send_message(prompt)
            results.append(f"**{agent.name}:**\n{response}")

        combined = "\n\n" + "=" * 50 + "\n"
        combined += "COLLABORATIVE RESPONSE\n"
        combined += "=" * 50 + "\n\n"
        combined += "\n\n---\n\n".join(results)

        return combined

    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the hybrid system.

        Returns:
            Dictionary containing status information
        """
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "context_name": self.context_name,
            "is_running": self._is_running,
            "is_initialized": self._is_initialized,
            "node_status": self.node.get_status(),
            "main_agent": self.main_agent.name if self.main_agent else None,
            "sub_agents": [agent.name for agent in self.sub_agents],
            "total_agents": len(self.all_agents),
            "orchestrator_running": self.orchestrator._is_running if self.orchestrator else False,
            "router_enabled": self.router is not None,
            "parent_hybrid_node_id": self._parent_hybrid_node_id,
            "child_hybrid_node_ids": self._child_hybrid_node_ids,
            "child_hybrid_node_count": self.child_hybrid_node_count,
            "resources": self.node.get_resource_info(),
        }

    async def stop(self) -> None:
        """
        Stop the hybrid system gracefully.

        This stops all agents, the orchestrator, the node, and the communication manager.
        """
        if not self._is_running:
            logger.warning(f"Hybrid node '{self.node_name}' is not running")
            return

        logger.info(f"Stopping hybrid node '{self.node_name}'...")

        # Stop orchestrator
        if self.orchestrator:
            await self.orchestrator.stop()

        # Stop all agents
        for agent in self.all_agents:
            await agent.stop()

        # Stop the node
        await self.node.stop()

        # Stop communication manager
        if self.comm_manager._is_running:
            await self.comm_manager.stop()

        self._is_running = False

        logger.info(f"Hybrid node '{self.node_name}' stopped successfully")

    def __str__(self) -> str:
        """String representation of the hybrid node"""
        status = "running" if self._is_running else "stopped"
        return f"HybridOrchestratorNode(id={self.node_id}, name={self.node_name}, status={status}, agents={len(self.all_agents)})"

    def __repr__(self) -> str:
        """Repr representation of the hybrid node"""
        return self.__str__()


class MultiNodeHybridSystem:
    """
    A system that manages multiple HybridOrchestratorNode instances.

    This class provides a simple way to create and manage multiple hybrid nodes
    that can communicate with each other via P2P networking.

    Example:
        ```python
        from daie import Agent, AgentConfig, set_llm
        from daie.agents import AgentRole
        from daie.core.hybrid import MultiNodeHybridSystem

        # Configure LLM
        set_llm(ollama_llm="llama3.2:1b", stream=True)

        # Create multi-node system
        system = MultiNodeHybridSystem()

        # Add research lab node
        research_node = system.create_node(
            node_id="research-lab",
            node_name="Research Lab",
            context_name="Research Lab"
        )

        # Add content creation node
        content_node = system.create_node(
            node_id="content-creation",
            node_name="Content Creation",
            context_name="Content Creation"
        )

        # Configure agents for each node...
        # (set main agent and sub-agents for each node)

        # Connect nodes
        system.connect_nodes("research-lab", "content-creation")

        # Start all nodes
        await system.start_all()

        # Execute tasks on specific nodes
        result = await system.execute_task("research-lab", "Research AI trends")

        # Cleanup
        await system.stop_all()
        ```
    """

    def __init__(self, comm_manager: Optional[CommunicationManager] = None):
        """
        Initialize the multi-node hybrid system.

        Args:
            comm_manager: Optional CommunicationManager instance (creates new one if not provided)
        """
        self.comm_manager = comm_manager or CommunicationManager()
        self.nodes: Dict[str, HybridOrchestratorNode] = {}
        self._is_running = False

        logger.info("MultiNodeHybridSystem created")

    def create_node(
        self,
        node_id: str,
        node_name: str = "Hybrid Node",
        context_name: str = "Hybrid System",
        main_role: str = "Coordinator",
        sub_role: str = "Specialist",
        enable_router: bool = True,
        resources: Optional[Dict[str, Any]] = None,
    ) -> HybridOrchestratorNode:
        """
        Create a new hybrid node in the system.

        Args:
            node_id: Unique identifier for the node
            node_name: Display name for the node
            context_name: Name of the orchestration context
            main_role: Role name for the main agent
            sub_role: Role name for sub-agents
            enable_router: Whether to enable intelligent AgentRouter
            resources: Optional dictionary of initial node resources

        Returns:
            The created HybridOrchestratorNode instance
        """
        if node_id in self.nodes:
            raise ValueError(f"Node with ID '{node_id}' already exists")

        node = HybridOrchestratorNode(
            node_id=node_id,
            node_name=node_name,
            context_name=context_name,
            main_role=main_role,
            sub_role=sub_role,
            enable_router=enable_router,
            comm_manager=self.comm_manager,
            resources=resources,
        )

        self.nodes[node_id] = node
        logger.info(f"Node '{node_name}' (ID: {node_id}) created in multi-node system")
        return node

    def get_node(self, node_id: str) -> HybridOrchestratorNode:
        """
        Get a node by its ID.

        Args:
            node_id: The ID of the node to retrieve

        Returns:
            The HybridOrchestratorNode instance

        Raises:
            KeyError: If node with given ID doesn't exist
        """
        if node_id not in self.nodes:
            raise KeyError(f"Node with ID '{node_id}' not found")
        return self.nodes[node_id]

    def connect_nodes(self, node_id1: str, node_id2: str) -> "MultiNodeHybridSystem":
        """
        Connect two nodes for P2P communication.

        Args:
            node_id1: ID of the first node
            node_id2: ID of the second node

        Returns:
            Self for method chaining
        """
        node1 = self.get_node(node_id1)
        node2 = self.get_node(node_id2)

        node1.connect_to_node(node_id2, peer_connections=self._build_peer_connections(node2))
        node2.connect_to_node(node_id1, peer_connections=self._build_peer_connections(node1))
        self._synchronize_network_connections(node1, node2)

        logger.info(f"Nodes '{node_id1}' and '{node_id2}' connected")
        return self

    def _build_peer_connections(self, node: HybridOrchestratorNode) -> Dict[str, str]:
        """
        Build a mapping of agent IDs to network URLs for all agents in a node.
        """
        connections: Dict[str, str] = {}
        for agent in node.all_agents:
            if agent.config.network_url:
                connections[agent.id] = agent.config.network_url
        return connections

    def _synchronize_network_connections(
        self, node1: HybridOrchestratorNode, node2: HybridOrchestratorNode
    ) -> None:
        """
        Ensure every agent in both connected nodes has direct peer network connections
        and updates the underlying communication registry.
        """
        for agent in node1.all_agents:
            if not agent.config.network_connections:
                agent.config.network_connections = {}
            agent.config.network_connections.update(self._build_peer_connections(node2))
            if hasattr(agent, "communication_manager") and agent.communication_manager:
                agent.communication_manager.registry.update_connections(
                    agent.id, agent.config.network_connections
                )

        for agent in node2.all_agents:
            if not agent.config.network_connections:
                agent.config.network_connections = {}
            agent.config.network_connections.update(self._build_peer_connections(node1))
            if hasattr(agent, "communication_manager") and agent.communication_manager:
                agent.communication_manager.registry.update_connections(
                    agent.id, agent.config.network_connections
                )

    def set_parent_child(self, parent_node_id: str, child_node_id: str) -> "MultiNodeHybridSystem":
        """
        Set a parent-child relationship between two nodes.

        Args:
            parent_node_id: ID of the parent node
            child_node_id: ID of the child node

        Returns:
            Self for method chaining
        """
        parent_node = self.get_node(parent_node_id)
        child_node = self.get_node(child_node_id)

        parent_node.add_child_hybrid_node(child_node_id)
        child_node.set_parent_hybrid_node(parent_node_id)

        logger.info(f"Node '{child_node_id}' set as child of '{parent_node_id}'")
        return self

    def remove_parent_child(
        self, parent_node_id: str, child_node_id: str
    ) -> "MultiNodeHybridSystem":
        """
        Remove a parent-child relationship between two nodes.

        Args:
            parent_node_id: ID of the parent node
            child_node_id: ID of the child node

        Returns:
            Self for method chaining
        """
        parent_node = self.get_node(parent_node_id)
        child_node = self.get_node(child_node_id)

        parent_node.remove_child_hybrid_node(child_node_id)
        child_node.set_parent_hybrid_node(None)

        logger.info(
            f"Parent-child relationship between '{parent_node_id}' and '{child_node_id}' removed"
        )
        return self

    def get_child_nodes(self, node_id: str) -> List[HybridOrchestratorNode]:
        """
        Get all child nodes of a specific node.

        Args:
            node_id: ID of the parent node

        Returns:
            List of child HybridOrchestratorNode instances
        """
        parent_node = self.get_node(node_id)
        child_ids = parent_node.child_hybrid_node_ids
        return [self.get_node(child_id) for child_id in child_ids if child_id in self.nodes]

    def get_parent_node(self, node_id: str) -> Optional[HybridOrchestratorNode]:
        """
        Get the parent node of a specific node.

        Args:
            node_id: ID of the child node

        Returns:
            Parent HybridOrchestratorNode instance or None if no parent
        """
        child_node = self.get_node(node_id)
        parent_id = child_node.parent_hybrid_node_id
        return self.get_node(parent_id) if parent_id and parent_id in self.nodes else None

    async def start_all(self) -> None:
        """
        Start all nodes in the system.
        """
        if self._is_running:
            logger.warning("Multi-node system is already running")
            return

        logger.info(f"Starting multi-node system with {len(self.nodes)} nodes...")

        # Start communication manager if not already running
        if not self.comm_manager._is_running:
            await self.comm_manager.start()

        # Start all nodes
        for node_id, node in self.nodes.items():
            await node.start()

        self._is_running = True
        logger.info("Multi-node system started successfully")

    async def execute_task(self, node_id: str, task: str) -> Any:
        """
        Execute a task on a specific node.

        Args:
            node_id: ID of the node to execute the task on
            task: The task to execute

        Returns:
            The result of the task execution
        """
        if not self._is_running:
            await self.start_all()

        node = self.get_node(node_id)
        return await node.execute_task(task)

    async def broadcast_task(self, task: str) -> Dict[str, Any]:
        """
        Broadcast a task to all nodes and collect results.

        Args:
            task: The task to broadcast

        Returns:
            Dictionary mapping node IDs to their results
        """
        if not self._is_running:
            await self.start_all()

        logger.info(f"Broadcasting task to all {len(self.nodes)} nodes: {task}")

        results = {}
        for node_id, node in self.nodes.items():
            try:
                result = await node.execute_task(task)
                results[node_id] = result
            except Exception as e:
                logger.error(f"Error executing task on node '{node_id}': {e}")
                results[node_id] = f"Error: {e}"

        return results

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of the entire multi-node system.

        Returns:
            Dictionary containing system status information
        """
        return {
            "total_nodes": len(self.nodes),
            "is_running": self._is_running,
            "nodes": {node_id: node.get_status() for node_id, node in self.nodes.items()},
        }

    async def stop_all(self) -> None:
        """
        Stop all nodes in the system.
        """
        if not self._is_running:
            logger.warning("Multi-node system is not running")
            return

        logger.info("Stopping multi-node system...")

        # Stop all nodes
        for node_id, node in self.nodes.items():
            await node.stop()

        # Stop communication manager
        if self.comm_manager._is_running:
            await self.comm_manager.stop()

        self._is_running = False
        logger.info("Multi-node system stopped successfully")

    def __str__(self) -> str:
        """String representation of the multi-node system"""
        status = "running" if self._is_running else "stopped"
        return f"MultiNodeHybridSystem(status={status}, nodes={len(self.nodes)})"

    def __repr__(self) -> str:
        """Repr representation of the multi-node system"""
        return self.__str__()
