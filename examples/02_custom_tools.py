# 🟡 Intermediate - Custom Tools Example
# Difficulty: Intermediate
# This example demonstrates custom @tool decorator + FileManagerTool with ReAct agent loop.

import asyncio

from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.tools import FileManagerTool, tool

set_llm(ollama_llm="wizard-vicuna-uncensored:7b", stream=True)


# Define a custom tool using the @tool decorator
@tool(name="calculate_math", description="Evaluate a basic math expression.")
async def calculate_math(expression: str) -> str:
    """Evaluates a math expression and returns the result."""
    try:
        # NOTE: eval is used here simply for demonstration purposes
        result = eval(expression)
        return f"The math result is: {result}"
    except Exception as e:
        return f"Error computing math: {e}"


async def main():
    agent = Agent(
        config=AgentConfig(
            name="MathBot",
            role=AgentRole.GENERAL_PURPOSE,
            system_prompt="You are a capable agent with access to math and file tools.",
        )
    )

    # Register our custom math tool
    agent.add_tool(calculate_math)

    # Register a library built-in tool
    agent.add_tool(FileManagerTool())

    await agent.start()

    # Execute complex tasks using the ReAct loop
    # The agent will auto-select the right tools to accomplish the goal!
    print("Agent executing task: 'Calculate 25 * 14 and save it to result.txt'")

    answer = await agent.execute_task(
        "Calculate 25 * 14 and save the result into a file called result.txt"
    )
    print("\nFinal LLM Answer:\n", answer)

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
