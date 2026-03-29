# 🔴 Advanced - Bidirectional P2P Networking with Routing
# Difficulty: Advanced
# This example demonstrates bidirectional agent communication with message routing
# through intermediate nodes when direct connections don't exist.

"""
Example 09: Bidirectional P2P Networking with Routing

Demonstrates:
  - Bidirectional connections between agents (A↔B, A↔C)
  - Network topology awareness (all agents know who's connected)
  - Message routing through intermediate nodes (B→C via A)
  - Async non-blocking message handling
  - Network topology visualization

Network Configuration:
  - network_url: The URL where THIS agent is hosted (others use this to reach it)
  - network_connections: Dict of peer_id -> URL for agents THIS agent can directly reach

Network Topology:
  Agent A (NodeAlfa) ←→ Agent B (NodeBravo)
  Agent A (NodeAlfa) ←→ Agent C (NodeCharlie)
  
  - A can send directly to B and C
  - B can send directly to A
  - C can send directly to A
  - B wants to send to C → routes through A
  - C wants to send to B → routes through A
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
    print("=" * 60)
    print("  Bidirectional P2P Networking with Routing Demo")
    print("=" * 60)

    # ──────────────────────────────────────────────
    # 1. Create a shared Communication Manager
    # ──────────────────────────────────────────────
    comm = CommunicationManager()
    await comm.start()

    # ──────────────────────────────────────────────
    # 2. Configure Agent A (NodeAlfa) - Central hub
    # ──────────────────────────────────────────────
    # network_url: The URL where THIS agent is hosted (others use this to reach it)
    # network_connections: Dict of peer_id -> URL for agents THIS agent can directly reach
    config_a = AgentConfig(
        name="NodeAlfa",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are NodeAlfa, a central networking hub agent.",
        network_url="http://localhost:8000",  # This agent is hosted on localhost:8000
        network_connections={},  # Will be populated after B and C are created
    )
    agent_a = Agent(config=config_a)
    await agent_a.start(communication_manager=comm)

    # ──────────────────────────────────────────────
    # 3. Configure Agent B (NodeBravo)
    # ──────────────────────────────────────────────
    # network_url: The URL where THIS agent is hosted (others use this to reach it)
    # network_connections: Dict of peer_id -> URL for agents THIS agent can directly reach
    config_b = AgentConfig(
        name="NodeBravo",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are NodeBravo, a worker agent connected to NodeAlfa.",
        network_url="http://localhost:8001",  # This agent is hosted on localhost:8001
        network_connections={
            agent_a.id: "http://localhost:8000"  # B knows A's URL (can directly reach A)
        },
    )
    agent_b = Agent(config=config_b)
    await agent_b.start(communication_manager=comm)

    # ──────────────────────────────────────────────
    # 4. Configure Agent C (NodeCharlie)
    # ──────────────────────────────────────────────
    # network_url: The URL where THIS agent is hosted (others use this to reach it)
    # network_connections: Dict of peer_id -> URL for agents THIS agent can directly reach
    config_c = AgentConfig(
        name="NodeCharlie",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are NodeCharlie, a worker agent connected to NodeAlfa.",
        network_url="http://localhost:8002",  # This agent is hosted on localhost:8002
        network_connections={
            agent_a.id: "http://localhost:8000"  # C knows A's URL (can directly reach A)
        },
    )
    agent_c = Agent(config=config_c)
    await agent_c.start(communication_manager=comm)

    # ──────────────────────────────────────────────
    # 5. Setup bidirectional connections for A
    # ──────────────────────────────────────────────
    # A needs to know both B and C
    comm.setup_bidirectional_connection(
        agent_a.id, agent_b.id,
        url_a="http://localhost:8000",
        url_b="http://localhost:8001"
    )
    comm.setup_bidirectional_connection(
        agent_a.id, agent_c.id,
        url_a="http://localhost:8000",
        url_b="http://localhost:8002"
    )

    print(f"\n  NodeAlfa   ID: {agent_a.id}")
    print(f"  NodeBravo  ID: {agent_b.id}")
    print(f"  NodeCharlie ID: {agent_c.id}\n")

    # ──────────────────────────────────────────────
    # 6. Display Network Topology
    # ──────────────────────────────────────────────
    print("[1] Network Topology:")
    topology = comm.get_network_topology()
    print(f"    Nodes: {len(topology['nodes'])}")
    for node_id, node_info in topology['nodes'].items():
        agent_name = "Unknown"
        if node_id == agent_a.id:
            agent_name = "NodeAlfa"
        elif node_id == agent_b.id:
            agent_name = "NodeBravo"
        elif node_id == agent_c.id:
            agent_name = "NodeCharlie"
        
        connections = node_info.get('connections', {})
        print(f"    - {agent_name} ({node_id[:8]}...): {len(connections)} connections")
        for peer_id, peer_url in connections.items():
            peer_name = "Unknown"
            if peer_id == agent_a.id:
                peer_name = "NodeAlfa"
            elif peer_id == agent_b.id:
                peer_name = "NodeBravo"
            elif peer_id == agent_c.id:
                peer_name = "NodeCharlie"
            print(f"      → {peer_name} ({peer_id[:8]}...) at {peer_url}")

    # ──────────────────────────────────────────────
    # 7. Direct Bidirectional Messaging: A → B
    # ──────────────────────────────────────────────
    print("\n[2] Direct Bidirectional Messaging: NodeAlfa → NodeBravo")
    msg_a_to_b = AgentMessage(
        sender_id=agent_a.id,
        receiver_id=agent_b.id,
        content="Hello NodeBravo! This is NodeAlfa. Can you hear me?",
        message_type="text",
    )
    result = await comm.send_message(msg_a_to_b)
    print(f"    Message delivered: {result}")

    # Wait a bit for response
    await asyncio.sleep(0.5)

    # ──────────────────────────────────────────────
    # 8. Direct Bidirectional Messaging: B → A
    # ──────────────────────────────────────────────
    print("\n[3] Direct Bidirectional Messaging: NodeBravo → NodeAlfa")
    msg_b_to_a = AgentMessage(
        sender_id=agent_b.id,
        receiver_id=agent_a.id,
        content="Hello NodeAlfa! This is NodeBravo. I can hear you loud and clear!",
        message_type="text",
    )
    result = await comm.send_message(msg_b_to_a)
    print(f"    Message delivered: {result}")

    await asyncio.sleep(0.5)

    # ──────────────────────────────────────────────
    # 9. Routed Messaging: B → C (via A)
    # ──────────────────────────────────────────────
    print("\n[4] Routed Messaging: NodeBravo → NodeCharlie (via NodeAlfa)")
    print("    Note: B has no direct connection to C, so message routes through A")
    
    # Check route
    route = comm.find_route(agent_b.id, agent_c.id)
    if route:
        route_names = []
        for node_id in route:
            if node_id == agent_a.id:
                route_names.append("NodeAlfa")
            elif node_id == agent_b.id:
                route_names.append("NodeBravo")
            elif node_id == agent_c.id:
                route_names.append("NodeCharlie")
            else:
                route_names.append(node_id[:8])
        print(f"    Route found: {' → '.join(route_names)}")
    
    msg_b_to_c = AgentMessage(
        sender_id=agent_b.id,
        receiver_id=agent_c.id,
        content="Hello NodeCharlie! This is NodeBravo. I'm sending this through NodeAlfa since we're not directly connected.",
        message_type="text",
    )
    result = await comm.send_message(msg_b_to_c)
    print(f"    Message delivered: {result}")

    await asyncio.sleep(0.5)

    # ──────────────────────────────────────────────
    # 10. Routed Messaging: C → B (via A)
    # ──────────────────────────────────────────────
    print("\n[5] Routed Messaging: NodeCharlie → NodeBravo (via NodeAlfa)")
    print("    Note: C has no direct connection to B, so message routes through A")
    
    msg_c_to_b = AgentMessage(
        sender_id=agent_c.id,
        receiver_id=agent_b.id,
        content="Hello NodeBravo! This is NodeCharlie. I'm also sending through NodeAlfa!",
        message_type="text",
    )
    result = await comm.send_message(msg_c_to_b)
    print(f"    Message delivered: {result}")

    await asyncio.sleep(0.5)

    # ──────────────────────────────────────────────
    # 11. Verify Network Awareness
    # ──────────────────────────────────────────────
    print("\n[6] Network Awareness Check:")
    print("    All agents should know about the network topology...")
    
    # Check what each agent knows
    peers_a = comm.get_connected_peers(agent_a.id)
    peers_b = comm.get_connected_peers(agent_b.id)
    peers_c = comm.get_connected_peers(agent_c.id)
    
    print(f"    NodeAlfa knows {len(peers_a)} peers: {list(peers_a.keys())}")
    print(f"    NodeBravo knows {len(peers_b)} peers: {list(peers_b.keys())}")
    print(f"    NodeCharlie knows {len(peers_c)} peers: {list(peers_c.keys())}")

    # ──────────────────────────────────────────────
    # 12. Async Non-blocking Demo
    # ──────────────────────────────────────────────
    print("\n[7] Async Non-blocking Demo:")
    print("    Sending multiple messages concurrently...")
    
    # Send multiple messages concurrently
    tasks = []
    for i in range(3):
        msg = AgentMessage(
            sender_id=agent_a.id,
            receiver_id=agent_b.id,
            content=f"Concurrent message {i+1} from NodeAlfa",
            message_type="text",
        )
        tasks.append(comm.send_message(msg))
    
    results = await asyncio.gather(*tasks)
    print(f"    All {len(results)} messages sent concurrently: {all(results)}")

    # ──────────────────────────────────────────────
    # 13. Communication Stats
    # ──────────────────────────────────────────────
    print("\n[8] Communication Manager Stats:")
    stats = comm.get_communication_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # ──────────────────────────────────────────────
    # Cleanup
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Demo complete! Cleaning up...")
    print("=" * 60)

    await agent_a.stop()
    await agent_b.stop()
    await agent_c.stop()
    comm.stop()


if __name__ == "__main__":
    asyncio.run(main())
