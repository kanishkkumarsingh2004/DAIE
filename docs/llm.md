# LLM Configuration

DAIE supports multiple LLM providers through a unified interface. Configure once, use everywhere.

## Supported Providers

| Provider | LLMType | Default Model | Notes |
|----------|----------|---------------|-------|
| Ollama | `LLMType.OLLAMA` | `llama3.2:latest` | Local, free, default |
| OpenAI | `LLMType.OPENAI` | `gpt-4o-mini` | Requires API key |
| Anthropic | `LLMType.ANTHROPIC` | `claude-3-sonnet-20240229` | Requires API key |
| Google | `LLMType.GOOGLE` | `gemini-pro` | Requires API key |
| Azure OpenAI | `LLMType.AZURE` | `gpt-4` | Requires API key + base URL |
| OpenRouter | `LLMType.OPENROUTER` | `mistralai/mistral-7b-instruct` | Requires API key |

---

## Basic Configuration

### Ollama (Default)

```python
from daie import set_llm

# Basic setup
set_llm(ollama_llm="llama3.2:latest")

# With streaming
set_llm(ollama_llm="llama3.2:latest", stream=True)

# With custom parameters
set_llm(ollama_llm="llama3.2:latest", temperature=0.7, max_tokens=1000)
```

### OpenAI

```python
from daie import set_llm, LLMType

set_llm(
    llm_type=LLMType.OPENAI,
    model_name="gpt-4o-mini",
    api_key="sk-..."
)
```

### Anthropic

```python
from daie import set_llm, LLMType

set_llm(
    llm_type=LLMType.ANTHROPIC,
    model_name="claude-3-sonnet-20240229",
    api_key="..."
)
```

### Google

```python
from daie import set_llm, LLMType

set_llm(
    llm_type=LLMType.GOOGLE,
    model_name="gemini-pro",
    api_key="..."
)
```

### Azure OpenAI

```python
from daie import set_llm, LLMType

set_llm(
    llm_type=LLMType.AZURE,
    model_name="gpt-4",
    api_key="...",
    base_url="https://<resource>.openai.azure.com"
)
```

### OpenRouter

```python
from daie import set_llm, LLMType

set_llm(
    llm_type=LLMType.OPENROUTER,
    model_name="mistralai/mistral-7b-instruct",
    api_key="..."
)
```

---

## Configuration Functions

### set_llm()

Set the global LLM configuration:

```python
from daie import set_llm, LLMType

set_llm(
    llm_type=LLMType.OLLAMA,      # Provider type
    model_name="llama3.2:latest",  # Model name
    temperature=0.7,               # Temperature (0.0-1.0)
    max_tokens=1000,               # Max tokens per response
    api_key=None,                  # API key (if required)
    base_url=None,                 # Base URL (for Azure/custom)
    ollama_llm=None,               # Shortcut for Ollama models
    stream=False,                  # Enable streaming
)
```

### get_llm_config()

Get the current LLM configuration:

```python
from daie import get_llm_config

cfg = get_llm_config()
print(cfg.llm_type)      # LLMType.OLLAMA
print(cfg.model_name)    # "llama3.2:latest"
print(cfg.stream)        # False
```

### get_llm()

Get the current LLM instance:

```python
from daie import get_llm

llm = get_llm()
response = llm.invoke("Hello, how are you?")
```

### reset_llm_config()

Reset the LLM configuration to defaults:

```python
from daie import reset_llm_config

reset_llm_config()
```

---

## Streaming

Streaming is a library-level setting — set it once, it applies everywhere:

```python
set_llm(ollama_llm="llama3.2:latest", stream=True)
```

### How Streaming Works

- **`send_message()`**: When `stream=True`, tokens are printed as they arrive. The full response is returned when complete.
- **`execute_task()`**: The reasoning loop runs without streaming (for reliability). The final answer is streamed.

### Per-Agent Streaming

Individual agents can override the global streaming setting:

```python
config = AgentConfig(
    name="MyAgent",
    stream=True  # Override global setting
)
```

---

## Per-Agent LLM Overrides

Each agent can have its own LLM settings that take priority over the global configuration:

```python
from daie import Agent, AgentConfig, set_llm

# Global config
set_llm(ollama_llm="llama3.2:latest", temperature=0.7)

# Agent with custom settings
agent = Agent(config=AgentConfig(
    name="CreativeAgent",
    temperature=0.9,      # Higher temperature for creativity
    max_tokens=2000,      # More tokens for longer responses
    llm_model="llama3.2:latest",
    llm_provider="ollama"
))
```

---

## Vision Models

DAIE supports vision models (e.g., `qwen3-vl:2b`) for image analysis:

```python
import cv2
import base64
from daie import Agent, set_llm
from daie.utils import CameraManager

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

## LLMConfig Dataclass

The `LLMConfig` dataclass holds all LLM configuration:

```python
from daie.core.llm_manager import LLMConfig, LLMType

config = LLMConfig(
    llm_type=LLMType.OLLAMA,
    model_name="llama3.2:latest",
    temperature=0.7,
    max_tokens=1000,
    api_key=None,
    base_url=None,
    stream=False,
    additional_params={}
)
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `llm_type` | `LLMType` | `LLMType.OLLAMA` | Provider type |
| `model_name` | `str` | `"llama3.2:latest"` | Model name |
| `temperature` | `float` | `0.7` | Temperature (0.0-1.0) |
| `max_tokens` | `int` | `1000` | Max tokens per response |
| `api_key` | `str \| None` | `None` | API key |
| `base_url` | `str \| None` | `None` | Base URL |
| `stream` | `bool` | `False` | Enable streaming |
| `additional_params` | `Dict[str, Any]` | `{}` | Additional parameters |

---

## Next Steps

- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — P2P networking and file transfers
- [RAG](rag.md) — Retrieval-Augmented Generation
