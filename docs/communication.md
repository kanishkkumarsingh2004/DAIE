# Communication

DAIE supports multi-agent communication via its `CommunicationManager`. Agents can discover peers, send messages, transfer files, and coordinate tasks over P2P networks.

## Features

- **Peer Discovery** via the built-in `NodeRegistry`
- **Direct Messaging** between agents (in-process or via HTTP for remote agents)
- **File Transfers** securely using Base64 encoding with `A2ASendFileTool`
- **Sender Authorization** with `allowed_senders` whitelists
- **Connection Authentication** with `auth_token`
- **Task Delegation** via the Agent Connect Protocol (ACP)

---

## CommunicationManager

The `CommunicationManager` handles all agent communication:

```python
from daie.communication import CommunicationManager

comm = CommunicationManager()
await comm.start()
# ... use comm ...
await comm.stop()
```

### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the communication manager (async) |
| `stop()` | Stop the communication manager (async) |
| `register_agent(agent)` | Register an agent for communication |
| `deregister_agent(agent_id)` | Deregister an agent |
| `get_agent(agent_id)` | Get an agent by ID |
| `send_message(message)` | Send a message to an agent |
| `broadcast_message(message)` | Broadcast a message to all agents |

### Properties

| Property | Description |
|----------|-------------|
| `is_connected` | Whether communication is connected |
| `peer_count` | Number of connected peers |

---

## Setting Up Networked Agents

### Basic Setup

```python
from daie import Agent, AgentConfig
from daie.communication import CommunicationManager

# Create shared communication bus
comm = CommunicationManager()
await comm.start()

# Create agents
# network_url: The URL where THIS agent is hosted (others use this to reach it)
agent1 = Agent(config=AgentConfig(
    name="NodeAlfa",
    network_url="http://localhost:8000",  # This agent is hosted on localhost:8000
))
await agent1.start(communication_manager=comm)

agent2 = Agent(config=AgentConfig(
    name="NodeBravo",
    network_url="http://localhost:8001",  # This agent is hosted on localhost:8001
))
await agent2.start(communication_manager=comm)
```

### With Authentication

```python
agent = Agent(config=AgentConfig(
    name="SecureNode",
    network_url="http://<your-public-ip-or-devtunnel>:8000",
    auth_token="secure_cross_machine_token123",
    allow_file_transfers=True
))
await agent.start(communication_manager=comm)
```

### With Sender Whitelist

```python
config = AgentConfig(
    name="SecureNode",
    allowed_senders=["trusted-agent-id-1", "trusted-agent-id-2"],
)
# Only messages from whitelisted sender IDs will be accepted.
# Empty list = allow all senders.
```

---

## Sending Messages

### Direct Message

```python
from daie.agents.message import AgentMessage

msg = AgentMessage(
    sender_id=agent1.id,
    receiver_id=agent2.id,
    content="Hello from NodeAlfa!",
    message_type="text",
)
await comm.send_message(msg)
```

### Using A2ASendMessageTool

```python
from daie.tools.a2a import A2ASendMessageTool

msg_tool = A2ASendMessageTool()
msg_tool.set_agent(agent1)

result = await msg_tool.execute({
    "target_agent_id": agent2.id,
    "message": "Hello from NodeAlfa!",
})
```

### Broadcast Message

```python
msg = AgentMessage(
    sender_id=agent1.id,
    receiver_id="*",  # Broadcast
    content="Announcement for all agents",
    message_type="text",
)
await comm.broadcast_message(msg)
```

---

## File Transfers

### Using A2ASendFileTool

```python
from daie.tools.a2a_file import A2ASendFileTool

file_tool = A2ASendFileTool()
file_tool.set_agent(agent1)

result = await file_tool.execute({
    "receiver_id": agent2.id,
    "file_path": "document.pdf",
    "message": "Here's the document you requested",
})
```

### Receiving Files

The receiving agent must have `allow_file_transfers=True` in its config:

```python
agent2 = Agent(config=AgentConfig(
    name="Receiver",
    allow_file_transfers=True,
))
```

Files are automatically saved to a `downloads/` directory.

---

## Task Delegation

### Using A2ADelegateTaskTool

```python
from daie.tools.a2a import A2ADelegateTaskTool

delegate_tool = A2ADelegateTaskTool()
delegate_tool.set_agent(coordinator)

result = await delegate_tool.execute({
    "target_agent_id": specialist.id,
    "task_payload": {"task": "Analyze this data and provide insights"},
    "mapping_rules": {},  # Optional ACP I/O mapping
})
```

### Agent Connect Protocol (ACP)

The ACP defines how tasks are delegated and results are returned:

1. **Coordinator** sends a task message with `correlation_id`
2. **Specialist** receives the task and executes it
3. **Specialist** sends back the result with the same `correlation_id`
4. **Coordinator** receives the result and resolves the pending future

---

## NodeRegistry

The `NodeRegistry` manages agent discovery:

```python
from daie.registry import NodeRegistry

registry = NodeRegistry()
await registry.start()  # Required to start discovery services

# Register a node
await registry.register_node(
    agent_id="agent-1",
    capabilities={"role": "specialist", "tools": ["web_search"]},
    network_url="http://localhost:8000"
)

# Get a node
node = registry.get_node("agent-1")

# List all nodes
nodes = registry.list_nodes()

# Stop the registry
await registry.stop()
```

> [!NOTE]
> When using `CommunicationManager`, the internal `NodeRegistry`'s lifecycle is managed automatically. You only need to explicitly `start()` and `stop()` the registry when using it in standalone mode.

---

## AgentMessage

The `AgentMessage` class defines the message structure:

```python
from daie.agents.message import AgentMessage

msg = AgentMessage(
    sender_id="agent-1",           # Sender agent ID
    receiver_id="agent-2",         # Receiver agent ID (or "*" for broadcast)
    content="Hello!",              # Message content
    message_type="text",           # Message type: "text", "task", "file"
    metadata={"key": "value"},     # Optional metadata
)
```

### Message Types

| Type | Description |
|------|-------------|
| `text` | Plain text message |
| `task` | Task delegation message |
| `file` | File transfer message |

---

## Cross-Machine Communication

For communication across different machines:

1. **Use DevTunnel or public IP** for the `network_url`
2. **Set authentication tokens** for security
3. **Configure firewall** to allow the communication port

```python
# Machine 1
agent1 = Agent(config=AgentConfig(
    name="RemoteAgent1",
    network_url="https://your-devtunnel-url.devtunnels.ms:8000",
    auth_token="secure_token_123",
))

# Machine 2
agent2 = Agent(config=AgentConfig(
    name="RemoteAgent2",
    network_url="https://your-devtunnel-url.devtunnels.ms:8001",
    auth_token="secure_token_123",
))
```

---

## Security & Hardening

DAIE includes built-in security features for production-ready decentralized environments.

### End-to-End Encryption (E2EE)

All agent-to-agent communication can be encrypted using X25519 key exchange and XSalsa20-Poly1305 symmetric encryption.

To enable E2EE, set `enable_e2e_encryption=True` in your `SystemConfig`:

```python
from daie.config import SystemConfig, AgentConfig
from daie import Agent

config = SystemConfig(enable_e2e_encryption=True)
agent = Agent(config=AgentConfig(name="SecureAgent"))
# Agents automatically generate X25519 keypairs on startup if not provided
```

### Inbound Rate Limiting

Protect your agents from message flooding by enabling rate limiting in `SystemConfig`:

```python
config = SystemConfig(
    enable_rate_limiting=True,
    rate_limit_max_messages=100,  # Max messages
    rate_limit_window=60.0        # Per 60 seconds
)
```

### Adaptive Reconnection

Nodes automatically attempt to reconnect to the network with an exponential backoff if the connection is lost. You can configure the heartbeat interval in your environment or via `SystemConfig`.

---

## Next Steps

- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Orchestrator](orchestrator.md) — Multi-agent coordination
- [RAG](rag.md) — Retrieval-Augmented Generation
