"""
ChatLoopConfig Module

Provides a pre-configured chat loop setup so users don't need to write
the full chat loop code. Simply pass an agent and run!

Features:
- Automatic error handling and recovery
- Graceful shutdown on interrupts
- Configurable exit commands
- Customizable prompts and messages
- Support for streaming responses
- Easy agent lifecycle management
"""

import asyncio
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from daie.agents.agent import Agent
from daie.core.llm_manager import get_llm_config


@dataclass
class ChatLoopConfig:
    """
    Configuration for a pre-built chat loop with advanced error handling.

    This class provides a simple way to run a chat loop with an existing
    agent without writing the full boilerplate code. Just pass the agent
    and call run() to start chatting!

    Features:
    - Automatic error handling and recovery
    - Graceful shutdown on interrupts
    - Configurable exit commands
    - Customizable prompts and messages
    - Support for streaming responses
    - Easy agent lifecycle management

    Example:
    >>> from daie import Agent, AgentConfig
    >>> from daie.chat import ChatLoopConfig
    >>>
    >>> # Create your agent
    >>> config = AgentConfig(name="LUNA", system_prompt="You are helpful.")
    >>> agent = Agent(config=config)
    >>>
    >>> # Run the chat loop with minimal code!
    >>> chat_loop = ChatLoopConfig(agent=agent)
    >>> chat_loop.run()
    """

    # Required: The agent to use for the chat loop
    agent: Agent
    """The agent instance to use for the chat loop"""

    # Chat loop behavior settings
    welcome_message: str = "=== Chat Loop ===\nType 'exit' or press Ctrl+C to quit.\n"
    """Welcome message displayed when chat starts"""

    exit_commands: List[str] = field(default_factory=lambda: ["exit", "quit", "bye", "goodbye"])
    """Commands that will exit the chat loop"""

    prompt_prefix: str = "You: "
    """Prefix displayed before user input"""

    show_agent_name: bool = False
    """Whether to show agent name before responses"""

    agent_name_prefix: str = "{agent_name}: "
    """Format for agent name prefix (use {agent_name} placeholder)"""

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
    start_agent: bool = True
    """Whether to start the agent automatically (default: True)"""

    stop_agent: bool = True
    """Whether to stop the agent automatically on exit (default: True)"""

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

    async def run_async(self) -> None:
        """
        Run the chat loop asynchronously with comprehensive error handling.

        This method handles the complete chat loop lifecycle:
        1. Clears screen if configured
        2. Calls on_start callback if provided
        3. Starts the agent (if start_agent=True)
        4. Displays welcome message
        5. Runs the interactive chat loop with error recovery
        6. Calls on_exit callback if provided
        7. Stops the agent cleanly on exit (if stop_agent=True)
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

            # Start the agent if configured
            if self.start_agent:
                try:
                    await self.agent.start()
                except Exception as e:
                    print(f"{self.error_prefix}Failed to start agent: {e}")
                    if self.on_error:
                        self.on_error(e)
                    return

            # Display welcome message
            print(self.welcome_message)

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
                        if self.show_agent_name and hasattr(self.agent, "config"):
                            agent_name = self.agent.config.name
                            prefix = self.agent_name_prefix.format(agent_name=agent_name)
                            print(f"{prefix}{response}")
                        else:
                            print(response)

                    print()  # Add blank line for readability

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

            # Stop the agent if configured
            if self.stop_agent:
                try:
                    await self.agent.stop()
                except Exception as e:
                    print(f"{self.error_prefix}Failed to stop agent: {e}")

            # Show goodbye message if configured
            if self.show_goodbye:
                print(self.goodbye_message)

    async def _send_message_with_retry(self, user_input: str) -> str:
        """
        Send message to agent with retry logic.

        Args:
            user_input: The user's input message

        Returns:
            The agent's response

        Raises:
            Exception: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await self.agent.send_message(user_input)

                # Handle error responses from agent
                if response.startswith("Error:"):
                    if self.show_errors:
                        print(f"{self.error_prefix}{response}")
                    return ""

                return response

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)

        # All retries failed
        raise last_error

    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        import os

        os.system("cls" if os.name == "nt" else "clear")

    def run(self) -> None:
        """
        Run the chat loop synchronously.

        This is the main entry point for users. Simply call this method
        to start the interactive chat loop with the configured agent.

        Features:
        - Automatic error handling
        - Graceful shutdown on Ctrl+C
        - Configurable exit commands
        - Customizable prompts and messages

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.chat import ChatLoopConfig
        >>>
        >>> config = AgentConfig(name="LUNA", system_prompt="You are helpful.")
        >>> agent = Agent(config=config)
        >>>
        >>> chat_loop = ChatLoopConfig(agent=agent)
        >>> chat_loop.run()
        """
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            print("\n\nChat loop interrupted by user.")
        except Exception as e:
            print(f"\n\nFatal error: {e}")
            sys.exit(1)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format.

        Returns:
            Dictionary representation of configuration
        """
        from dataclasses import fields

        data = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name == "agent":
                # Skip agent as it's not serializable
                continue
            elif f.name in ("on_start", "on_exit", "on_error"):
                # Skip callbacks as they're not serializable
                continue
            elif isinstance(value, (list, dict, str, int, float, bool)):
                data[f.name] = value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], agent: Agent) -> "ChatLoopConfig":
        """
        Create a ChatLoopConfig instance from a dictionary.

        Args:
            data: Dictionary containing configuration values
            agent: The agent instance to use

        Returns:
            ChatLoopConfig instance
        """
        config = cls(agent=agent)
        for key, value in data.items():
            if hasattr(config, key) and key not in ("agent", "on_start", "on_exit", "on_error"):
                setattr(config, key, value)
        return config

    @classmethod
    def quick_start(cls, agent: Agent, **kwargs) -> "ChatLoopConfig":
        """
        Quick start method for simple use cases.

        This is the simplest way to start a chat loop. Just pass an agent
        and optionally override any settings.

        Args:
            agent: The agent instance to use
            **kwargs: Optional settings to override

        Returns:
            ChatLoopConfig instance ready to run

        Example:
        >>> from daie import Agent, AgentConfig
        >>> from daie.chat import ChatLoopConfig
        >>>
        >>> config = AgentConfig(name="LUNA", system_prompt="You are helpful.")
        >>> agent = Agent(config=config)
        >>>
        >>> # One-liner to start chat!
        >>> ChatLoopConfig.quick_start(agent).run()
        """
        return cls(agent=agent, **kwargs)
