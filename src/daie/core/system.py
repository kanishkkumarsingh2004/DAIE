"""
Decentralized AI System - Main orchestrator for the AI ecosystem
"""

import asyncio
import logging
import signal
from typing import List, Optional, Dict, Any
import os
from pathlib import Path

from daie.agents import Agent
from daie.tools import ToolRegistry
from daie.communication import CommunicationManager
from daie.memory import MemoryManager
from daie.config import SystemConfig

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
        self._shutdown_event: Optional[asyncio.Event] = None

        # Set up logging
        from daie.utils.logger import setup_system_logger
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
            # Create PID file
            self._create_pid_file()
            
            # Initialize communication manager
            self.communication_manager.start()
            
            # Initialize memory manager
            self.memory_manager.start()
            
            # Start all agents
            for agent in self.agents.values():
                agent.start(self.communication_manager, self.memory_manager, self.tool_registry)
            
            self._is_running = True
            logger.info(f"System started successfully with {len(self.agents)} agents")
            
            # Run event loop with shutdown handlers
            self._loop = asyncio.get_event_loop()
            self._shutdown_event = asyncio.Event()
            
            # Set up signal handlers
            self._loop.add_signal_handler(signal.SIGINT, self._signal_handler)
            self._loop.add_signal_handler(signal.SIGTERM, self._signal_handler)
            
            # Run event loop until shutdown
            self._loop.run_until_complete(self._run_event_loop())
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            self.stop()
            raise

    async def _run_event_loop(self):
        """Internal method to run the event loop until shutdown"""
        try:
            await self._shutdown_event.wait()
        finally:
            self.stop()

    def _signal_handler(self):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal")
        if self._shutdown_event and not self._shutdown_event.is_set():
            self._shutdown_event.set()

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
            if self._loop and self._loop.is_running():
                try:
                    self._loop.stop()
                except Exception:
                    pass
            
            self._is_running = False
            
            # Remove PID file
            self._remove_pid_file()
            
            logger.info("System stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during system shutdown: {e}")

    def _create_pid_file(self):
        """Create PID file to track running process"""
        pid = os.getpid()
        pid_dir = Path.home() / ".dai"
        pid_dir.mkdir(exist_ok=True)
        pid_file = pid_dir / "core.pid"
        with open(pid_file, "w") as f:
            f.write(str(pid))
        logger.debug(f"PID file created at {pid_file} with PID {pid}")

    def _remove_pid_file(self):
        """Remove PID file"""
        pid_dir = Path.home() / ".dai"
        pid_file = pid_dir / "core.pid"
        if pid_file.exists():
            try:
                pid_file.unlink()
                logger.debug(f"PID file removed from {pid_file}")
            except Exception as e:
                logger.error(f"Failed to remove PID file: {e}")

    @classmethod
    def get_running_pid(cls) -> Optional[int]:
        """Get PID of running core process"""
        pid_dir = Path.home() / ".dai"
        pid_file = pid_dir / "core.pid"
        if pid_file.exists():
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                # Check if process is actually running
                if cls._is_process_running(pid):
                    return pid
                else:
                    # PID file exists but process doesn't, clean it up
                    try:
                        pid_file.unlink()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error reading PID file: {e}")
        return None

    @staticmethod
    def _is_process_running(pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            # Send signal 0 to check if process exists (doesn't kill it)
            os.kill(pid, 0)
            return True
        except OSError:
            return False

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
