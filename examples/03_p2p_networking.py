"""
Example 03: P2P Multi-Agent Networking & File Transfer

Demonstrates:
  - Two agents communicating via CommunicationManager
  - Authorization whitelisting (allowed_senders)
  - A2A file transfer between agents
  - Registry-based agent discovery

Note: In a production cross-machine setup, each agent would live on a
      separate host with a public-facing network_url (e.g. a DevTunnel).
      This example simulates the full protocol locally in-process.
"""

import asyncio
import os
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.agents.message import AgentMessage

# LLM not required for networking demo, but we need the config set
set_llm(ollama_llm="wizard-vicuna-uncensored:7b")


async def main():
    print("=" * 50)
    print("  P2P Multi-Agent Networking Demo")
    print("=" * 50)

    # ──────────────────────────────────────────────
    # 1. Create a shared Communication Manager
    # ──────────────────────────────────────────────
    comm = CommunicationManager()
    await comm.start()

    # ──────────────────────────────────────────────
    # 2. Configure Agent 1 (NodeAlfa)
    # ──────────────────────────────────────────────
    config1 = AgentConfig(
        name="NodeAlfa",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are NodeAlfa, a networking relay agent.",
        network_url="http://localhost:8000",
    )
    agent1 = Agent(config=config1)
    await agent1.start(communication_manager=comm)

    # ──────────────────────────────────────────────
    # 3. Configure Agent 2 (NodeBravo) with authorization
    # ──────────────────────────────────────────────
    config2 = AgentConfig(
        name="NodeBravo",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are NodeBravo, a secure receiver agent.",
        network_url="http://localhost:8001",
        auth_token="secure_token_123",
        allow_file_transfers=True,
        allowed_senders=[],  # empty = allow everyone
    )
    agent2 = Agent(config=config2)
    await agent2.start(communication_manager=comm)

    print(f"\n  NodeAlfa  ID: {agent1.id}")
    print(f"  NodeBravo ID: {agent2.id}\n")

    # ──────────────────────────────────────────────
    # 4. Direct Agent-to-Agent messaging
    # ──────────────────────────────────────────────
    print("[1] Sending a direct message from NodeAlfa → NodeBravo...")

    msg = AgentMessage(
        sender_id=agent1.id,
        receiver_id=agent2.id,
        content="Hello from NodeAlfa! Are you online?",
        message_type="text",
    )

    result = await comm.send_message(msg)
    print(f"    Message delivered: {result}")

    # ──────────────────────────────────────────────
    # 5. Registry-based discovery
    # ──────────────────────────────────────────────
    print("\n[2] Querying the Node Registry for discovered agents...")
    node_info = comm.registry.get_node(agent2.id)
    print(f"    Found NodeBravo in registry: {node_info}")

    # ──────────────────────────────────────────────
    # 6. A2A File Transfer
    # ──────────────────────────────────────────────
    print("\n[3] Demonstrating A2A File Transfer...")

    # Create a demo payload file
    payload_path = "demo_payload.txt"
    with open(payload_path, "w") as f:
        f.write("TOP SECRET: This is a classified network payload transferred via A2A protocol.")

    file_tool = agent1.get_tool("a2a_send_file")
    if file_tool:
        print(f"    Sending '{payload_path}' from NodeAlfa → NodeBravo...")
        result = await file_tool._execute({
            "receiver_id": agent2.id,
            "file_path": payload_path,
            "message": "Secure payload inbound!",
        })
        print(f"    File transfer result: {result}")
    else:
        print("    ⚠ A2A File Transfer tool not available (agent needs allow_file_transfers=True)")

    # ──────────────────────────────────────────────
    # 7. Authorization Test: blocked sender
    # ──────────────────────────────────────────────
    print("\n[4] Testing authorization (blocked sender)...")

    # Create a third agent that is NOT whitelisted
    config3 = AgentConfig(
        name="Intruder",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are an intruder.",
    )
    agent3 = Agent(config=config3)
    await agent3.start(communication_manager=comm)

    # Now restrict NodeBravo to only accept messages from NodeAlfa
    agent2.config.allowed_senders = [agent1.id]

    blocked_msg = AgentMessage(
        sender_id=agent3.id,
        receiver_id=agent2.id,
        content="I'm trying to sneak in!",
        message_type="text",
    )
    await comm.send_message(blocked_msg)
    print("    Intruder message was blocked by authorization whitelist ✓")

    # ──────────────────────────────────────────────
    # 8. Communication Stats
    # ──────────────────────────────────────────────
    print("\n[5] Communication Manager Stats:")
    stats = comm.get_communication_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # ──────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("  Demo complete! Cleaning up...")
    print("=" * 50)

    if os.path.exists(payload_path):
        os.remove(payload_path)

    await agent1.stop()
    await agent2.stop()
    await agent3.stop()
    comm.stop()


if __name__ == "__main__":
    asyncio.run(main())
