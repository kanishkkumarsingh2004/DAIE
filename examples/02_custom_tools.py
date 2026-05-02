# 🟡 Intermediate - Custom Tools Example
# Difficulty: Intermediate
# This example demonstrates custom @tool decorator + FileManagerTool with ReAct agent loop.

import asyncio

from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.tools import FileManagerTool, tool

set_llm(ollama_llm="wizard-vicuna-uncensored:7b", stream=True)


# Define a custom tool using the @tool decorator
@tool(name="reverse_string", description="Reverses a string.")
async def reverse_string(text: str) -> str:
    """Reverses the given text and returns it."""
    try:
        result = text[::-1]
        return f"The reversed string is: {result}"
    except Exception as e:
        return f"Error reversing string: {e}"


async def main():
    agent = Agent(
        config=AgentConfig(
            name="StringBot",
            role=AgentRole.GENERAL_PURPOSE,
            system_prompt="You are a capable agent with access to string manipulation and file tools.",
        )
    )

    # Register our custom string tool
    agent.add_tool(reverse_string)

    # Register a library built-in tool
    agent.add_tool(FileManagerTool())

    await agent.start()

    # Execute complex tasks using the ReAct loop
    # The agent will auto-select the right tools to accomplish the goal!
    print("Agent executing task: 'Reverse the string 'decentralized' and save it to result.txt'")

    answer = await agent.execute_task(
        "Reverse the string 'decentralized' and save the result into a file called result.txt"
    )
    print("\nFinal LLM Answer:\n", answer)

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
