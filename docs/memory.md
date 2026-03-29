# Memory Management

DAIE provides a memory management system that allows agents to store and retrieve information across conversations and tasks.

## Features

- **Persistent Storage** — Memory is saved to disk and persists across sessions
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
memory_manager.start()
```

### Binary File (Default)

Uses Python's pickle format for fast serialization and deserialization.

**Features:**
- Fast read/write operations
- Compact file size
- Native Python object support
- Simple implementation

**Usage:**
```python
from daie.config import SystemConfig
from daie.memory import MemoryManager

config = SystemConfig(memory_storage_type="binary")
memory_manager = MemoryManager(config=config)
memory_manager.start()
```

---

## Quick Start

```python
from daie import Agent, AgentConfig, set_llm
from daie.memory import MemoryManager
from daie.config import SystemConfig

set_llm(ollama_llm="llama3.2:latest")

# Create memory manager with binary storage (default)
memory_manager = MemoryManager()
memory_manager.start()

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

# Start the memory manager
memory_manager.start()

# Stop the memory manager
memory_manager.stop()
```

### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the memory manager and initialize storage |
| `stop()` | Stop the memory manager and save state |
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

## Integration with Agents

Memory is automatically integrated with agents when a `MemoryManager` is provided:

```python
from daie import Agent, AgentConfig
from daie.memory import MemoryManager
from daie.config import SystemConfig

# Use vector database for best performance
config = SystemConfig(memory_storage_type="vector")
memory_manager = MemoryManager(config=config)
memory_manager.start()

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

---

## Next Steps

- [Agents](agents.md) — Agent configuration and the ReAct loop
- [RAG](rag.md) — Retrieval-Augmented Generation for document-based knowledge
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — P2P networking and file transfers
