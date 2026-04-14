# Getting Started with the Decentralized AI Ecosystem (DAIE)

Welcome to the **Decentralized AI Ecosystem (DAIE)**—a high-performance, production-ready framework designed for building autonomous, tool-capable AI agents that can deliberate, coordinate, and execute complex tasks across a decentralized network.

---

## 🚀 Installation

DAIE requires **Python 3.10+**. We recommend using a virtual environment.

```bash
pip install daie
```

### Optional Extras
Tailor your installation for specific environments:

```bash
pip install "daie[dev]"      # Full development suite (pytest, mypy, black)
pip install "daie[docs]"     # Documentation generators (Sphinx, RTD)
pip install "daie[all]"      # Every dependency for maximum capability
```

**Core Dependencies:** `pydantic`, `nats-py`, `websockets`, `uvicorn`, `kademlia`, `numpy`, `pyyaml`, `selenium`.

---

## 🔥 Quick Start

### 1. The Autonomous Agent
Create a specialized agent with a distinct persona and streaming capabilities.

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole

# Global LLM configuration (Ollama, OpenAI, Anthropic, etc.)
set_llm(ollama_llm="llama3.2:latest", stream=True)

async def main():
    agent = Agent(config=AgentConfig(
        name="Oracle",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a high-level strategic intelligence.",
        personality="analytical, precise, and visionary",
        behavior="uses structured logic and occasional metaphors",
        temperature=0.7
    ))
    
    await agent.start()
    
    # Direct streaming chat
    response = await agent.send_message("What is the future of decentralized coordination?")
    
    await agent.stop()

asyncio.run(main())
```

### 2. High-Stakes consensus: The Parliament
When a task is too complex for a single mind, use the **Parliament** architecture for peer-reviewed deliberation.

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents.parliament import Parliament

async def run_parliament():
    # Define a panel of experts
    experts = [
        Agent(config=AgentConfig(name="Strategist", goal="Focus on long-term implications")),
        Agent(config=AgentConfig(name="Technician", goal="Focus on feasibility and implementation")),
        Agent(config=AgentConfig(name="Ethicist", goal="Focus on safety and human alignment"))
    ]
    
    # Initialize the assembly
    assembly = Parliament(sub_agents=experts)
    await assembly.start()
    
    # Multi-round peer review for a refined answer
    result = await assembly.deliberate("Design a global resource distribution algorithm.")
    
    print(f"Consensus Answer: {result['final_answer']}")
    print(f"Confidence Level: {result['consensus_confidence']}%")
    
    await assembly.stop()

# asyncio.run(run_parliament())
```

### 3. The Hybrid Pipeline: "Deliberate then Delegate"
Bridges the gap between deep strategic thinking and active execution by combining a **Parliament** with an **Orchestrator**.

```python
from daie.agents.hybrid_parliament import HybridParliamentOrchestrator
from daie.agents.orchestrator import OrchestratorAgent

async def run_hybrid():
    # 1. Setup the 'Think Tank' (Parliament)
    assembly = Parliament(sub_agents=[...]) 
    
    # 2. Setup the 'Ops Hub' (Orchestrator)
    ops_manager = OrchestratorAgent(config=AgentConfig(name="OpsManager"))
    
    # 3. Connect them via the Hybrid Pipeline
    pipeline = HybridParliamentOrchestrator(
        parliament=assembly,
        orchestrator=ops_manager
    )
    
    # Parliament deliberates on the roadmap -> Orchestrator executes sub-tasks
    final_output = await pipeline.execute("Establish a secure P2P node mesh across 3 regions.")
    print(final_output)
```

---

## 🌐 Core Concepts

### 🧠 The ReAct Loop
DAIE agents operate on a **Reasoning + Acting** loop. They don't just guess; they observe their environment, reason about the next step, select the appropriate tool, and iterate until the objective is achieved.

### 🎭 Agent Personas
Personas are not just cosmetic. They influence the **Reasoning** phase, allowing you to create agents with different risk profiles, expertise areas, and communication styles.

### 📡 P2P Networking
Every DAIE agent can act as a **Node** in a decentralized network. They communicate via encrypted protocols, sharing knowledge and delegating tasks across the mesh without a central server.

---

## 🛠 Command Line Interface

DAIE comes with a powerful CLI for managing agents and the ecosystem directly.

```bash
# Initialize the system configuration
daie core init

# Start the central core system
daie core start --background

# Create a new agent via an interactive wizard
daie agent create

# List all configured agents
daie agent list

# Check the status of the core system
daie core status
```

---

## 📚 Next Steps

- **[Agents Guide](agents.md)**: Deep dive into agent configuration and lifecycle.
- **[Tool Registry](tools.md)**: Learn how to give your agents "hands" to interact with the world.
- **[Parliament Architecture](parliament.md)**: Master the art of multi-agent deliberation.
- **[RAG & Memory](rag.md)**: Implementing persistent knowledge bases.
- **[Networking](communication.md)**: Setup multi-node decentralized clusters.
