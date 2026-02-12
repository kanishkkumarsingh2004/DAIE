#!/usr/bin/env python3
"""
Main example file demonstrating an AI agent with full tool access and audio capabilities.

This example creates an agent that has access to all prebuilt tools (API calls, file management,
browser automation) and supports audio input/output functionality.
"""

import logging
import asyncio
import sys
from daie.tools import tool
from daie.agents import Agent
from daie.agents.config import AgentConfig, AgentRole
from daie.tools import (
    APICallTool,
    HTTPGetTool,
    HTTPPostTool,
    APIToolkit,
    SeleniumChromeTool,
    SeleniumToolkit,
    FileManagerTool,
    FileManagerToolkit,
)
from daie.utils.audio import AudioManager

model_name = "wizard-vicuna-uncensored:latest"


@tool(
    name="greeting",
    description="Generate a friendly greeting message. Can handle greetings with or without names.",
    category="general",
    version="1.0.0"
)
def greeting_tool() -> str:
        return "Hello! Nice to meet you!"
        
config = AgentConfig(
     name="ALEX",
     role=AgentRole.GENERAL_PURPOSE,
     system_prompt="you are ALEX a friendly ai agent",
     capabilities=["greeting"],
     llm_model=model_name
)   


agent = Agent(config=config)
agent.add_tool(greeting_tool)




async def listen_for_user_input(agent: Agent, logger: logging.Logger):
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
    await listen_for_user_input(agent, logging.getLogger("main"))



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
