# Agents

The `Agent` class is the core of DAIE. Each agent has a unique identity, tools, and can reason autonomously using the ReAct loop.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER / APPLICATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         IDENTITY                                    │    │
│  │  • Name                                                             │    │
│  │  • Role                                                             │    │
│  │  • Goal                                                             │    │
│  │  • Backstory                                                        │    │
│  │  • System Prompt                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         PERSONA                                     │    │
│  │  • Gender                                                           │    │
│  │  • Personality                                                      │    │
│  │  • Behavior                                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      REACT LOOP ENGINE                              │    │
│  │  • Reasoning                                                        │    │
│  │  • Tool Selection                                                   │    │
│  │  • Execution                                                        │    │
│  │  • Iteration                                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                        │
│                    ▼               ▼               ▼                        │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐    │
│  │      TOOLS          │ │      MEMORY         │ │      RAG ENGINE     │    │
│  │  • File Manager     │ │  • Working Memory   │ │  • Document Load    │    │
│  │  • API Calls        │ │  • Semantic Memory  │ │  • TF-IDF Index     │    │
│  │  • Selenium         │ │  • Episodic Memory  │ │  • Context Retrieve │    │
│  │  • A2A Messaging    │ │                     │ │                     │    │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    COMMUNICATION MANAGER                            │    │
│  │  • P2P networking                                                   │    │
│  │  • HTTP messaging                                                   │    │
│  │  • Authentication                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM MANAGER                                    │
│  • Ollama  • OpenAI  • Anthropic  • Google  • Azure  • OpenRouter           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Creating an Agent

### Basic Agent

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole

set_llm(ollama_llm="llama3.2:latest")

agent = Agent(config=AgentConfig(
    name="MyAgent",
    role=AgentRole.GENERAL_PURPOSE,
    goal="Help users with tasks",
    system_prompt="You are a helpful AI assistant.",
))

await agent.start()
```

### Agent with Persona

```python
agent = Agent(config=AgentConfig(
    name="Alex",
    role=AgentRole.GENERAL_PURPOSE,
    system_prompt="You are a helpful assistant.",
    gender="female",
    personality="sassy, witty, and very direct",
    behavior="always uses emojis and speaks enthusiastically",
    temperature=0.9,
    max_tokens=1024
))
```

### Agent with RAG

```python
agent = Agent(config=AgentConfig(
    name="Expert",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a domain expert.",
    rag_document_path="data/expert_knowledge/",
    enable_rag=True,
    rag_strict_context=False  # Set True to ONLY answer from documents
))
```

---

## AgentConfig

The `AgentConfig` dataclass defines all parameters for an agent:

### Identity

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"DefaultAgent"` | Agent display name |
| `role` | `AgentRole` | `GENERAL_PURPOSE` | Agent role type |
| `goal` | `str` | `"Perform general tasks"` | Agent's main purpose |
| `backstory` | `str` | `"Default AI agent"` | Agent's backstory |
| `system_prompt` | `str` | `"You are a helpful AI agent..."` | System prompt for LLM |
| `capabilities` | `List[str]` | `[]` | List of capabilities |

### LLM Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm_provider` | `str` | `"ollama"` | LLM provider |
| `llm_model` | `str` | `"llama3"` | Default LLM model |
| `temperature` | `float` | `0.7` | LLM temperature (0.0-1.0) |
| `max_tokens` | `int` | `1000` | Maximum tokens per response |
| `stream` | `bool` | `False` | Whether to stream tokens |

### Persona Traits

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gender` | `Literal["male", "female"] \| None` | `None` | Agent gender |
| `personality` | `str \| None` | `None` | Personality traits |
| `behavior` | `str \| None` | `None` | Behavioral instructions |

### Task Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task_timeout` | `int` | `60` | Task timeout in seconds |
| `max_concurrent_tasks` | `int` | `5` | Max concurrent tasks |
| `response_delay` | `float` | `0.5` | Delay before responding |

### P2P Networking

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `network_url` | `str \| None` | `None` | Base URL for P2P communication |
| `auth_token` | `str \| None` | `None` | Authentication token |
| `allow_file_transfers` | `bool` | `False` | Allow incoming file transfers |
| `allowed_senders` | `List[str]` | `[]` | Whitelist of sender IDs (empty = allow all) |
| `communication_timeout` | `int` | `30` | Communication timeout in seconds |
| `heartbeat_interval` | `int` | `10` | Heartbeat interval in seconds |

### RAG Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rag_document_path` | `str \| None` | `None` | Path to documents directory |
| `enable_rag` | `bool` | `False` | Enable RAG functionality |
| `rag_strict_context` | `bool` | `False` | Only answer from documents |

### Audio & Camera Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_audio_input` | `bool` | `False` | Enable microphone |
| `enable_audio_output` | `bool` | `False` | Enable speaker |
| `audio_device_index` | `int` | `-1` | Audio device index (-1 = default) |
| `audio_sample_rate` | `int` | `16000` | Audio sampling rate in Hz |
| `enable_camera` | `bool` | `False` | Enable camera |
| `camera_device_index` | `int` | `0` | Camera device index |
| `camera_resolution` | `str` | `"640x480"` | Camera resolution |
| `camera_fps` | `int` | `30` | Camera frames per second |

---

## AgentRole

The `AgentRole` enum defines agent role types:

```python
from daie.agents.config import AgentRole

AgentRole.GENERAL_PURPOSE  # "general-purpose"
AgentRole.SPECIALIZED      # "specialized"
AgentRole.WORKER           # "worker"
AgentRole.COORDINATOR      # "coordinator"
AgentRole.ANALYZER         # "analyzer"
AgentRole.EXECUTOR         # "executor"
```

---

## Agent Methods

### Lifecycle

```python
# Start the agent (initializes task queue, RAG engine, communication)
await agent.start(
    communication_manager=comm,  # Optional
    memory_manager=mem,          # Optional
    tool_registry=registry       # Optional
)

# Stop the agent
await agent.stop()
```

### Tool Management

```python
# Add a tool
agent.add_tool(tool)

# Remove a tool
agent.remove_tool("tool_name")

# Get a tool
tool = agent.get_tool("tool_name")

# List all tools
tools = agent.list_tools()
```

### Task Execution

```python
# Execute a task (ReAct loop)
result = await agent.execute_task("Calculate 25 * 14")

# Execute a direct tool call
result = await agent.execute_task({
    "name": "file_manager",
    "params": {"action": "create_file", "path": "test.txt", "content": "hello"}
})
```

### Messaging

```python
# Send a conversational message (no tool loop)
response = await agent.send_message("Hello!")

# Send a message to another agent
from daie.agents.message import AgentMessage

msg = AgentMessage(
    sender_id=agent.id,
    receiver_id="other-agent-id",
    content="Hello!",
    message_type="text",
)
await agent.send_message(msg)

# Send a task to another agent
await agent.send_task({"task": "Do something"}, receiver_id="other-agent-id")
```

---

## The ReAct Loop

The `execute_task()` method implements a ReAct (Reasoning + Acting) loop:

1. **LLM reasons** about the task and outputs JSON: `{"thought": "...", "tool": "...", "params": {...}}`
2. **Tool is executed** and the result is added to history
3. **LLM sees the result** and reasons again
4. **Loop continues** until the LLM outputs `{"thought": "...", "answer": "..."}` or the iteration limit (8) is reached

### Example Flow

```
execute_task("Create notes.txt")
  │
  ├─ LLM: {"thought":"Need to create a file", "tool":"file_manager", "params":{"action":"create_file",...}}
  ├─ Run FileManagerTool → {"success":true,...}
  ├─ LLM: {"thought":"File created", "answer":"Done! File created."}
  └─ return "Done! File created."
```

---

## RAG Integration

When RAG is enabled, the agent automatically:

1. **Loads documents** from `rag_document_path` on startup
2. **Retrieves relevant context** for each query using TF-IDF
3. **Augments the prompt** with retrieved context
4. **Optionally restricts** answers to document content (if `rag_strict_context=True`)

```python
config = AgentConfig(
    name="Expert",
    rag_document_path="data/knowledge/",
    enable_rag=True,
    rag_strict_context=True  # Only answer from documents
)
agent = Agent(config=config)
await agent.start()

# Agent will retrieve relevant context before answering
result = await agent.execute_task("What is DAIE?")
```

---

## Next Steps

- [Tools](tools.md) — Pre-built tools and creating custom tools
- [LLM Configuration](llm.md) — Multi-provider LLM setup
- [Communication](communication.md) — P2P networking and file transfers
- [RAG](rag.md) — Retrieval-Augmented Generation
- [Orchestrator](orchestrator.md) — Multi-agent coordination
