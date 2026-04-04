"""
NodeChatConfig Module

Provides a pre-configured setup for HybridOrchestratorNode so users don't need to write
the full boilerplate code. Simply configure and run!

Features:
- Accepts an already-created HybridOrchestratorNode externally
- Automatic setup of Node, Orchestrator, and CommunicationManager
- Resource management on the hybrid node
- Task execution using the orchestrator
- Intelligent message routing with AgentRouter
- Collaborative task execution across all agents
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from daie.core.hybrid import HybridOrchestratorNode
from daie.core.llm_manager import get_llm_config


@dataclass
class NodeChatConfig:
    """
    Configuration for running a pre-built HybridOrchestratorNode with advanced error handling.

    This class provides a simple way to run a hybrid orchestrator node
    without writing the full boilerplate code. Just pass the node
    and call run() to start the interactive system!

    Features:
    - Accepts an already-created HybridOrchestratorNode externally
    - Automatic setup of Node, Orchestrator, and CommunicationManager
    - Resource management on the hybrid node
    - Task execution using the orchestrator
    - Intelligent message routing with AgentRouter
    - Collaborative task execution across all agents

    Example:
    >>> from daie import Agent, AgentConfig
    >>> from daie.core.hybrid import HybridOrchestratorNode
    >>> from daie.chat import NodeChatConfig
    >>>
    >>> # Create your hybrid node externally
    >>> hybrid = HybridOrchestratorNode(
    ...     node_id="research-lab",
    ...     node_name="AI Research Lab",
    ...     context_name="Research Lab",
    ...     main_role="Professor",
    ...     sub_role="Researcher"
    ... )
    >>>
    >>> # Add agents
    >>> professor = Agent(config=AgentConfig(name="Professor", ...))
    >>> hybrid.set_main_agent(professor)
    >>>
    >>> # Run the hybrid node with minimal code!
    >>> config = NodeChatConfig(hybrid_node=hybrid)
    ... config.run()
    """

    # Required: The hybrid node to run
    hybrid_node: HybridOrchestratorNode
    """The HybridOrchestratorNode instance to run"""

    # Logging settings
    enable_logging: bool = True
    """Whether to enable logging"""

    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR)"""

    log_file: Optional[str] = None
    """Log file path (None for console only)"""

    # Interactive mode settings
    welcome_message: str = (
        "=== Hybrid Orchestrator Node ===\nType your task to execute (or 'exit' to quit)\n"
    )
    """Welcome message displayed when interactive mode starts"""

    exit_commands: List[str] = field(default_factory=lambda: ["exit", "quit"])
    """Commands that will exit the interactive loop"""

    prompt_prefix: str = "You: "
    """Prefix displayed before user input"""

    show_status_on_start: bool = True
    """Whether to show system status when starting"""

    # Callback hooks
    on_start: Optional[Callable[[], None]] = None
    """Callback function called when node starts"""

    on_exit: Optional[Callable[[], None]] = None
    """Callback function called when node exits"""

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
                logging.basicConfig(
                    level=getattr(logging, self.log_level.upper()), format=log_format
                )

    async def run_async(self) -> None:
        """
        Run the hybrid orchestrator node asynchronously with comprehensive error handling.

        This method handles the complete node lifecycle:
        1. Sets up logging
        2. Calls on_start callback if provided
        3. Starts the hybrid node
        4. Displays system status if configured
        5. Runs the interactive loop with error recovery
        6. Calls on_exit callback if provided
        7. Stops the node cleanly on exit
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

            # Start the hybrid system
            print("\n[*] Starting hybrid system...")
            await self.hybrid_node.start()
            print("[+] Hybrid system started successfully!")

            # Display status if configured
            if self.show_status_on_start:
                status = self.hybrid_node.get_status()
                print("\n[*] System Status:")
                print(f"  - Node: {status['node_name']} (ID: {status['node_id']})")
                print(f"  - Context: {status['context_name']}")
                print(f"  - Total Agents: {status['total_agents']}")
                print(f"  - Main Agent: {status['main_agent']}")
                print(f"  - Sub-Agents: {', '.join(status['sub_agents'])}")
                print(f"  - Router: {'enabled' if status['router_enabled'] else 'disabled'}")
                print(f"  - Resources: {status['resources']}")

            # Display welcome message
            print(f"\n{self.welcome_message}")
            print("Commands:")
            print("  - 'route <message>' - Route message to best agent")
            print("  - 'collab <task>' - Execute collaborative task")
            print("  - 'status' - Show system status")
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
                        status = self.hybrid_node.get_status()
                        print("\n\033[93mSystem Status:\033[0m")
                        print(f"  Running: {status['is_running']}")
                        print(f"  Agents: {status['total_agents']}")
                        print(f"  Resources: {status['resources']}")
                        continue

                    # Handle route command
                    if user_input.lower().startswith("route "):
                        message = user_input[6:].strip()
                        print("\n\033[92mRouting message to best agent...\033[0m")
                        response = await self.hybrid_node.route_message(message)
                        print("\n\033[93mResponse:\033[0m")
                        print(f"{response}\n")
                        continue

                    # Handle collab command
                    if user_input.lower().startswith("collab "):
                        task = user_input[7:].strip()
                        print("\n\033[92mExecuting collaborative task...\033[0m")
                        response = await self.hybrid_node.execute_collaborative_task(task)
                        print("\n\033[93mCollaborative Response:\033[0m")
                        print(f"{response}\n")
                        continue

                    # Default: execute task via orchestrator
                    print("\n\033[92mOrchestrating the task...\033[0m")
                    result = await self.hybrid_node.execute_task(user_input)

                    # Extract answer if it still looks like JSON
                    final_display = result
                    if isinstance(result, str) and result.strip().startswith("{"):
                        try:
                            import json

                            parsed = json.loads(result)
                            final_display = parsed.get("answer", result)
                        except Exception:
                            pass

                    # Always print — execute_task never streams, so nothing
                    # has been printed to stdout yet regardless of stream setting
                    from daie.core.llm_manager import get_llm_config

                    cfg = get_llm_config()
                    if not cfg.stream:
                        print("\n\033[93mFinal Answer:\033[0m")
                        print(f"{final_display}\n")

                    print("-" * 30 + "\n")

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
            logging.error(f"Fatal error in hybrid node: {e}", exc_info=True)
            if self.on_error:
                self.on_error(e)

        finally:
            # Call on_exit callback if provided
            if self.on_exit:
                try:
                    self.on_exit()
                except Exception as e:
                    print(f"Warning: on_exit callback failed: {e}")

            # Stop the hybrid system
            print("\n[*] Shutting down hybrid system...")
            try:
                await self.hybrid_node.stop()
                print("[+] Hybrid system stopped successfully.")
            except Exception as e:
                print(f"\033[91mError stopping hybrid system:\033[0m {e}")

            print("\n[*] Demo completed. Goodbye!")

    def run(self) -> None:
        """
        Run the hybrid orchestrator node synchronously.

        This is the main entry point for users. Simply call this method
        to start the interactive hybrid orchestrator node.

        Features:
        - Accepts an already-created HybridOrchestratorNode externally
        - Automatic setup of Node, Orchestrator, and CommunicationManager
        - Resource management on the hybrid node
        - Task execution using the orchestrator
        - Intelligent message routing with AgentRouter
        - Collaborative task execution across all agents

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.core.hybrid import HybridOrchestratorNode
        >>> from daie.chat import NodeChatConfig
        >>>
        >>> hybrid = HybridOrchestratorNode(
        ...     node_id="research-lab",
        ...     node_name="AI Research Lab",
        ...     context_name="Research Lab",
        ...     main_role="Professor",
        ...     sub_role="Researcher"
        ... )
        >>>
        >>> professor = Agent(config=AgentConfig(name="Professor", ...))
        >>> hybrid.set_main_agent(professor)
        >>>
        >>> config = NodeChatConfig(hybrid_node=hybrid)
        ... config.run()
        """
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            print("\n\nHybrid orchestrator node interrupted by user.")
        except Exception as e:
            print(f"\n\nFatal error: {e}")
            import sys

            sys.exit(1)

    @classmethod
    def quick_start(cls, hybrid_node: HybridOrchestratorNode, **kwargs) -> "NodeChatConfig":
        """
        Quick start method for simple use cases.

        This is the simplest way to start a hybrid orchestrator node. Just pass
        the hybrid node and optionally override any settings.

        Args:
            hybrid_node: The HybridOrchestratorNode instance to run
            **kwargs: Optional settings to override

        Returns:
            NodeChatConfig instance ready to run

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.core.hybrid import HybridOrchestratorNode
        >>> from daie.chat import NodeChatConfig
        >>>
        >>> hybrid = HybridOrchestratorNode(
        ...     node_id="research-lab",
        ...     node_name="AI Research Lab",
        ...     context_name="Research Lab",
        ...     main_role="Professor",
        ...     sub_role="Researcher"
        ... )
        >>>
        >>> professor = Agent(config=AgentConfig(name="Professor", ...))
        >>> hybrid.set_main_agent(professor)
        >>>
        >>> # One-liner to start hybrid node!
        >>> NodeChatConfig.quick_start(hybrid_node=hybrid).run()
        """
        return cls(hybrid_node=hybrid_node, **kwargs)
