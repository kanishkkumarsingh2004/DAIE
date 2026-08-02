# 🔴 Advanced - Hybrid Orchestrator Node
# Difficulty: Advanced
# This example demonstrates the HybridOrchestratorNode class for combining Node and Orchestrator architectures.

"""
Example 10: Hybrid Orchestrator Node

Demonstrates:
  - Creating a HybridOrchestratorNode that combines Node and Orchestrator
  - Automatic setup of Node, Orchestrator, and CommunicationManager
  - Resource management on the hybrid node
  - Task execution using the orchestrator
  - Intelligent message routing with AgentRouter
  - Collaborative task execution across all agents
"""

import asyncio
import logging

from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.config import SystemConfig
from daie.core.hybrid import HybridOrchestratorNode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="hybrid_node.log",
    filemode="w",
)


async def main():
    """Main entry point for the hybrid orchestrator node example."""
    print("\n" + "=" * 60)
    print("   HYBRID ORCHESTRATOR NODE DEMO")
    print("=" * 60)

    # Configure LLM
    set_llm(ollama_llm="llama3.2:1b", stream=True)

    # ──────────────────────────────────────────────
    # 1. Create the Hybrid Orchestrator Node
    # ──────────────────────────────────────────────
    print("\n[*] Creating Hybrid Orchestrator Node...")

    # Disable NATS (no NATS server is running locally).
    # Setting nats_url to an empty string / None prevents the communication
    # manager from attempting connections and avoids log spam.
    system_config = SystemConfig(nats_url="")
    comm_manager = CommunicationManager(config=system_config)

    hybrid = HybridOrchestratorNode(
        node_id="research-lab-001",
        node_name="AI Research Lab",
        context_name="Research Lab",
        main_role="Professor",
        sub_role="Researcher",
        enable_router=True,
        comm_manager=comm_manager,
        resources={
            "gpu_count": 4,
            "memory_gb": 32,
            "model_cache": {"llama3.2": True, "codellama": True},
            "max_concurrent_tasks": 10,
        },
    )

    print(f"[+] Created: {hybrid}")

    # ──────────────────────────────────────────────
    # 2. Create and set the main agent (orchestrator)
    # ──────────────────────────────────────────────
    print("\n[*] Creating main agent (Professor)...")

    professor = Agent(
        config=AgentConfig(
            name="Professor",
            role=AgentRole.COORDINATOR,
            system_prompt=(
                "You are an expert professor coordinating research projects. "
                "You answer questions directly and thoroughly. "
                "When you need to delegate work to another agent, you may use ONLY these tools: "
                "a2a_send_message (send a message to an agent), "
                "a2a_delegate_task (assign a task to an agent), "
                "a2a_send_file (send a file to an agent). "
                "Do NOT attempt to call any other tools. "
                "For mathematical calculations, compute the answer yourself and state it clearly."
            ),
            personality="wise, methodical, and encouraging",
        )
    )

    hybrid.set_main_agent(professor)
    print(f"[+] Main agent set: {professor.name}")

    # ──────────────────────────────────────────────
    # 3. Create and add sub-agents
    # ──────────────────────────────────────────────
    print("\n[*] Creating sub-agents...")

    # Researcher agent
    researcher = Agent(
        config=AgentConfig(
            name="Researcher",
            role=AgentRole.SPECIALIZED,
            system_prompt="You are a diligent research specialist. You conduct thorough research and gather comprehensive information on any topic.",
            personality="analytical, thorough, and curious",
        )
    )
    hybrid.add_sub_agent(researcher)
    print(f"[+] Added sub-agent: {researcher.name}")

    # Analyst agent
    analyst = Agent(
        config=AgentConfig(
            name="Analyst",
            role=AgentRole.SPECIALIZED,
            system_prompt="You are an expert data analyst. You analyze data, identify trends, and provide insightful interpretations.",
            personality="precise, logical, and detail-oriented",
        )
    )
    hybrid.add_sub_agent(analyst)
    print(f"[+] Added sub-agent: {analyst.name}")

    # Writer agent
    writer = Agent(
        config=AgentConfig(
            name="Writer",
            role=AgentRole.SPECIALIZED,
            system_prompt="You are a skilled technical writer. You create clear, engaging, and well-structured content.",
            personality="creative, articulate, and concise",
        )
    )
    hybrid.add_sub_agent(writer)
    print(f"[+] Added sub-agent: {writer.name}")

    # ──────────────────────────────────────────────
    # 4. Start the hybrid system
    # ──────────────────────────────────────────────
    print("\n[*] Starting hybrid system...")
    await hybrid.start()
    print("[+] Hybrid system started successfully!")

    # Display status
    status = hybrid.get_status()
    print("\n[*] System Status:")
    print(f"  - Node: {status['node_name']} (ID: {status['node_id']})")
    print(f"  - Context: {status['context_name']}")
    print(f"  - Total Agents: {status['total_agents']}")
    print(f"  - Main Agent: {status['main_agent']}")
    print(f"  - Sub-Agents: {', '.join(status['sub_agents'])}")
    print(f"  - Router: {'enabled' if status['router_enabled'] else 'disabled'}")
    print(f"  - Resources: {status['resources']}")

    # ──────────────────────────────────────────────
    # 5. Interactive task execution
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("   INTERACTIVE MODE")
    print("=" * 60)
    print("\nType your task to execute (or 'exit' to quit)")
    print("Commands:")
    print("  - 'route <message>' - Route message to best agent")
    print("  - 'collab <task>' - Execute collaborative task")
    print("  - 'status' - Show system status")
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
                status = hybrid.get_status()
                print("\n\033[93mSystem Status:\033[0m")
                print(f"  Running: {status['is_running']}")
                print(f"  Agents: {status['total_agents']}")
                print(f"  Resources: {status['resources']}")
                continue

            # Handle route command
            if user_input.lower().startswith("route "):
                message = user_input[6:].strip()
                print("\n\033[92mRouting message to best agent...\033[0m")
                response = await hybrid.route_message(message)
                print("\n\033[93mResponse:\033[0m")
                print(f"{response}\n")
                continue

            # Handle collab command
            if user_input.lower().startswith("collab "):
                task = user_input[7:].strip()
                print("\n\033[92mExecuting collaborative task...\033[0m")
                response = await hybrid.execute_collaborative_task(task)
                print("\n\033[93mCollaborative Response:\033[0m")
                print(f"{response}\n")
                continue

            # Default: execute task via orchestrator
            print("\n\033[92mProfessor is orchestrating the task...\033[0m")
            result = await hybrid.execute_task(user_input)

            # Extract answer if it still looks like JSON
            final_display = result
            if isinstance(result, str) and result.strip().startswith("{"):
                try:
                    import json

                    parsed = json.loads(result)
                    final_display = parsed.get("answer", result)
                except:
                    pass

            print("\n\033[93mFinal Answer from Professor:\033[0m")
            print(f"{final_display}\n")

            print("-" * 30 + "\n")

        except KeyboardInterrupt:
            print("\n\n[*] Interrupted by user. Type 'exit' to quit.")
            continue
        except Exception as e:
            print(f"\n\033[91mError:\033[0m {e}")
            logging.error(f"Error in main loop: {e}", exc_info=True)

    # ──────────────────────────────────────────────
    # 6. Cleanup
    # ──────────────────────────────────────────────
    print("\n[*] Shutting down hybrid system...")
    await hybrid.stop()
    print("[+] Hybrid system stopped successfully.")
    print("\n[*] Demo completed. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[*] Program interrupted. Goodbye!")
