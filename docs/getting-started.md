# Getting Started with DAIE

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

**Core dependencies:** cryptography, python-dotenv, pydantic, pydantic-settings, pyyaml, requests, rich, typer, selenium, webdriver-manager, uvicorn, nats-py, numpy, opencv-python, pyaudio

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
    # network_url: The URL where THIS agent is hosted (others use this to reach it)
    agent1 = Agent(config=AgentConfig(
        name="NodeAlfa",
        role=AgentRole.GENERAL_PURPOSE,
        network_url="http://localhost:8000",  # This agent is hosted on localhost:8000
    ))
    await agent1.start(communication_manager=comm)

    # Agent 2 (with auth + file transfers)
    # network_url: The URL where THIS agent is hosted (others use this to reach it)
    agent2 = Agent(config=AgentConfig(
        name="NodeBravo",
        role=AgentRole.GENERAL_PURPOSE,
        network_url="http://localhost:8001",  # This agent is hosted on localhost:8001
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
        await file_tool.execute({
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

---

## Core Concepts

### The ReAct Loop

DAIE agents use a **ReAct (Reasoning + Acting)** loop:

1. **LLM reasons** about the task
2. **Picks a tool** (or gives a final answer)
3. **Sees the result** of the tool execution
4. **Iterates** until it produces a final answer

This allows agents to autonomously solve complex, multi-step tasks.

### Agent Persona

Agents can have personality traits that are injected into every LLM prompt:

- `gender` — "male" or "female"
- `personality` — free-form string (e.g., "sarcastic, witty, very direct")
- `behavior` — free-form string (e.g., "always starts sentences with Hmm")

### Streaming

Streaming is a library-level setting — set it once, it applies everywhere:

```python
set_llm(ollama_llm="llama3.2:latest", stream=True)
```

When `stream=True`, `send_message()` prints tokens as they arrive and returns the full response string when done.
`execute_task()` always runs the reasoning loop without streaming (for reliability), then streams the final answer.

---

## Next Steps

- [Agents](agents.md) — Deep dive into agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [LLM Configuration](llm.md) — Multi-provider LLM setup
- [Communication](communication.md) — P2P networking and file transfers
- [RAG](rag.md) — Retrieval-Augmented Generation
- [Orchestrator](orchestrator.md) — Multi-agent coordination
