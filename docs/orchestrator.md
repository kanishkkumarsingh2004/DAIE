# Orchestrator

The Orchestrator enables multi-agent coordination, allowing a main agent to delegate tasks to sub-agents and aggregate their results.

## Features

- **Multi-Agent Coordination** — Coordinate multiple agents to solve complex tasks
- **Task Delegation** — Main agent delegates tasks to specialized sub-agents
- **Result Aggregation** — Combine results from multiple agents into a final answer
- **Flexible Context** — Configure different coordination contexts (e.g., research lab, courtroom)
- **Role-Based Agents** — Define main agent and sub-agent roles

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER / APPLICATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATOR                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         MAIN AGENT                                  │    │
│  │  • Receives user task                                               │    │
│  │  • Analyzes and decomposes task                                     │    │
│  │  • Delegates sub-tasks to sub-agents                                │    │
│  │  • Aggregates results into final answer                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                        │
│                    ▼               ▼               ▼                        │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐    │
│  │    SUB-AGENT 1      │ │    SUB-AGENT 2      │ │    SUB-AGENT N      │    │
│  │  • Receives task    │ │  • Receives task    │ │  • Receives task    │    │
│  │  • Executes work    │ │  • Executes work    │ │  • Executes work    │    │
│  │  • Returns result   │ │  • Returns result   │ │  • Returns result   │    │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘    │
│                    │               │               │                        │
│                    └───────────────┴───────────────┘                        │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    COMMUNICATION MANAGER                            │    │
│  │  • A2A messaging (a2a_send_message)                                 │    │
│  │  • Task delegation (a2a_delegate_task)                              │    │
│  │  • P2P networking                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM MANAGER                                    │
│  • Ollama  • OpenAI  • Anthropic  • Google  • Azure  • OpenRouter           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```python
from daie import Agent, AgentConfig, Orchestrator
from daie.agents import AgentRole

# Create main agent (coordinator)
main_agent = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You are a research coordinator.",
))

# Create sub-agents
sub_agent1 = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a research specialist.",
))

sub_agent2 = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a data analyst.",
))

# Create orchestrator
orchestrator = Orchestrator(
    main_agent=main_agent,
    sub_agents=[sub_agent1, sub_agent2],
    context_name="research_lab",
    main_role="Professor",
    sub_role="Researcher"
)

# Start orchestrator
await orchestrator.start()

# Execute a task
result = await orchestrator.execute_task(
    "Research the latest developments in AI and provide a summary"
)

# Stop orchestrator
await orchestrator.stop()
```

---

## Orchestrator Class

### Constructor

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

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `main_agent` | `Agent` | — | The main coordinating agent |
| `sub_agents` | `List[Agent]` | — | List of sub-agents to coordinate |
| `context_name` | `str` | `"Classroom"` | Name of the coordination context |
| `main_role` | `str` | `"Teacher"` | Role name for the main agent |
| `sub_role` | `str` | `"Student"` | Role name for sub-agents |
| `comm_manager` | `CommunicationManager \| None` | `None` | Communication manager for agent messaging |

### Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the orchestrator and all agents (async) |
| `execute_task(task)` | Execute a task using the orchestrator (async) |
| `stop()` | Stop the orchestrator and all agents (async) |

---

## How It Works

### 1. System Prompt Injection

The orchestrator automatically modifies agent system prompts:

**Main Agent Prompt:**
```
You are the PROFESSOR in a research_lab. Your researchers are:
- Researcher (ID: agent-123) - Goal: Conduct research
- Analyst (ID: agent-456) - Goal: Analyze data

ORCHESTRATION RULES:
1. If the user input is a greeting, DO NOT delegate to others. Respond directly.
2. For tasks requiring specialized work, break them down and delegate sub-tasks to researchers individually.
3. To delegate to a sub-agent, you MUST use the tool 'a2a_delegate_task' with parameters 'target_agent_id' and 'task_payload'.
4. Example tool call: {"thought":"Delegating work", "tool":"a2a_delegate_task", "params":{"target_agent_id":"agent_id", "task_payload":{"task":"Specific task description"}}}
5. After receiving answers, combine them into a final response.
6. FINAL ANSWER FORMAT: Your final response MUST be a clear, professional, and well-structured string in the 'answer' field.
```

**Sub-Agent Prompt:**
```
You are a RESEARCHER in a research_lab. Your professor is Professor (ID: agent-789).
Other researchers in the research_lab are:
- Analyst (ID: agent-456)

You should follow instructions from the professor.
You can discuss with others using 'a2a_send_message' if it helps solve the task.
```

### 2. Task Delegation Flow

```
User Task: "Research AI developments and analyze trends"
    │
    ├─ Main Agent (Professor) receives task
    │   ├─ Thought: "I need to delegate research and analysis"
    │   ├─ Tool: a2a_delegate_task → Researcher
    │   │   └─ Task: "Research latest AI developments"
    │   └─ Tool: a2a_delegate_task → Analyst
    │       └─ Task: "Analyze AI trends from research"
    │
    ├─ Researcher executes research task
    │   └─ Returns: "AI developments include..."
    │
    ├─ Analyst executes analysis task
    │   └─ Returns: "Trends show..."
    │
    └─ Main Agent combines results
        └─ Final Answer: "Based on research and analysis..."
```

---

## Example: Research Lab

```python
from daie import Agent, AgentConfig, Orchestrator
from daie.agents import AgentRole

# Create research team
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You are a research professor coordinating a research lab.",
))

researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a research specialist focused on gathering information.",
))

analyst = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a data analyst focused on analyzing trends.",
))

# Create orchestrator
orchestrator = Orchestrator(
    main_agent=professor,
    sub_agents=[researcher, analyst],
    context_name="research_lab",
    main_role="Professor",
    sub_role="Researcher"
)

# Execute research task
await orchestrator.start()
response = await orchestrator.execute_task("Research decentralized consensus")
await orchestrator.stop()
```

---

## Example: Courtroom

```python
from daie import Agent, AgentConfig, Orchestrator
from daie.agents import AgentRole

# Create courtroom team
judge = Agent(config=AgentConfig(
    name="Judge",
    role=AgentRole.COORDINATOR,
    system_prompt="You are a judge presiding over a courtroom.",
))

prosecutor = Agent(config=AgentConfig(
    name="Prosecutor",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a prosecutor arguing for the prosecution.",
))

defense = Agent(config=AgentConfig(
    name="Defense",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a defense attorney arguing for the defense.",
))

# Create orchestrator
orchestrator = Orchestrator(
    main_agent=judge,
    sub_agents=[prosecutor, defense],
    context_name="courtroom",
    main_role="Judge",
    sub_role="Attorney"
)

# Execute courtroom scenario
await orchestrator.start()
result = await orchestrator.execute_task(
    "Hear arguments about whether AI should be regulated"
)
await orchestrator.stop()
```

---

## Integration with Communication

The orchestrator uses the `CommunicationManager` for agent-to-agent messaging:

```python
from daie.communication import CommunicationManager

# Create communication manager
comm = CommunicationManager()
await comm.start()

# Create orchestrator with communication
orchestrator = Orchestrator(
    main_agent=main_agent,
    sub_agents=[sub_agent1, sub_agent2],
    comm_manager=comm
)

# Agents can now communicate via A2A tools
await orchestrator.start()

# ... do work ...

await orchestrator.stop()
await comm.stop()
```

---

## Best Practices

1. **Clear Roles** — Define clear roles and goals for each agent
2. **Specialized Prompts** — Provide detailed system prompts for each agent
3. **Appropriate Context** — Choose meaningful context names
4. **Task Decomposition** — Break complex tasks into sub-tasks
5. **Result Aggregation** — Ensure main agent effectively combines results

---

## Next Steps

- [Node vs Orchestrator](node-vs-orchestrator.md) — Complete comparison guide with use cases
- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Communication](communication.md) — P2P networking and file transfers
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [RAG](rag.md) — Retrieval-Augmented Generation for document-based knowledge
