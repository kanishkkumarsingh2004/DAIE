"""
Example 14: Complex Container Mesh Architecture

This example demonstrates how to use the `NetworkBlock` container to build a complex
decentralized mesh architecture. We create a "Research & Publishing Ecosystem"
where different nodes (Blocks) have different specialized architectures and 
are connected via graph-like 'edges'.

Architecture:
1. Research Lab (Hybrid Node): Coordinates research tasks.
2. Data Analyst (Standalone Agent): Performs deep data analysis.
3. Content Writer (Standalone Agent): Formats findings into reports.

Topology:
Research Lab <---> Data Analyst <---> Content Writer
      ^                                     |
      └─────────────────────────────────────┘
(A bidirectional mesh where each node knows its neighbors)
"""

import os
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.container import NetworkBlock
from daie.core.hybrid import HybridOrchestratorNode

# Optional: Set your LLM preference
set_llm(ollama_llm="llama3.2:1b")

def create_research_mesh():
    print("=== Building Complex Container Mesh ===")

    # -------------------------------------------------------------------------
    # 1. Setup Node A: The Research Lab (Hybrid Architecture)
    # -------------------------------------------------------------------------
    # This node uses a HybridOrchestratorNode which manages multiple internal agents.
    lab_node = HybridOrchestratorNode(
        node_id="research-lab-01",
        node_name="Global Research Lab",
        context_name="Scientific Research"
    )
    
    professor = Agent(config=AgentConfig(
        name="Professor X",
        role=AgentRole.COORDINATOR,
        system_prompt="You coordinate research projects and delegate data to the analyst."
    ))
    researcher = Agent(config=AgentConfig(
        name="Researcher Alpha",
        role=AgentRole.RESEARCHER,
        system_prompt="You gather raw facts and data."
    ))
    
    lab_node.set_main_agent(professor)
    lab_node.add_sub_agent(researcher)

    # -------------------------------------------------------------------------
    # 2. Setup Node B: The Data Analyst (Standalone Agent)
    # -------------------------------------------------------------------------
    analyst_agent = Agent(config=AgentConfig(
        name="Analyst Prime",
        role=AgentRole.ANALYZER,
        system_prompt="You receive raw research and identify complex patterns."
    ))

    # -------------------------------------------------------------------------
    # 3. Setup Node C: The Publisher (Standalone Agent)
    # -------------------------------------------------------------------------
    writer_agent = Agent(config=AgentConfig(
        name="Lead Writer",
        role=AgentRole.ASSISTANT,
        system_prompt="You turn analyzed data into professional blog posts."
    ))

    # -------------------------------------------------------------------------
    # 4. Containerize into Blocks with 'Edges' (Graph Topology)
    # -------------------------------------------------------------------------
    
    # NetworkBlock A: The Lab (Coordinator)
    # It knows about the Analyst.
    lab_block = NetworkBlock(
        architecture=lab_node,
        host="0.0.0.0",
        port=8000,
        chat=False,  # Run as network server
        edges=["http://localhost:8001"] # Connected to Analyst
    )

    # NetworkBlock B: The Analyst
    # It knows about the Lab (to send questions) and the Writer (to send results).
    analyst_block = NetworkBlock(
        architecture=analyst_agent,
        host="0.0.0.0",
        port=8001,
        chat=False,
        edges=["http://localhost:8000", "http://localhost:8002"]
    )

    # NetworkBlock C: The Writer
    # It knows about the Lab (to confirm publishing).
    writer_block = NetworkBlock(
        architecture=writer_agent,
        host="0.0.0.0",
        port=8002,
        chat=True,  # Let's run this one in CHAT mode for the user to interact
        edges=["http://localhost:8000"]
    )

    print(f"\n[Mesh Topology Created]")
    print(f"Node A (Lab)     : Port 8000 -> Edges: {lab_block.edges}")
    print(f"Node B (Analyst) : Port 8001 -> Edges: {analyst_block.edges}")
    print(f"Node C (Writer)  : Port 8002 -> Edges: {writer_block.edges} (Chat Mode Active)")
    
    print("\nIn a production environment, you would run each network_block in its own process/container:")
    print("  - lab_block.run()")
    print("  - analyst_block.run()")
    print("  - writer_block.run()")
    
    print("\nStarting Node C (Writer) in Chat Mode for demonstration...")
    writer_block.run()

if __name__ == "__main__":
    create_research_mesh()
