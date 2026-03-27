# Memory Management

DAIE provides a memory management system that allows agents to store and retrieve information across conversations and tasks.

## Features

- **Persistent Storage** — Memory is saved to disk and persists across sessions
- **Multiple Memory Types** — Working memory, semantic memory, and episodic memory
- **Tag-Based Retrieval** — Retrieve memories by tags for efficient filtering
- **Agent-Specific Memory** — Each agent has its own isolated memory space
- **Automatic Initialization** — Memory is automatically initialized when an agent starts

---

## Quick Start

```python
from daie import Agent, AgentConfig, set_llm
from daie.memory import MemoryManager

set_llm(ollama_llm="llama3.2:latest")

# Create memory manager
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

# Create memory manager
memory_manager = MemoryManager()

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
| `delete_memory(agent_id, memory_id)` | Delete a specific memory |
| `clear_agent_memory(agent_id)` | Clear all memories for an agent |

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

---

## Memory Structure

Each memory item contains:

```python
@dataclass
class MemoryItem:
    id: str                    # Unique identifier
    agent_id: str              # Agent this memory belongs to
    content: str               # The memory content
    memory_type: str           # "working", "semantic", or "episodic"
    tags: List[str]            # Tags for categorization
    created_at: float          # Timestamp of creation
    updated_at: float          # Timestamp of last update
    metadata: Dict[str, Any]   # Additional metadata
```

---

## Integration with Agents

Memory is automatically integrated with agents when a `MemoryManager` is provided:

```python
from daie import Agent, AgentConfig
from daie.memory import MemoryManager

memory_manager = MemoryManager()
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
├── agent-123/
│   ├── working/
│   │   └── memories.json
│   ├── semantic/
│   │   └── memories.json
│   └── episodic/
│       └── memories.json
└── agent-456/
    └── ...
```

---

## Best Practices

1. **Use Tags Effectively** — Tags help organize and retrieve memories efficiently
2. **Choose Appropriate Memory Types** — Use working memory for temporary context, semantic for facts, episodic for events
3. **Regular Cleanup** — Clear old working memories to prevent clutter
4. **Meaningful Content** — Store concise, meaningful content for better retrieval

---

## Next Steps

- [Agents](agents.md) — Agent configuration and the ReAct loop
- [RAG](rag.md) — Retrieval-Augmented Generation for document-based knowledge
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — P2P networking and file transfers
