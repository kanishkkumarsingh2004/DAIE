# Node

A Node is a higher-level abstraction that represents a participating entity in the decentralized AI network. Nodes can host multiple agents, manage connections to peer nodes, and track resources.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Node (Logical Container)                 │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Agent 1   │  │   Agent 2   │  │   Agent 3   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│              CommunicationManager (P2P Layer)               │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼─────┐      ┌─────▼────┐      ┌──────▼───┐
   │  Node A  │◄────►│  Node B  │◄────►│  Node C  │
   └──────────┘      └──────────┘      └──────────┘
```

## Core Components

### Node Class

The [`Node`](../src/daie/core/node.py:11) class represents a node in the decentralized AI network:

```python
from daie.core.node import Node

# Create a node
node = Node(node_id="node-1", name="Production Node")

# Start the node
node.start()

# Add agents to the node
node.add_agent("agent-1")
node.add_agent("agent-2")

# Connect to peer nodes
node.connect("node-2")
node.connect("node-3")
```

**Key Features:**
- Host multiple agents on a single node
- Manage connections to peer nodes
- Store and retrieve resources
- Track node status and agent counts
- Method chaining for fluent API

## Use Cases

### 1. Multi-Agent Hosting

Host multiple agents on a single node:

```python
from daie.core.node import Node

# Create a node
node = Node(node_id="production-node", name="Production Node")
node.start()

# Add multiple agents
node.add_agent("agent-1")
node.add_agent("agent-2")
node.add_agent("agent-3")

# Check agent count
print(f"Node has {node.agent_count} agents")
# Output: Node has 3 agents

# List all agents
print(f"Agents: {node.agents}")
# Output: Agents: ['agent-1', 'agent-2', 'agent-3']
```

### 2. Peer Node Connections

Manage connections to peer nodes:

```python
from daie.core.node import Node

# Create nodes
node_a = Node(node_id="node-a", name="Node A")
node_b = Node(node_id="node-b", name="Node B")
node_c = Node(node_id="node-c", name="Node C")

# Start nodes
node_a.start()
node_b.start()
node_c.start()

# Connect nodes
node_a.connect("node-b")
node_a.connect("node-c")
node_b.connect("node-c")

# Check connections
print(f"Node A connections: {node_a.connections}")
# Output: Node A connections: ['node-b', 'node-c']

# Check if connected
print(f"Node A connected to Node B: {node_a.is_connected('node-b')}")
# Output: Node A connected to Node B: True
```

### 3. Resource Management

Store and retrieve resources on a node:

```python
from daie.core.node import Node

node = Node(node_id="node-1", name="Resource Node")
node.start()

# Set resources
node.set_resource("gpu_count", 4)
node.set_resource("memory_gb", 32)
node.set_resource("model_cache", {"llama2": True, "mistral": True})

# Get resources
gpu_count = node.get_resource("gpu_count")
print(f"GPU count: {gpu_count}")
# Output: GPU count: 4

# Get resource with default
cpu_count = node.get_resource("cpu_count", default=8)
print(f"CPU count: {cpu_count}")
# Output: CPU count: 8

# Get all resource info
resources = node.get_resource_info()
print(f"Resources: {resources}")
# Output: Resources: {'gpu_count': 4, 'memory_gb': 32, 'model_cache': {...}}
```

### 4. Node Status Monitoring

Monitor node status and health:

```python
from daie.core.node import Node

node = Node(node_id="node-1", name="Monitoring Node")
node.start()

# Add agents
node.add_agent("agent-1")
node.add_agent("agent-2")

# Connect to peers
node.connect("node-2")
node.connect("node-3")

# Get node status
status = node.get_status()
print(f"Node Status: {status}")
# Output:
# Node Status: {
#     'node_id': 'node-1',
#     'name': 'Monitoring Node',
#     'status': 'active',
#     'agent_count': 2,
#     'agents': ['agent-1', 'agent-2'],
#     'connection_count': 2,
#     'connections': ['node-2', 'node-3'],
#     'resources': {}
# }
```

### 5. Agent Management

Add and remove agents from a node:

```python
from daie.core.node import Node

node = Node(node_id="node-1", name="Agent Management Node")
node.start()

# Add agents
node.add_agent("agent-1")
node.add_agent("agent-2")
node.add_agent("agent-3")

# Check if agent exists
has_agent = node.has_agent("agent-2")
print(f"Has agent-2: {has_agent}")
# Output: Has agent-2: True

# Remove an agent
node.remove_agent("agent-2")

# Check agent count
print(f"Agent count: {node.agent_count}")
# Output: Agent count: 2
```

### 6. Connection Management

Manage peer node connections:

```python
from daie.core.node import Node

node = Node(node_id="node-1", name="Connection Node")
node.start()

# Connect to peers
node.connect("node-2")
node.connect("node-3")
node.connect("node-4")

# Check connection count
print(f"Connection count: {node.connection_count}")
# Output: Connection count: 3

# Disconnect from a peer
node.disconnect("node-3")

# Check connections
print(f"Connections: {node.connections}")
# Output: Connections: ['node-2', 'node-4']
```

## Node vs P2P Networking

| Aspect | Node | P2P Networking |
|--------|------|----------------|
| **Purpose** | Container/host for agents | Communication protocol |
| **Scope** | Manages multiple agents on one host | Enables agent-to-agent communication |
| **Use Case** | Organizing agents, managing resources | Message routing, discovery, file transfer |
| **Abstraction Level** | Higher-level (logical grouping) | Lower-level (communication layer) |

## Integration with P2P Networking

Nodes work together with P2P networking to provide a complete decentralized AI ecosystem:

```python
from daie.core.node import Node
from daie.communication import CommunicationManager
from daie import Agent, AgentConfig

# Create communication manager (P2P layer)
comm = CommunicationManager()
await comm.start()

# Create a node
node = Node(node_id="node-1", name="Production Node")
node.start()

# Create agents
# network_url: The URL where THIS agent is hosted (others use this to reach it)
agent1 = Agent(config=AgentConfig(
    name="Agent1",
    network_url="http://localhost:8000",  # This agent is hosted on localhost:8000
))
agent2 = Agent(config=AgentConfig(
    name="Agent2",
    network_url="http://localhost:8001",  # This agent is hosted on localhost:8001
))

# Register agents with communication manager
await agent1.start(communication_manager=comm)
await agent2.start(communication_manager=comm)

# Add agents to node
node.add_agent(agent1.id)
node.add_agent(agent2.id)

# Connect to peer nodes
node.connect("node-2")
node.connect("node-3")

# Now agents can communicate via P2P, and the node manages them
```

## API Reference

### Node Constructor

```python
Node(node_id: str, name: str = "Unknown Node")
```

**Parameters:**
- `node_id`: Unique identifier for the node
- `name`: Display name for the node

### Node Properties

| Property | Description |
|----------|-------------|
| `is_active` | Check if the node is active |
| `agents` | Get list of agents on this node |
| `agent_count` | Get number of agents on this node |
| `connections` | Get list of connected peer nodes |
| `connection_count` | Get number of connected peer nodes |

### Node Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the node |
| `stop()` | Stop the node |
| `add_agent(agent_id)` | Add an agent to this node |
| `remove_agent(agent_id)` | Remove an agent from this node |
| `has_agent(agent_id)` | Check if an agent exists on this node |
| `connect(peer_node_id)` | Establish a connection to a peer node |
| `disconnect(peer_node_id)` | Disconnect from a peer node |
| `is_connected(peer_node_id)` | Check if connected to a specific peer node |
| `set_resource(name, value)` | Set a resource value for this node |
| `get_resource(name, default)` | Get a resource value from this node |
| `get_resource_info()` | Get information about all resources on this node |
| `get_status()` | Get node status information |

## Example

See [`examples/03_p2p_networking.py`](../examples/03_p2p_networking.py:1) for a complete working example that demonstrates P2P networking with agents.

## Next Steps

- [Node vs Orchestrator](node-vs-orchestrator.md) — Complete comparison guide with use cases
- [P2P Networking](p2p.md) — P2P communication protocol
- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — Detailed communication documentation
