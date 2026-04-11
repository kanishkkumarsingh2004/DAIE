"""
Hybrid Parliament Orchestrator Demo.

Demonstrates the ultimate combination of two powerful architectures:
1. The Parliament: A mixture-of-agents setup that debates abstract tasks to reach a definitive consensus roadmap.
2. The Orchestrator: Takes the finalized parliament roadmap and actually assigns/delegates sub-agents to execute it.
"""

from daie import Agent, AgentConfig, AgentRole
from daie.agents import Parliament, OrchestratorAgent, HybridParliamentOrchestrator

# Ensure the mock or real LLM is set
from daie.core import set_llm

set_llm(ollama_llm="llama3.2")

# --- 1. Construct the Parliament Assembly ---
# These agents debate and construct the plan
architect_config = AgentConfig(
    name="Architect",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a Software Architect. Plan structurally.",
)
researcher_config = AgentConfig(
    name="Researcher",
    role=AgentRole.RESEARCHER,
    system_prompt="You are a Data Researcher. Prioritize information gathering.",
)
manager_config = AgentConfig(
    name="Manager",
    role=AgentRole.GENERAL_PURPOSE,
    system_prompt="You are a Product Manager. Prioritize timeline and feasibility.",
)

parliament_agents = [
    Agent(config=architect_config),
    Agent(config=researcher_config),
    Agent(config=manager_config),
]

# We let the Architect be the speaker/synthesizer
parliament = Parliament(
    sub_agents=parliament_agents, speaker=parliament_agents[0], max_review_rounds=2
)

# --- 2. Construct the Orchestrator ---
# This agent takes the Parliament's plan and executes it by calling tools
orchestrator = OrchestratorAgent()

# --- 3. Bind them into the Hybrid Pipeline ---
# Enforce a 60% minimum consensus confidence to prevent the Orchestrator from chasing bad plans
hybrid_pipeline = HybridParliamentOrchestrator(
    parliament=parliament, orchestrator=orchestrator, min_confidence_threshold=60.0
)

# --- 4. Launch the integrated Chat Loop ---
from daie.chat import HybridParliamentChatConfig

config = HybridParliamentChatConfig(hybrid_pipeline=hybrid_pipeline)

print("\n🚀 Hybrid Pipeline successfully assembled!")
print("Here are some complex strategic tasks you could try entering:")
print(" - 'Analyze the financial impact of the Indian Budget 2026 on the tech sector.'")
print(" - 'Design a decentralized P2P network protocol and document the execution steps.'")
print(" - 'Write a full-stack React app that integrates with an external LLM provider.'\n")

# Launches the interactive loop (auto-starts all sub-agents and the orchestrator under the hood)
config.run()
