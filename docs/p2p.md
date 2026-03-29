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

### 4. Cross-Machine Communication (Connecting Two Agents on Different Devices)

This guide shows you how to connect two AI agents running on different devices (computers) on the same network or across the internet.

#### Prerequisites

1. **Both devices must have DAIE installed:**
   ```bash
   pip install daie
   ```

2. **Both devices must have Ollama installed and running:**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull a model
   ollama pull llama3.2:1b
   
   # Start Ollama server
   ollama serve
   ```

3. **Network connectivity:**
   - Same WiFi/LAN network (for local communication)
   - OR internet access with port forwarding/DevTunnel (for remote communication)

---

#### Method 1: Local Network (Same WiFi/LAN)

**Step 1: Find Device IP Addresses**

On **Device 1** (e.g., your laptop):
```bash
# Linux/Mac
ifconfig | grep "inet "

# Windows
ipconfig
```
Note the IP address (e.g., `192.168.1.100`)

On **Device 2** (e.g., your desktop):
```bash
# Linux/Mac
ifconfig | grep "inet "

# Windows
ipconfig
```
Note the IP address (e.g., `192.168.1.101`)

**Step 2: Create Agent on Device 1**

Create a file called `agent_device1.py`:

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.communication import CommunicationManager

set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    # Create communication manager
    comm = CommunicationManager()
    await comm.start()
    
    # Create agent on Device 1
    agent1 = Agent(config=AgentConfig(
        name="AgentOnDevice1",
        network_url="http://192.168.1.100:8000",  # Device 1's IP
        auth_token="secure_token_123",
        allow_file_transfers=True
    ))
    
    await agent1.start(communication_manager=comm)
    
    print(f"Agent 1 started on {agent1.config.network_url}")
    print(f"Agent ID: {agent1.id}")
    print("Waiting for messages from Device 2...")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent1.stop()
        comm.stop()

asyncio.run(main())
```

**Step 3: Create Agent on Device 2**

Create a file called `agent_device2.py`:

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.communication import CommunicationManager
from daie.agents.message import AgentMessage

set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    # Create communication manager
    comm = CommunicationManager()
    await comm.start()
    
    # Create agent on Device 2
    agent2 = Agent(config=AgentConfig(
        name="AgentOnDevice2",
        network_url="http://192.168.1.101:8000",  # Device 2's IP
        auth_token="secure_token_123",
        allow_file_transfers=True
    ))
    
    await agent2.start(communication_manager=comm)
    
    print(f"Agent 2 started on {agent2.config.network_url}")
    print(f"Agent ID: {agent2.id}")
    
    # Wait a bit for Agent 1 to start
    await asyncio.sleep(2)
    
    # Send a message to Agent 1
    msg = AgentMessage(
        sender_id=agent2.id,
        receiver_id="agent-on-device1",  # Agent 1's name (lowercase, hyphenated)
        content="Hello from Device 2!",
        message_type="text",
    )
    
    await comm.send_message(msg)
    print("Message sent to Agent 1!")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent2.stop()
        comm.stop()

asyncio.run(main())
```

**Step 4: Run Both Agents**

On **Device 1**:
```bash
python agent_device1.py
```

On **Device 2**:
```bash
python agent_device2.py
```

**Step 5: Verify Connection**

You should see:
- Device 1: "Agent 1 started on http://192.168.1.100:8000"
- Device 2: "Agent 2 started on http://192.168.1.101:8000"
- Device 2: "Message sent to Agent 1!"
- Device 1: Receives the message from Device 2

---

#### Method 2: Internet (Using DevTunnel)

For connecting devices across the internet (different networks), use Microsoft DevTunnel:

**Step 1: Install DevTunnel CLI**

On **both devices**:
```bash
# Install DevTunnel
curl -sL https://aka.ms/DevTunnelCliInstall | bash

# Login to DevTunnel
devtunnel user login
```

**Step 2: Create DevTunnel on Device 1**

```bash
# Create a tunnel for port 8000
devtunnel create -p 8000

# Host the tunnel
devtunnel host
```

This will give you a URL like: `https://abc123.devtunnels.ms:8000`

**Step 3: Create Agent on Device 1**

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.communication import CommunicationManager

set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    comm = CommunicationManager()
    await comm.start()
    
    agent1 = Agent(config=AgentConfig(
        name="AgentOnDevice1",
        network_url="https://abc123.devtunnels.ms:8000",  # DevTunnel URL
        auth_token="secure_token_123",
        allow_file_transfers=True
    ))
    
    await agent1.start(communication_manager=comm)
    
    print(f"Agent 1 started on {agent1.config.network_url}")
    print("Waiting for messages from Device 2...")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent1.stop()
        comm.stop()

asyncio.run(main())
```

**Step 4: Create DevTunnel on Device 2**

```bash
# Create a tunnel for port 8000
devtunnel create -p 8000

# Host the tunnel
devtunnel host
```

This will give you a URL like: `https://xyz789.devtunnels.ms:8000`

**Step 5: Create Agent on Device 2**

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.communication import CommunicationManager
from daie.agents.message import AgentMessage

set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    comm = CommunicationManager()
    await comm.start()
    
    agent2 = Agent(config=AgentConfig(
        name="AgentOnDevice2",
        network_url="https://xyz789.devtunnels.ms:8000",  # DevTunnel URL
        auth_token="secure_token_123",
        allow_file_transfers=True
    ))
    
    await agent2.start(communication_manager=comm)
    
    print(f"Agent 2 started on {agent2.config.network_url}")
    
    await asyncio.sleep(2)
    
    msg = AgentMessage(
        sender_id=agent2.id,
        receiver_id="agent-on-device1",
        content="Hello from Device 2 via the internet!",
        message_type="text",
    )
    
    await comm.send_message(msg)
    print("Message sent to Agent 1!")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent2.stop()
        comm.stop()

asyncio.run(main())
```

**Step 6: Run Both Agents**

On **Device 1**:
```bash
python agent_device1.py
```

On **Device 2**:
```bash
python agent_device2.py
```

---

#### Method 3: Complete Example with File Transfer

Here's a complete example that demonstrates both messaging and file transfer:

**Device 1 (Receiver):**

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.communication import CommunicationManager

set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    comm = CommunicationManager()
    await comm.start()
    
    agent1 = Agent(config=AgentConfig(
        name="FileReceiver",
        network_url="http://192.168.1.100:8000",
        auth_token="secure_token_123",
        allow_file_transfers=True
    ))
    
    await agent1.start(communication_manager=comm)
    
    print(f"File Receiver Agent started on {agent1.config.network_url}")
    print("Waiting for files from Device 2...")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent1.stop()
        comm.stop()

asyncio.run(main())
```

**Device 2 (Sender):**

```python
import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.communication import CommunicationManager
from daie.tools.a2a_file import A2ASendFileTool

set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    comm = CommunicationManager()
    await comm.start()
    
    agent2 = Agent(config=AgentConfig(
        name="FileSender",
        network_url="http://192.168.1.101:8000",
        auth_token="secure_token_123",
        allow_file_transfers=True
    ))
    
    await agent2.start(communication_manager=comm)
    
    print(f"File Sender Agent started on {agent2.config.network_url}")
    
    await asyncio.sleep(2)
    
    # Create a test file
    with open("test_document.txt", "w") as f:
        f.write("This is a test document from Device 2.")
    
    # Send file to Agent 1
    file_tool = A2ASendFileTool()
    file_tool.set_agent(agent2)
    
    result = await file_tool.execute({
        "receiver_id": "file-receiver",  # Agent 1's name
        "file_path": "test_document.txt",
        "message": "Here's a document from Device 2!",
    })
    
    print(f"File transfer result: {result}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent2.stop()
        comm.stop()

asyncio.run(main())
```

---

#### Troubleshooting

| Problem | Solution |
|---------|----------|
| **Connection refused** | Check if Ollama is running: `ollama serve` |
| **Cannot connect to remote agent** | Verify IP addresses and firewall settings |
| **Authentication failed** | Ensure both agents use the same `auth_token` |
| **Port already in use** | Change port in `network_url` (e.g., `:8001`) |
| **DevTunnel not working** | Run `devtunnel host` on both devices |
| **Firewall blocking** | Open ports 8000-8001 in firewall settings |
| **Agent not receiving messages** | Check if agent is started with `communication_manager` |

#### Firewall Configuration

**Linux (UFW):**
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
```

**Windows:**
```powershell
# Open PowerShell as Administrator
New-NetFirewallRule -DisplayName "DAIE Agent 8000" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "DAIE Agent 8001" -Direction Inbound -Port 8001 -Protocol TCP -Action Allow
```

**macOS:**
```bash
# macOS doesn't block outgoing connections by default
# For incoming, use System Preferences > Security & Privacy > Firewall
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
