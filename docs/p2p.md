# P2P Networking

DAIE supports peer-to-peer (P2P networking for multi-agent communication. Agents can discover peers, send messages, transfer files, and coordinate tasks over decentralized networks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    P2P Network Layer                        │
│                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐  │
│  │   Agent A   │◄────►│   Agent B   │◄────►│   Agent C   │  │
│  └─────────────┘      └─────────────┘      └─────────────┘  │
│         │                    │                    │         │
│         └────────────────────┼────────────────────┘         │
│                              │                              │
│                    CommunicationManager                     │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │   NodeRegistry    │                    │
│                    │  (Discovery)      │                    │
│                    └───────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### CommunicationManager

The [`CommunicationManager`](../src/daie/communication/manager.py:32) handles all P2P communication:

```python
from daie.communication import CommunicationManager

comm = CommunicationManager()
await comm.start()
```

**Key Features:**
- Direct agent-to-agent messaging
- Broadcast messaging to all agents
- File transfer via A2A protocol
- Cross-machine communication via HTTP
- Sender authorization with whitelists
- Connection authentication with tokens

### NodeRegistry

The [`NodeRegistry`](../src/daie/registry/manager.py:15) manages agent discovery:

```python
from daie.registry import NodeRegistry

registry = NodeRegistry()

# Register an agent
registry.register_node(
    agent_id="agent-1",
    capabilities={"role": "specialist", "tools": ["web_search"]},
    network_url="http://localhost:8000"
)

# Discover agents
agents = registry.discover_agents(capability_query="specialist")
```

## Use Cases

### 1. Direct Agent Communication

Agents can send messages directly to each other:

```python
from daie import Agent, AgentConfig
from daie.communication import CommunicationManager
from daie.agents.message import AgentMessage

# Create communication manager
comm = CommunicationManager()
await comm.start()

# Create agents
agent1 = Agent(config=AgentConfig(
    name="NodeAlfa",
    network_url="http://localhost:8000",
))
await agent1.start(communication_manager=comm)

agent2 = Agent(config=AgentConfig(
    name="NodeBravo",
    network_url="http://localhost:8001",
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
```

### 2. Broadcast Messaging

Send messages to all connected agents:

```python
msg = AgentMessage(
    sender_id=agent1.id,
    receiver_id="*",  # Broadcast
    content="Announcement for all agents",
    message_type="text",
)
await comm.broadcast_message(msg)
```

### 3. File Transfer

Transfer files between agents using A2A protocol:

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

### 4. Cross-Machine Communication

Enable communication across different machines:

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

### 5. Task Delegation

Delegate tasks to specialized agents:

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

## Security Features

### Sender Authorization

Restrict which agents can send messages:

```python
config = AgentConfig(
    name="SecureNode",
    allowed_senders=["trusted-agent-id-1", "trusted-agent-id-2"],
)
# Only messages from whitelisted sender IDs will be accepted.
# Empty list = allow all senders.
```

### Connection Authentication

Use authentication tokens for secure communication:

```python
agent = Agent(config=AgentConfig(
    name="SecureNode",
    network_url="http://<your-public-ip-or-devtunnel>:8000",
    auth_token="secure_cross_machine_token123",
    allow_file_transfers=True
))
```

## Agent Connect Protocol (ACP)

The ACP defines how tasks are delegated and results are returned:

1. **Coordinator** sends a task message with `correlation_id`
2. **Specialist** receives the task and executes it
3. **Specialist** sends back the result with the same `correlation_id`
4. **Coordinator** receives the result and resolves the pending future

## Message Types

| Type | Description |
|------|-------------|
| `text` | Plain text message |
| `task` | Task delegation message |
| `file` | File transfer message |

## API Reference

### CommunicationManager Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the communication manager |
| `stop()` | Stop the communication manager |
| `register_agent(agent)` | Register an agent for communication |
| `deregister_agent(agent_id)` | Deregister an agent |
| `get_agent(agent_id)` | Get an agent by ID |
| `send_message(message)` | Send a message to an agent |
| `broadcast_message(message)` | Broadcast a message to all agents |

### CommunicationManager Properties

| Property | Description |
|----------|-------------|
| `is_connected` | Whether communication is connected |
| `peer_count` | Number of connected peers |

### NodeRegistry Methods

| Method | Description |
|--------|-------------|
| `register_node(agent_id, capabilities, network_url)` | Register a node |
| `deregister_node(agent_id)` | Deregister a node |
| `get_node(agent_id)` | Get node metadata |
| `discover_agents(capability_query)` | Find agents by capability |

## Example

See [`examples/03_p2p_networking.py`](../examples/03_p2p_networking.py:1) for a complete working example.

## Next Steps

- [Node](node.md) — Node abstraction for managing agents
- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — Detailed communication documentation
