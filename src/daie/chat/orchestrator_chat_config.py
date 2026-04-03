"""
OrchestratorChatConfig Module

Provides a simple chat loop for a single Orchestrator (main agent + sub-agents)
so users don't need to write the full boilerplate code. Simply pass the 
orchestrator and run!

This focuses on simple task orchestration interaction - just like
ChatLoopConfig but for multi-agent orchestrators.
"""

import asyncio
import re
import logging
import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Any, Dict

from daie.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorChatConfig:
    """
    Configuration for a simple chat loop with a single Orchestrator.

    This class provides a simple way to run a chat loop with an Orchestrator
    instance without writing the full boilerplate code. Just pass the 
    orchestrator and call run()!

    Features:
    - Accepts a single Orchestrator instance
    - Simple chat loop for task-oriented multi-agent work
    - Automatic error handling and recovery
    - Graceful shutdown on interrupts
    - Configurable prompts and messages

    Example:
    >>> from daie import Agent, AgentConfig
    >>> from daie.core.orchestrator import Orchestrator
    >>> from daie.chat import OrchestratorChatConfig
    >>>
    >>> # Create your agents
    >>> main_agent = Agent(config=AgentConfig(name="Manager", ...))
    >>> sub_agent1 = Agent(config=AgentConfig(name="Researcher", ...))
    >>>
    >>> # Create orchestrator
    >>> orch = Orchestrator(main_agent=main_agent, sub_agents=[sub_agent1])
    >>>
    >>> # Run simple chat loop!
    >>> config = OrchestratorChatConfig(orchestrator=orch)
    >>> config.run()
    """

    # Required: The orchestrator to use for chat
    orchestrator: Orchestrator
    """The Orchestrator instance to use for identifying and delegating tasks"""

    # Chat loop behavior settings
    welcome_message: str = "=== Orchestrator Chat Loop ===\nType your task for the orchestrator (or 'exit' to quit)\n"
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
    start_orchestrator: bool = True
    """Whether to start the orchestrator automatically (default: True)"""

    stop_orchestrator: bool = True
    """Whether to stop the orchestrator automatically on exit (default: True)"""

    clear_screen_on_start: bool = False
    """Whether to clear screen when chat starts"""

    show_goodbye: bool = True
    """Whether to show goodbye message on exit"""

    goodbye_message: str = "\nGoodbye! Orchestration session ended."
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

            # Start the orchestrator if configured
            if self.start_orchestrator:
                try:
                    print(f"\n[*] Starting {self.orchestrator.context_name}...")
                    await self.orchestrator.start()
                    print(f"[+] Orchestrator '{self.orchestrator.main_agent.name}' is ready.")
                except Exception as e:
                    print(f"{self.error_prefix}Failed to start orchestrator: {e}")
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
                    user_input = input(self.prompt_prefix).strip()

                    # Check for exit commands
                    if user_input.lower() in self.exit_commands:
                        break

                    # Skip empty input
                    if not user_input:
                        continue

                    # Send message and get response with retry logic
                    response = await self._send_message_with_retry(user_input)

                    # Robustly parse the response if it contains JSON
                    final_display = response
                    if response:
                        parsed = self._extract_json(response)
                        if parsed and isinstance(parsed, dict) and "answer" in parsed:
                            ans = parsed["answer"]
                            # answer must be a string — convert if LLM returned a list/dict
                            final_display = ans if isinstance(ans, str) else json.dumps(ans, ensure_ascii=False)

                    # When stream=True the agent already printed the answer via
                    # _stream_final_answer() inside execute_task. Only print here
                    # when stream=False.
                    if final_display:
                        from daie.core.llm_manager import get_llm_config

                        cfg = get_llm_config()
                        if not cfg.stream:
                            print(f"\n{final_display}\n")

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

            # Stop the orchestrator if configured
            if self.stop_orchestrator:
                try:
                    print(f"\n[*] Shutting down {self.orchestrator.context_name}...")
                    await self.orchestrator.stop()
                except Exception as e:
                    print(f"{self.error_prefix}Failed to stop orchestrator: {e}")

            # Show goodbye message if configured
            if self.show_goodbye:
                print(self.goodbye_message)

    async def _send_message_with_retry(self, user_input: str) -> str:
        """
        Send message to orchestrator with retry logic.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Use execute_task for Orchestrator
                response = await self.orchestrator.execute_task(user_input)

                # Handle error responses
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

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract the first valid JSON object from text."""
        import json
        # Strip code fences
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

        def try_parse(s):
            try:
                return json.loads(s)
            except:
                return None

        # Try whole string
        res = try_parse(text)
        if res: return res

        # Search for first { } block
        search_from = 0
        while True:
            start = text.find("{", search_from)
            if start == -1: break
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "{": depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        res = try_parse(candidate)
                        if res: return res
                        break
            search_from = start + 1
        return None

    def run(self) -> None:
        """
        Run the chat loop synchronously.
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
    def quick_start(cls, orchestrator: Orchestrator, **kwargs) -> "OrchestratorChatConfig":
        """
        Quick start method for simple use cases.
        """
        return cls(orchestrator=orchestrator, **kwargs)
