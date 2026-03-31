#!/usr/bin/env python3
"""
Example demonstrating OpenRouter LLM integration with AI Agent chat interface.

This example creates a chat application using an AI agent connected to OpenRouter LLM
with streaming capabilities.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from daie.agents import Agent
from daie.agents.config import AgentConfig, AgentRole
from daie.core.llm_manager import LLMType, get_llm_manager
from daie.tools import tool

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


@tool(
    name="greeting",
    description="Generate a friendly greeting message. Can handle greetings with or without names.",
    category="general",
    version="1.0.0",
)
def greeting_tool() -> str:
    return "Hello! Nice to meet you! I'm your AI assistant powered by OpenRouter LLM. How can I help you today?"


# Get OpenRouter API key from environment variable
OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER")

if not OPEN_ROUTER_KEY:
    print("Error: OPEN_ROUTER environment variable not found. Please check your .env file.")
    sys.exit(1)

# Configure OpenRouter LLM
llm_manager = get_llm_manager()
llm_manager.set_llm(
    llm_type=LLMType.OPENROUTER,
    model_name="deepseek/deepseek-r1-0528:free",
    api_key=OPEN_ROUTER_KEY,
    temperature=0.7,
    max_tokens=1000,
)

# Create agent configuration
config = AgentConfig(
    name="OpenRouter Assistant",
    role=AgentRole.GENERAL_PURPOSE,
    system_prompt="You are a helpful and friendly AI assistant powered by OpenRouter LLM. You have access to various tools to help users with their tasks. Respond conversationally and provide useful information.",
    capabilities=["greeting"],
    llm_provider="openrouter",
    llm_model="deepseek/deepseek-r1-0528:free",
)

# Create and configure agent
agent = Agent(config=config)
agent.add_tool(greeting_tool)


async def listen_for_user_input(agent: Agent, logger: logging.Logger):
    """Listen for user input and interact with the agent"""
    print("=" * 50)
    print("OpenRouter AI Assistant")
    print("=" * 50)
    print("Type 'quit', 'exit', or 'q' to end the conversation")
    print("Type 'help' to see available commands")
    print("=" * 50)

    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                logger.info("User requested to quit")
                print("\nGoodbye! Have a great day!")
                break

            if user_input.lower() == "help":
                print("\nAvailable commands:")
                print("- help: Show this help message")
                print("- quit/exit/q: End the conversation")
                print("- Any other text: Ask a question or request assistance")
                continue

            if not user_input:
                continue

            logger.info(f"Processing user input: {user_input}")

            # Execute task using the agent
            result = await agent.execute_task(user_input)

            if isinstance(result, dict) and "success" in result:
                # Tool execution result
                print(f"\nAssistant:")
                if result.get("success"):
                    print(f"Success!")
                    if "contents" in result:
                        print(f"Files in directory:")
                        for item in result.get("contents", []):
                            print(f"  - {item['name']}")
                    elif "path" in result:
                        print(f"Operation completed on: {result.get('path')}")
                    else:
                        print(f"{result}")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
            else:
                # Conversational response - use streaming if available
                print(f"\nAssistant:")
                llm = get_llm_manager().get_llm()
                response = llm.invoke(
                    result if result else "I'm here to help. What would you like to know?", stream=True
                )

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            print("\nGoodbye! Have a great day!")
            break
        except EOFError:
            logger.info("EOF received, exiting")
            print("\nGoodbye! Have a great day!")
            break
        except Exception as e:
            logger.error(f"Error in input processing: {e}")
            print(f"\nError: {e}")


async def main():
    """Main function to run the chat application"""
    await listen_for_user_input(agent, logging.getLogger("main"))


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nUser interrupted. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        print(f"\n{traceback.format_exc()}")
        sys.exit(1)
