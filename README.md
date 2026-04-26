# 🚀 DAIE — Decentralized AI Ecosystem

**Build autonomous AI agents that reason, use tools, communicate over P2P networks, and stream responses — powered by any LLM**

*The lightweight, offline-first alternative to LangChain for building production-ready AI agents*

---

## Why DAIE?

| Feature | DAIE | LangChain | CrewAI |
|---------|------|-----------|--------|
| **Offline-first** | ✅ Full Ollama support | ❌ Cloud-dependent | ❌ Cloud-dependent |
| **P2P Networking** | ✅ Decentralized / No Central Server | ❌ No | ❌ No |
| **Parallel Execution**| ✅ Smart Concurrency Controller | ⚠️ Complex/Manual | ⚠️ Basic |
| **Persistent Memory** | ✅ SQLite/Vector + Shared Namespaces | ⚠️ Manual Storage | ⚠️ Limited |
| **Peer Review** | ✅ MoA / Parliament Consensus | ❌ No | ❌ No |
| **Intelligent Routing** | ✅ Content-aware Agent Selection | ❌ No | ❌ No |
| **Temporal Context** | ✅ Native Date/Time Awareness | ❌ No | ❌ No |
| **Agent Personas** | ✅ Gender, Personality, Behavior | ❌ Limited | ❌ Limited |
| **File Transfer** | ✅ A2A Secure Network Transfer | ❌ No | ❌ No |
| **Vision Support** | ✅ Camera + Vision Models | ⚠️ Limited | ❌ No |
| **Streaming** | ✅ Library-level (tokens as they arrive) | ⚠️ Per-call | ❌ No |
| **Dependencies** | 🪶 Ultra-lightweight (Zero-dep Core) | 📦📦📦 Heavy | 📦📦 Medium |

**DAIE is for you if you want:**
- 🏠 **Offline-first AI** — Run everything locally with Ollama/Llama.cpp, no API keys required.
- 🔗 **Decentralized Intelligence** — Agents communicate directly over P2P networks; build a global "Living LLM" tapestry.
- ⚡ **Parallel Efficiency** — True parallel agent execution with smart concurrency limits to protect your GPU/VRAM.
- 🧠 **Collective Intelligence** — Shared persistent memory namespaces allow agent clusters to learn and evolve together.
- 🏛️ **Unbreakable Reasoning** — Use the **Parliament Architecture** to pitch specialists against each other for peer-reviewed consensus.
- 🎭 **Rich Personality** — Go beyond "helpful assistant" with deeply configured personas, traits, and behavioral guardrails.
- 👁️ **Visual Awareness** — Direct camera integration and vision model support out of the box.
- 💬 **Ready-to-Ship Loops** — Professional chat interfaces for individual agents, nodes, and hybrid multi-agent systems.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER / APPLICATION                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      DAIE FRAMEWORK                         │
│    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│    │   AGENTS    │  │    TOOLS    │  │   MEMORY    │        │
│    │  • ReAct    │  │  • File     │  │  • Working  │        │
│    │  • Persona  │  │  • API      │  │  • Semantic │        │
│    │  • Config   │  │  • Selenium │  │  • Episodic │        │
│    └─────────────┘  └─────────────┘  └─────────────┘        │
│           │                │                │               │
│           ▼                ▼                ▼               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │       ORCHESTRATOR & PARLIAMENT (Multi-Agent)       │    │
│  │  • Task delegation  • Peer-Review & Consensus       │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              AGENT ROUTER (Intelligent)             │    │
│  │  • LLM-based routing  • Content analysis            │    │
│  │  • Dynamic agent selection  • Routing history       │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              COMMUNICATION MANAGER                  │    │
│  │  • P2P networking  • WebSocket Support  • Auth      │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  LLM MANAGER                        │    │
│  │  • Ollama  • OpenAI  • Anthropic  • Google  • Azure │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG ENGINE (TF-IDF)                      │
│  • Document loading  • Context retrieval  • Knowledge base  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌐 DAIE Ecosystem Layers (Network Stack)

DAIE follows a 4-layer architectural stack, similar to the OSI model, enabling nested coordination and distributed intelligence across a decentralized mesh.

```
┌─────────────────────────────────────────────────────────────┐
│             L4: MULTI-NODE HYBRID SYSTEM LAYER              │
│       (Global Mesh, Cross-Device P2P, N-Layer Nesting)      │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               L3: HYBRID ORCHESTRATOR NODE LAYER            │
│         (Resource Management, Node-level P2P, Lifecycle)    │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   L2: COORDINATION LAYER                    │
│        (Orchestrator, Parliament, Task Delegation, MoA)     │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      L1: LEAF AGENT LAYER                   │
│          (ReAct Loop, Persona, Memory, Tool Usage)          │
└─────────────────────────────────────────────────────────────┘
```

| Layer | Component | Primary Function | Operational Scope |
|-------|-----------|------------------|-------------------|
| **L4: System** | `MultiNodeHybridSystem` | Global Mesh & Topology | Cross-Device / Global |
| **L3: Node** | `HybridOrchestratorNode` / `Block` | Containerization & Hosting | Host / Virtual Node |
| **L2: Coordination** | `Orchestrator` / `Parliament` | Task Delegation & Logic | Domain / Workflow |
| **L1: Agent** | `Agent` | Cognition & Tool Execution | Individual Intelligence |

### Layer Deep Dive

#### 🧠 L1: Leaf Agent Layer (The Cognition Layer)
*   **Role**: The fundamental unit of decentralized intelligence.
*   **Capabilities**: Implements the **ReAct** (Reasoning + Acting) loop, manages local **Persistent Memory**, and executes **Tools** (File System, Web Search, Browser Automation).
*   **Context**: Operates as a standalone entity with a specific persona, gender, and behavior profile.

#### 🤝 L2: Coordination Layer (The Management Layer)
*   **Role**: Aggregates and orchestrates multiple L1 agents into a functional team.
*   **Capabilities**:
    *   **Orchestrator**: Handles hierarchical task decomposition and sequential delegation via **ACP (Agent Connect Protocol)**.
    *   **Parliament**: Enables peer-review consensus (Mixture-of-Agents) where specialists deliberate and verify outputs.
*   **Context**: Manages domain-specific workflows (e.g., a "Legal Research Lab" or "Software Dev Team").

#### 🏗️ L3: Hybrid Node Layer (The Infrastructure Layer)
*   **Role**: Provides the host environment, containerization, and resource management.
*   **Capabilities**:
    *   **HybridOrchestratorNode**: Combines node infrastructure with local orchestrators.
    *   **Block Container**: Wraps any architecture for instant P2P deployment, terminal interaction, and "conscious" network awareness.
*   **Context**: Represents a physical or virtual machine participating in the ecosystem.

#### 🌐 L4: Multi-Node System Layer (The Ecosystem Layer)
*   **Role**: The global fabric connecting disparate L3 nodes into a unified, decentralized mesh.
*   **Capabilities**: Supports **N-Layer Nesting** (nodes containing nodes), cross-device P2P routing, and global peer discovery via **Kademlia/DHT**.
*   **Containerization**: Uses the **Block** system to wrap architectures for deployment.
*   **Context**: The "living tapestry" of AI—enabling parent/child node relationships across the globe.

### How the Layers Interact (Encapsulation)

DAIE follows a strict **Encapsulation Pattern** to ensure modularity and scalability:

1.  **L1 (Agent)** is the execution engine. It knows *how* to use a tool (e.g., "Write this file") but doesn't need to know the global goal.
2.  **L2 (Coordination)** provides the "Strategic Intent". It breaks down a high-level mission (e.g., "Build a website") and maps it to specific L1 agent capabilities.
3.  **L3 (Node)** provides the "Host Environment". It ensures that L1 and L2 have the necessary physical resources (GPU, VRAM, Network ports) and security boundaries to operate safely.
4.  **L4 (System)** provides the "Global Fabric". It connects multiple L3 nodes into a unified directory, allowing an agent on a laptop in London to seamlessly delegate a task to an agent on a server in Tokyo.

---

---


## Features

### 🤖 AI Agents
- **ReAct agent loop** — LLM reasons → picks a tool → sees the result → iterates until it gives a final answer
- **Parliament Architecture** — A "Mixture-of-Agents" peer-review mechanism supporting configurable `max_review_rounds` and dynamic `TF-IDF` early stopping to reach mathematical Pydantic-enforced consensus.
- **Distributed/P2P Parliament** — Parliament can span multiple physical nodes. Agents on different machines participate in deliberation via broadcast-based signaling.
- **Hybrid Parliament Orchestration** — Synthesizes abstract high-level tasks via the parliament, dynamically pushing the resulting roadmap into an Orchestrator.
- **Multi-Agent Orchestration** — Coordinate main agents and sub-agents for complex goals (e.g. Research Lab, Courtroom)
- **Intelligent Agent Router** — LLM-based routing that automatically selects the best agent for each message based on content analysis
- **Agent persona** — configure `gender`, `personality`, and `behavior` traits injected directly into the LLM prompt
- **Per-agent LLM overrides** — each agent can have its own `temperature` and `max_tokens`
- **Real-Time Temporal Awareness** — All agents have instant knowledge of current date, time, and timezone context via automatic prompt injection.
- **Parallel Execution Layer** — Smart concurrency management via `ParallelExecutor` mapping native thread locks to cleanly parallelize local topology without hitting GPU/OOM faults.

### 🧠 Persistent Memory
- **Persistent Storage** — Support for `SQLiteStorage` backend, ensuring agent memories survive restarts.
- **Shared Memory Namespaces** — Agents in an `Orchestrator` or `Parliament` can share a unified memory context for collective intelligence.
- **Auto-Summarization** — Automatic condensation of episodic memories into long-term summaries using LLM to keep the working context lean.
- **Memory Snapshots** — Manual `save_memory()` and `load_memory()` methods for versioned agent states.

### 🔍 RAG Systems

### ⚙️ Automation Tools
- **Hardened Tools** — Secure sandbox-ready code execution, robust web search (DuckDuckGo + Tavily), and modern Playwright browser automation.
- **Pre-built tools** — file system, HTTP API calls, SQLite/PostgreSQL Database, Selenium & Playwright browser automation.
- **Custom tools** — decorate any function with `@tool` and it works identically to built-in tools
- **A2A file transfer** — securely send files between agents over the network using Base64 encoding

### 💬 Chatbots & Vision
- **Streaming tokens** — set `stream=True` once, tokens print as they arrive
- **Vision Capabilities** — Support for vision models (e.g. `qwen3-vl:2b`) with camera integration
- **Camera & audio** — optional OpenCV camera capture and PyAudio microphone/speaker support
- **Chat Loop Configs** — Pre-configured chat loops for agents, nodes, orchestrators, and hybrid systems

### 🌐 Networking & Communication
- **P2P networking** — agents communicate across machines via WebSocket with authentication & authorization
- **Block Containerization** — Wrap any agent or node into a "Block" for instant deployment as a network server or terminal chat loop.
- **Agent-to-Agent (A2A) Delegation** — Agents can autonomously find and delegate tasks to other agents over the network using specialized tools.
- **WebSocket Support** — Real-time bidirectional communication
- **Multi-provider LLM** — Ollama (default), OpenAI, Anthropic, Google, Azure, OpenRouter

### 🛠️ Developer Tools
- **CLI** — manage agents and the core system from the terminal

---

## Documentation

For detailed documentation, see the [docs](docs/) folder:

### 🚀 Getting Started
- [Getting Started](docs/getting-started.md) — Installation, quick start, and basic concepts

### 🤖 AI Agents
- [Agents](docs/agents.md) — Agent creation, configuration, and the ReAct loop
- [Parliament](docs/parliament.md) — Mixture-of-Agents deliberation, peer review, and consensus synthesis
- [Orchestrator](docs/orchestrator.md) — Multi-agent coordination and task delegation
- [Hybrid Pipeline](docs/hybrid-pipeline.md) — Sequential strategic planning (Parliament) and task execution (Orchestrator)
- [Memory](docs/memory.md) — Agent memory management (working, semantic, episodic)
- [Agent Router](docs/agents.md#intelligent-agent-routing) — LLM-based intelligent agent routing

### 🔍 RAG Systems
- [RAG](docs/rag.md) — Retrieval-Augmented Generation with TF-IDF

### ⚙️ Automation Tools
- [Tools](docs/tools.md) — Pre-built tools, custom tools, and the @tool decorator

### 🌐 Networking & Communication
- [P2P Networking](docs/p2p.md) — Peer-to-peer communication protocol for agents
- [Network Configuration](docs/network_configuration.md) — Detailed guide on `network_url` and `network_connections`
- [Container Blocks](docs/container-blocks.md) — Deploying architectures as containerized Blocks
- [Node](docs/node.md) — Node abstraction for managing agents and resources
- [Orchestrator](docs/orchestrator.md) — Multi-agent coordination and task delegation
- [Node vs Orchestrator](docs/node-vs-orchestrator.md) — Complete comparison guide with 100+ use cases and decision matrix
- [Communication](docs/communication.md) — P2P networking, messaging, and file transfers
- [LLM Configuration](docs/llm.md) — Multi-provider LLM setup and streaming
- [Chat Configs](docs/chat-configs.md) — Pre-configured chat loops for agents, nodes, orchestrators, and hybrid systems

### 🏗️ Architecture Patterns
- **Parliament Pattern**: Strict peer-reviewed consensus engine with structural Pydantic outputs and dynamic early stopping, dramatically reducing hallucination rates.
- **Node Architecture**: Distributed infrastructure for multi-location systems.
- **Orchestrator Pattern**: Hierarchical workflow coordination for complex tasks.
- **Hybrid Architecture**: Combine Node + Orchestrator for enterprise-scale systems.
- **HybridOrchestratorNode**: Simplified hybrid setup combining Node + Orchestrator in one class.
- [HybridParliamentOrchestrator](docs/hybrid-pipeline.md): Combines Parliament's theoretical strategic modeling natively with the Orchestrator's execution delegation.
- **Agent Router**: LLM-based intelligent routing for optimal agent selection.

### 🛠️ Developer Tools
- [CLI](docs/cli.md) — Command-line interface for agent and system management
- [Utils](docs/utils.md) — Camera, audio, encryption, and utility functions
- [API Reference](docs/api-reference.md) — Complete API reference for all modules

---

## ⚡ Quick Start (30 seconds)

```bash
# 1. Install DAIE
pip install daie

# 2. Install Ollama (local LLM)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:1b

# 3. Run your first agent
python -c "
import asyncio
from daie import Agent, AgentConfig, set_llm

set_llm(ollama_llm='llama3.2:1b', stream=True)

async def main():
    agent = Agent(config=AgentConfig(name='Alex', personality='helpful and witty'))
    await agent.start()
    response = await agent.send_message('Hello! What can you do?')
    await agent.stop()

asyncio.run(main())
"
```

**That's it!** You now have a working AI agent in 30 seconds.

---

## 🎯 Real Output Example

```
$ python examples/01_basic_chat.py

=== Basic Chat Loop ===
Type 'exit' or press Ctrl+C to quit.

You: What's the weather like today?

LUNA: 🌤️ Hey there! I'd love to help with the weather, but I don't have access to real-time data. However, I can tell you that I'm feeling sunny and energetic today! ☀️

If you want actual weather info, you could:
1. Ask me to search the web using my browser tool
2. Tell me your location and I'll look it up
3. Just chat with me about anything else!

What would you like to do? 😊

You: Search for weather in San Francisco

LUNA: 🌍 Connecting to the globe! Let me find that for you.

[Using tool: web_search]
[Querying DuckDuckGo & Tavily fallback...]
[Search completed in 0.8s]

LUNA: 🌁 Here's the current situation in San Francisco:
- Temperature: 62°F (17°C)
- Conditions: Partly cloudy
- Humidity: 75%
- Wind: 12 mph from the west

Perfect weather for a walk across the Golden Gate Bridge! 🌉
```

---

## Installation

```bash
pip install daie
```

**Optional extras:**

```bash
pip install "daie[dev]"      # pytest, black, mypy, flake8, pytest-asyncio, pytest-cov
pip install "daie[docs]"     # sphinx, sphinx-rtd-theme, nbsphinx
```

**Requires Python 3.10+**

**Core dependencies:** `pyyaml`, `selenium`, `webdriver-manager`, `uvicorn`, `websockets`, `nats-py`, `pyaudio`, `zeroconf`, `kademlia`, `numpy`, `pydantic`, `pydantic-settings`

> [!TIP]
> **Zero-Dependency Philosophy**: DAIE includes in-house, lightweight replacements for `requests`, `python-dotenv`, `rich`, `typer`, and `cryptography` to keep the core footprint minimal and avoid dependency hell.

---

## Quick Start

### 1. Simple streaming chat with persona

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole

set_llm(ollama_llm="wizard-vicuna-uncensored:7b", stream=True)

async def main():
    agent = Agent(config=AgentConfig(
        name="Alex",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a helpful and concise AI assistant.",
        gender="female",
        personality="sassy, witty, and very direct",
        behavior="always uses emojis and speaks enthusiastically",
        temperature=0.9,
        max_tokens=1024
    ))
    await agent.start()

    print("=== Chat Loop ===")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ("exit", "quit"):
                break
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        response = await agent.send_message(user_input)
        print("\n")

    await agent.stop()

asyncio.run(main())
```

### 2. Agent with tools (ReAct loop)

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.tools import FileManagerTool, APICallTool, tool

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Custom tool via decorator
@tool(name="calculate_math", description="Evaluate a basic math expression.")
async def calculate_math(expression: str) -> str:
    return str(eval(expression))

async def main():
    agent = Agent(config=AgentConfig(
        name="MathBot",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a capable agent with access to math and file tools.",
    ))

    agent.add_tool(calculate_math)
    agent.add_tool(FileManagerTool())

    await agent.start()

    # LLM autonomously picks the right tools via the ReAct loop
    result = await agent.execute_task(
        "Calculate 25 * 14 and save the result into a file called result.txt"
    )
    print("Final Answer:", result)

    await agent.stop()

asyncio.run(main())
```

### 3. P2P multi-agent networking & file transfer

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.agents.message import AgentMessage

set_llm(ollama_llm="wizard-vicuna-uncensored:7b")

async def main():
    # Shared communication bus
    comm = CommunicationManager()
    await comm.start()

    # Agent 1
    agent1 = Agent(config=AgentConfig(
        name="NodeAlfa",
        role=AgentRole.GENERAL_PURPOSE,
        network_url="ws://localhost:8000",
    ))
    await agent1.start(communication_manager=comm)

    # Agent 2 (with auth + file transfers)
    agent2 = Agent(config=AgentConfig(
        name="NodeBravo",
        role=AgentRole.GENERAL_PURPOSE,
        network_url="ws://localhost:8001",
        auth_token="secure_token_123",
        allow_file_transfers=True,
    ))
    await agent2.start(communication_manager=comm)

    # Send direct message
    msg = AgentMessage(
        sender_id=agent1.id,
        receiver_id=agent2.id,
        content="Hello from NodeAlfa!",
        message_type="text",
    )
    await comm.send_message(msg)

    # A2A file transfer
    file_tool = agent1.get_tool("a2a_send_file")
    if file_tool:
        await file_tool._execute({
            "receiver_id": agent2.id,
            "file_path": "payload.txt",
            "message": "Secure payload!",
        })

    await agent1.stop()
    await agent2.stop()
    await comm.stop()

asyncio.run(main())
```

### 4. Multi-Agent Orchestration

The `Orchestrator` allows a main agent to coordinate multiple sub-agents to solve complex problems.

```python
from daie import Agent, AgentConfig, Orchestrator
from daie.agents import AgentRole

Professor = Agent(config=AgentConfig(name="Professor", role=AgentRole.COORDINATOR))
Nova = Agent(config=AgentConfig(name="NOVA", goal="Handle technical research"))

orchestrator = Orchestrator(
    main_agent=Professor,
    sub_agents=[Nova],
    context_name="research_lab"
)

await orchestrator.start()
response = await orchestrator.execute_task("Research decentralized consensus")
```

### 5. Decentralized RAG

Agents can maintain independent knowledge bases using simple directory-based RAG.

```python
config = AgentConfig(
    name="Expert",
    rag_document_path="data/expert_knowledge/"  # Local folder with .txt, .pdf, .md files
)
agent = Agent(config=config)
# The agent will automatically retrieve relevant context before answering
```

### 6. Intelligent Agent Routing

The `AgentRouter` uses LLM to automatically select the best agent for each message based on content analysis.

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole, AgentRouter

set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    # Create specialized agents
    assistant = Agent(config=AgentConfig(
        name="Assistant",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a helpful general-purpose assistant."
    ))
    
    coder = Agent(config=AgentConfig(
        name="Coder",
        role=AgentRole.SPECIALIZED,
        system_prompt="You are an expert programmer. Write clean, efficient code."
    ))
    
    researcher = Agent(config=AgentConfig(
        name="Researcher",
        role=AgentRole.SPECIALIZED,
        system_prompt="You are a research specialist. Analyze and summarize information."
    ))
    
    # Create router from agents list
    router = AgentRouter.from_agents([assistant, coder, researcher])
    
    # Router automatically selects the best agent
    agent_type = await router.route("Write a Python function to sort a list")
    # Returns: "coder"
    
    agent_type = await router.route("Explain quantum computing")
    # Returns: "researcher"
    
    agent_type = await router.route("What's the weather like?")
    # Returns: "assistant"
    
    # Get routing history
    history = router.get_routing_history()
    print(f"Routed {len(history)} messages")

asyncio.run(main())
```

### 7. Parliament Deliberation

The `Parliament` allows you to pitch specialists against one another to peer-review answers iteratively until they generate a verified architectural consensus string (halting early to save cost if they naturally agree using TF-IDF checks).

```python
from daie import Agent, AgentConfig
from daie.agents import Parliament, AgentRole
from daie.chat import ParliamentChatConfig

coder = Agent(config=AgentConfig(name="Coder", role=AgentRole.SOFTWARE_ENGINEER))
auditor = Agent(config=AgentConfig(name="Security", role=AgentRole.SECURITY_AUDITOR))
manager = Agent(config=AgentConfig(name="Manager", role=AgentRole.GENERAL_PURPOSE))

# Construct a parliament mapping maximum 3 review iterations 
parliament = Parliament(sub_agents=[coder, auditor, manager], max_review_rounds=3)

# Start an interactive discussion cleanly using standard loop formats
config = ParliamentChatConfig(parliament=parliament)
config.run()
```

### 8. Hybrid Parliament Orchestration

Combines deep abstract debates into actual execution via the `HybridParliamentOrchestrator`. Sub-agents outline a roadmap, and the orchestrator dynamically delegates task nodes securely.

```python
from daie.agents import OrchestratorAgent, HybridParliamentOrchestrator
from daie.chat import HybridParliamentChatConfig

# Re-use our abstract parliament setup from above
orchestrator = OrchestratorAgent()

hybrid_pipeline = HybridParliamentOrchestrator(
    parliament=parliament,
    orchestrator=orchestrator,
    min_confidence_threshold=60.0  # Failsafe abort for terrible planning protocols
)

config = HybridParliamentChatConfig(hybrid_pipeline=hybrid_pipeline)
config.run()
```

### 9. Full-Power One-File Demo (Orchestrator + Tools + Guardrails)

Copy this into a single file (e.g., `demo.py`) and run it to see the full architecture in action.

```python
import asyncio
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole
from daie.tools import FileManagerTool, APICallTool, tool

# 1. Setup - Local LLM with streaming enabled
set_llm(ollama_llm="llama3.2:1b", stream=True)

# 2. Define a custom tool for the agents to use
@tool(name="code_executor", description="Executes snippets of python code safely.")
async def execute_code(code: str) -> str:
    # In a real app, use a sandbox!
    return f"Code executed successfully. Output: [Simulated result for {len(code)} chars]"

async def main():
    print("🚀 Initializing Decentralized AI Ecosystem Demo...")

    # 3. Create a specialized Researcher agent
    researcher = Agent(config=AgentConfig(
        name="Researcher",
        role=AgentRole.SPECIALIZED,
        goal="Gather and summarize technical information",
        rag_document_path="docs/",  # Optional: local knowledge base
    ))

    # 4. Create a specialized Coder agent with guardrails
    coder = Agent(config=AgentConfig(
        name="Coder",
        role=AgentRole.SPECIALIZED,
        goal="Write and verify optimized Python code",
        max_tokens_per_task=2000,   # Production guardrail
        max_tool_calls_per_task=5,  # Production guardrail
    ))
    coder.add_tool(execute_code)
    coder.add_tool(FileManagerTool())

    # 5. Create the Orchestrator to coordinate them
    # The Coordinator agent manages the sub-agents autonomously
    boss = Agent(config=AgentConfig(name="Boss", role=AgentRole.COORDINATOR))
    
    system = Orchestrator(
        main_agent=boss,
        sub_agents=[researcher, coder],
        context_name="SoftwareDevelopmentLab"
    )

    # 6. Start the system (Lifecycle management is mandatory)
    await system.start()

    print("\n--- System is online. Executing high-level task ---")
    
    # 7. Execute a complex multi-step task
    task = "Research how to implement uuid7 in Python, then write a sample script and save it to 'uuid_sample.py'."
    result = await system.execute_task(task)

    print("\n--- Task Complete ---")
    print(f"Final Outcome:\n{result}")

    # 8. Shutdown cleanly
    await system.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 10. Chat Loop Config (Pre-configured Chat Loops)

The `daie.chat` module provides pre-configured chat loop setups so you don't need to write the full boilerplate code. Simply configure and run!

```python
from daie import Agent, AgentConfig, set_llm
from daie.chat import ChatLoopConfig

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create your agent
agent = Agent(config=AgentConfig(
    name="LUNA",
    system_prompt="You are a helpful AI assistant.",
    personality="friendly and helpful"
))

# Run the chat loop with minimal code!
chat_loop = ChatLoopConfig(agent=agent)
chat_loop.run()
```

**Available Chat Loop Configs:**

| Config | Target | Use Case |
|--------|--------|----------|
| `ChatLoopConfig` | Simple Agent | Basic chat with an agent |
| `NodeChatConfig` | Single Node | Advanced chat with orchestrator and sub-agents |
| `OrchestratorChatConfig` | Multi-Node System | Multi-node collaboration and task execution |
| `HybridChatConfig` | Hybrid System | Simple chat with hybrid systems |

📖 **Full guide**: [Chat Configs](docs/chat-configs.md) — Complete documentation for all chat loop configurations

---

## Agent Configuration

```python
from daie.agents.config import AgentConfig, AgentRole

config = AgentConfig(
    name="MyAgent name",   # (ALEX, NOVA, BOB, etc)
    role=AgentRole.GENERAL_PURPOSE,   # or SPECIALIZED, COORDINATOR, WORKER, ANALYZER, EXECUTOR
    goal="Help users with tasks",
    backstory="A capable AI assistant",
    system_prompt="You are a helpful assistant.",

    # Persona traits (automatically injected into LLM prompts)
    gender="female",                             # Literal["male", "female"] or None
    personality="sarcastic, witty, very direct",  # free-form string
    behavior="always starts sentences with Hmm",  # free-form string

    # Temporal Context
    include_datetime=True,               # Inject current date/time context

    # Per-agent LLM overrides (take priority over global set_llm settings)
    temperature=0.7,
    max_tokens=1000,

    # Task settings
    task_timeout=30,       # seconds before execute_task times out

    # P2P Networking
    network_url="ws://your-ip-or-devtunnel:8000",
    auth_token="secure_secret_here",
    allow_file_transfers=True,
    allowed_senders=["agent-id-1", "agent-id-2"],   # whitelist (empty = allow all)
)
```

---

## LLM Configuration

```python
from daie import set_llm, get_llm_config, LLMType

# Ollama (local, default)
set_llm(ollama_llm="llama3.2:latest", temperature=0.7, max_tokens=1000)
set_llm(ollama_llm="gemma3:1b", stream=True)   # enable streaming

# OpenAI
set_llm(llm_type=LLMType.OPENAI, model_name="gpt-4o-mini", api_key="sk-...")

# Anthropic
set_llm(llm_type=LLMType.ANTHROPIC, model_name="claude-3-sonnet-20240229", api_key="...")

# Google
set_llm(llm_type=LLMType.GOOGLE, model_name="gemini-pro", api_key="...")

# Azure OpenAI
set_llm(llm_type=LLMType.AZURE, model_name="gpt-4", api_key="...", base_url="https://<resource>.openai.azure.com")

# OpenRouter
set_llm(llm_type=LLMType.OPENROUTER, model_name="mistralai/mistral-7b-instruct", api_key="...")

# Check current config
cfg = get_llm_config()
print(cfg.llm_type, cfg.model_name, cfg.stream)
```

### Streaming

Streaming is a library-level setting — set it once, it applies everywhere:

```python
set_llm(ollama_llm="llama3.2:latest", stream=True)
```

When `stream=True`, `send_message()` prints tokens as they arrive and returns the full response string when done.
`execute_task()` always runs the reasoning loop without streaming (for reliability), then streams the final answer.

---

## Tools

### Pre-built tools

| Tool | Description |
|---|---|
| `FileManagerTool` | Complete file and directory manipulation |
| `APICallTool` | Comprehensive HTTP requests (GET/POST/etc) |
| `WebSearchTool` | Robust web search (DuckDuckGo + Tavily fallback) |
| `CodeSandboxTool` | Secure Python code execution in restricted context |
| `DatabaseTool` | Execute SQL queries against SQLite or PostgreSQL |
| `PlaywrightBrowserTool`| Modern, fast browser automation (Highly Recommended) |
| `SeleniumChromeTool` | Legacy browser automation with deep Chrome support |
| `A2ASendFileTool` | Transfer files securely between agents over P2P network |
| `A2ASendMessageTool` | Send messages between agents |
| `A2ADelegateTaskTool` | Delegate tasks to other agents via ACP |
| `CalendarEmailTool` | Mock interactions for schedule and mail management |

### FileManagerTool actions

```python
from daie.tools import FileManagerTool

fm = FileManagerTool()

# Create
await fm.execute({"action": "create_file", "path": "notes.txt", "content": "hello"})

# Read
result = await fm.execute({"action": "read_file", "path": "notes.txt"})
print(result["content"])

# List directory
result = await fm.execute({"action": "list_contents", "path": ".", "recursive": False})

# Delete
await fm.execute({"action": "delete_file", "path": "notes.txt"})
```

### APICallTool

```python
from daie.tools import APICallTool

api = APICallTool()
result = await api.execute({
    "url": "https://api.github.com/users/octocat",
    "method": "GET",
    "headers": {"Accept": "application/json"},
})
print(result["json"])
```

### SeleniumChromeTool (browser automation)

```python
from daie.tools import SeleniumChromeTool

browser = SeleniumChromeTool()

await browser.execute({"action": "open_url", "url": "https://example.com", "headless": True})
result = await browser.execute({"action": "get_title"})
print(result["page_title"])

await browser.execute({"action": "screenshot", "screenshot_path": "page.png"})
```

### Custom `@tool` decorator

```python
from daie.tools import tool

@tool(name="calculate", description="Evaluate a math expression")
async def calculate(expression: str) -> str:
    return str(eval(expression))  # use safely in production

agent.add_tool(calculate)
result = await agent.execute_task("What is 12 * 34?")
```

---

## P2P Networking & File Transfers

DAIE supports multi-agent communication via its `CommunicationManager`. Agents can:

- **Discover peers** via the built-in `NodeRegistry`
- **Send direct messages** between agents (in-process or via WebSocket for remote agents)
- **Transfer files** securely using Base64 encoding with the `A2ASendFileTool`
- **Authorize senders** with `allowed_senders` whitelists
- **Authenticate connections** with `auth_token`

### Setting Up Networked Agents

```python
from daie import Agent, AgentConfig
from daie.communication import CommunicationManager

comm = CommunicationManager()
await comm.start()

config = AgentConfig(
    name="NetworkWorker",
    network_url="ws://<your-public-ip-or-devtunnel>:8000",
    auth_token="secure_cross_machine_token123",
    allow_file_transfers=True
)
agent = Agent(config=config)
await agent.start(communication_manager=comm)
```

### Authorization Whitelist

```python
config = AgentConfig(
    name="SecureNode",
    allowed_senders=["trusted-agent-id-1", "trusted-agent-id-2"],
)
# Only messages from whitelisted sender IDs will be accepted.
# Empty list = allow all senders.
```

---

## Camera (OpenCV)

```bash
pip install opencv-python
```

```python
from daie.utils import CameraManager, capture_image, list_camera_devices

# List cameras
devices = list_camera_devices()
print("Available cameras:", devices)

# Capture a single image
capture_image("photo.jpg", device_index=0)

# Stream frames
cam = CameraManager()
cam.initialize_camera(device_index=0)

def on_frame(frame):
    print("Got frame:", frame.shape)

cam.start_streaming(callback=on_frame)
# ... do work ...
cam.stop_streaming()
cam.release()
```

### Vision Chat with Qwen-VL

DAIE supports local vision models via Ollama.

```python
import cv2
import base64
from daie import Agent, set_llm

set_llm(ollama_llm="qwen3-vl:2b")

# Capture and encode image
cam = CameraManager()
frame = cam.get_frame()
_, buffer = cv2.imencode('.jpg', frame)
img_b64 = base64.b64encode(buffer).decode('utf-8')

# Query the vision agent
agent = Agent()
response = await agent.execute_task("What do you see?", images=[img_b64])
```

---

## Audio (PyAudio)

```bash
pip install pyaudio
```

```python
from daie.utils import AudioManager, record_audio_file, play_audio_file

# List audio devices
am = AudioManager()
am.initialize_audio()
devices = am.list_audio_devices()
print(devices)

# Record 5 seconds to a WAV file
record_audio_file("recording.wav", duration=5.0, sample_rate=16000)

# Play it back
play_audio_file("recording.wav")
```

---

## CLI

```bash
# Agent management
daie agent list
daie agent create --name "MyAgent" --role "general-purpose"
daie agent start <agent-id>
daie agent stop <agent-id>
daie agent status <agent-id>
daie agent delete <agent-id>

# Core system
daie core init
daie core start
daie core stop
daie core status
daie core health
daie core logs
```

---

## Architecture

```
src/daie/
├── agents/         Agent, AgentConfig, AgentRole, AgentMessage, Orchestrator, AgentRouter
├── core/           LLMManager, LLMConfig, LLMType, set_llm(), get_llm(), DecentralizedAISystem, Node
├── tools/          Tool base class, @tool decorator, FileManagerTool, WebSearchTool,
│                   CodeSandboxTool, DatabaseTool, PlaywrightBrowserTool, APICallTool,
│                   A2ASendFileTool, A2ASendMessageTool, A2ADelegateTaskTool, VisionTool
├── utils/          AudioManager, CameraManager, encryption, logging, serialization
├── communication/  CommunicationManager (in-memory + WebSocket P2P)
├── registry/       NodeRegistry (decentralized agent discovery)
├── memory/         MemoryManager (working, semantic, episodic)
├── protocols/      Protocol definitions (ACP - Agent Connect Protocol)
├── rag/            RAGEngine, DocumentLoader (TF-IDF retrieval)
└── cli/            Typer-based CLI (agent management, core system control)
```

**ReAct loop flow:**

```
execute_task("Create notes.txt")
  │
  ├─ LLM: {"tool":"file_manager","params":{"action":"create_file",...}}
  ├─ Run FileManagerTool → {"success":true,...}
  ├─ LLM: {"answer":"Done! File created."}
  └─ return "Done! File created."
```

---

## Examples

### 💬 Chatbots
| Level | File | Description |
|---|---|---|
| 🟢 Beginner | `examples/01_basic_chat.py` | Interactive streaming chat with persona traits (gender, personality, behavior) |
| 🟡 Intermediate | `examples/05_vision_chat.py` | Real-time vision-enabled chat using `qwen3-vl:2b` and local camera |
| 🟡 Intermediate | `examples/12_chat_loop_config.py` | Pre-configured chat loops for agents, nodes, orchestrators, and hybrid systems |

### 🤖 AI Agents
| Level | File | Description |
|---|---|---|
| 🟡 Intermediate | `examples/02_custom_tools.py` | Custom `@tool` decorator + `FileManagerTool` with ReAct agent loop |
| 🟡 Intermediate | `examples/09_intelligent_routing.py` | LLM-based intelligent agent routing with multiple specialized agents |
| 🔴 Advanced | `examples/classroom_demo.py` | Multi-agent classroom orchestration with Professor and Student agents |
| 🔴 Advanced | `examples/courtroom_demo.py` | Multi-agent courtroom simulation with Judge, Prosecutor, and Defender |

### 🔍 RAG Systems
| Level | File | Description |
|---|---|---|
| 🟡 Intermediate | `examples/04_rag_chat.py` | RAG-enabled chat with document-based knowledge retrieval |

### 🌐 Networking & Communication
| Level | File | Description |
|---|---|---|
| 🔴 Advanced | `examples/03_p2p_networking.py` | Multi-agent P2P messaging, authorization, and A2A file transfer |
| 🔴 Advanced | `examples/07_node_agents_interactive.py` | Interactive Node-based chat system with multiple agents |
| 🔴 Advanced | `examples/08_node_agents_demo.py` | Automated Node demonstration with resource management |

### 🏗️ Architecture Examples
| Level | File | Description |
|---|---|---|
| 🔴 Advanced | `examples/classroom_demo.py` | Multi-agent classroom orchestration with Professor and Student agents |
| 🔴 Advanced | `examples/courtroom_demo.py` | Multi-agent courtroom simulation with Judge, Prosecutor, and Defender |

Run any example:

```bash
source venv/bin/activate
python examples/01_basic_chat.py
```

---

## 🏗️ Architecture Patterns

### When to Use Node
**Use Node when you need:**
- Distributed networks across multiple machines/locations
- Resource management (GPU, memory, model cache)
- Peer-to-peer communication between agents
- Horizontal scalability by adding nodes
- Edge computing with local processing
- High availability with no single point of failure
- Geographic distribution across regions
- Multi-tenant systems with resource isolation

**Don't use Node when:**
- Simple task coordination on a single machine
- Quick prototyping without infrastructure setup
- Stateless operations that don't need resource management
- Team lacks distributed systems expertise

### When to Use Orchestrator
**Use Orchestrator when you need:**
- Task decomposition into manageable sub-tasks
- Specialized agents with different skills
- Result aggregation from multiple agents
- Workflow coordination with clear hierarchy
- Research/analysis tasks requiring multiple experts
- Content creation workflows
- Customer support routing
- Multi-step workflows

**Don't use Orchestrator when:**
- Flat peer structure with equal agents
- Direct communication without mediation
- Resource management is required
- Distributed network across multiple machines

### When to Use Hybrid (Node + Orchestrator)
**Use Hybrid when you need:**
- Enterprise-scale systems with multiple teams
- Distributed teams with local coordination
- Resource-aware task execution
- Complex distributed workflows
- Maximum scalability and flexibility
- Edge computing with central coordination
- Multi-location with specialized teams

**Decision Matrix:**
| Scenario | Node | Orchestrator | Hybrid |
|----------|------|--------------|--------|
| Single machine, simple tasks | ❌ | ✅ | ❌ |
| Multiple machines, no coordination | ✅ | ❌ | ❌ |
| Single machine, complex workflows | ❌ | ✅ | ❌ |
| Multiple machines, complex workflows | ❌ | ❌ | ✅ |
| Resource management needed | ✅ | ❌ | ✅ |
| Task delegation needed | ❌ | ✅ | ✅ |
| Geographic distribution | ✅ | ❌ | ✅ |
| Enterprise-scale systems | ✅ | ❌ | ✅ |

📖 **Full guide**: [Node vs Orchestrator](docs/node-vs-orchestrator.md) — 100+ use cases, decision matrix, and real-world examples

---

## 🌍 Real-World Use Cases

### Distributed Research Network
- Multiple labs across different locations
- Each lab manages its own resources (GPU clusters, specialized hardware)
- Labs collaborate on research projects
- Orchestrator within each lab coordinates local tasks

### Smart City Traffic Management
- Multiple districts with local coordination
- Each district manages traffic cameras and sensors
- Orchestrator coordinates traffic signals within district
- Nodes share traffic data across districts

### Multi-Location Customer Support
- Support centers in different time zones
- 24/7 coverage across time zones
- Each center manages its own resources
- Orchestrator routes tickets to appropriate specialist

### Autonomous Vehicle Fleet
- Each vehicle manages its own sensors and compute
- Orchestrator coordinates navigation decisions
- Nodes share traffic and road condition data
- Resource management tracks battery, compute, sensors

### Distributed Content Creation
- Multiple teams (writing, design, video)
- Each team manages its own tools and resources
- Orchestrator coordinates content workflow
- Nodes share assets and drafts

---

## 💡 Project Ideas

### Beginner Projects
1. **Personal AI Assistant Network** — Create a node with multiple specialized assistants (calendar, email, research, coding)
2. **Study Group Simulator** — Simulate a study group with a professor and students using Orchestrator

### Intermediate Projects
3. **Multi-Location News Network** — Create a distributed news network with editorial teams in different locations
4. **E-commerce Support System** — Build a distributed customer support system with specialized teams

### Advanced Projects
5. **Distributed AI Research Lab** — Create a research network with multiple labs, each with specialized equipment and expertise
6. **Smart Factory Automation** — Build an automated factory system with multiple production lines

📖 **Full project ideas**: [Node vs Orchestrator](docs/node-vs-orchestrator.md) — Detailed code examples for each project

---

## 🔧 Core Components

### Agent System
- **ReAct Loop**: LLM reasons → picks a tool → sees result → iterates until final answer
- **Persona System**: Configure gender, personality, and behavior traits
- **Tool Integration**: 8+ pre-built tools with custom `@tool` decorator
- **Memory Management**: Working, semantic, and episodic memory
- **Chat Loop Configs**: Pre-configured chat loops for agents, nodes, orchestrators, and hybrid systems

### Multi-Agent Coordination
- **Orchestrator**: Main agent coordinates sub-agents for complex tasks
- **HybridOrchestratorNode**: Simplified hybrid setup combining Node + Orchestrator in one class
- **Agent Router**: LLM-based intelligent routing for optimal agent selection
- **Task Delegation**: Automatic task decomposition and result aggregation

### Networking & Communication
- **P2P Networking**: Direct agent-to-agent communication via WebSocket
- **Authentication**: Token-based auth with sender whitelists
- **File Transfer**: Secure A2A file transfer with Base64 encoding
- **Node Registry**: Decentralized agent discovery

### RAG System
- **TF-IDF Retrieval**: Simple but effective document retrieval
- **Per-Agent Knowledge**: Each agent can have its own knowledge base
- **Document Loading**: Support for .txt, .pdf, .md files

### LLM Support
- **Multi-Provider**: Ollama (default), OpenAI, Anthropic, Google, Azure, OpenRouter
- **Streaming**: Library-level streaming for real-time responses
- **Per-Agent Overrides**: Each agent can have its own temperature and max_tokens

---

## 📊 Performance & Scalability

### Performance Ratings

| Component | Rating | Notes |
|-----------|--------|-------|
| **Setup Time** | ⭐⭐⭐⭐⭐ | Quick to get started |
| **Scalability** | ⭐⭐⭐⭐⭐ | Horizontal (nodes) + vertical (sub-agents) |
| **Resource Efficiency** | ⭐⭐⭐⭐⭐ | Built-in resource tracking per node |
| **Communication Speed** | ⭐⭐⭐⭐ | Direct P2P + A2A messaging |
| **Fault Tolerance** | ⭐⭐⭐⭐ | Distributed + orchestrator backup |
| **Complexity** | ⭐⭐⭐ | Moderate learning curve |

### Scalability Features
- **Horizontal Scaling**: Add nodes to increase capacity
- **Vertical Scaling**: Add sub-agents to orchestrators
- **Load Distribution**: Distribute work across multiple machines
- **Resource Isolation**: Separate resources per node
- **Geographic Distribution**: Deploy across multiple regions

### Optimization Tips
1. **Use streaming** for real-time responses
2. **Enable RAG** for context-aware answers
3. **Configure personas** for better agent behavior
4. **Use AgentRouter** for intelligent task routing
5. **Deploy nodes** close to data sources
6. **Monitor resources** per node
7. **Implement health checks** for node status

---

## 🔒 Security Features

- **Authentication**: Token-based auth for agent connections
- **Authorization**: Sender whitelists for message filtering
- **Encryption**: Built-in encryption utilities
- **Secure File Transfer**: Base64 encoding for A2A file transfers
- **Resource Isolation**: Per-node resource isolation
- **Access Control**: Per-node and per-agent access control

---

## 🛠️ Developer Experience

### Easy Setup
```bash
pip install daie
```

### Simple API
```python
from daie import Agent, AgentConfig, set_llm

set_llm(ollama_llm="llama3.2:1b", stream=True)
agent = Agent(config=AgentConfig(name="Alex", personality="helpful"))
await agent.start()
response = await agent.send_message("Hello!")
```

### Pre-configured Chat Loops
```python
from daie import Agent, AgentConfig
from daie.chat import ChatLoopConfig

agent = Agent(config=AgentConfig(name="LUNA", personality="friendly"))
chat_loop = ChatLoopConfig(agent=agent)
chat_loop.run()  # Start interactive chat with minimal code!
```

### Comprehensive Documentation
- [Getting Started](docs/getting-started.md) — Installation and quick start
- [Agents](docs/agents.md) — Agent creation and configuration
- [Node vs Orchestrator](docs/node-vs-orchestrator.md) — Architecture comparison
- [Tools](docs/tools.md) — Pre-built and custom tools
- [Examples](examples/) — Working code examples

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=src/daie tests/
```

---

## Development

```bash
git clone https://github.com/kanishkkumarsingh2004/DAIE.git
cd DAIE
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run example chat loop
python examples/01_basic_chat.py
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not connect to Ollama` | Run `ollama serve` and pull a model: `ollama pull wizard-vicuna-uncensored:7b` |
| `ModuleNotFoundError: cv2` | `pip install opencv-python` |
| `ModuleNotFoundError: pyaudio` | `pip install pyaudio` |
| Agent not responding | Call `await agent.start()` before `execute_task()` |
| Task timeout | Increase `task_timeout` in `AgentConfig` |
| LLM returns plain text instead of JSON | Normal — the agent treats plain text as a final answer |
| `execute_task` takes 30-60s on first call | The local LLM model is loading into memory. Subsequent calls are faster |
| `Failed to load registry` warning | Ensure `node_registry.json` contains valid JSON (not empty) |
| Persona traits not applied | Verify `gender`, `personality`, or `behavior` are set in `AgentConfig` |

---

## Current Status

### ✅ Production Ready
DAIE is a mature, production-ready framework with comprehensive features:

- **Core Framework**: Fully implemented and tested
- **Agent System**: Complete with ReAct loop, personas, and tool integration
- **Multi-Agent Orchestration**: Orchestrator pattern for complex task coordination
- **Intelligent Routing**: LLM-based agent selection with AgentRouter
- **P2P Networking**: Full peer-to-peer communication with authentication
- **RAG System**: TF-IDF based retrieval with per-agent knowledge bases
- **Tools**: 12+ pre-built tools with custom `@tool` decorator support
- **Memory Management**: Working, semantic, and episodic memory systems
- **CLI**: Complete command-line interface for agent and system management
- **Documentation**: Comprehensive docs with examples and guides
- **Chat Loop Configs**: Pre-configured chat loops for agents, nodes, orchestrators, and hybrid systems

### 📊 Test Coverage
- **Unit Tests**: 20+ test files covering all major components
- **Integration Tests**: End-to-end testing for multi-agent scenarios
- **Example Tests**: All examples have corresponding test coverage

### 🔧 Recent Improvements
- **Zero-Drift Temporal Awareness**: Solved frozen-in-time hallucinations via mandatory date/time injection for all agents.
- **Tool Hardening**: Added sandbox-ready code execution, modern Playwright support, and SQL database interactions.
- **Communication Stabilization**: Implemented inbound/outbound rate limiting for high-reliability NATS delivery.
- **Improved Use Cases**: Added decision matrix and 100+ architecture scenarios to documentation.

## 🤝 Community & Support

### Getting Help
- **Documentation**: Comprehensive docs in the [docs](docs/) folder
- **Examples**: Working code examples in the [examples](examples/) folder
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions

### Contributing
We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run tests**: `pytest tests/`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup
```bash
git clone https://github.com/kanishkkumarsingh2004/DAIE.git
cd DAIE
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

### Code Style
- **Formatter**: Black
- **Linter**: Flake8
- **Type Checker**: MyPy
- **Tests**: pytest with pytest-asyncio

---

## 📚 Learning Resources

### Tutorials
1. **Getting Started**: [docs/getting-started.md](docs/getting-started.md)
2. **Building Your First Agent**: [examples/01_basic_chat.py](examples/01_basic_chat.py)
3. **Adding Tools**: [examples/02_custom_tools.py](examples/02_custom_tools.py)
4. **P2P Networking**: [examples/03_p2p_networking.py](examples/03_p2p_networking.py)
5. **Multi-Agent Orchestration**: [examples/classroom_demo.py](examples/classroom_demo.py)
6. **Pre-configured Chat Loops**: [examples/12_chat_loop_config.py](examples/12_chat_loop_config.py)

### Architecture Guides
- **Node vs Orchestrator**: [docs/node-vs-orchestrator.md](docs/node-vs-orchestrator.md)
- **Agent Configuration**: [docs/agents.md](docs/agents.md)
- **Communication**: [docs/communication.md](docs/communication.md)
- **Memory Management**: [docs/memory.md](docs/memory.md)
- **Chat Configs**: [docs/chat-configs.md](docs/chat-configs.md)

### Video Tutorials
- Coming soon!

---

## 📊 Statistics

- **Lines of Code**: 10,000+
- **Test Files**: 20+
- **Examples**: 10+
- **Documentation Pages**: 15+
- **Supported LLM Providers**: 6 (Ollama, OpenAI, Anthropic, Google, Azure, OpenRouter)
- **Pre-built Tools**: 12+
- **Architecture Patterns**: 3 (Node, Orchestrator, Hybrid)
- **Chat Loop Configs**: 4 (ChatLoopConfig, NodeChatConfig, OrchestratorChatConfig, HybridChatConfig)

---

## 🙏 Acknowledgments

- **Ollama** for local LLM support
- **LangChain** for inspiration
- **FastAPI** for HTTP server
- **Pydantic** for data validation
- **Rich** for beautiful terminal output
- **Typer** for CLI framework

---

## License

MIT — see [LICENSE](LICENSE)

## Author

Built by **Kanishk Kumar Singh** — kanishkkumar2004@gmail.com

---

## ⭐ Star History

If you find DAIE useful, please give it a star on GitHub! It helps others discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=kanishkkumarsingh2004/DAIE&type=Date)](https://star-history.com/#kanishkkumarsingh2004/DAIE&Date)
