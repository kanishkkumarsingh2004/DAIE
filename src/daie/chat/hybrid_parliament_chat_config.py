"""
HybridParliamentChatConfig Module

Provides a simple chat loop for the HybridParliamentOrchestrator architecture so users don't need
to write the full boilerplate code. Simply pass the hybrid pipeline instance and run!
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from daie.agents.hybrid_parliament import HybridParliamentOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class HybridParliamentChatConfig:
    """
    Configuration for a simple chat loop with a HybridParliamentOrchestrator.

    This class provides a simple way to run a chat loop with a Hybrid pipeline
    instance without writing the full boilerplate code. Just pass the pipeline
    and call run()!
    """

    # Required: The hybrid pipeline to use for chat
    hybrid_pipeline: HybridParliamentOrchestrator
    """The HybridParliamentOrchestrator instance to use for deliberative peer review and execution"""

    # Chat loop behavior settings
    welcome_message: str = (
        "=== Hybrid Parliament + Orchestrator Chat Loop ===\nType your task for strategic roadmap delegation (or 'exit' to quit)\n"
    )
    """Welcome message displayed when chat starts"""

    exit_commands: List[str] = field(default_factory=lambda: ["exit", "quit", "bye", "goodbye"])
    """Commands that will exit the chat loop"""

    prompt_prefix: str = "Task: "
    """Prefix displayed before user input"""

    # Error handling settings
    error_prefix: str = "⚠️ Error: "
    """Prefix for error messages"""

    show_errors: bool = True
    """Whether to show error messages to user"""

    max_retries: int = 2
    """Maximum number of retries on error before giving up"""

    retry_delay: float = 1.0
    """Delay in seconds between retries"""

    # Advanced settings
    start_pipeline: bool = True
    """Whether to start the pipeline agents automatically (default: True)"""

    stop_pipeline: bool = True
    """Whether to stop the pipeline agents automatically on exit (default: True)"""

    clear_screen_on_start: bool = False
    """Whether to clear screen when chat starts"""

    show_goodbye: bool = True
    """Whether to show goodbye message on exit"""

    goodbye_message: str = "\nGoodbye! Hybrid pipeline session ended."
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

            # Start the pipeline if configured
            if self.start_pipeline:
                try:
                    print("\n[*] Starting Hybrid Pipeline Assemblies...")
                    await self.hybrid_pipeline.parliament.start()
                    await self.hybrid_pipeline.orchestrator.start()
                    print("[+] Hybrid Pipeline (Parliament Assembly + Orchestrator) is ready.")
                except Exception as e:
                    print(f"{self.error_prefix}Failed to start pipeline: {e}")
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
                    print(
                        "[*] Hybrid Pipeline Delegating... (this may take a moment due to assembly limits)"
                    )
                    response = await self._send_message_with_retry(user_input)

                    final_display = str(response)

                    if final_display:
                        from daie.core.llm_manager import get_llm_config

                        cfg = get_llm_config()
                        if not getattr(cfg, "stream", False):
                            print(f"\n[HYBRID PIPELINE FINAL RESULT]\n{final_display}\n")

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

            # Stop the pipeline if configured
            if self.stop_pipeline:
                try:
                    print("\n[*] Adjourning Hybrid Assemblies...")
                    await self.hybrid_pipeline.parliament.stop()
                    await self.hybrid_pipeline.orchestrator.stop()
                except Exception as e:
                    print(f"{self.error_prefix}Failed to adjourn pipeline: {e}")

            # Show goodbye message if configured
            if self.show_goodbye:
                print(self.goodbye_message)

    async def _send_message_with_retry(self, user_input: str) -> str:
        """
        Send message to pipeline with retry logic.
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Use deliberate for Hybrid Parliament
                response = await self.hybrid_pipeline.execute(user_input)

                # Handle error responses if parsing absolutely failed to string
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
        cls, hybrid_pipeline: HybridParliamentOrchestrator, **kwargs
    ) -> "HybridParliamentChatConfig":
        """
        Quick start method for simple use cases.
        """
        return cls(hybrid_pipeline=hybrid_pipeline, **kwargs)
