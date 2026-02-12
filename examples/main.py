#!/usr/bin/env python3
"""
Main example file demonstrating an AI agent with full tool access and audio capabilities.

This example creates an agent that has access to all prebuilt tools (API calls, file management,
browser automation) and supports audio input/output functionality.
"""

import logging
import asyncio
import sys
from daie.agents import Agent
from daie.agents.config import AgentConfig, AgentRole
from daie.tools import (
    APIToolkit,
    SeleniumToolkit,
    FileManagerToolkit,
)
from daie.utils.audio import AudioManager
from daie.utils.logger import setup_logging


def setup_logging_config():
    """Set up logging configuration for the example"""
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    return logger


def create_agent_config() -> AgentConfig:
    """Create a comprehensive agent configuration with all capabilities"""
    return AgentConfig(
        name="NOVA",
        role=AgentRole.GENERAL_PURPOSE,
        goal="Perform a wide range of tasks using all available tools with audio capabilities",
        backstory="Created as a versatile AI assistant with access to all prebuilt tools and audio I/O",
        system_prompt=(
            "You are NOVA, a friendly and versatile AI assistant with access to all prebuilt tools. "
            "Your primary goal is to help users with their tasks and engage in natural conversations. "
            "You can use tools for making API calls, managing files, and automating web browsers. "
            "You also have audio input and output capabilities, allowing you to listen to user commands and respond with speech. "
            "Always try to understand the user's intent and choose the most appropriate tool for the task. "
            "If the user greets you, respond with a friendly greeting instead of using a tool. "
            "For other tasks, analyze the user's request and determine which tool to use based on the capabilities of each tool. "
            "If you are unsure which tool to use, ask the user for clarification. Always provide helpful and informative responses, whether through tools or conversation."
        ),
        capabilities=[
            "api_requests",
            "http_get",
            "http_post",
            "file_management",
            "browser_automation",
            "audio_input",
            "audio_output",
        ],
        enable_audio_input=True,
        enable_audio_output=True,
        llm_provider="ollama",
        llm_model="llama3.2:latest",
        temperature=0.7,
        max_tokens=1000,
        max_concurrent_tasks=10,
        task_timeout=60,
    )


def create_agent_with_all_tools(config: AgentConfig) -> Agent:
    """Create an agent and equip it with all available tools"""
    agent = Agent(config=config)

    # Add API tools
    for tool in APIToolkit.get_tools():
        agent.add_tool(tool)

    # Add browser automation tools
    for tool in SeleniumToolkit.get_tools():
        agent.add_tool(tool)

    # Add file management tools
    for tool in FileManagerToolkit.get_tools():
        agent.add_tool(tool)

    return agent


async def demonstrate_agent_capabilities(agent: Agent, logger: logging.Logger):
    """Demonstrate the agent's capabilities"""
    logger.info(f"Agent '{agent.config.name}' created with all tools")

    # Show available tools
    logger.info(f"Available tools: {list(agent.tools.keys())}")

    # Test audio capabilities
    logger.info("\nTesting audio capabilities...")
    try:
        audio_manager = AudioManager(agent.config)
        if audio_manager.initialize_audio():
            devices = audio_manager.list_audio_devices()
            logger.info(f"Audio devices available: {len(devices)}")
            for device in devices:
                logger.info(f"  Device {device['id']}: {device['name']}")
        else:
            logger.warning("Audio initialization failed")
    except Exception as e:
        logger.error(f"Audio test failed: {e}")

    # Test dynamic task analysis
    logger.info("\nTesting dynamic task analysis...")
    try:
        # Test with natural language task description
        logger.info("1. Testing 'List current directory'")
        result = await agent.execute_task("List all files in the current directory")
        logger.info(f"Result: {result}")

        # Test creating a file
        logger.info("\n2. Testing 'Create test file'")
        result = await agent.execute_task(
            "Create a file called test_dynamic.txt with content 'Hello from dynamic task analysis'"
        )
        logger.info(f"Result: {result}")

        # Test reading the file
        logger.info("\n3. Testing 'Read test file'")
        result = await agent.execute_task("Read the contents of test_dynamic.txt")
        logger.info(f"Result: {result}")

        # Test deleting the file
        logger.info("\n4. Testing 'Delete test file'")
        result = await agent.execute_task("Delete test_dynamic.txt")
        logger.info(f"Result: {result}")

    except Exception as e:
        logger.error(f"Dynamic task analysis test failed: {e}")
        # Clean up if file was created
        import os

        if os.path.exists("test_dynamic.txt"):
            os.remove("test_dynamic.txt")


async def listen_for_user_input(agent: Agent, logger: logging.Logger):
    """Interactive loop for user input"""
    print("\n" + "="*60)
    print("NOVA Agent Interactive Mode")
    print("="*60)
    print("Type your task or question, or 'quit' to exit")
    print("="*60 + "\n")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYour task: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                logger.info("User requested to quit")
                break

            if not user_input:
                continue

            logger.info(f"Processing task: {user_input}")

            # Execute task using new method that automatically determines tool
            result = await agent.execute_task(user_input)

            if isinstance(result, dict) and "success" in result:
                # Tool execution result
                print(f"\nTool result:")
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
                # Conversational response
                print(f"\nAgent response:\n{result}")

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            break
        except EOFError:
            logger.info("EOF received, exiting")
            break
        except Exception as e:
            logger.error(f"Error in input processing: {e}")


async def main():
    """Main entry point"""
    logger = setup_logging_config()

    try:
        logger.info("Creating agent with all capabilities...")
        config = create_agent_config()
        agent = create_agent_with_all_tools(config)

        logger.info("Starting agent...")
        await agent.start()

        await demonstrate_agent_capabilities(agent, logger)

        # Start interactive mode
        await listen_for_user_input(agent, logger)

        logger.info("Stopping agent...")
        await agent.stop()

    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error("Exiting...")
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nUser interrupted. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
