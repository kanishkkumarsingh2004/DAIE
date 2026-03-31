# Network Configuration Guide

This guide explains the network configuration parameters used in DAIE for P2P agent communication.

## Overview

DAIE uses two key network configuration parameters in [`AgentConfig`](../src/daie/agents/config.py:22):

1. **`network_url`** - The URL on which the current agent is hosted
2. **`network_connections`** - Dictionary of URLs for other agents this agent can directly communicate with

## Detailed Explanation

### `network_url`

**Purpose:** Defines the base URL where this agent's HTTP server is accessible.

**Type:** `Optional[str]`

**Example:**
```python
config = AgentConfig(
    name="MyAgent",
    network_url="http://localhost:8000",  # This agent is hosted on localhost:8000
)
```

**Use Cases:**
- Local development: `http://localhost:8000`
- Local network: `http://192.168.1.100:8000`
- Internet via DevTunnel: `https://abc123.devtunnels.ms:8000`
- Production server: `https://my-agent.example.com`

**How It's Used:**
- Other agents use this URL to send messages to this agent
- Registered in the [`NodeRegistry`](../src/daie/registry/manager.py:15) for discovery
- Used for direct HTTP communication when no direct connection exists

### `network_connections`

**Purpose:** Maps peer agent IDs to their network URLs for direct bidirectional communication.

**Type:** `Dict[str, str]`

**Example:**
```python
config = AgentConfig(
    name="MyAgent",
    network_url="http://localhost:8000",
    network_connections={
        "agent_b_id": "http://localhost:8001",  # I can directly reach Agent B
        "agent_c_id": "http://localhost:8002",  # I can directly reach Agent C
    }
)
```

**Use Cases:**
- Pre-configured direct connections between agents
- Bidirectional communication setup
- Network topology definition
- Routing optimization (avoid intermediate hops)

**How It's Used:**
- Checked first when sending messages (line 296-298 in [`manager.py`](../src/daie/communication/manager.py:296))
- Used for direct P2P communication without routing
- Stored in [`NodeRegistry`](../src/daie/registry/manager.py:15) for topology awareness
- Enables message routing through intermediate nodes

## Relationship Between `network_url` and `network_connections`

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent A Configuration                    │
├─────────────────────────────────────────────────────────────┤
│  network_url: "http://localhost:8000"                        │
│  network_connections: {                                      │
│    "agent_b": "http://localhost:8001",  ← Direct connection  │
│    "agent_c": "http://localhost:8002",  ← Direct connection  │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- `network_url` is **this agent's address** (where others can find it)
- `network_connections` contains **other agents' addresses** (where this agent can find them)
- Together they enable bidirectional communication

## Message Routing Logic

The [`CommunicationManager`](../src/daie/communication/manager.py:32) uses this priority when sending messages:

1. **Direct Connection Check** (lines 294-298)
   ```python
   sender_connections = sender_node.get("network_connections", {})
   if message.receiver_id in sender_connections:
       direct_url = sender_connections[message.receiver_id]
   ```

2. **Receiver's Network URL** (lines 304-308)
   ```python
   elif receiver_node.get("network_url"):
       network_url = receiver_node["network_url"]
   ```

3. **Route Through Intermediate Nodes** (lines 310-333)
   ```python
   route = self.registry.find_route(message.sender_id, message.receiver_id)
   if route and len(route) > 1:
       # Route through intermediate node
   ```

## Complete Example

```python
from daie import Agent, AgentConfig
from daie.communication import CommunicationManager

# Create communication manager
comm = CommunicationManager()
await comm.start()

# Agent A: Central hub
config_a = AgentConfig(
    name="NodeAlfa",
    network_url="http://localhost:8000",  # A is hosted here
    network_connections={},  # Will be populated after B and C are created
)

# Agent B: Connected to A
config_b = AgentConfig(
    name="NodeBravo",
    network_url="http://localhost:8001",  # B is hosted here
    network_connections={
        "node_alfa_id": "http://localhost:8000",  # B knows A's URL
    },
)

# Agent C: Connected to A
config_c = AgentConfig(
    name="NodeCharlie",
    network_url="http://localhost:8002",  # C is hosted here
    network_connections={
        "node_alfa_id": "http://localhost:8000",  # C knows A's URL
    },
)

# Create agents
agent_a = Agent(config=config_a)
agent_b = Agent(config=config_b)
agent_c = Agent(config=config_c)

# Start agents
await agent_a.start(communication_manager=comm)
await agent_b.start(communication_manager=comm)
await agent_c.start(communication_manager=comm)

# Setup bidirectional connections for A
comm.setup_bidirectional_connection(
    agent_a.id, agent_b.id,
    url_a="http://localhost:8000",
    url_b="http://localhost:8001"
)
comm.setup_bidirectional_connection(
    agent_a.id, agent_c.id,
    url_a="http://localhost:8000",
    url_b="http://localhost:8002"
)

# ... do work ...

await agent_a.stop()
await agent_b.stop()
await agent_c.stop()
await comm.stop()
```

## Network Topology Visualization

After registration, the network topology looks like:

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Topology                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  NodeAlfa (http://localhost:8000)                           │
│    ├─► NodeBravo (http://localhost:8001)                    │
│    └─► NodeCharlie (http://localhost:8002)                  │
│                                                             │
│  NodeBravo (http://localhost:8001)                          │
│    └─► NodeAlfa (http://localhost:8000)                     │
│                                                             │
│  NodeCharlie (http://localhost:8002)                        │
│    └─► NodeAlfa (http://localhost:8000)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Always set `network_url`** for agents that need to communicate over the network
2. **Use `network_connections`** for pre-configured direct connections
3. **Setup bidirectional connections** using [`setup_bidirectional_connection()`](../src/daie/communication/manager.py:568)
4. **Use consistent URLs** across all agents in the network
5. **Consider security** - use HTTPS for internet communication
6. **Use authentication tokens** for secure communication

## Troubleshooting

### Agent can't receive messages
- Check if `network_url` is correctly set
- Verify the URL is accessible from other agents
- Ensure the agent's HTTP server is running

### Messages not routing correctly
- Verify `network_connections` are properly configured
- Check if bidirectional connections are setup
- Use [`find_route()`](../src/daie/communication/manager.py:543) to debug routing

### Connection timeouts
- Increase `communication_timeout` in [`AgentConfig`](../src/daie/agents/config.py:95)
- Check network connectivity between agents
- Verify firewall settings

## API Reference

### AgentConfig

- [`network_url`](../src/daie/agents/config.py:84): Base URL for this agent
- [`network_connections`](../src/daie/agents/config.py:87): Dictionary of peer_id -> network_url

### CommunicationManager

- [`setup_bidirectional_connection()`](../src/daie/communication/manager.py:568): Setup bidirectional connection
- [`get_connected_peers()`](../src/daie/communication/manager.py:556): Get all connected peers
- [`find_route()`](../src/daie/communication/manager.py:543): Find route between agents
- [`get_network_topology()`](../src/daie/communication/manager.py:534): Get complete network topology

### NodeRegistry

- [`register_node()`](../src/daie/registry/manager.py:46): Register agent with network config
- [`get_node()`](../src/daie/registry/manager.py:104): Get agent's network configuration
- [`get_network_topology()`](../src/daie/registry/manager.py:108): Get network topology
- [`find_route()`](../src/daie/registry/manager.py:135): Find route between agents
