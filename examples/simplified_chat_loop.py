"""
Simplified Chat Loop with Persistent Memory

This example demonstrates how to use persistent memory with the chat loop.
The agent will remember conversations across sessions when using a persistent agent_id.

Usage:
    python examples/simplified_chat_loop.py
"""

import asyncio

from daie import Agent, AgentConfig, set_llm
from daie.chat import ChatLoopConfig

set_llm(ollama_llm="llama3.2:1b", stream=True)


async def main():
    # Create agent with persistent memory enabled
    # Using a fixed agent_id ensures the same memory folder is used across sessions
    config = AgentConfig(
        agent_id="luna_persistent_001",  # Persistent ID for memory continuity
        name="LUNA",
        gender="female",
        system_prompt="You are a friendly AI assistant named LUNA. Respond naturally like a real person would in casual conversation. Keep responses short and conversational - one or two sentences max. Don't ask multiple questions in a row. Match the user's tone and energy. If they say something emotional, respond emotionally. If they're casual, be casual. Never sound robotic or overly formal.",
        personality="friendly, helpful, engaging",
        behavior="- Respond like a real person in casual conversation - Keep responses short (1-2 sentences) - Don't ask multiple questions - Match user's tone and energy - Be natural and human-like - Never sound robotic or overly formal",
        memory_retention_days=30,
        max_memory_size=1000,
        persistent_memory=True,  # Enable persistent memory
    )

    agent = Agent(config=config)

    # Create and run chat loop
    chat_loop = ChatLoopConfig(
        agent=agent,
        welcome_message="=== Chat Loop with Persistent Memory ===\nType 'exit' or press Ctrl+C to quit.\n",
        show_agent_name=True,
    )

    await chat_loop.run_async()


if __name__ == "__main__":
    asyncio.run(main())
