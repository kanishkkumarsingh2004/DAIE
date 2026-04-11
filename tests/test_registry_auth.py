import asyncio

from daie.agents import Agent, AgentConfig
from daie.agents.message import AgentMessage
from daie.communication import CommunicationManager
from daie.registry import NodeRegistry


async def test_registry():
    print("--- Testing NodeRegistry ---")
    registry = NodeRegistry("test_registry.json")

    # Register agents
    registry.register_node("agent_math", {"role": "calculator", "skills": ["math", "add"]})
    registry.register_node("agent_search", {"role": "searcher", "skills": ["web", "scrape"]})

    # Discover
    math_agents = registry.discover_agents("math")
    print(f"Discovered math agents: {[a['agent_id'] for a in math_agents]}")
    assert len(math_agents) == 1 and math_agents[0]["agent_id"] == "agent_math"

    search_agents = registry.discover_agents("search")
    print(f"Discovered search agents: {[a['agent_id'] for a in search_agents]}")
    assert len(search_agents) == 1 and search_agents[0]["agent_id"] == "agent_search"

    # Deregister
    registry.deregister_node("agent_math")
    math_agents_after = registry.discover_agents("math")
    assert len(math_agents_after) == 0
    print("Deregistration successful.")


async def test_auth():
    print("\n--- Testing Authorization (allowed_senders) ---")
    comm = CommunicationManager()
    await comm.start()

    # Agent 1 (Open)
    config1 = AgentConfig(name="OpenAgent", allowed_senders=[])
    agent1 = Agent(config=config1)
    agent1.id = "agent1"

    # Agent 2 (Restricted to Agent 1)
    config2 = AgentConfig(name="SecureAgent", allowed_senders=["agent1"])
    agent2 = Agent(config=config2)
    agent2.id = "agent2"

    # Agent 3 (Malicious / Unauthorized)
    config3 = AgentConfig(name="MaliciousAgent", allowed_senders=[])
    agent3 = Agent(config=config3)
    agent3.id = "agent3"

    # Register agents to communication manager
    agent1.communication_manager = comm
    agent2.communication_manager = comm
    agent3.communication_manager = comm

    comm.register_agent(agent1)
    comm.register_agent(agent2)
    comm.register_agent(agent3)

    # We will track messages received via a custom handler
    received = []
    agent2.set_message_handler(lambda msg: received.append(msg))

    # Agent 1 sends to Agent 2 (Should succeed)
    msg_valid = AgentMessage(
        sender_id="agent1", receiver_id="agent2", content="Hello from 1", message_type="text"
    )
    await comm.send_message(msg_valid)

    # Agent 3 sends to Agent 2 (Should fail/block)
    msg_invalid = AgentMessage(
        sender_id="agent3", receiver_id="agent2", content="Hello from 3", message_type="text"
    )
    await comm.send_message(msg_invalid)

    # Allow async handling to process
    await asyncio.sleep(0.5)

    print(f"Agent 2 received {len(received)} messages.")
    for m in received:
        print(f" -> From: {m.sender_id}, Content: {m.content}")

    assert len(received) == 1
    assert received[0].sender_id == "agent1"

    await comm.stop()


async def test_mdns_discovery():
    print("\n--- Testing mDNS Discovery ---")
    registry = NodeRegistry("test_registry.json", enable_mdns=True, enable_dht=False)
    await registry.start()

    # Register agent with network URL
    registry.register_node(
        "agent_mdns", {"role": "test", "skills": ["mdns"]}, network_url="http://localhost:8000"
    )

    # Discover via mDNS
    discovered = registry.discover_agents_mdns(timeout=1.0)
    print(f"Discovered via mDNS: {[a['agent_id'] for a in discovered]}")

    # Cleanup
    await registry.stop()
    print("mDNS discovery test completed.")


async def test_dht_discovery():
    print("\n--- Testing DHT Discovery ---")
    registry = NodeRegistry("test_registry.json", enable_mdns=False, enable_dht=True, dht_port=8469)
    await registry.start()

    # Register agent with network URL
    registry.register_node(
        "agent_dht", {"role": "test", "skills": ["dht"]}, network_url="http://localhost:8001"
    )

    # Wait for DHT propagation
    await asyncio.sleep(1.0)

    # Discover via DHT
    discovered = await registry.discover_agents_dht(["agent_dht"])
    print(f"Discovered via DHT: {[a['agent_id'] for a in discovered]}")

    # Cleanup
    await registry.stop()
    print("DHT discovery test completed.")


async def main():
    await test_registry()
    await test_auth()
    await test_mdns_discovery()
    await test_dht_discovery()
    import os

    if os.path.exists("test_registry.json"):
        os.remove("test_registry.json")


if __name__ == "__main__":
    asyncio.run(main())
