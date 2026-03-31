# 🔴 Advanced - Multi-Node Hybrid System
# Difficulty: Advanced
# This example demonstrates the MultiNodeHybridSystem class for managing multiple hybrid nodes.

"""
Example 11: Multi-Node Hybrid System

Demonstrates:
  - Creating a MultiNodeHybridSystem with multiple hybrid nodes
  - Configuring different orchestrators on each node
  - Connecting nodes for P2P communication
  - Executing tasks on specific nodes
  - Broadcasting tasks to all nodes
  - Cross-node collaboration
"""

import asyncio
import logging

from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.core.hybrid import MultiNodeHybridSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="multi_node_hybrid.log",
    filemode="w",
)


async def main():
    """Main entry point for the multi-node hybrid system example."""
    print("\n" + "=" * 60)
    print("   MULTI-NODE HYBRID SYSTEM DEMO")
    print("=" * 60)

    # Configure LLM
    set_llm(ollama_llm="llama3.2:1b", stream=True)

    # ──────────────────────────────────────────────
    # 1. Create the Multi-Node Hybrid System
    # ──────────────────────────────────────────────
    print("\n[*] Creating Multi-Node Hybrid System...")

    system = MultiNodeHybridSystem()
    print(f"[+] Created: {system}")

    # ──────────────────────────────────────────────
    # 2. Create Research Lab Node
    # ──────────────────────────────────────────────
    print("\n[*] Creating Research Lab Node...")

    research_node = system.create_node(
        node_id="research-lab",
        node_name="AI Research Lab",
        context_name="Research Lab",
        main_role="Professor",
        sub_role="Researcher",
        resources={"gpu_count": 4, "memory_gb": 32, "specialization": "AI Research"},
    )

    # Configure research team
    professor = Agent(
        config=AgentConfig(
            name="Professor",
            role=AgentRole.COORDINATOR,
            system_prompt="You coordinate research projects and guide your research team.",
            personality="wise and methodical",
        )
    )
    research_node.set_main_agent(professor)

    researcher = Agent(
        config=AgentConfig(
            name="Researcher",
            role=AgentRole.SPECIALIZED,
            system_prompt="You conduct thorough research and gather information.",
            personality="analytical and curious",
        )
    )
    research_node.add_sub_agent(researcher)

    analyst = Agent(
        config=AgentConfig(
            name="Analyst",
            role=AgentRole.SPECIALIZED,
            system_prompt="You analyze data and identify trends.",
            personality="precise and logical",
        )
    )
    research_node.add_sub_agent(analyst)

    print(f"[+] Research Lab Node configured with {len(research_node.all_agents)} agents")

    # ──────────────────────────────────────────────
    # 3. Create Content Creation Node
    # ──────────────────────────────────────────────
    print("\n[*] Creating Content Creation Node...")

    content_node = system.create_node(
        node_id="content-creation",
        node_name="Content Creation Studio",
        context_name="Content Creation",
        main_role="Editor",
        sub_role="Creator",
        resources={"gpu_count": 2, "memory_gb": 16, "specialization": "Content Creation"},
    )

    # Configure content team
    editor = Agent(
        config=AgentConfig(
            name="Editor",
            role=AgentRole.COORDINATOR,
            system_prompt="You coordinate content creation and ensure quality.",
            personality="creative and detail-oriented",
        )
    )
    content_node.set_main_agent(editor)

    writer = Agent(
        config=AgentConfig(
            name="Writer",
            role=AgentRole.SPECIALIZED,
            system_prompt="You write clear and engaging content.",
            personality="articulate and creative",
        )
    )
    content_node.add_sub_agent(writer)

    designer = Agent(
        config=AgentConfig(
            name="Designer",
            role=AgentRole.SPECIALIZED,
            system_prompt="You create visual designs and graphics.",
            personality="visual and innovative",
        )
    )
    content_node.add_sub_agent(designer)

    print(f"[+] Content Creation Node configured with {len(content_node.all_agents)} agents")

    # ──────────────────────────────────────────────
    # 4. Create Analysis Center Node
    # ──────────────────────────────────────────────
    print("\n[*] Creating Analysis Center Node...")

    analysis_node = system.create_node(
        node_id="analysis-center",
        node_name="Data Analysis Center",
        context_name="Analysis Center",
        main_role="Lead Analyst",
        sub_role="Data Scientist",
        resources={"gpu_count": 8, "memory_gb": 64, "specialization": "Data Analysis"},
    )

    # Configure analysis team
    lead_analyst = Agent(
        config=AgentConfig(
            name="LeadAnalyst",
            role=AgentRole.COORDINATOR,
            system_prompt="You lead data analysis projects and coordinate insights.",
            personality="strategic and insightful",
        )
    )
    analysis_node.set_main_agent(lead_analyst)

    data_scientist = Agent(
        config=AgentConfig(
            name="DataScientist",
            role=AgentRole.SPECIALIZED,
            system_prompt="You perform advanced data analysis and modeling.",
            personality="analytical and precise",
        )
    )
    analysis_node.add_sub_agent(data_scientist)

    print(f"[+] Analysis Center Node configured with {len(analysis_node.all_agents)} agents")

    # ──────────────────────────────────────────────
    # 5. Connect nodes for P2P communication
    # ──────────────────────────────────────────────
    print("\n[*] Connecting nodes...")

    system.connect_nodes("research-lab", "content-creation")
    system.connect_nodes("research-lab", "analysis-center")
    system.connect_nodes("content-creation", "analysis-center")

    print("[+] All nodes connected")

    # ──────────────────────────────────────────────
    # 6. Start all nodes
    # ──────────────────────────────────────────────
    print("\n[*] Starting all nodes...")
    await system.start_all()
    print("[+] All nodes started successfully!")

    # Display system status
    status = system.get_system_status()
    print(f"\n[*] System Status:")
    print(f"  Total Nodes: {status['total_nodes']}")
    print(f"  Running: {status['is_running']}")

    for node_id, node_status in status["nodes"].items():
        print(f"\n  Node: {node_status['node_name']} (ID: {node_id})")
        print(f"    - Context: {node_status['context_name']}")
        print(f"    - Agents: {node_status['total_agents']}")
        print(f"    - Main Agent: {node_status['main_agent']}")
        print(f"    - Sub-Agents: {', '.join(node_status['sub_agents'])}")
        print(f"    - Resources: {node_status['resources']}")

    # ──────────────────────────────────────────────
    # 7. Interactive task execution
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("   INTERACTIVE MODE")
    print("=" * 60)
    print("\nCommands:")
    print("  - 'research <task>' - Execute task on Research Lab")
    print("  - 'content <task>' - Execute task on Content Creation")
    print("  - 'analysis <task>' - Execute task on Analysis Center")
    print("  - 'broadcast <task>' - Broadcast task to all nodes")
    print("  - 'status' - Show system status")
    print("  - 'exit' - Quit")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("\033[94mYou:\033[0m ").strip()

            if not user_input:
                continue

            # Handle exit command
            if user_input.lower() in ["exit", "quit"]:
                print("\n[*] Ending session...")
                break

            # Handle status command
            if user_input.lower() == "status":
                status = system.get_system_status()
                print(f"\n\033[93mSystem Status:\033[0m")
                print(f"  Running: {status['is_running']}")
                print(f"  Total Nodes: {status['total_nodes']}")
                for node_id, node_status in status["nodes"].items():
                    print(f"  - {node_id}: {node_status['total_agents']} agents")
                continue

            # Handle research command
            if user_input.lower().startswith("research "):
                task = user_input[9:].strip()
                print(f"\n\033[92mExecuting on Research Lab...\033[0m")
                result = await system.execute_task("research-lab", task)
                print(f"\n\033[93mResearch Lab Result:\033[0m")
                print(f"{result}\n")
                continue

            # Handle content command
            if user_input.lower().startswith("content "):
                task = user_input[8:].strip()
                print(f"\n\033[92mExecuting on Content Creation...\033[0m")
                result = await system.execute_task("content-creation", task)
                print(f"\n\033[93mContent Creation Result:\033[0m")
                print(f"{result}\n")
                continue

            # Handle analysis command
            if user_input.lower().startswith("analysis "):
                task = user_input[9:].strip()
                print(f"\n\033[92mExecuting on Analysis Center...\033[0m")
                result = await system.execute_task("analysis-center", task)
                print(f"\n\033[93mAnalysis Center Result:\033[0m")
                print(f"{result}\n")
                continue

            # Handle broadcast command
            if user_input.lower().startswith("broadcast "):
                task = user_input[10:].strip()
                print(f"\n\033[92mBroadcasting to all nodes...\033[0m")
                results = await system.broadcast_task(task)
                print(f"\n\033[93mBroadcast Results:\033[0m")
                for node_id, result in results.items():
                    print(f"\n  {node_id}:")
                    print(f"  {result}\n")
                continue

            # Default: show help
            print("\n\033[93mUnknown command. Available commands:\033[0m")
            print("  - 'research <task>' - Execute on Research Lab")
            print("  - 'content <task>' - Execute on Content Creation")
            print("  - 'analysis <task>' - Execute on Analysis Center")
            print("  - 'broadcast <task>' - Broadcast to all nodes")
            print("  - 'status' - Show system status")
            print("  - 'exit' - Quit")

        except KeyboardInterrupt:
            print("\n\n[*] Interrupted by user. Type 'exit' to quit.")
            continue
        except Exception as e:
            print(f"\n\033[91mError:\033[0m {e}")
            logging.error(f"Error in main loop: {e}", exc_info=True)

    # ──────────────────────────────────────────────
    # 8. Cleanup
    # ──────────────────────────────────────────────
    print("\n[*] Shutting down multi-node system...")
    await system.stop_all()
    print("[+] Multi-node system stopped successfully.")
    print("\n[*] Demo completed. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[*] Program interrupted. Goodbye!")
