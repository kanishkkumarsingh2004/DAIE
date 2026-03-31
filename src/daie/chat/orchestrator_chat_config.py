"""
OrchestratorChatConfig Module

Provides a pre-configured setup for MultiNodeHybridSystem so users don't need to write
the full boilerplate code. Simply configure and run!

Features:
- Accepts an already-created MultiNodeHybridSystem externally
- Creating a MultiNodeHybridSystem with multiple hybrid nodes
- Configuring different orchestrators on each node
- Connecting nodes for P2P communication
- Executing tasks on specific nodes
- Broadcasting tasks to all nodes
- Cross-node collaboration
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from daie.core.hybrid import MultiNodeHybridSystem
from daie.core.llm_manager import get_llm_config


@dataclass
class OrchestratorChatConfig:
    """
    Configuration for running a pre-built MultiNodeHybridSystem with advanced error handling.

    This class provides a simple way to run a multi-node hybrid system
    without writing the full boilerplate code. Just pass the system
    and call run() to start the interactive system!

    Features:
    - Accepts an already-created MultiNodeHybridSystem externally
    - Creating a MultiNodeHybridSystem with multiple hybrid nodes
    - Configuring different orchestrators on each node
    - Connecting nodes for P2P communication
    - Executing tasks on specific nodes
    - Broadcasting tasks to all nodes
    - Cross-node collaboration

    Example:
    >>> from daie import Agent, AgentConfig
    >>> from daie.core.hybrid import MultiNodeHybridSystem
    >>> from daie.chat import OrchestratorChatConfig
    >>>
    >>> # Create your multi-node system externally
    >>> system = MultiNodeHybridSystem()
    >>>
    >>> # Create and configure nodes
    >>> research_node = system.create_node(
    ...     node_id="research-lab",
    ...     node_name="AI Research Lab",
    ...     context_name="Research Lab",
    ...     main_role="Professor",
    ...     sub_role="Researcher"
    ... )
    >>>
    >>> # Add agents
    >>> professor = Agent(config=AgentConfig(name="Professor", ...))
    >>> research_node.set_main_agent(professor)
    >>>
    >>> # Run the multi-node system with minimal code!
    >>> config = OrchestratorChatConfig(system=system)
    ... config.run()
    """

    # Required: The multi-node system to run
    system: MultiNodeHybridSystem
    """The MultiNodeHybridSystem instance to run"""

    # Logging settings
    enable_logging: bool = True
    """Whether to enable logging"""

    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR)"""

    log_file: Optional[str] = None
    """Log file path (None for console only)"""

    # Interactive mode settings
    welcome_message: str = "=== Multi-Node Hybrid System ===\nType your command (or 'exit' to quit)\n"
    """Welcome message displayed when interactive mode starts"""

    exit_commands: List[str] = field(default_factory=lambda: ["exit", "quit"])
    """Commands that will exit the interactive loop"""

    prompt_prefix: str = "You: "
    """Prefix displayed before user input"""

    show_status_on_start: bool = True
    """Whether to show system status when starting"""

    # Callback hooks
    on_start: Optional[Callable[[], None]] = None
    """Callback function called when system starts"""

    on_exit: Optional[Callable[[], None]] = None
    """Callback function called when system exits"""

    on_error: Optional[Callable[[Exception], None]] = None
    """Callback function called when an error occurs"""

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        if self.enable_logging:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            if self.log_file:
                logging.basicConfig(
                    level=getattr(logging, self.log_level.upper()),
                    format=log_format,
                    filename=self.log_file,
                    filemode="w",
                )
            else:
                logging.basicConfig(level=getattr(logging, self.log_level.upper()), format=log_format)

    async def run_async(self) -> None:
        """
        Run the multi-node hybrid system asynchronously with comprehensive error handling.

        This method handles the complete system lifecycle:
        1. Sets up logging
        2. Calls on_start callback if provided
        3. Starts the multi-node system
        4. Displays system status if configured
        5. Runs the interactive loop with error recovery
        6. Calls on_exit callback if provided
        7. Stops the system cleanly on exit
        """
        try:
            # Setup logging
            self._setup_logging()

            # Call on_start callback if provided
            if self.on_start:
                try:
                    self.on_start()
                except Exception as e:
                    print(f"Warning: on_start callback failed: {e}")

            # Start all nodes
            print("\n[*] Starting all nodes...")
            await self.system.start_all()
            print("[+] All nodes started successfully!")

            # Display status if configured
            if self.show_status_on_start:
                status = self.system.get_system_status()
                print("\n[*] System Status:")
                print(f"  Total Nodes: {status['total_nodes']}")
                print(f"  Running: {status['is_running']}")

                for node_id, node_status in status["nodes"].items():
                    print(f"\n  Node: {node_status['node_name']} (ID: {node_id})")
                    print(f"    - Context: {node_status['context_name']}")
                    print(f"    - Agents: {node_status['total_agents']}")
                    print(f"    - Main Agent: {node_status['main_agent']}")
                    print(f"    - Sub-Agents: {', '.join(node_status['sub_agents'])}")
                    print(f"    - Resources: {node_status['resources']}")

            # Display welcome message
            print(f"\n{self.welcome_message}")
            print("Commands:")
            status = self.system.get_system_status()
            for node_id in status["nodes"].keys():
                print(f"  - '{node_id} <task>' - Execute task on {node_id}")
            print("  - 'broadcast <task>' - Broadcast task to all nodes")
            print("  - 'status' - Show system status")
            print("  - 'exit' - Quit")
            print("=" * 60 + "\n")

            # Interactive loop
            while True:
                try:
                    user_input = input(self.prompt_prefix).strip()

                    if not user_input:
                        continue

                    # Handle exit commands
                    if user_input.lower() in self.exit_commands:
                        print("\n[*] Ending session...")
                        break

                    # Handle status command
                    if user_input.lower() == "status":
                        status = self.system.get_system_status()
                        print("\n\033[93mSystem Status:\033[0m")
                        print(f"  Running: {status['is_running']}")
                        print(f"  Total Nodes: {status['total_nodes']}")
                        for node_id, node_status in status["nodes"].items():
                            print(f"  - {node_id}: {node_status['total_agents']} agents")
                        continue

                    # Handle broadcast command
                    if user_input.lower().startswith("broadcast "):
                        task = user_input[10:].strip()
                        print("\n\033[92mBroadcasting to all nodes...\033[0m")
                        results = await self.system.broadcast_task(task)
                        # Display response only if streaming is disabled
                        # (when streaming is enabled, tokens are already printed as they arrive)
                        cfg = get_llm_config()
                        if not cfg.stream:
                            print("\n\033[93mBroadcast Results:\033[0m")
                            for node_id, result in results.items():
                                print(f"\n  {node_id}:")
                                print(f"  {result}\n")
                        continue

                    # Handle node-specific commands
                    handled = False
                    status = self.system.get_system_status()
                    for node_id in status["nodes"].keys():
                        if user_input.lower().startswith(f"{node_id} "):
                            task = user_input[len(node_id) + 1:].strip()
                            print(f"\n\033[92mExecuting on {node_id}...\033[0m")
                            result = await self.system.execute_task(node_id, task)
                            # Display response only if streaming is disabled
                            # (when streaming is enabled, tokens are already printed as they arrive)
                            cfg = get_llm_config()
                            if not cfg.stream:
                                print(f"\n\033[93m{node_id} Result:\033[0m")
                                print(f"{result}\n")
                            handled = True
                            break

                    if handled:
                        continue

                    # Default: show help
                    print("\n\033[93mUnknown command. Available commands:\033[0m")
                    for node_id in status["nodes"].keys():
                        print(f"  - '{node_id} <task>' - Execute on {node_id}")
                    print("  - 'broadcast <task>' - Broadcast to all nodes")
                    print("  - 'status' - Show system status")
                    print("  - 'exit' - Quit")

                except KeyboardInterrupt:
                    print("\n\n[*] Interrupted by user. Type 'exit' to quit.")
                    continue
                except Exception as e:
                    print(f"\n\033[91mError:\033[0m {e}")
                    logging.error(f"Error in main loop: {e}", exc_info=True)
                    if self.on_error:
                        self.on_error(e)

        except Exception as e:
            print(f"\n\033[91mFatal error:\033[0m {e}")
            logging.error(f"Fatal error in hybrid system: {e}", exc_info=True)
            if self.on_error:
                self.on_error(e)

        finally:
            # Call on_exit callback if provided
            if self.on_exit:
                try:
                    self.on_exit()
                except Exception as e:
                    print(f"Warning: on_exit callback failed: {e}")

            # Stop the system
            print("\n[*] Shutting down multi-node system...")
            try:
                await self.system.stop_all()
                print("[+] Multi-node system stopped successfully.")
            except Exception as e:
                print(f"\033[91mError stopping system:\033[0m {e}")

            print("\n[*] Demo completed. Goodbye!")

    def run(self) -> None:
        """
        Run the multi-node hybrid system synchronously.

        This is the main entry point for users. Simply call this method
        to start the interactive multi-node hybrid system.

        Features:
        - Accepts an already-created MultiNodeHybridSystem externally
        - Creating a MultiNodeHybridSystem with multiple hybrid nodes
        - Configuring different orchestrators on each node
        - Connecting nodes for P2P communication
        - Executing tasks on specific nodes
        - Broadcasting tasks to all nodes
        - Cross-node collaboration

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.core.hybrid import MultiNodeHybridSystem
        >>> from daie.chat import OrchestratorChatConfig
        >>>
        >>> system = MultiNodeHybridSystem()
        >>>
        >>> research_node = system.create_node(
        ...     node_id="research-lab",
        ...     node_name="AI Research Lab",
        ...     context_name="Research Lab",
        ...     main_role="Professor",
        ...     sub_role="Researcher"
        ... )
        >>>
        >>> professor = Agent(config=AgentConfig(name="Professor", ...))
        >>> research_node.set_main_agent(professor)
        >>>
        >>> config = OrchestratorChatConfig(system=system)
        ... config.run()
        """
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            print("\n\nMulti-node hybrid system interrupted by user.")
        except Exception as e:
            print(f"\n\nFatal error: {e}")
            import sys

            sys.exit(1)

    @classmethod
    def quick_start(cls, system: MultiNodeHybridSystem, **kwargs) -> "OrchestratorChatConfig":
        """
        Quick start method for simple use cases.

        This is the simplest way to start a multi-node hybrid system. Just pass
        the system and optionally override any settings.

        Args:
            system: The MultiNodeHybridSystem instance to run
            **kwargs: Optional settings to override

        Returns:
            OrchestratorChatConfig instance ready to run

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.core.hybrid import MultiNodeHybridSystem
        >>> from daie.chat import OrchestratorChatConfig
        >>>
        >>> system = MultiNodeHybridSystem()
        >>>
        >>> research_node = system.create_node(
        ...     node_id="research-lab",
        ...     node_name="AI Research Lab",
        ...     context_name="Research Lab",
        ...     main_role="Professor",
        ...     sub_role="Researcher"
        ... )
        >>>
        >>> professor = Agent(config=AgentConfig(name="Professor", ...))
        >>> research_node.set_main_agent(professor)
        >>>
        >>> # One-liner to start multi-node system!
        >>> OrchestratorChatConfig.quick_start(system=system).run()
        """
        return cls(system=system, **kwargs)
