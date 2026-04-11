# Memory Management

DAIE provides a memory management system that allows agents to store and retrieve information across conversations and tasks.

## Features

- **Persistent Storage** — Memory is saved to disk and persists across sessions
- **In-Memory Mode** — Optional in-memory only mode for temporary memory
- **Multiple Memory Types** — Working memory, semantic memory, and episodic memory
- **Tag-Based Retrieval** — Retrieve memories by tags for efficient filtering
- **Agent-Specific Memory** — Each agent has its own isolated memory space
- **Automatic Initialization** — Memory is automatically initialized when an agent starts
- **Multiple Storage Backends** — Choose between vector database or binary storage
- **Semantic Search** — Vector database backend enables semantic similarity search

---

## Storage Backends

DAIE supports two storage backends for persistent memory:

### Vector Database (Recommended)

Uses ChromaDB for semantic search capabilities. This is the fastest and most powerful option.

**Features:**
- Semantic search using embeddings
- Fast retrieval with vector indexing
- Persistent storage
- Metadata filtering

**Requirements:**
```bash
pip install chromadb
```

**Usage:**
```python
from daie.config import SystemConfig
from daie.memory import MemoryManager

config = SystemConfig(memory_storage_type="vector")
memory_manager = MemoryManager(config=config)
await memory_manager.start()
```

### Binary File (Default)
...
```

### SQLite Database (Robust Persistence)

Uses SQLite for relational storage, supporting concurrent access and complex querying. This is the best option for multi-agent systems sharing a memory pool.

**Features:**
- ACID compliance (Atomicity, Consistency, Isolation, Durability)
- Concurrent access via WAL (Write-Ahead Logging) mode
- Relational structure for complex filtering
- Native integration with Windows, Linux, and macOS

**Usage:**
```python
from daie.config import SystemConfig
from daie.memory import MemoryManager

config = SystemConfig(memory_storage_type="sqlite")
memory_manager = MemoryManager(config=config)
await memory_manager.start()
```

---

## Persistent vs In-Memory Mode

DAIE supports two memory modes controlled by the `persistent_memory` configuration parameter:

### Persistent Memory (Default)

When `persistent_memory=True` (default), memory is saved to disk and persists across application restarts. This is the recommended mode for production systems.

```python
from daie.config import SystemConfig
from daie.memory import MemoryManager

# Persistent memory (default)
config = SystemConfig(persistent_memory=True)
memory_manager = MemoryManager(config=config)
await memory_manager.start()

# Memory will be saved to disk and restored on restart
```

### In-Memory Only

When `persistent_memory=False`, memory is stored only in RAM and is lost when the application restarts. This is useful for:
- Testing and development
- Temporary sessions
- Scenarios where disk I/O should be minimized

```python
from daie.config import SystemConfig
from daie.memory import MemoryManager

# In-memory only (no persistence)
config = SystemConfig(persistent_memory=False)
memory_manager = MemoryManager(config=config)
await memory_manager.start()

# Memory will be lost when application stops
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `persistent_memory` | bool | `True` | Whether to persist memory across restarts |
| `memory_storage_type` | str | `"binary"` | Storage backend type ("sqlite", "vector", "binary") |
| `memory_root_path` | str | `"./agent_memory"` | Root directory for memory storage |

### Environment Variables

You can also configure persistent memory via environment variables:

```bash
export PERSISTENT_MEMORY=false  # Enable in-memory only mode
export MEMORY_STORAGE_TYPE=binary
export MEMORY_ROOT_PATH=./agent_memory
```

---

## Quick Start

### Persistent Memory (Default)

```python
from daie import Agent, AgentConfig, set_llm
from daie.memory import MemoryManager
from daie.config import SystemConfig

set_llm(ollama_llm="llama3.2:latest")

# Create memory manager with binary storage (default)
memory_manager = MemoryManager()
await memory_manager.start()

# Create agent with memory
agent = Agent(config=AgentConfig(
    name="MemoryAgent",
    system_prompt="You are a helpful assistant with memory.",
))

# Start agent with memory manager
await agent.start(memory_manager=memory_manager)

# Store a memory
memory_manager.store_memory(
    agent_id=agent.id,
    content="User prefers concise answers",
    memory_type="working",
    tags=["user_preference", "communication_style"]
)

# Retrieve memories
memories = memory_manager.retrieve_memories(
    agent_id=agent.id,
    memory_type="working",
    tags=["user_preference"]
)

# Semantic search (only with vector backend)
similar = memory_manager.search_similar(
    agent_id=agent.id,
    query="user preferences",
    limit=5
)
```

### In-Memory Only

```python
from daie import Agent, AgentConfig, set_llm
from daie.memory import MemoryManager
from daie.config import SystemConfig

set_llm(ollama_llm="llama3.2:latest")

# Create memory manager with in-memory only (no persistence)
config = SystemConfig(persistent_memory=False)
memory_manager = MemoryManager(config=config)
await memory_manager.start()

# Create agent with memory
agent = Agent(config=AgentConfig(
    name="MemoryAgent",
    system_prompt="You are a helpful assistant with memory.",
))

# Start agent with memory manager
await agent.start(memory_manager=memory_manager)

# Store a memory (will be lost when application stops)
memory_manager.store_memory(
    agent_id=agent.id,
    content="User prefers concise answers",
    memory_type="working",
    tags=["user_preference", "communication_style"]
)
```

---

## Shared Memory Namespaces

DAIE allows agents to share memory pools across multiple instances using **Namespaces**. This is particularly powerful for `Orchestrator` groups or `Parliament` specialized teams.

### How it works

When multiple agents have the same `memory_namespace` configured in their `AgentConfig`, they will read and write to the same logical storage partition in the `MemoryManager`.

### Usage

```python
from daie import Agent, AgentConfig

shared_name = "strategic_planning_2024"

# Agent A
agent_a = Agent(config=AgentConfig(
    name="Architect",
    memory_namespace=shared_name
))

# Agent B
agent_b = Agent(config=AgentConfig(
    name="Auditor",
    memory_namespace=shared_name
))

# Any episodic or semantic memory stored by Agent A 
# will be visible to Agent B during its retrieval cycles.
```

### Integration with Multi-Agent Systems

The `Orchestrator` and `HybridParliamentOrchestrator` automatically inject a shared namespace into all their sub-agents if one is provided during initialization.

```python
orchestrator = Orchestrator(
    main_agent=boss,
    sub_agents=[worker1, worker2],
    shared_namespace="team_context"
)
```

---

## Memory Types

### Working Memory

Short-term memory for current session context:

```python
memory_manager.store_memory(
    agent_id=agent.id,
    content="User is working on a Python project",
    memory_type="working",
    tags=["current_task", "python"]
)
```

### Semantic Memory

Long-term memory for facts and knowledge:

```python
memory_manager.store_memory(
    agent_id=agent.id,
    content="Python was created by Guido van Rossum in 1991",
    memory_type="semantic",
    tags=["python", "history", "fact"]
)
```

### Episodic Memory

Memory for specific events and experiences:

```python
memory_manager.store_memory(
    agent_id=agent.id,
    content="User asked about machine learning on 2024-01-15",
    memory_type="episodic",
    tags=["machine_learning", "user_interaction"]
)
```

---

## MemoryManager

### Initialization

```python
from daie.memory import MemoryManager
from daie.config import SystemConfig

# Create memory manager with default (binary) storage
memory_manager = MemoryManager()

# Or with specific storage type
config = SystemConfig(memory_storage_type="vector")
memory_manager = MemoryManager(config=config)

# Or with in-memory only (no persistence)
config = SystemConfig(persistent_memory=False)
memory_manager = MemoryManager(config=config)

# Start the memory manager
await memory_manager.start()

# Stop the memory manager
await memory_manager.stop()
```

### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the memory manager and initialize storage (async) |
| `stop()` | Stop the memory manager and save state (async) |
| `initialize_agent_memory(agent_id)` | Initialize memory for a specific agent |
| `store_memory(agent_id, content, memory_type, tags)` | Store a memory item |
| `retrieve_memories(agent_id, memory_type, tags)` | Retrieve memories by type and tags |
| `search_similar(agent_id, query, memory_type, limit)` | Semantic search for similar memories |
| `delete_memory(agent_id, memory_id)` | Delete a specific memory |
| `clear_agent_memory(agent_id)` | Clear all memories for an agent |
| `get_memory_count(agent_id, memory_type)` | Get count of memory items |
| `get_storage_info()` | Get information about storage backend |

### Storing Memories

```python
memory_manager.store_memory(
    agent_id="agent-123",
    content="The user prefers dark mode",
    memory_type="working",  # "working", "semantic", or "episodic"
    tags=["user_preference", "ui_settings"]
)
```

### Retrieving Memories

```python
# Retrieve all working memories
memories = memory_manager.retrieve_memories(
    agent_id="agent-123",
    memory_type="working"
)

# Retrieve memories with specific tags
memories = memory_manager.retrieve_memories(
    agent_id="agent-123",
    tags=["user_preference"]
)

# Retrieve by both type and tags
memories = memory_manager.retrieve_memories(
    agent_id="agent-123",
    memory_type="semantic",
    tags=["python"]
)
```

### Semantic Search

```python
# Search for similar memories (vector backend only)
similar = memory_manager.search_similar(
    agent_id="agent-123",
    query="user preferences",
    memory_type="working",  # Optional: filter by type
    limit=10
)

# Works with all backends (falls back to text matching)
similar = memory_manager.search_similar(
    agent_id="agent-123",
    query="Python programming",
    limit=5
)
```

---

## Memory Structure

Each memory item contains:

```python
@dataclass
class MemoryItem:
    id: str                    # Unique identifier
    content: str               # The memory content
    memory_type: str           # "working", "semantic", or "episodic"
    timestamp: float           # Timestamp of creation
    metadata: Dict[str, Any]   # Additional metadata
    tags: List[str]            # Tags for categorization
```

---

## Autonomous Memory Summarization (Episodic)

To maintain long-term context without overwhelming the LLM or storage, DAIE supports autonomous background summarization of episodic memory.

### How it works

1.  **Trigger**: After every `Agent.execute_task` completion, the agent checks if summarization is enabled.
2.  **Threshold**: If the number of episodic memory items exceeds `memory_summarization_threshold`, a summarization task is scheduled.
3.  **Background Execution**: The summarization runs in a background thread to avoid blocking the agent's response to the user.
4.  **Consolidation**: Multiple related episodic memories are compressed into a single, high-density "Summary" memory item, and the original granular items are archived or removed.

### Configuration

Enable summarization in your `AgentConfig`:

```python
from daie import AgentConfig

config = AgentConfig(
    name="SmartAgent",
    enable_memory_summarization=True,
    memory_summarization_threshold=20,  # Summarize every 20 items
)
```

### Benefits

-   **Reduced Latency**: Keeps the retrieved context window small and relevant.
-   **Lower Costs**: Reduces token usage by consolidating redundant information.
-   **Long-term Consistency**: Prevents "forgetting" by distilling key events into stable summaries.

---

## Integration with Agents

Memory is automatically integrated with agents when a `MemoryManager` is provided:

```python
from daie import Agent, AgentConfig
from daie.memory import MemoryManager
from daie.config import SystemConfig

# Use vector database for best performance
config = SystemConfig(memory_storage_type="vector")
memory_manager = MemoryManager(config=config)
await memory_manager.start()

agent = Agent(config=AgentConfig(
    name="SmartAgent",
    system_prompt="You are a helpful assistant.",
))

# Start agent with memory manager
await agent.start(memory_manager=memory_manager)

# The agent can now access and store memories
# Memory is automatically used in the ReAct loop
```

---

## Storage Location

By default, memories are stored in the `agent_memory/` directory:

```
agent_memory/
├── .chroma/              # Vector database files (if using vector backend)
├── agent-123/
│   └── memory.pkl        # Binary file (if using binary backend)
└── agent-456/
    └── ...
```

---

## Performance Comparison

| Backend | Write Speed | Read Speed | File Size | Semantic Search |
|---------|-------------|------------|-----------|-----------------|
| Vector | Fast | Very Fast | Medium | ✅ Yes |
| Binary | Very Fast | Very Fast | Small | ❌ No (text matching) |

**Recommendation:** Use `vector` backend for production systems requiring semantic search capabilities. Use `binary` for simple, fast storage without semantic search needs.

---

## Best Practices

1. **Use Vector Backend** — For production systems, use the vector database backend for semantic search capabilities
2. **Use Tags Effectively** — Tags help organize and retrieve memories efficiently
3. **Choose Appropriate Memory Types** — Use working memory for temporary context, semantic for facts, episodic for events
4. **Regular Cleanup** — Clear old working memories to prevent clutter
5. **Meaningful Content** — Store concise, meaningful content for better retrieval
6. **Install Dependencies** — Install ChromaDB for vector backend: `pip install chromadb`
7. **Use Persistent Memory** — Enable `persistent_memory=True` for production systems to preserve memory across restarts
8. **Use In-Memory Mode for Testing** — Use `persistent_memory=False` for testing and development to avoid disk I/O

---

## Next Steps

- [Agents](agents.md) — Agent configuration and the ReAct loop
- [RAG](rag.md) — Retrieval-Augmented Generation for document-based knowledge
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — P2P networking and file transfers
