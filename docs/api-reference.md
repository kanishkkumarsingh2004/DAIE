# API Reference

Complete API reference for the DAIE library.

## Core Modules

### Agent

The main agent class for creating AI agents.

```python
from daie import Agent, AgentConfig
```

#### Constructor

```python
Agent(config: AgentConfig)
```

#### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the agent |
| `stop()` | Stop the agent |
| `execute_task(task: str)` | Execute a task using the ReAct loop |
| `send_message(message: str)` | Send a message to the agent |
| `add_tool(tool)` | Add a tool to the agent |
| `remove_tool(tool_name: str)` | Remove a tool from the agent |
| `get_tool(tool_name: str)` | Get a tool by name |
| `list_tools()` | List all available tools |

#### Properties

| Property | Description |
|----------|-------------|
| `id` | Unique agent identifier |
| `name` | Agent name |
| `role` | Agent role |
| `status` | Agent status |
| `tools` | List of available tools |

---

### AgentConfig

Configuration class for agents.

```python
from daie import AgentConfig
```

#### Constructor

```python
AgentConfig(
    name: str = "DefaultAgent",
    role: AgentRole = AgentRole.GENERAL_PURPOSE,
    goal: str = "Perform general tasks",
    system_prompt: str = "You are a helpful AI agent.",
    capabilities: List[str] = [],
    llm_provider: str = "ollama",
    llm_model: str = "llama3.2:latest",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    stream: bool = False,
    enable_rag: bool = False,
    rag_document_path: Optional[str] = None,
    rag_strict_context: bool = False,
    enable_audio: bool = False,
    enable_camera: bool = False,
    network_url: Optional[str] = None,
    auth_token: Optional[str] = None,
    allow_file_transfers: bool = False,
    allowed_senders: List[str] = [],
    task_timeout: int = 30,
    max_concurrent_tasks: int = 5
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | `"DefaultAgent"` | Agent name |
| `role` | `AgentRole` | `GENERAL_PURPOSE` | Agent role |
| `goal` | `str` | `"Perform general tasks"` | Agent goal |
| `system_prompt` | `str` | `"You are a helpful AI agent."` | System prompt |
| `capabilities` | `List[str]` | `[]` | Agent capabilities |
| `llm_provider` | `str` | `"ollama"` | LLM provider |
| `llm_model` | `str` | `"llama3.2:latest"` | LLM model |
| `temperature` | `float` | `0.7` | LLM temperature |
| `max_tokens` | `int` | `1000` | Maximum tokens |
| `stream` | `bool` | `False` | Enable streaming |
| `enable_rag` | `bool` | `False` | Enable RAG |
| `rag_document_path` | `Optional[str]` | `None` | RAG document path |
| `rag_strict_context` | `bool` | `False` | RAG strict context mode |
| `enable_audio` | `bool` | `False` | Enable audio |
| `enable_camera` | `bool` | `False` | Enable camera |
| `network_url` | `Optional[str]` | `None` | Network URL |
| `auth_token` | `Optional[str]` | `None` | Authentication token |
| `allow_file_transfers` | `bool` | `False` | Allow file transfers |
| `allowed_senders` | `List[str]` | `[]` | Allowed senders |
| `task_timeout` | `int` | `30` | Task timeout |
| `max_concurrent_tasks` | `int` | `5` | Max concurrent tasks |

---

### AgentRole

Enum for agent roles.

```python
from daie.agents import AgentRole
```

#### Values

| Value | Description |
|-------|-------------|
| `GENERAL_PURPOSE` | General purpose agent |
| `SPECIALIZED` | Specialized agent |
| `COORDINATOR` | Coordinator agent |
| `WORKER` | Worker agent |
| `ANALYZER` | Analyzer agent |
| `EXECUTOR` | Executor agent |

---

### Orchestrator

Multi-agent coordination system.

```python
from daie import Orchestrator
```

#### Constructor

```python
Orchestrator(
    main_agent: Agent,
    sub_agents: List[Agent],
    context_name: str = "Classroom",
    main_role: str = "Teacher",
    sub_role: str = "Student",
    comm_manager: Optional[CommunicationManager] = None
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the orchestrator |
| `stop()` | Stop the orchestrator |
| `execute_task(task: str)` | Execute a task |

---

## Tools

### Tool

Base class for all tools.

```python
from daie.tools import Tool
```

#### Constructor

```python
Tool(
    name: str,
    description: str,
    parameters: Dict[str, Any] = {}
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `execute(**kwargs)` | Execute the tool |
| `validate(**kwargs)` | Validate parameters |

---

### FileManagerTool

File management tool.

```python
from daie.tools import FileManagerTool
```

#### Actions

| Action | Description |
|--------|-------------|
| `create_file` | Create a file |
| `read_file` | Read a file |
| `write_file` | Write to a file |
| `delete_file` | Delete a file |
| `list_files` | List files in directory |
| `create_directory` | Create a directory |
| `delete_directory` | Delete a directory |

---

### APICallTool

HTTP API call tool.

```python
from daie.tools import APICallTool
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | API endpoint URL |
| `method` | `str` | HTTP method |
| `headers` | `Dict` | Request headers |
| `data` | `Dict` | Request data |
| `params` | `Dict` | Query parameters |

---

### SeleniumChromeTool

Browser automation tool.

```python
from daie.tools import SeleniumChromeTool
```

#### Actions

| Action | Description |
|--------|-------------|
| `open_url` | Open a URL |
| `click` | Click an element |
| `type` | Type text |
| `get_text` | Get element text |
| `screenshot` | Take screenshot |
| `execute_script` | Execute JavaScript |

---

## Communication

### CommunicationManager

Agent communication manager.

```python
from daie.communication import CommunicationManager
```

#### Constructor

```python
CommunicationManager()
```

#### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the manager |
| `stop()` | Stop the manager |
| `register_agent(agent)` | Register an agent |
| `send_message(message)` | Send a message |
| `broadcast_message(message)` | Broadcast a message |

---

### AgentMessage

Message class for agent communication.

```python
from daie.agents.message import AgentMessage
```

#### Constructor

```python
AgentMessage(
    sender_id: str,
    receiver_id: str,
    content: str,
    message_type: str = "text",
    metadata: Dict[str, Any] = {}
)
```

---

## Memory

### MemoryManager

Memory management system.

```python
from daie.memory import MemoryManager
```

#### Constructor

```python
MemoryManager()
```

#### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the manager |
| `stop()` | Stop the manager |
| `store_memory(agent_id, content, memory_type, tags)` | Store a memory |
| `retrieve_memories(agent_id, memory_type, tags)` | Retrieve memories |
| `delete_memory(agent_id, memory_id)` | Delete a memory |
| `clear_agent_memory(agent_id)` | Clear agent memory |

---

## RAG

### RAGEngine

Retrieval-Augmented Generation engine.

```python
from daie.rag import RAGEngine
```

#### Constructor

```python
RAGEngine(
    document_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `load()` | Load documents |
| `retrieve(query, top_k)` | Retrieve relevant chunks |
| `build_context(query, top_k)` | Build context string |

---

## LLM

### set_llm

Set the LLM configuration.

```python
from daie import set_llm

set_llm(
    llm_provider: str = "ollama",
    llm_model: str = "llama3.2:latest",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    stream: bool = False
)
```

---

## CLI

### Commands

| Command | Description |
|---------|-------------|
| `daie --help` | Show help |
| `daie --version` | Show version |
| `daie core init` | Initialize system |
| `daie core start` | Start core system |
| `daie core stop` | Stop core system |
| `daie core status` | Show status |
| `daie agent create` | Create agent |
| `daie agent list` | List agents |
| `daie agent start` | Start agent |
| `daie agent stop` | Stop agent |

---

## Next Steps

- [Getting Started](getting-started.md) — Installation and basic concepts
- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — P2P networking and file transfers
