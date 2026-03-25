# DAIE — Decentralized AI Ecosystem

A Python library for building AI agents that reason, use tools, and stream responses — powered by any LLM (Ollama, OpenAI, Anthropic, Google, Azure, OpenRouter).

---

## Features

- **ReAct agent loop** — LLM reasons → picks a tool → sees the result → iterates until it gives a final answer
- **Streaming tokens** — set `stream=True` once, tokens print as they arrive
- **Pre-built tools** — file system, HTTP API calls, Selenium Chrome browser automation
- **Custom tools** — decorate any async function with `@tool` and it works identically to built-in tools
- **Multi-provider LLM** — Ollama (default), OpenAI, Anthropic, Google, Azure, OpenRouter
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

### 1. Simple chat with streaming

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole

set_llm(ollama_llm="llama3.2:latest", stream=True)

async def main():
    agent = Agent(config=AgentConfig(
        name="ALEX",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are ALEX, a helpful assistant.",
    ))
    await agent.start()
    await agent.send_message("What is the capital of France?")
    await agent.stop()

asyncio.run(main())
```

### 2. Agent with tools (ReAct loop)

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.tools import FileManagerTool, APICallTool, tool

set_llm(ollama_llm="llama3.2:latest")

# Custom tool via decorator
@tool(name="greet", description="Greet a person by name")
async def greet(name: str) -> str:
    return f"Hello, {name}!"

async def main():
    agent = Agent(config=AgentConfig(
        name="Bot",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a helpful assistant with access to tools.",
    ))

    agent.add_tool(greet)
    agent.add_tool(FileManagerTool())
    agent.add_tool(APICallTool())

    await agent.start()

    # LLM decides which tool to use
    result = await agent.execute_task("Create a file called notes.txt with content 'hello world'")
    print(result)

    result = await agent.execute_task("Greet Alice")
    print(result)

    await agent.stop()

asyncio.run(main())
```

### 3. Interactive chat loop

```python
import asyncio
from daie import Agent, AgentConfig, set_llm, LLMType
from daie.agents import AgentRole

set_llm(ollama_llm="gemma3:1b", temperature=0.3, max_tokens=1500, stream=True)

async def main():
    agent = Agent(config=AgentConfig(name="ALEX", role=AgentRole.GENERAL_PURPOSE))
    await agent.start()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        response = await agent.send_message(user_input)
        if not get_llm_config().stream:
            print(f"ALEX: {response}")
        print()

    await agent.stop()

asyncio.run(main())
```

---

## P2P Networking & File Transfers

DAIE supports cross-machine, peer-to-peer communication over HTTP via its `CommunicationManager`. Agents can securely discover peers, delegate tasks over the network (using ACP maps), and securely transfer files utilizing base64 encoding.

### Setting Up a Networked Agent
Configure your agent with a `network_url` and an `auth_token`.

```python
from daie import Agent, AgentConfig
from daie.communication import CommunicationManager

config = AgentConfig(
    name="NetworkWorker",
    network_url="http://<your-public-ip-or-devtunnel>:8000",
    auth_token="secure_cross_machine_token123",
    allow_file_transfers=True
)
agent = Agent(config=config)

# Start comms, which runs the local REST server
comm = CommunicationManager()
await comm.start()
await agent.start(communication_manager=comm)
```

### Exposing the P2P Port Local Sever
By calling `CommunicationManager.start()`, DAIE spins up an embedded FastAPI REST endpoint (`POST /api/v1/a2a/message`) behind the scenes. Network requests containing standard `AgentMessage` bodies will hit this HTTP receiver payload and pipe directly down into your agent's processing loop.

### Secure File Transfers
As long as `allow_file_transfers` is marked `True`, the `A2ASendFileTool` allows your agents to dispatch files to authorized peers. Unauthorized files are automatically rejected without writing an outcome to disk. 

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
    gender="female",
    personality="sarcastic, witty, very direct",
    behavior="always starts sentences with Hmm",

    temperature=0.7,       # overrides global LLM setting for this agent
    max_tokens=1000,
    task_timeout=30,       # seconds before execute_task times out
)
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
├── agents/         Agent, AgentConfig, AgentRole, AgentMessage
├── core/           LLMManager, set_llm(), get_llm()
├── tools/          Tool base class, @tool decorator, FileManagerTool,
│                   APICallTool, SeleniumChromeTool, ToolRegistry
├── utils/          AudioManager, CameraManager, encryption, logging
├── communication/  CommunicationManager (in-memory / NATS)
├── memory/         MemoryManager (working, semantic, episodic)
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

## Development

```bash
git clone https://github.com/yourusername/decentralized-ai-ecosystem.git
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run example chat loop
python simple_ollama_chat_loop.py
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Could not connect to Ollama` | Run `ollama serve` and pull a model: `ollama pull llama3.2` |
| `ModuleNotFoundError: cv2` | `pip install "daie[vision]"` |
| `ModuleNotFoundError: pyaudio` | `pip install "daie[audio]"` |
| Agent not responding | Call `await agent.start()` before `execute_task()` |
| Task timeout | Increase `task_timeout` in `AgentConfig` |
| LLM returns plain text instead of JSON | Normal — the agent treats plain text as a final answer |

---

## Changelog

### v1.1.0 
- Networked P2P Architecture using `httpx` and `fastapi` for robust peer-to-peer Agent interaction.
- Support for cross-machine `A2ASendFileTool` with built-in Base64 security blocking uninvited file transfers.
- `AgentConfig` enhancements providing decentralized node discovery support with DevTunnel and manual IPs.
- Configurable authentication tokens (`auth_token`) for incoming connections.
- Added Persona parameters to `AgentConfig`: `gender`, `personality`, and `behavior` which are automatically woven into the ReAct and Chat loops.
- Increased Ollama HTTP timeouts (to 300s) to easily support massive local models (like `wizard-vicuna-uncensored:7b`), and fixed silent crash bugs during HTTP streaming.

### v1.0.3 
- ReAct-style tool-use loop in `execute_task()` — LLM reasons and picks tools autonomously
- Token streaming via `set_llm(stream=True)` — library-level, no per-call config needed
- Compact tool schema in system prompt — works with small models like `gemma3:1b`
- Fixed `camera.py` — added missing `numpy` import, added `CV2_AVAILABLE` guards
- Fixed `tools/__init__.py` — lazy selenium imports, no crash without browser extras
- Fixed `pyproject.toml` — only actually-used packages in core dependencies
- 193 tests passing

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
