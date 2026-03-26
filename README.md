# DAIE — Decentralized AI Ecosystem

A Python library for building AI agents that reason, use tools, communicate over P2P networks, and stream responses — powered by any LLM (Ollama, OpenAI, Anthropic, Google, Azure, OpenRouter).

---

## Features

- **ReAct agent loop** — LLM reasons → picks a tool → sees the result → iterates until it gives a final answer
- **Multi-Agent Orchestration** — Coordinate main agents and sub-agents for complex goals (e.g. Research Lab, Courtroom)
- **Decentralized RAG** — Every agent can have its own unique knowledge base (TF-IDF retrieval)
- **Vision Capabilities** — Support for vision models (e.g. `qwen3-vl:2b`) with camera integration
- **Streaming tokens** — set `stream=True` once, tokens print as they arrive
- **Pre-built tools** — file system, HTTP API calls, Selenium Chrome browser automation
- **Custom tools** — decorate any function with `@tool` and it works identically to built-in tools
- **Multi-provider LLM** — Ollama (default), OpenAI, Anthropic, Google, Azure, OpenRouter
- **P2P networking** — agents communicate across machines via HTTP with authentication & authorization
- **A2A file transfer** — securely send files between agents over the network using Base64 encoding
- **Agent persona** — configure `gender`, `personality`, and `behavior` traits injected directly into the LLM prompt
- **Per-agent LLM overrides** — each agent can have its own `temperature` and `max_tokens`
- **Camera & audio** — optional OpenCV camera capture and PyAudio microphone/speaker support
- **CLI** — manage agents and the core system from the terminal

---

## Installation

```bash
pip install daie
```

**Optional extras:**

```bash
pip install "daie[audio]"    # PyAudio microphone/speaker support
pip install "daie[vision]"   # OpenCV camera support
pip install "daie[full]"     # audio + vision
pip install "daie[dev]"      # pytest, black, mypy, flake8
```

**Requires Python 3.10+**

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

set_llm(ollama_llm="wizard-vicuna-uncensored:7b")

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
        network_url="http://localhost:8000",
    ))
    await agent1.start(communication_manager=comm)

    # Agent 2 (with auth + file transfers)
    agent2 = Agent(config=AgentConfig(
        name="NodeBravo",
        role=AgentRole.GENERAL_PURPOSE,
        network_url="http://localhost:8001",
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
    comm.stop()

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

## Agent Configuration

```python
from daie.agents.config import AgentConfig, AgentRole

config = AgentConfig(
    name="MyAgent name",   # (ALEX, NOVA, BOB, etc)
    role=AgentRole.GENERAL_PURPOSE,   # or SPECIALIZED, COORDINATOR, WORKER
    goal="Help users with tasks",
    backstory="A capable AI assistant",
    system_prompt="You are a helpful assistant.",

    # Persona traits (automatically injected into LLM prompts)
    gender="female",                             # Literal["male", "female"] or None
    personality="sarcastic, witty, very direct",  # free-form string
    behavior="always starts sentences with Hmm",  # free-form string

    # Per-agent LLM overrides (take priority over global set_llm settings)
    temperature=0.7,
    max_tokens=1000,

    # Task settings
    task_timeout=30,       # seconds before execute_task times out

    # P2P Networking
    network_url="http://your-ip-or-devtunnel:8000",
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
| `FileManagerTool` | Create, read, write, delete, copy, move files and directories |
| `APICallTool` | HTTP GET / POST / PUT / DELETE / PATCH requests |
| `HTTPGetTool` | Simplified HTTP GET |
| `HTTPPostTool` | Simplified HTTP POST |
| `A2ASendFileTool` | Transfer files securely between agents over P2P network |
| `SeleniumChromeTool` | Full Chrome browser automation (requires `pip install "daie[browser]"`) |

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
- **Send direct messages** between agents (in-process or via HTTP for remote agents)
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
    network_url="http://<your-public-ip-or-devtunnel>:8000",
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
pip install "daie[vision]"
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
pip install "daie[audio]"
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
daie/
├── agents/         Agent, AgentConfig, AgentRole, AgentMessage, Orchestrator
├── core/           LLMManager, set_llm(), get_llm()
├── tools/          Tool base class, @tool decorator, FileManagerTool,
│                   APICallTool, A2ASendFileTool, SeleniumChromeTool, ToolRegistry
├── utils/          AudioManager, CameraManager, encryption, logging
├── communication/  CommunicationManager (in-memory + HTTP P2P)
├── registry/       NodeRegistry (decentralized agent discovery)
├── memory/         MemoryManager (working, semantic, episodic)
├── protocols/      Protocol definitions (ACP)
├── config/         SystemConfig, environment settings
└── cli/            Typer-based CLI
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

| File | Description |
|---|---|
| `examples/01_basic_chat.py` | Interactive streaming chat with persona traits (gender, personality, behavior) |
| `examples/02_custom_tools.py` | Custom `@tool` decorator + `FileManagerTool` with ReAct agent loop |
| `examples/03_p2p_networking.py` | Multi-agent P2P messaging, authorization, and A2A file transfer |
| `examples/05_vision_chat.py` | Real-time vision-enabled chat using `qwen3-vl:2b` and local camera |

Run any example:

```bash
source venv/bin/activate
python examples/01_basic_chat.py
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
| `ModuleNotFoundError: cv2` | `pip install "daie[vision]"` |
| `ModuleNotFoundError: pyaudio` | `pip install "daie[audio]"` |
| Agent not responding | Call `await agent.start()` before `execute_task()` |
| Task timeout | Increase `task_timeout` in `AgentConfig` |
| LLM returns plain text instead of JSON | Normal — the agent treats plain text as a final answer |
| `execute_task` takes 30-60s on first call | The local LLM model is loading into memory. Subsequent calls are faster |
| `Failed to load registry` warning | Ensure `node_registry.json` contains valid JSON (not empty) |
| Persona traits not applied | Verify `gender`, `personality`, or `behavior` are set in `AgentConfig` |

---

## Changelog

### v1.0.4
- Generic Multi-Agent Orchestration: Replaced rigid `Classroom` with a flexible `Orchestrator` supporting any coordination context.
- Decentralized RAG: Enabled unique `rag_document_path` per agent, allowing specialized knowledge bases within the same system.
- Vision Support: Integrated `images` parameter in `LLMManager` for Ollama models (e.g. `qwen3-vl:2b`).
- New Example: Added `examples/05_vision_chat.py` for real-time camera-based AI chat.
- Smart Delegation: Orchestrator now injects sub-agent goals into the coordinator's system prompt for intelligent task routing.
- Agent Persona system: configurable `gender`, `personality`, and `behavior` traits dynamically injected into LLM prompts for both chat and ReAct tool loops.
- Per-agent LLM overrides: `temperature` and `max_tokens` from `AgentConfig` are now passed into every `invoke()` call, allowing multiple agents with different settings on the same global LLM.
- Increased Ollama HTTP timeouts (to 300s) to support massive local models (e.g. `wizard-vicuna-uncensored:7b`).
- Fixed silent crash bugs during HTTP streaming with proper error reporting.
- Rewrote `examples/03_p2p_networking.py` to correctly demonstrate in-process multi-agent messaging, authorization, and file transfer.
- Added graceful `Ctrl+C` handling in `examples/01_basic_chat.py`.

### v1.0.3
- Networked P2P Architecture using `httpx` and `fastapi` for robust peer-to-peer Agent interaction.
- Support for cross-machine `A2ASendFileTool` with built-in Base64 security blocking uninvited file transfers.
- `AgentConfig` enhancements providing decentralized node discovery support with DevTunnel and manual IPs.
- Configurable authentication tokens (`auth_token`) for incoming connections.

### v1.0.2
- ReAct-style tool-use loop in `execute_task()` — LLM reasons and picks tools autonomously
- Token streaming via `set_llm(stream=True)` — library-level, no per-call config needed
- Compact tool schema in system prompt — works with small models like `gemma3:1b`
- Fixed `camera.py` — added missing `numpy` import, added `CV2_AVAILABLE` guards
- Fixed `tools/__init__.py` — lazy selenium imports, no crash without browser extras
- Fixed `pyproject.toml` — only actually-used packages in core dependencies

### v1.0.1
- HTTP session pooling for LLM calls
- Lazy task queue initialization
- Configurable task timeouts
- Optional selenium/fastapi imports

### v1.0.0
- Initial release

---

## License

MIT — see [LICENSE](LICENSE)

## Author

Built by **Kanishk Kumar Singh** — kanishkkumar2004@gmail.com
