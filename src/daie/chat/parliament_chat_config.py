"""
ParliamentChatConfig Module

Provides a simple chat loop for a Parliament architecture so users don't need
to write the full boilerplate code. Simply pass the parliament instance and run!
"""

import asyncio
import re
import logging
import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Any, Dict

from daie.agents.parliament import Parliament

logger = logging.getLogger(__name__)


@dataclass
class ParliamentChatConfig:
    """
    Configuration for a simple chat loop with a Parliament.

    This class provides a simple way to run a chat loop with a Parliament
    instance without writing the full boilerplate code. Just pass the
    parliament and call run()!
    """

    # Required: The parliament to use for chat
    parliament: Parliament
    """The Parliament instance to use for deliberative peer review"""

    # Chat loop behavior settings
    welcome_message: str = "=== Parliament Deliberative Chat Loop ===\nType your topic for debate (or 'exit' to quit)\n"
    """Welcome message displayed when chat starts"""

    exit_commands: List[str] = field(
        default_factory=lambda: ["exit", "quit", "bye", "goodbye"]
    )
    """Commands that will exit the chat loop"""

    prompt_prefix: str = "Topic: "
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
    start_parliament: bool = True
    """Whether to start the parliament agents automatically (default: True)"""

    stop_parliament: bool = True
    """Whether to stop the parliament agents automatically on exit (default: True)"""

    clear_screen_on_start: bool = False
    """Whether to clear screen when chat starts"""

    show_goodbye: bool = True
    """Whether to show goodbye message on exit"""

    goodbye_message: str = "\nGoodbye! Deliberation session ended."
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

            # Start the parliament if configured
            if self.start_parliament:
                try:
                    print("\n[*] Starting Parliament Assembly...")
                    await self.parliament.start()
                    print(f"[+] Parliament with {len(self.parliament.sub_agents)} members is ready.")
                except Exception as e:
                    print(f"{self.error_prefix}Failed to start parliament: {e}")
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
                    print("[*] Deliberating... (this may take a moment)")
                    response = await self._send_message_with_retry(user_input)

                    # Robustly parse the response if it contains JSON
                    final_display = response
                    if response:
                        parsed = self._extract_json(response)
                        if parsed and isinstance(parsed, dict) and "answer" in parsed:
                            ans = parsed["answer"]
                            final_display = (
                                ans
                                if isinstance(ans, str)
                                else json.dumps(ans, ensure_ascii=False)
                            )

                    if final_display:
                        from daie.core.llm_manager import get_llm_config
                        cfg = get_llm_config()
                        if not getattr(cfg, 'stream', False):
                            print(f"\n[SPEAKER SYNTHESIS]\n{final_display}\n")

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

            # Stop the parliament if configured
            if self.stop_parliament:
                try:
                    print("\n[*] Adjourning Parliament...")
                    await self.parliament.stop()
                except Exception as e:
                    print(f"{self.error_prefix}Failed to adjourn parliament: {e}")

            # Show goodbye message if configured
            if self.show_goodbye:
                print(self.goodbye_message)

    async def _send_message_with_retry(self, user_input: str) -> str:
        """
        Send message to parliament with retry logic.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Use deliberate for Parliament
                response = await self.parliament.deliberate(user_input)

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
        if last_error:
            raise last_error
        return ""

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract the first valid JSON object from text."""
        import json

        # Strip code fences
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

        def try_parse(s):
            try:
                return json.loads(s)
            except Exception:
                return None

        # Try whole string
        res = try_parse(text)
        if res:
            return res

        # Search for first { } block
        search_from = 0
        while True:
            start = text.find("{", search_from)
            if start == -1:
                break
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        res = try_parse(candidate)
                        if res:
                            return res
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
    def quick_start(
        cls, parliament: Parliament, **kwargs
    ) -> "ParliamentChatConfig":
        """
        Quick start method for simple use cases.
        """
        return cls(parliament=parliament, **kwargs)
