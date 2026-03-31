"""
Test Memory Persistence

This script tests that memory persistence works correctly across sessions.
It simulates two chat sessions with the same agent_id to verify that
the agent remembers information from the first session.

Usage:
    python examples/test_memory_persistence.py
"""

import asyncio
import os
import shutil

from daie import Agent, AgentConfig


async def test_memory_persistence():
    """Test that memory persists across sessions"""

    # Clean up any existing memory for this test
    memory_path = "./agent_memory/test_persistent_agent"
    if os.path.exists(memory_path):
        shutil.rmtree(memory_path)
        print(f"Cleaned up existing memory at: {memory_path}")

    print("\n" + "=" * 60)
    print("SESSION 1: Storing information")
    print("=" * 60)

    # Session 1: Create agent and store information
    config1 = AgentConfig(
        name="LUNA",
        agent_id="test_persistent_agent",  # Persistent ID
        system_prompt="You are a friendly AI assistant named LUNA. Respond naturally like a real person would in casual conversation. Keep responses short and conversational - one or two sentences max. Don't ask multiple questions in a row. Match the user's tone and energy. If they say something emotional, respond emotionally. If they're casual, be casual. Never sound robotic or overly formal.",
        persistent_memory=True,
    )

    agent1 = Agent(config=config1)

    # Start the agent to initialize memory manager
    await agent1.start()

    # Store some information
    print("\nUser: hi my name is kanishk")
    response1 = await agent1.send_message("hi my name is kanishk")
    print(f"LUNA: {response1}")

    print("\nUser: what is your name")
    response2 = await agent1.send_message("what is your name")
    print(f"LUNA: {response2}")

    # Stop the agent
    await agent1.stop()

    print("\n" + "=" * 60)
    print("SESSION 2: Retrieving information")
    print("=" * 60)

    # Session 2: Create a new agent instance with the same agent_id
    config2 = AgentConfig(
        name="LUNA",
        agent_id="test_persistent_agent",  # Same persistent ID
        system_prompt="You are a friendly AI assistant named LUNA. Respond naturally like a real person would in casual conversation. Keep responses short and conversational - one or two sentences max. Don't ask multiple questions in a row. Match the user's tone and energy. If they say something emotional, respond emotionally. If they're casual, be casual. Never sound robotic or overly formal.",
        persistent_memory=True,
    )

    agent2 = Agent(config=config2)

    # Start the agent to load existing memories
    await agent2.start()

    # Ask for the stored information
    print("\nUser: what is my name")
    response3 = await agent2.send_message("what is my name")
    print(f"LUNA: {response3}")

    # Check if the agent remembered the name
    if "kanishk" in response3.lower():
        print("\n✅ SUCCESS: Agent remembered the user's name!")
    else:
        print("\n❌ FAILURE: Agent did not remember the user's name")
        print(f"Expected 'kanishk' in response, got: {response3}")

    # Stop the agent
    await agent2.stop()

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_memory_persistence())
