"""
HybridChatConfig Module

Provides a simple chat loop for hybrid systems (HybridOrchestratorNode or MultiNodeHybridSystem)
so users don't need to write the full boilerplate code. Simply pass the hybrid system and run!

This is a simplified version that focuses on basic chat interaction without
complex command parsing - just like ChatLoopConfig but for hybrid systems.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Union

from daie.core.hybrid import HybridOrchestratorNode, MultiNodeHybridSystem
from daie.core.llm_manager import get_llm_config


@dataclass
class HybridChatConfig:
    """
    Configuration for a simple chat loop with hybrid systems.

    This class provides a simple way to run a chat loop with a hybrid system
    (either HybridOrchestratorNode or MultiNodeHybridSystem) without writing
    the full boilerplate code. Just pass the hybrid system and call run()!

    Unlike NodeChatConfig and OrchestratorChatConfig which provide advanced
    command parsing, this focuses on simple chat interaction - just like
    ChatLoopConfig but for hybrid systems.

    Features:
    - Accepts HybridOrchestratorNode or MultiNodeHybridSystem externally
    - Simple chat loop without complex command parsing
    - Automatic error handling and recovery
    - Graceful shutdown on interrupts
    - Configurable prompts and messages

    Example:
    >>> from daie import Agent, AgentConfig
    >>> from daie.core.hybrid import HybridOrchestratorNode
    >>> from daie.chat import HybridChatConfig
    >>>
    >>> # Create your hybrid system externally
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
    >>> # Run simple chat loop with minimal code!
    >>> config = HybridChatConfig(hybrid_system=hybrid)
    ... config.run()
    """

    # Required: The hybrid system to use for chat
    hybrid_system: Union[HybridOrchestratorNode, MultiNodeHybridSystem]
    """The hybrid system instance to use for chat"""

    # Chat loop behavior settings
    welcome_message: str = "=== Hybrid Chat Loop ===\nType your message to the hybrid system (or 'exit' to quit)\n"
    """Welcome message displayed when chat starts"""

    exit_commands: List[str] = field(default_factory=lambda: ["exit", "quit", "bye", "goodbye"])
    """Commands that will exit the chat loop"""

    prompt_prefix: str = "You: "
    """Prefix displayed before user input"""

    # Error handling settings
    error_prefix: str = "⚠️ Error: "
    """Prefix for error messages"""

    show_errors: bool = True
    """Whether to show error messages to user"""

    max_retries: int = 3
    """Maximum number of retries on error before giving up"""

    retry_delay: float = 1.0
    """Delay in seconds between retries"""

    # Advanced settings
    start_system: bool = True
    """Whether to start the hybrid system automatically (default: True)"""

    stop_system: bool = True
    """Whether to stop the hybrid system automatically on exit (default: True)"""

    clear_screen_on_start: bool = False
    """Whether to clear screen when chat starts"""

    show_goodbye: bool = True
    """Whether to show goodbye message on exit"""

    goodbye_message: str = "\nGoodbye! Chat session ended."
    """Goodbye message displayed when chat ends"""

    # Callback hooks
    on_start: Optional[Callable[[], None]] = None
    """Callback function called when chat loop starts"""

    on_exit: Optional[Callable[[], None]] = None
    """Callback function called when chat loop exits"""

    on_error: Optional[Callable[[Exception], None]] = None
    """Callback function called when an error occurs"""

    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        import os

        os.system("cls" if os.name == "nt" else "clear")

    async def run_async(self) -> None:
        """
        Run the chat loop asynchronously with comprehensive error handling.

        This method handles the complete chat loop lifecycle:
        1. Clears screen if configured
        2. Calls on_start callback if provided
        3. Starts the hybrid system (if start_system=True)
        4. Displays welcome message
        5. Runs the interactive chat loop with error recovery
        6. Calls on_exit callback if provided
        7. Stops the hybrid system cleanly on exit (if stop_system=True)
        8. Displays goodbye message if configured
        """
        try:
            # Clear screen if configured
            if self.clear_screen_on_start:
                self._clear_screen()

            # Call on_start callback if provided
            if self.on_start:
                try:
                    self.on_start()
                except Exception as e:
                    print(f"Warning: on_start callback failed: {e}")

            # Start the hybrid system if configured
            if self.start_system:
                try:
                    print("\n[*] Starting hybrid system...")
                    await self.hybrid_system.start()
                    print("[+] Hybrid system started successfully!")
                except Exception as e:
                    print(f"{self.error_prefix}Failed to start hybrid system: {e}")
                    if self.on_error:
                        self.on_error(e)
                    return

            # Display welcome message
            print(f"\n{self.welcome_message}")

            # Chat loop with error recovery
            retry_count = 0
            while True:
                try:
                    # Get user input
                    user_input = input(self.prompt_prefix)

                    # Check for exit commands
                    if user_input.lower().strip() in self.exit_commands:
                        break

                    # Skip empty input
                    if not user_input.strip():
                        continue

                    # Send message and get response with retry logic
                    response = await self._send_message_with_retry(user_input)

                    # Display response only if streaming is disabled
                    # (when streaming is enabled, tokens are already printed as they arrive)
                    cfg = get_llm_config()
                    if response and not cfg.stream:
                        print(f"\n{response}\n")

                    # Reset retry count on successful interaction
                    retry_count = 0

                except KeyboardInterrupt:
                    print("\n\nExiting chat loop...")
                    break
                except EOFError:
                    print("\n\nInput stream closed. Exiting...")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        print(f"{self.error_prefix}Maximum retries reached. Exiting...")
                        if self.on_error:
                            self.on_error(e)
                        break

                    if self.show_errors:
                        print(f"{self.error_prefix}{e}")
                        print(f"Retrying... ({retry_count}/{self.max_retries})")

                    if self.on_error:
                        self.on_error(e)

                    # Wait before retry
                    await asyncio.sleep(self.retry_delay)

        except Exception as e:
            print(f"{self.error_prefix}Fatal error in chat loop: {e}")
            if self.on_error:
                self.on_error(e)

        finally:
            # Call on_exit callback if provided
            if self.on_exit:
                try:
                    self.on_exit()
                except Exception as e:
                    print(f"Warning: on_exit callback failed: {e}")

            # Stop the hybrid system if configured
            if self.stop_system:
                try:
                    print("\n[*] Shutting down hybrid system...")
                    await self.hybrid_system.stop()
                    print("[+] Hybrid system stopped successfully.")
                except Exception as e:
                    print(f"{self.error_prefix}Failed to stop hybrid system: {e}")

            # Show goodbye message if configured
            if self.show_goodbye:
                print(self.goodbye_message)

    async def _send_message_with_retry(self, user_input: str) -> str:
        """
        Send message to hybrid system with retry logic.

        Args:
            user_input: The user's input message

        Returns:
            The hybrid system's response

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Use execute_task for HybridOrchestratorNode
                if isinstance(self.hybrid_system, HybridOrchestratorNode):
                    response = await self.hybrid_system.execute_task(user_input)
                # Use execute_task on first node for MultiNodeHybridSystem
                elif isinstance(self.hybrid_system, MultiNodeHybridSystem):
                    status = self.hybrid_system.get_system_status()
                    if status["nodes"]:
                        first_node_id = list(status["nodes"].keys())[0]
                        response = await self.hybrid_system.execute_task(first_node_id, user_input)
                    else:
                        return "Error: No nodes available in the hybrid system"
                else:
                    return f"Error: Unsupported hybrid system type: {type(self.hybrid_system)}"

                # Handle error responses from hybrid system
                if isinstance(response, str) and response.startswith("Error:"):
                    if self.show_errors:
                        print(f"{self.error_prefix}{response}")
                    return ""

                return str(response)

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)

        # All retries failed
        raise last_error

    def run(self) -> None:
        """
        Run the chat loop synchronously.

        This is the main entry point for users. Simply call this method
        to start the interactive chat loop with the configured hybrid system.

        Features:
        - Accepts HybridOrchestratorNode or MultiNodeHybridSystem externally
        - Simple chat loop without complex command parsing
        - Automatic error handling and recovery
        - Graceful shutdown on interrupts
        - Configurable prompts and messages

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.core.hybrid import HybridOrchestratorNode
        >>> from daie.chat import HybridChatConfig
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
        >>> config = HybridChatConfig(hybrid_system=hybrid)
        ... config.run()
        """
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            print("\n\nChat loop interrupted by user.")
        except Exception as e:
            print(f"\n\nFatal error: {e}")
            import sys

            sys.exit(1)

    @classmethod
    def quick_start(
        cls, hybrid_system: Union[HybridOrchestratorNode, MultiNodeHybridSystem], **kwargs
    ) -> "HybridChatConfig":
        """
        Quick start method for simple use cases.

        This is the simplest way to start a chat loop with a hybrid system. Just pass
        the hybrid system and optionally override any settings.

        Args:
            hybrid_system: The hybrid system instance to use for chat
            **kwargs: Optional settings to override

        Returns:
            HybridChatConfig instance ready to run

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.core.hybrid import HybridOrchestratorNode
        >>> from daie.chat import HybridChatConfig
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
        >>> # One-liner to start chat loop!
        >>> HybridChatConfig.quick_start(hybrid_system=hybrid).run()
        """
        return cls(hybrid_system=hybrid_system, **kwargs)
