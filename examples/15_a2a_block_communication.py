"""
Example 15: Agent-to-Agent (A2A) NetworkBlock Communication

This example demonstrates how a simple agent in one NetworkBlock can communicate with
an orchestrator in another NetworkBlock using the A2A protocol.

Architecture:
1. Orchestrator NetworkBlock (Port 8000): A Hybrid Node with multiple sub-agents.
2. Visitor NetworkBlock (Port 8001): A simple agent that wants to query the Orchestrator.

The 'Visitor' will use its auto-equipped A2A tools to ask the 'Orchestrator'
about its internal state.
"""

import multiprocessing
import time
import os
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.container import NetworkBlock
from daie.core.hybrid import HybridOrchestratorNode

# Configure your LLM here
set_llm(ollama_llm="llama3.2:1b", stream=True)

def run_server_node(network_block):
    """Function to run a network_block as a background server."""
    network_block.run()

def main():
    print("=== Setting up A2A NetworkBlock Communication ===")

    # -------------------------------------------------------------------------
    # 1. Setup Node A: The Orchestrator (Hybrid Node)
    # -------------------------------------------------------------------------
    # We give the main agent a fixed ID so the visitor knows who to call
    orch_main_agent = Agent(config=AgentConfig(
        agent_id="central-boss",
        name="Boss",
        role=AgentRole.COORDINATOR
    ))

    orch_node = HybridOrchestratorNode(
        node_id="main-orch-node",
        node_name="Central Orchestrator"
    )
    orch_node.set_main_agent(orch_main_agent)

    # Give it 3 sub-agents to make the count interesting
    for i in range(3):
        orch_node.add_sub_agent(Agent(config=AgentConfig(name=f"Worker-{i+1}")))
    
    # Wrap in a NetworkBlock
    orch_block = NetworkBlock(
        architecture=orch_node,
        port=8000,
        chat=False
    )

    # -------------------------------------------------------------------------
    # 2. Setup Node B: The Visitor (Simple Agent)
    # -------------------------------------------------------------------------
    visitor_agent = Agent(config=AgentConfig(
        agent_id="visitor-agent",
        name="NetworkExplorer",
        role=AgentRole.ASSISTANT,
        system_prompt="You are a network explorer. You use your A2A tools to gather info from other nodes."
    ))
    
    # Manually map the ID in the agent's connection pool BEFORE network_block init
    # so it gets injected into the system prompt knowledge
    visitor_agent.config.network_connections["central-boss"] = "http://localhost:8000"

    # Wrap in a NetworkBlock and point an 'edge' to the Orchestrator
    # We map the specific agent ID to its URL in the edges
    visitor_block = NetworkBlock(
        architecture=visitor_agent,
        port=8001,
        chat=True, # We will chat with this one
        edges=["http://localhost:8000"] 
    )

    print("\n[Topology Summary]")
    print(f"Node A (Orchestrator): http://localhost:8000 (Internal agents: 4)")
    print(f"Node B (Visitor)     : http://localhost:8001 (Connected to Node A)")

    # -------------------------------------------------------------------------
    # 3. Execution Logic
    # -------------------------------------------------------------------------
    print("\nStarting Orchestrator in background...")
    p = multiprocessing.Process(target=run_server_node, args=(orch_block,))
    p.daemon = True
    p.start()
    
    # Give the server a moment to boot
    time.sleep(3)

    print("\nStarting Visitor Chat Loop.")
    print("TRY THIS: Ask 'Use your A2A tool to ask agent 'central-boss' how many agents are in their node.'")
    
    try:
        visitor_block.run()
    except KeyboardInterrupt:
        print("\nStopping mesh...")
    finally:
        p.terminate()

if __name__ == "__main__":
    main()
