"""
Decentralized AI System - Main orchestrator for the AI ecosystem
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any

from decentralized_ai.agents import Agent
from decentralized_ai.tools import ToolRegistry
from decentralized_ai.communication import CommunicationManager
from decentralized_ai.memory import MemoryManager
from decentralized_ai.config import SystemConfig

logger = logging.getLogger(__name__)


class DecentralizedAISystem:
    """
    Main orchestrator for the Decentralized AI Ecosystem

    This class manages the overall system lifecycle, including:
    - System initialization and configuration
    - Agent management
    - Communication setup
    - Memory management
    - System monitoring

    Example:
    >>> system = DecentralizedAISystem()
    >>> system.add_agent(agent1)
    >>> system.add_agent(agent2)
    >>> system.start()
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        """
        Initialize the Decentralized AI System

        Args:
            config: Optional system configuration. If None, default configuration is used.
        """
        self.config = config or SystemConfig()
        self.agents: Dict[str, Agent] = {}
        self.tool_registry = ToolRegistry()
        self.communication_manager = CommunicationManager(config=self.config)
        self.memory_manager = MemoryManager(config=self.config)
        self._is_running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Set up logging
        from decentralized_ai.utils.logger import setup_system_logger
        setup_system_logger(self.config)

    def add_agent(self, agent: Agent) -> "DecentralizedAISystem":
        """
        Add an agent to the system

        Args:
            agent: Agent instance to add

        Returns:
            self for method chaining
        """
        if agent.id in self.agents:
            raise ValueError(f"Agent with ID {agent.id} already exists")
        
        self.agents[agent.id] = agent
        logger.info(f"Agent {agent.name} (ID: {agent.id}) added to system")
        return self

    def add_tool(self, tool: Any) -> "DecentralizedAISystem":
        """
        Add a tool to the system's tool registry

        Args:
            tool: Tool instance to add

        Returns:
            self for method chaining
        """
        self.tool_registry.register(tool)
        logger.info(f"Tool {tool.name} added to system")
        return self

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID

        Args:
            agent_id: Agent ID

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """
        List all agents in the system

        Returns:
            List of agent instances
        """
        return list(self.agents.values())

    def start(self) -> None:
        """
        Start the decentralized AI system

        This method initializes all components, starts all agents,
        and begins system operation.
        """
        if self._is_running:
            logger.warning("System is already running")
            return

        logger.info("Starting Decentralized AI System...")
        
        try:
            # Initialize communication manager
            self.communication_manager.start()
            
            # Initialize memory manager
            self.memory_manager.start()
            
            # Start all agents
            for agent in self.agents.values():
                agent.start(self.communication_manager, self.memory_manager, self.tool_registry)
            
            self._is_running = True
            logger.info(f"System started successfully with {len(self.agents)} agents")
            
            # Run event loop
            self._loop = asyncio.get_event_loop()
            self._loop.run_forever()
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """
        Stop the decentralized AI system

        This method stops all agents and shuts down the system.
        """
        if not self._is_running:
            logger.warning("System is already stopped")
            return

        logger.info("Stopping Decentralized AI System...")
        
        try:
            # Stop all agents
            for agent in self.agents.values():
                agent.stop()
            
            # Stop memory manager
            self.memory_manager.stop()
            
            # Stop communication manager
            self.communication_manager.stop()
            
            # Stop event loop
            if self._loop:
                self._loop.stop()
            
            self._is_running = False
            logger.info("System stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during system shutdown: {e}")

    @property
    def is_running(self) -> bool:
        """Check if the system is currently running"""
        return self._is_running

    def get_status(self) -> Dict[str, Any]:
        """
        Get system status information

        Returns:
            Dictionary containing system status
        """
        return {
            "running": self._is_running,
            "agent_count": len(self.agents),
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role,
                    "status": "running" if agent.is_running else "stopped"
                }
                for agent in self.agents.values()
            ],
            "tool_count": len(self.tool_registry.list_tools()),
            "communication": {
                "connected": self.communication_manager.is_connected,
                "peers": self.communication_manager.get_peer_count()
            },
            "memory": {
                "initialized": self.memory_manager.is_initialized
            }
        }
