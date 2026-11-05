import asyncio
import os
import shutil
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole, Parliament, HybridParliamentOrchestrator, OrchestratorAgent
from daie.memory.sqlite_storage import SQLiteStorage
from daie.communication import CommunicationManager

# 1. Setup global LLM
# Note: In a production environment, use a larger model for synthesis
set_llm(ollama_llm="llama3.2:1b", stream=True)


async def grand_demo():
    print("🚀 Starting Grand DAIE Integration Demo...")
    print("--- Persistent Shared Memory + Distributed Parliament + Hybrid Orchestration ---\n")

    # Cleanup previous demo runs
    demo_db_path = "./grand_demo_memory"
    if os.path.exists(demo_db_path):
        shutil.rmtree(demo_db_path)

    # 2. Setup Persistent Memory Manager with SQLite
    # This will be shared across all agents in the namespace 'grand_consortium'
    storage = SQLiteStorage()
    storage.initialize(demo_db_path)

    # Communication manager for distributed parliament
    comm = CommunicationManager()
    await comm.start()

    # We'll inject this namespace into our configurations
    shared_namespace = "autonomous_consortium_001"

    # 3. Create Parliament of specialized agents
    # They will deliberate on a complex strategic problem
    coder = Agent(
        config=AgentConfig(
            name="LeadArchitect",
            role=AgentRole.SPECIALIZED,
            memory_namespace=shared_namespace,
        )
    )
    security = Agent(
        config=AgentConfig(
            name="SecurityChief", role=AgentRole.SECURITY_AUDITOR, memory_namespace=shared_namespace
        )
    )
    manager = Agent(
        config=AgentConfig(
            name="ProductManager", role=AgentRole.GENERAL_PURPOSE, memory_namespace=shared_namespace
        )
    )

    # Initialize Parliament with max 2 review rounds for speed in demo
    parliament = Parliament(
        sub_agents=[coder, security, manager],
        max_review_rounds=2,
        distributed=False,  # Local execution for demo
        communication_manager=comm,
        distributed_timeout=10,
    )

    # 4. Create Orchestrator for execution
    # This agent will carry out the plan synthesized by the Parliament
    executor_boss = OrchestratorAgent(
        config=AgentConfig(
            name="ExecutionDirector", role=AgentRole.COORDINATOR, memory_namespace=shared_namespace
        )
    )

    # Simple hybrid pipeline
    pipeline = HybridParliamentOrchestrator(
        parliament=parliament,
        orchestrator=executor_boss,
        min_confidence_threshold=10.0,  # Lower threshold for demo
    )

    # 5. Start the system
    # All agents will be registered to the same communication bus automatically
    print("--- System Online. Starting deliberation phase ---")

    task = (
        "Design a secure P2P file-sharing protocol for DAIE agents "
        "and outline the Python classes required."
    )

    # The pipeline will:
    # 1. Deliberate via Parliament (with peer review)
    # 2. Synthesize a Roadmap
    # 3. Use Orchestrator to begin execution/detailing
    result = await pipeline.execute(task)

    print("\n\n--- Final Pipeline Result ---")
    print(result)

    # 6. Verify Persistence and Shared Memory
    print("\n--- Verifying Persistent Memory in SQLite ---")
    # We can create a new agent pointing to the same namespace and see if it can 'remember'
    from daie.memory import MemoryManager
    from daie.config import SystemConfig
    
    memory_manager = MemoryManager(config=SystemConfig(persistent_memory=True, memory_storage_type="binary", memory_root_path=demo_db_path))
    memory_manager.start()
    
    new_auditor = Agent(
        config=AgentConfig(name="PostAuditAgent", memory_namespace=shared_namespace)
    )
    await new_auditor.start(communication_manager=comm, memory_manager=memory_manager)

    # Check what's in the shared memory
    memories = new_auditor.memory_manager.retrieve_memories(
        new_auditor.id, memory_type="episodic", namespace=shared_namespace
    )

    print(
        f"PostAuditAgent found {len(memories)} items in the shared namespace '{shared_namespace}'."
    )
    if memories:
        print(f"Sample content from shared memory: {memories[0].content[:100]}...")

    # 7. Cleanup
    await new_auditor.stop()
    memory_manager.stop()
    await coder.stop()
    await security.stop()
    await manager.stop()
    await executor_boss.stop()
    await comm.stop()
    await security.stop()
    await manager.stop()
    await executor_boss.stop()

    print("\n✅ Demo Complete!")


if __name__ == "__main__":
    asyncio.run(grand_demo())
