# Chat Configs

The `daie.chat` module provides pre-configured chat loop setups so users don't need to write the full boilerplate code. Simply configure and run!

## Overview

The module includes four main configurations:

1. **ChatLoopConfig** - Simple chat loop for agents
2. **NodeChatConfig** - Advanced chat for single node with orchestrator
3. **OrchestratorChatConfig** - Advanced chat for multi-node systems
4. **HybridChatConfig** - Simple chat loop for hybrid systems
5. **ParliamentChatConfig** - Specialized chat loop for multi-agent deliberation

All configs accept pre-created objects externally and provide a simple `run()` method to start the interactive session.

---

## Approach

The chat configs follow a consistent approach:

1. **Accept Pre-Created Objects**: All configs accept already-created objects (Agent, HybridOrchestratorNode, MultiNodeHybridSystem) externally
2. **Simple API**: Just pass the object and call `run()`
3. **Error Handling**: Automatic error handling and recovery with retry logic
4. **Graceful Shutdown**: Handle interrupts (Ctrl+C) and EOF gracefully
5. **Customizable**: Welcome messages, exit commands, prompts, callbacks
6. **Lifecycle Management**: Automatically start/stop the underlying systems

This approach allows users to:
- Create objects with full control over their configuration
- Use the same objects across multiple configs if needed
- Avoid boilerplate code for interactive loops
- Focus on their application logic rather than chat loop implementation

---

## File Structure

```
src/daie/chat/
├── __init__.py                    # Module exports
├── chat_loop_config.py            # ChatLoopConfig implementation
├── node_chat_config.py            # NodeChatConfig implementation
├── orchestrator_chat_config.py    # OrchestratorChatConfig implementation
├── hybrid_chat_config.py          # HybridChatConfig implementation
└── parliament_chat_config.py      # ParliamentChatConfig implementation
```

### Dependencies

- **ChatLoopConfig**: Depends on `daie.agents.agent.Agent`
- **NodeChatConfig**: Depends on `daie.core.hybrid.HybridOrchestratorNode`
- **OrchestratorChatConfig**: Depends on `daie.core.hybrid.MultiNodeHybridSystem`
- **HybridChatConfig**: Depends on both `HybridOrchestratorNode` and `MultiNodeHybridSystem`
- **ParliamentChatConfig**: Depends on `daie.agents.parliament.Parliament`

All configs are independent of each other and can be used separately or together.

---

## ChatLoopConfig

Simple chat loop for agents. This is the most basic configuration for running a chat loop with an agent.

### Features

- Accepts an already-created Agent externally
- Automatic error handling and recovery
- Graceful shutdown on interrupts (Ctrl+C)
- Configurable exit commands
- Customizable prompts and messages
- Support for streaming responses
- Easy agent lifecycle management

### Usage

```python
from daie import Agent, AgentConfig
from daie.chat import ChatLoopConfig

# Create your agent
config = AgentConfig(
    name="LUNA",
    system_prompt="You are a helpful AI assistant.",
    personality="friendly and helpful"
)
agent = Agent(config=config)

# Run the chat loop with minimal code!
chat_loop = ChatLoopConfig(agent=agent)
chat_loop.run()
```

### Quick Start

```python
# One-liner to start chat!
ChatLoopConfig.quick_start(agent).run()
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent` | Agent | Required | The agent instance to use for the chat loop |
| `welcome_message` | str | "=== Chat Loop ===\nType 'exit' or press Ctrl+C to quit.\n" | Welcome message displayed when chat starts |
| `exit_commands` | List[str] | ["exit", "quit", "bye", "goodbye"] | Commands that will exit the chat loop |
| `prompt_prefix` | str | "You: " | Prefix displayed before user input |
| `show_agent_name` | bool | False | Whether to show agent name before responses |
| `agent_name_prefix` | str | "{agent_name}: " | Format for agent name prefix |
| `error_prefix` | str | "⚠️ Error: " | Prefix for error messages |
| `show_errors` | bool | True | Whether to show error messages to user |
| `max_retries` | int | 3 | Maximum number of retries on error before giving up |
| `retry_delay` | float | 1.0 | Delay in seconds between retries |
| `start_agent` | bool | True | Whether to start the agent automatically |
| `stop_agent` | bool | True | Whether to stop the agent automatically on exit |
| `clear_screen_on_start` | bool | False | Whether to clear screen when chat starts |
| `show_goodbye` | bool | True | Whether to show goodbye message on exit |
| `goodbye_message` | str | "\nGoodbye! Chat session ended." | Goodbye message displayed when chat ends |
| `on_start` | Optional[Callable] | None | Callback function called when chat loop starts |
| `on_exit` | Optional[Callable] | None | Callback function called when chat loop exits |
| `on_error` | Optional[Callable] | None | Callback function called when an error occurs |

---

## NodeChatConfig

Advanced chat for single node with orchestrator and sub-agents. Provides command parsing for routing, collaboration, and status checking.

### Features

- Accepts an already-created HybridOrchestratorNode externally
- Automatic setup of Node, Orchestrator, and CommunicationManager
- Resource management on the hybrid node
- Task execution using the orchestrator
- Intelligent message routing with AgentRouter
- Collaborative task execution across all agents
- Command parsing for advanced interactions

### Usage

```python
from daie import Agent, AgentConfig
from daie.core.hybrid import HybridOrchestratorNode
from daie.chat import NodeChatConfig

# Create your hybrid node externally
hybrid = HybridOrchestratorNode(
    node_id="research-lab",
    node_name="AI Research Lab",
    context_name="Research Lab",
    main_role="Professor",
    sub_role="Researcher"
)

# Add agents
professor = Agent(config=AgentConfig(
    name="Professor",
    system_prompt="You coordinate research projects.",
    personality="wise and methodical"
))
hybrid.set_main_agent(professor)

researcher = Agent(config=AgentConfig(
    name="Researcher",
    system_prompt="You conduct thorough research.",
    personality="analytical and curious"
))
hybrid.add_sub_agent(researcher)

# Run the hybrid node with minimal code!
config = NodeChatConfig(hybrid_node=hybrid)
config.run()
```

### Quick Start

```python
# One-liner to start hybrid node!
NodeChatConfig.quick_start(hybrid_node=hybrid).run()
```

### Available Commands

- `route <message>` - Route message to best agent
- `collab <task>` - Execute collaborative task
- `status` - Show system status
- `exit` or `quit` - Exit the chat

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hybrid_node` | HybridOrchestratorNode | Required | The HybridOrchestratorNode instance to run |
| `enable_logging` | bool | True | Whether to enable logging |
| `log_level` | str | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `log_file` | Optional[str] | None | Log file path (None for console only) |
| `welcome_message` | str | "=== Hybrid Orchestrator Node ===\nType your task to execute (or 'exit' to quit)\n" | Welcome message displayed when interactive mode starts |
| `exit_commands` | List[str] | ["exit", "quit"] | Commands that will exit the interactive loop |
| `prompt_prefix` | str | "You: " | Prefix displayed before user input |
| `show_status_on_start` | bool | True | Whether to show system status when starting |
| `on_start` | Optional[Callable] | None | Callback function called when node starts |
| `on_exit` | Optional[Callable] | None | Callback function called when node exits |
| `on_error` | Optional[Callable] | None | Callback function called when an error occurs |

---

## OrchestratorChatConfig

Advanced chat for multi-node hybrid systems. Provides command parsing for node-specific execution, broadcasting, and status checking.

### Features

- Accepts an already-created MultiNodeHybridSystem externally
- Creating a MultiNodeHybridSystem with multiple hybrid nodes
- Configuring different orchestrators on each node
- Connecting nodes for P2P communication
- Executing tasks on specific nodes
- Broadcasting tasks to all nodes
- Cross-node collaboration
- Command parsing for advanced interactions

### Usage

```python
from daie import Agent, AgentConfig
from daie.core.hybrid import MultiNodeHybridSystem
from daie.chat import OrchestratorChatConfig

# Create your multi-node system externally
system = MultiNodeHybridSystem()

# Create and configure nodes
research_node = system.create_node(
    node_id="research-lab",
    node_name="AI Research Lab",
    context_name="Research Lab",
    main_role="Professor",
    sub_role="Researcher"
)

# Add agents
professor = Agent(config=AgentConfig(
    name="Professor",
    system_prompt="You coordinate research projects.",
    personality="wise and methodical"
))
research_node.set_main_agent(professor)

researcher = Agent(config=AgentConfig(
    name="Researcher",
    system_prompt="You conduct thorough research.",
    personality="analytical and curious"
))
research_node.add_sub_agent(researcher)

# Create another node
content_node = system.create_node(
    node_id="content-creation",
    node_name="Content Creation Studio",
    context_name="Content Creation",
    main_role="Editor",
    sub_role="Creator"
)

editor = Agent(config=AgentConfig(
    name="Editor",
    system_prompt="You coordinate content creation.",
    personality="creative and detail-oriented"
))
content_node.set_main_agent(editor)

# Connect nodes
system.connect_nodes("research-lab", "content-creation")

# Run the multi-node system with minimal code!
config = OrchestratorChatConfig(system=system)
config.run()
```

### Quick Start

```python
# One-liner to start multi-node system!
OrchestratorChatConfig.quick_start(system=system).run()
```

### Available Commands

- `<node_id> <task>` - Execute task on specific node (e.g., "research-lab analyze this data")
- `broadcast <task>` - Broadcast task to all nodes
- `status` - Show system status
- `exit` or `quit` - Exit the chat

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `system` | MultiNodeHybridSystem | Required | The MultiNodeHybridSystem instance to run |
| `enable_logging` | bool | True | Whether to enable logging |
| `log_level` | str | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `log_file` | Optional[str] | None | Log file path (None for console only) |
| `welcome_message` | str | "=== Multi-Node Hybrid System ===\nType your command (or 'exit' to quit)\n" | Welcome message displayed when interactive mode starts |
| `exit_commands` | List[str] | ["exit", "quit"] | Commands that will exit the interactive loop |
| `prompt_prefix` | str | "You: " | Prefix displayed before user input |
| `show_status_on_start` | bool | True | Whether to show system status when starting |
| `on_start` | Optional[Callable] | None | Callback function called when system starts |
| `on_exit` | Optional[Callable] | None | Callback function called when system exits |
| `on_error` | Optional[Callable] | None | Callback function called when an error occurs |

---

## HybridChatConfig

Simple chat loop for hybrid systems. This is a simplified version that focuses on basic chat interaction without complex command parsing - just like ChatLoopConfig but for hybrid systems.

### Features

- Accepts HybridOrchestratorNode or MultiNodeHybridSystem externally
- Simple chat loop without complex command parsing
- Automatic error handling and recovery
- Graceful shutdown on interrupts
- Configurable prompts and messages

### Usage with HybridOrchestratorNode

```python
from daie import Agent, AgentConfig
from daie.core.hybrid import HybridOrchestratorNode
from daie.chat import HybridChatConfig

# Create your hybrid system externally
hybrid = HybridOrchestratorNode(
    node_id="research-lab",
    node_name="AI Research Lab",
    context_name="Research Lab",
    main_role="Professor",
    sub_role="Researcher"
)

# Add agents
professor = Agent(config=AgentConfig(
    name="Professor",
    system_prompt="You coordinate research projects.",
    personality="wise and methodical"
))
hybrid.set_main_agent(professor)

# Run simple chat loop with minimal code!
config = HybridChatConfig(hybrid_system=hybrid)
config.run()
```

### Usage with MultiNodeHybridSystem

```python
from daie import Agent, AgentConfig
from daie.core.hybrid import MultiNodeHybridSystem
from daie.chat import HybridChatConfig

# Create your multi-node system externally
system = MultiNodeHybridSystem()

# Create and configure nodes
research_node = system.create_node(
    node_id="research-lab",
    node_name="AI Research Lab",
    context_name="Research Lab",
    main_role="Professor",
    sub_role="Researcher"
)

# Add agents
professor = Agent(config=AgentConfig(
    name="Professor",
    system_prompt="You coordinate research projects.",
    personality="wise and methodical"
))
research_node.set_main_agent(professor)

# Run simple chat loop with minimal code!
config = HybridChatConfig(hybrid_system=system)
config.run()
```

### Quick Start

```python
# One-liner to start chat loop!
HybridChatConfig.quick_start(hybrid_system=hybrid).run()
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `hybrid_system` | Union[HybridOrchestratorNode, MultiNodeHybridSystem] | Required | The hybrid system instance to use for chat |
| `welcome_message` | str | "=== Hybrid Chat Loop ===\nType your message to the hybrid system (or 'exit' to quit)\n" | Welcome message displayed when chat starts |
| `exit_commands` | List[str] | ["exit", "quit", "bye", "goodbye"] | Commands that will exit the chat loop |
| `prompt_prefix` | str | "You: " | Prefix displayed before user input |
| `error_prefix` | str | "⚠️ Error: " | Prefix for error messages |
| `show_errors` | bool | True | Whether to show error messages to user |
| `max_retries` | int | 3 | Maximum number of retries on error before giving up |
| `retry_delay` | float | 1.0 | Delay in seconds between retries |
| `start_system` | bool | True | Whether to start the hybrid system automatically |
| `stop_system` | bool | True | Whether to stop the hybrid system automatically on exit |
| `clear_screen_on_start` | bool | False | Whether to clear screen when chat starts |
| `show_goodbye` | bool | True | Whether to show goodbye message on exit |
| `goodbye_message` | str | "\nGoodbye! Chat session ended." | Goodbye message displayed when chat ends |
| `on_start` | Optional[Callable] | None | Callback function called when chat loop starts |
| `on_exit` | Optional[Callable] | None | Callback function called when chat loop exits |
| `on_error` | Optional[Callable] | None | Callback function called when an error occurs |

---

## ParliamentChatConfig

Specialized interface for engaging with a `Parliament`. Handles starting the entire assembly, waiting for parallel answers and peer reviews, and streaming back the synthesized result without exposing the internal async flow to the user.

### Features

- Accepts a pre-created `Parliament` instance.
- Built-in multi-turn loop supporting complex JSON and text parsing from the synthesizer.
- Wait-state management since parliament deliberation can take longer than single LLM generation.
- Graceful `start_parliament` and `stop_parliament` hooks to preserve memory.

### Usage

```python
from daie import Agent, AgentConfig, AgentRole
from daie.agents import Parliament
from daie.chat import ParliamentChatConfig

agents = [
    Agent(config=AgentConfig(name="Economist", role=AgentRole.DATA_ANALYST)),
    Agent(config=AgentConfig(name="Lawyer", role=AgentRole.SECURITY_AUDITOR))
]

parliament = Parliament(sub_agents=agents, speaker=agents[0])

# Start the interactive debate loop!
config = ParliamentChatConfig(parliament=parliament)
config.run()
```

### Quick Start

```python
ParliamentChatConfig.quick_start(parliament=parliament).run()
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parliament` | Parliament | Required | The parliament instance to deliberate with |
| `welcome_message` | str | "... Type your topic for debate ..." | Welcome message displayed when chat starts |
| `exit_commands` | List[str] | ["exit", "quit", "bye", "goodbye"] | Commands that will exit the chat loop |
| `prompt_prefix` | str | "Topic: " | Prefix displayed before user input |
| `start_parliament` | bool | True | Whether to automatically call `start()` on the parliament |
| `stop_parliament` | bool | True | Whether to automatically call `stop()` on the parliament |
| `show_errors` | bool | True | Whether to show error messages to user |

---

## Comparison

| Feature | ChatLoopConfig | NodeChatConfig | OrchestratorChatConfig | HybridChatConfig | ParliamentChatConfig |
|----------|----------------|----------------|------------------------|------------------|----------------------|
| **Target** | Simple Agent | Single Node | Multi-Node System | Hybrid System | Multi-Agent Parliament |
| **Complexity** | Simple | Advanced | Advanced | Simple | Advanced (Internal) |
| **Command Parsing** | No | Yes | Yes | No | No (Takes topics) |
| **Use Case** | Basic chat | Research lab | Multi-node collaboration | Simple hybrid chat | Debate / Peer-review Synthesis |
| **Lifecycle Management** | Agent start/stop | Node start/stop | System start/stop | System start/stop | Parliament start/stop |
| **Error Handling** | Retry logic | Retry logic | Retry logic | Retry logic | Retry logic |
| **Callbacks** | on_start, on_exit... | on_start, on_exit... | on_start, on_exit... | on_start, on_exit... | on_start, on_exit... |

---

## Best Practices

1. **Use Quick Start for Simple Cases**: For simple use cases, use the `quick_start()` method
2. **Customize for Production**: For production use, customize welcome messages, error handling, and callbacks
3. **Handle Errors Gracefully**: Use `on_error` callbacks to handle errors appropriately
4. **Manage Lifecycle**: Use `start_system`/`stop_system` or `start_agent`/`stop_agent` to control lifecycle
5. **Use Appropriate Config**: Choose the right config for your use case:
   - ChatLoopConfig for simple agent chat
   - NodeChatConfig for single node with advanced commands
   - OrchestratorChatConfig for multi-node systems
   - HybridChatConfig for simple hybrid chat
   - ParliamentChatConfig for high-quality peer-reviewed answers

---

## Examples

See [`examples/12_chat_loop_config.py`](../examples/12_chat_loop_config.py) for comprehensive examples of all chat configurations.
