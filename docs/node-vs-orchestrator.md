# Node vs Orchestrator: Complete Comparison Guide

A comprehensive guide comparing Node, Orchestrator, and Hybrid architectures in DAIE, with real-world use cases, project ideas, and practical examples.

---

## Table of Contents

- [Overview](#overview)
- [Architecture Comparison](#architecture-comparison)
- [Key Differences](#key-differences)
- [When to Use Node](#when-to-use-node)
- [When to Use Orchestrator](#when-to-use-orchestrator)
- [When to Use Orchestrator + Node (Hybrid)](#when-to-use-orchestrator--node-hybrid)
- [Using Node and Orchestrator Together (Hybrid)](#using-node-and-orchestrator-together)
- [Intelligent Agent Router](#intelligent-agent-router)
- [Network Configuration](#network-configuration)
- [Real-World Use Cases](#real-world-use-cases)
- [Project Ideas](#project-ideas)
- [Pros and Cons](#pros-and-cons)
- [Performance Comparison](#performance-comparison)
- [Best Practices](#best-practices)

---

## Overview

DAIE provides three powerful abstractions for building multi-agent systems:

### Node
A **Node** is a logical container that represents a participating entity in the decentralized AI network. It hosts multiple agents, manages resources, and connects to peer nodes.

### Orchestrator
An **Orchestrator** is a coordination pattern where a main agent delegates tasks to specialized sub-agents and aggregates their results.

### Hybrid (Node + Orchestrator)
A **Hybrid** approach combines both Node and Orchestrator architectures, allowing you to build distributed systems with both infrastructure management and workflow coordination. This is the most powerful and flexible approach for enterprise-scale multi-agent systems.

### HybridOrchestratorNode
A **HybridOrchestratorNode** is a simplified wrapper that combines Node and Orchestrator into a single, easy-to-use class. It handles the complexity of wiring together infrastructure management (Node) with workflow coordination (Orchestrator), providing a batteries-included approach for hybrid architectures. Use this when you want the benefits of hybrid without the boilerplate code.

---

## Architecture Comparison

### Node Architecture

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

**Key Characteristics:**
- **Flat structure** — All agents are equal peers
- **Decentralized** — No single point of control
- **Resource-aware** — Manages GPU, memory, model cache
- **P2P networking** — Direct node-to-node communication
- **Scalable** — Add nodes horizontally

### Orchestrator Architecture

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
```

**Key Characteristics:**
- **Hierarchical structure** — Main agent coordinates sub-agents
- **Centralized control** — Main agent makes decisions
- **Task-focused** — Decomposes and delegates tasks
- **Result aggregation** — Combines sub-agent outputs
- **Context-aware** — Different contexts (research lab, courtroom, etc.)

---

## Key Differences

### Comprehensive Comparison Table

| Domain | Aspect | Node | Orchestrator | Hybrid |
|--------|--------|------|--------------|--------|
| **Architecture** | Structure | Flat (peer-to-peer) | Hierarchical (main → sub-agents) | Mixed (nodes + orchestrators) |
| | Control Model | Decentralized | Centralized | Distributed coordination |
| | Abstraction Level | Infrastructure layer | Workflow layer | Both layers |
| | Design Pattern | Container/Host | Coordinator/Worker | Container + Coordinator |
| **Purpose** | Primary Goal | Host agents, manage resources | Coordinate task execution | Host + coordinate across nodes |
| | Focus | Infrastructure management | Workflow orchestration | Infrastructure + workflow |
| | Scope | Node-level operations | Task-level operations | Node + task operations |
| | Responsibility | Agent hosting & resource tracking | Task decomposition & result aggregation | Both hosting and coordination |
| **Communication** | Pattern | Direct agent-to-agent | Main agent delegates to sub-agents | P2P + delegation |
| | Protocol | P2P networking (native) | A2A messaging via CommunicationManager | P2P + A2A messaging |
| | Message Flow | Any-to-any | Hub-and-spoke (main ↔ sub-agents) | Any-to-any + hub-and-spoke |
| | Discovery | Node registry | Agent registry | Node + agent registry |
| **Scalability** | Direction | Horizontal (add nodes) | Vertical (add sub-agents) | Both horizontal and vertical |
| | Limit | Limited by network topology | Limited by main agent capacity | Limited by network + main agent |
| | Growth Model | Add more nodes | Add more sub-agents | Add nodes + sub-agents |
| | Bottleneck | Network bandwidth | Main agent processing | Network + main agent |
| **Resource Management** | Capability | ✅ Built-in (GPU, memory, model cache) | ❌ Not included | ✅ Built-in per node |
| | Tracking | Per-node resource monitoring | Not applicable | Per-node resource monitoring |
| | Allocation | Node-level resource allocation | Agent-level task allocation | Node + agent allocation |
| | Isolation | Resource isolation per node | No resource isolation | Resource isolation per node |
| **Task Management** | Delegation | ❌ Manual coordination required | ✅ Automatic task decomposition | ✅ Automatic across nodes |
| | Aggregation | ❌ Manual result combination | ✅ Automatic result aggregation | ✅ Automatic across nodes |
| | Workflow | No built-in workflow | Built-in workflow coordination | Built-in + cross-node workflow |
| | Scheduling | No task scheduling | Task scheduling via main agent | Task scheduling across nodes |
| **Fault Tolerance** | Failure Handling | No single point of failure | Main agent is single point of failure | Distributed + orchestrator backup |
| | Recovery | Node-level recovery | Orchestrator-level recovery | Node + orchestrator recovery |
| | Redundancy | Multiple nodes can replicate | No built-in redundancy | Node replication + orchestrator backup |
| | Resilience | High (distributed) | Low (centralized) | High (distributed + backup) |
| **Complexity** | Setup | More complex initial setup | Quick and simple setup | Most complex (both) |
| | Management | Requires distributed systems knowledge | Requires workflow design knowledge | Requires both skill sets |
| | Debugging | Harder (distributed debugging) | Easier (centralized logging) | Hardest (distributed + centralized) |
| | Maintenance | Node-by-node maintenance | Single orchestrator maintenance | Node + orchestrator maintenance |
| **Performance** | Latency | Lower (direct P2P) | Higher (main agent mediation) | Mixed (P2P + mediation) |
| | Throughput | Higher (parallel nodes) | Lower (main agent bottleneck) | Highest (parallel + coordination) |
| | Overhead | Network overhead | Coordination overhead | Network + coordination overhead |
| | Efficiency | Resource-efficient | Task-efficient | Resource + task efficient |
| **Use Cases** | Best For | Distributed networks, resource management | Task coordination, workflow automation | Complex distributed workflows |
| | Ideal Scenario | Multi-location, hardware-aware systems | Complex tasks, specialized teams | Enterprise multi-team distributed systems |
| | Industry | Edge computing, IoT, distributed AI | Research, analysis, content creation | Enterprise AI, distributed research |
| | Scale | Enterprise-scale infrastructure | Team-scale workflows | Enterprise + team-scale |
| **Integration** | With P2P | Native integration | Via CommunicationManager | Native P2P + A2A |
| | With Tools | Tools run on agents within node | Tools run on sub-agents | Tools on agents + sub-agents |
| | With Memory | Per-node memory management | Per-agent memory management | Per-node + per-agent memory |
| | With RAG | Per-node knowledge bases | Per-agent knowledge bases | Per-node + per-agent RAG |
| **Deployment** | Location | Multi-location (geographic) | Single location (logical) | Multi-location + logical |
| | Infrastructure | Requires network infrastructure | Requires compute infrastructure | Network + compute infrastructure |
| | Distribution | Naturally distributed | Naturally centralized | Distributed + centralized |
| | Edge Support | ✅ Excellent for edge computing | ❌ Not designed for edge | ✅ Edge + central coordination |
| **Monitoring** | Health Checks | Node status monitoring | Orchestrator status monitoring | Node + orchestrator monitoring |
| | Metrics | Resource utilization, node health | Task completion, agent performance | Resource + task metrics |
| | Logging | Per-node logging | Centralized orchestrator logging | Per-node + centralized logging |
| | Observability | Distributed tracing required | Centralized observability | Distributed + centralized observability |
| **Security** | Isolation | Node-level security isolation | Agent-level security | Node + agent security |
| | Authentication | Node-to-node authentication | Agent-to-agent authentication | Node + agent authentication |
| | Authorization | Per-node access control | Per-agent access control | Per-node + per-agent access control |
| | Attack Surface | Multiple entry points | Single entry point (main agent) | Multiple + single entry points |
| **Development** | Learning Curve | Steeper (distributed concepts) | Gentler (workflow concepts) | Steepest (both concepts) |
| | Code Complexity | Higher (coordination logic) | Lower (delegation logic) | Highest (both logic types) |
| | Testing | Harder (integration testing) | Easier (unit testing) | Hardest (integration + unit) |
| | Debugging | Distributed debugging tools | Centralized debugging | Distributed + centralized debugging |
| **Operations** | Deployment | Complex (multiple nodes) | Simple (single orchestrator) | Most complex (nodes + orchestrators) |
| | Scaling | Add nodes as needed | Add sub-agents as needed | Add nodes + sub-agents |
| | Updates | Rolling updates per node | Update orchestrator once | Rolling + orchestrator updates |
| | Backup | Per-node backup | Orchestrator state backup | Per-node + orchestrator backup |
| **Cost** | Infrastructure | Higher (multiple machines) | Lower (single machine) | Highest (multiple + orchestrator) |
| | Maintenance | Higher (distributed maintenance) | Lower (centralized maintenance) | Highest (distributed + centralized) |
| | Scaling Cost | Linear (add nodes) | Sub-linear (add sub-agents) | Linear + sub-linear |
| | Operational Cost | Higher (network, monitoring) | Lower (single point management) | Highest (network + coordination) |

---

## When to Use Node

### ✅ Use Node When:

1. **Building a distributed network** — You need multiple machines/locations working together as a cohesive system
2. **Managing resources** — Track GPU, memory, model cache, CPU, disk, and network bandwidth per location
3. **Peer-to-peer communication** — Agents need to communicate directly without a central coordinator
4. **Scalable infrastructure** — Add capacity by adding nodes horizontally across the network
5. **Multi-location deployment** — Different physical/logical locations (e.g., data centers, edge devices, cloud regions)
6. **Resource isolation** — Separate resources per node to prevent interference and ensure predictable performance
7. **Network topology** — Need to model network connections, latency, and bandwidth constraints
8. **Edge computing** — Deploy AI agents on edge devices (IoT sensors, mobile devices, embedded systems)
9. **Geographic distribution** — Systems spanning multiple regions, countries, or continents
10. **High availability** — No single point of failure; system continues operating if one node fails
11. **Load distribution** — Distribute computational load across multiple machines
12. **Hardware diversity** — Different nodes have different hardware capabilities (GPU types, memory sizes)
13. **Data locality** — Keep data close to where it's processed to reduce latency
14. **Fault tolerance** — System should survive individual node failures
15. **Independent scaling** — Scale different parts of the system independently
16. **Multi-tenant systems** — Different users or organizations share the same infrastructure
17. **Hybrid cloud** — Combine on-premises and cloud resources
18. **Real-time processing** — Low-latency requirements that benefit from local processing
19. **Bandwidth optimization** — Reduce data transfer by processing locally
20. **Regulatory compliance** — Data must stay in specific geographic regions
21. **Cost optimization** — Use cheaper local resources when available
22. **Redundancy** — Multiple nodes can replicate the same functionality
23. **Microservices architecture** — Each node hosts a subset of agents/services
24. **Container orchestration** — Integrate with Kubernetes, Docker Swarm, or similar platforms
25. **Monitoring and observability** — Track resource utilization, node health, and performance metrics per location

### ❌ Don't Use Node When:

1. **Simple task coordination** — Just need to delegate tasks without infrastructure concerns
2. **Single machine** — All agents run on one machine with no distributed requirements
3. **No resource tracking** — Don't care about GPU, memory, or hardware resources
4. **Hierarchical workflows** — Need clear main/sub-agent structure with centralized control
5. **Quick prototyping** — Need to get something running fast without infrastructure setup
6. **Stateless operations** — Tasks that don't require persistent state or resource management
7. **Simple chatbots** — Single-agent conversational systems
8. **Batch processing** — One-off tasks that don't need distributed coordination
9. **Development/testing** — Local development environments where distribution isn't needed
10. **Low-complexity systems** — Systems with fewer than 3-4 agents that don't justify the overhead
11. **Tightly coupled agents** — Agents that need constant, low-latency communication
12. **Shared memory requirements** — Agents that need to share large amounts of data in memory
13. **Synchronous workflows** — Tasks that must execute in strict sequential order
14. **Budget constraints** — Limited resources that can't support distributed infrastructure
15. **Team lacks distributed systems expertise** — No one on the team understands P2P networking or distributed coordination

---

## When to Use Orchestrator

### ✅ Use Orchestrator When:

1. **Task decomposition** — Complex tasks need breaking down into manageable sub-tasks
2. **Specialized agents** — Different agents for different skills (researcher, analyst, writer, coder)
3. **Result aggregation** — Need to combine multiple outputs into a cohesive final result
4. **Workflow coordination** — Clear main agent coordinating others through a defined process
5. **Research/analysis tasks** — Need research + analysis + writing in a coordinated pipeline
6. **Debate/simulation** — Multiple perspectives (courtroom, classroom, boardroom simulations)
7. **Complex problem solving** — Need multiple expert opinions synthesized together
8. **Multi-step workflows** — Tasks that require sequential or parallel execution of sub-tasks
9. **Content creation** — Writing, editing, reviewing, and publishing workflows
10. **Data processing pipelines** — ETL (Extract, Transform, Load) operations with multiple stages
11. **Customer support routing** — Route inquiries to appropriate specialists based on topic
12. **Code review workflows** — Write, review, test, and deploy code with specialized agents
13. **Educational systems** — Tutoring, grading, curriculum development with different expert roles
14. **Medical diagnosis** — Multiple specialists contributing to a diagnosis
15. **Legal case analysis** — Research, analysis, argumentation, and documentation
16. **Financial analysis** — Data gathering, analysis, modeling, and reporting
17. **Project management** — Planning, execution, monitoring, and reporting with different roles
18. **Quality assurance** — Testing, validation, and verification workflows
19. **Translation workflows** — Translate, review, and polish content
20. **Design workflows** — Research, ideation, prototyping, and refinement
21. **Decision making** — Gather input from multiple experts before making a decision
22. **Brainstorming sessions** — Generate and evaluate ideas from different perspectives
23. **Report generation** — Gather data, analyze, visualize, and write reports
24. **Meeting facilitation** — Coordinate discussions, take notes, and summarize action items
25. **Training programs** — Develop, deliver, and assess training content
26. **Compliance checking** — Review documents against multiple regulatory requirements
27. **Risk assessment** — Identify, analyze, and prioritize risks from different angles
28. **Product development** — Research, design, prototype, test, and launch products
29. **Marketing campaigns** — Research, strategy, content creation, and performance analysis
30. **Event planning** — Coordinate logistics, speakers, attendees, and resources

### ❌ Don't Use Orchestrator When:

1. **Flat peer structure** — All agents are equal with no hierarchy
2. **Direct communication** — Agents need to talk directly without mediation
3. **Resource management** — Need to track hardware resources (GPU, memory, etc.)
4. **Distributed network** — Multiple machines/locations requiring infrastructure management
5. **Simple chat** — Just one agent responding to user queries
6. **Real-time collaboration** — Agents need to work simultaneously on the same task
7. **Independent tasks** — Tasks that don't benefit from coordination
8. **Stateless operations** — Tasks that don't require persistent coordination state
9. **High-frequency requests** — Very high request volumes where orchestration overhead is prohibitive
10. **Simple automation** — Basic if-then workflows that don't need AI coordination
11. **Data storage** — Pure data storage and retrieval without processing
12. **Monitoring/alerting** — Simple threshold-based monitoring without AI analysis
13. **Batch jobs** — One-off processing tasks without coordination needs
14. **Single-agent systems** — Systems with only one agent
15. **Tightly coupled systems** — Components that are already tightly integrated
16. **Performance-critical paths** — Latency-sensitive operations where orchestration overhead matters
17. **Simple routing** — Basic message routing without AI decision-making
18. **Static workflows** — Workflows that never change and don't need dynamic coordination
19. **Resource-constrained environments** — Limited compute that can't support orchestration overhead
20. **Legacy system integration** — Systems that can't be modified to work with orchestration

---

## When to Use Orchestrator + Node (Hybrid)

### ✅ Use Orchestrator + Node When:

1. **Enterprise-scale systems** — Large organizations with multiple teams, departments, or locations
2. **Distributed teams with local coordination** — Teams in different locations that need both local and global coordination
3. **Resource-aware task execution** — Tasks that need to consider available hardware resources (GPU, memory) while coordinating workflows
4. **Complex distributed workflows** — Workflows that span multiple nodes and require orchestration at each level
5. **Multi-location with specialized teams** — Different locations with specialized agents that need coordination
6. **Edge computing with central coordination** — Edge devices processing data locally with central orchestration
7. **Maximum scalability and flexibility** — Need both horizontal (nodes) and vertical (sub-agents) scaling
8. **Large-scale, complex multi-agent systems** — Systems with dozens or hundreds of agents across multiple nodes
9. **Hybrid cloud deployments** — Combine on-premises, private cloud, and public cloud resources
10. **Global content delivery networks** — Distribute content processing across geographic regions
11. **Multi-region customer support** — Support centers in different time zones with specialized teams
12. **Distributed research networks** — Research labs collaborating across institutions
13. **Smart city infrastructure** — Multiple districts with local coordination and city-wide orchestration
14. **Autonomous vehicle fleets** — Vehicles with local processing and fleet-wide coordination
15. **Industrial IoT networks** — Factory floors with local automation and enterprise-wide coordination
16. **Healthcare networks** — Hospitals with local patient care and network-wide research coordination
17. **Financial trading systems** — Trading desks with local execution and global risk management
18. **E-commerce platforms** — Regional warehouses with local fulfillment and global inventory coordination
19. **Media production networks** — Studios with local production and network-wide distribution
20. **Educational institutions** — Campuses with local teaching and institution-wide curriculum coordination
21. **Government agencies** — Departments with local operations and agency-wide policy coordination
22. **Supply chain management** — Local suppliers with regional coordination and global logistics
23. **Telecommunications networks** — Local cell towers with regional coordination and network-wide optimization
24. **Energy grid management** — Local power plants with regional coordination and grid-wide balancing
25. **Transportation networks** — Local stations with regional coordination and network-wide scheduling
26. **Retail chains** — Individual stores with regional coordination and chain-wide inventory management
27. **Hospitality networks** — Individual hotels with regional coordination and chain-wide booking management
28. **Airlines** — Individual aircraft with regional coordination and fleet-wide scheduling
29. **Shipping/logistics** — Individual vehicles with regional coordination and fleet-wide routing
30. **Agricultural networks** — Individual farms with regional coordination and supply chain management
31. **Environmental monitoring** — Local sensors with regional coordination and global climate analysis
32. **Security systems** — Local cameras with regional coordination and network-wide threat detection
33. **Communication networks** — Local base stations with regional coordination and network-wide optimization
34. **Data center management** — Individual servers with rack-level coordination and data center-wide optimization
35. **Cloud computing platforms** — Individual instances with availability zone coordination and region-wide load balancing
36. **Content delivery networks** — Edge servers with regional coordination and global content distribution
37. **Gaming platforms** — Game servers with regional coordination and global matchmaking
38. **Social media platforms** — Regional servers with local content moderation and global policy enforcement
39. **Search engines** — Regional indexers with local query processing and global result ranking
40. **Recommendation systems** — Local user profiling with regional preference aggregation and global recommendation generation

### ❌ Don't Use Orchestrator + Node When:

1. **Simple single-machine systems** — All agents run on one machine with no distributed requirements
2. **Quick prototypes** — Need to get something running fast without infrastructure setup
3. **Single-agent chatbots** — Simple conversational systems with one agent
4. **Stateless batch jobs** — One-off processing tasks without coordination needs
5. **Resource-constrained environments** — Limited compute that can't support both Node and Orchestrator overhead
6. **Team lacks expertise** — No one on the team understands both distributed systems and workflow orchestration
7. **Budget constraints** — Can't afford the infrastructure and maintenance costs
8. **Simple automation** — Basic if-then workflows that don't need AI coordination
9. **Data storage only** — Pure data storage and retrieval without processing
10. **Monitoring/alerting only** — Simple threshold-based monitoring without AI analysis
11. **Single location** — All agents in one location with no distribution needs
12. **No resource tracking** — Don't care about GPU, memory, or hardware resources
13. **Flat peer structure** — All agents are equal with no hierarchy
14. **Direct communication only** — Agents need to talk directly without any coordination
15. **Performance-critical paths** — Latency-sensitive operations where both Node and Orchestrator overhead matters
16. **Simple routing** — Basic message routing without AI decision-making
17. **Static workflows** — Workflows that never change and don't need dynamic coordination
18. **Legacy systems** — Systems that can't be modified to work with both Node and Orchestrator
19. **Tightly coupled systems** — Components that are already tightly integrated
20. **Independent tasks** — Tasks that don't benefit from coordination or distribution

### Decision Matrix: Node vs Orchestrator vs Hybrid

| Scenario | Node | Orchestrator | Hybrid |
|----------|------|--------------|--------|
| Single machine, simple tasks | ❌ | ✅ | ❌ |
| Multiple machines, no coordination | ✅ | ❌ | ❌ |
| Single machine, complex workflows | ❌ | ✅ | ❌ |
| Multiple machines, complex workflows | ❌ | ❌ | ✅ |
| Resource management needed | ✅ | ❌ | ✅ |
| Task delegation needed | ❌ | ✅ | ✅ |
| Geographic distribution | ✅ | ❌ | ✅ |
| Hierarchical workflows | ❌ | ✅ | ✅ |
| Edge computing | ✅ | ❌ | ✅ |
| Research/analysis tasks | ❌ | ✅ | ✅ |
| Enterprise-scale systems | ✅ | ❌ | ✅ |
| Quick prototyping | ❌ | ✅ | ❌ |
| High availability required | ✅ | ❌ | ✅ |
| Simple chatbot | ❌ | ✅ | ❌ |
| Distributed teams | ✅ | ❌ | ✅ |
| Specialized agent teams | ❌ | ✅ | ✅ |
| Multi-location support | ✅ | ❌ | ✅ |
| Content creation workflows | ❌ | ✅ | ✅ |
| IoT/Edge networks | ✅ | ❌ | ✅ |
| Customer support routing | ❌ | ✅ | ✅ |

---

## Using Node and Orchestrator Together

**Yes!** Node and Orchestrator can be used together for powerful multi-agent systems. This hybrid approach combines the best of both architectures.

### Architecture: Node + Orchestrator (Hybrid)

```
┌─────────────────────────────────────────────────────────────┐
│                    Node (Production Server)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    ORCHESTRATOR                     │    │
│  │  ┌─────────────┐                                    │    │
│  │  │  Professor  │ (Main Agent)                       │    │
│  │  └─────────────┘                                    │    │
│  │         │                                           │    │
│  │         ├─────────────────┬─────────────────┐       │    │
│  │         ▼                 ▼                 ▼       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ Researcher  │  │   Analyst   │  │   Writer    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
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

### Example: Multi-Node Research Network

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.core.node import Node

# Configure LLM
set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create communication manager
comm = CommunicationManager()
await comm.start()

# ──────────────────────────────────────────────
# Node 1: Research Lab (with Orchestrator)
# ──────────────────────────────────────────────
research_node = Node(node_id="research-lab", name="Research Lab")
await research_node.start()

# Create research team
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate research projects.",
))
researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research and gather information.",
))
analyst = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You analyze data and identify trends.",
))

# Start agents
await professor.start(communication_manager=comm)
await researcher.start(communication_manager=comm)
await analyst.start(communication_manager=comm)

# Add agents to node
research_node.add_agent(professor.id)
research_node.add_agent(researcher.id)
research_node.add_agent(analyst.id)

# Create orchestrator on this node
research_orchestrator = Orchestrator(
    main_agent=professor,
    sub_agents=[researcher, analyst],
    context_name="research_lab",
    main_role="Professor",
    sub_role="Researcher"
)
await research_orchestrator.start()

# ──────────────────────────────────────────────
# Node 2: Analysis Center
# ──────────────────────────────────────────────
analysis_node = Node(node_id="analysis-center", name="Analysis Center")
analysis_node.start()

data_scientist = Agent(config=AgentConfig(
    name="DataScientist",
    role=AgentRole.SPECIALIZED,
    system_prompt="You perform advanced data analysis.",
))
await data_scientist.start(communication_manager=comm)
analysis_node.add_agent(data_scientist.id)

# ──────────────────────────────────────────────
# Connect nodes
# ──────────────────────────────────────────────
research_node.connect("analysis-center")
analysis_node.connect("research-lab")

# ──────────────────────────────────────────────
# Execute cross-node collaborative task
# ──────────────────────────────────────────────
result = await research_orchestrator.execute_task(
    "Research AI trends and analyze their market impact"
await research_node.start()

# Create research team
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate research projects.",
))
researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research and gather information.",
))
analyst = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You analyze data and identify trends.",
))

# Start agents
await professor.start(communication_manager=comm)
await researcher.start(communication_manager=comm)
await analyst.start(communication_manager=comm)

# Add agents to node
research_node.add_agent(professor.id)
research_node.add_agent(researcher.id)
research_node.add_agent(analyst.id)

# Create orchestrator on this node
research_orchestrator = Orchestrator(
    main_agent=professor,
    sub_agents=[researcher, analyst],
    context_name="research_lab",
    main_role="Professor",
    sub_role="Researcher"
)
await research_orchestrator.start()

# ──────────────────────────────────────────────
# Node 2: Analysis Center
# ──────────────────────────────────────────────
analysis_node = Node(node_id="analysis-center", name="Analysis Center")
await await research_node.start()

data_scientist = Agent(config=AgentConfig(
    name="DataScientist",
    role=AgentRole.SPECIALIZED,
    system_prompt="You perform advanced data analysis.",
))
await data_scientist.start(communication_manager=comm)
analysis_node.add_agent(data_scientist.id)

# ──────────────────────────────────────────────
# Connect nodes
# ──────────────────────────────────────────────
research_node.connect("analysis-center")
analysis_node.connect("research-lab")

# ──────────────────────────────────────────────
# Execute cross-node collaborative task
# ──────────────────────────────────────────────
result = await research_orchestrator.execute_task(
    "Research AI trends and analyze their market impact"
)

# Cleanup
await research_orchestrator.stop()
await data_scientist.stop()
await research_node.stop()
await analysis_node.stop()
await comm.stop()
```

---

## Using Node and Orchestrator Together

**Yes!** Node and Orchestrator can be used together for powerful multi-agent systems. This hybrid approach combines the best of both architectures.

### Architecture: Node + Orchestrator (Hybrid)

```
┌─────────────────────────────────────────────────────────────┐
│                    Node (Production Server)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    ORCHESTRATOR                     │    │
│  │  ┌─────────────┐                                    │    │
│  │  │  Professor  │ (Main Agent)                       │    │
│  │  └─────────────┘                                    │    │
│  │         │                                           │    │
│  │         ├─────────────────┬─────────────────┐       │    │
│  │         ▼                 ▼                 ▼       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ Researcher  │  │   Analyst   │  │   Writer    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
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

### Example: Multi-Node Research Network

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.core.node import Node

# Configure LLM
set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create communication manager
comm = CommunicationManager()
await comm.start()

# ──────────────────────────────────────────────
# Node 1: Research Lab (with Orchestrator)
# ──────────────────────────────────────────────
research_node = Node(node_id="research-lab", name="Research Lab")
await research_node.start()

# Create research team
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate research projects.",
))
researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research and gather information.",
))
analyst = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You analyze data and identify trends.",
))

# Start agents
await professor.start(communication_manager=comm)
await researcher.start(communication_manager=comm)
await analyst.start(communication_manager=comm)

# Add agents to node
research_node.add_agent(professor.id)
research_node.add_agent(researcher.id)
research_node.add_agent(analyst.id)

# Create orchestrator on this node
research_orchestrator = Orchestrator(
    main_agent=professor,
    sub_agents=[researcher, analyst],
    context_name="research_lab",
    main_role="Professor",
    sub_role="Researcher"
)
await research_orchestrator.start()

# ──────────────────────────────────────────────
# Node 2: Analysis Center
# ──────────────────────────────────────────────
analysis_node = Node(node_id="analysis-center", name="Analysis Center")
await analysis_node.start()

data_scientist = Agent(config=AgentConfig(
    name="DataScientist",
    role=AgentRole.SPECIALIZED,
    system_prompt="You perform advanced data analysis.",
))
await data_scientist.start(communication_manager=comm)
analysis_node.add_agent(data_scientist.id)

# ──────────────────────────────────────────────
# Connect nodes
# ──────────────────────────────────────────────
research_node.connect("analysis-center")
analysis_node.connect("research-lab")

# ──────────────────────────────────────────────
# Execute cross-node collaborative task
# ──────────────────────────────────────────────
result = await research_orchestrator.execute_task(
    "Research AI trends and analyze their market impact"
)

# Cleanup
await research_orchestrator.stop()
await data_scientist.stop()
await research_node.stop()
await analysis_node.stop()
await comm.stop()
```

---

## HybridOrchestratorNode: Simple Hybrid Setup

The manual approach above gives you full control, but requires significant boilerplate code. For a simpler, batteries-included experience, use the **`HybridOrchestratorNode`** class.

### What is HybridOrchestratorNode?

`HybridOrchestratorNode` is a high-level abstraction that automatically combines Node and Orchestrator architectures into a single, easy-to-use class. It handles all the wiring for you:

- ✅ **Automatic Node creation** — Creates and manages the Node internally
- ✅ **Automatic Orchestrator setup** — Wires up the Orchestrator with your agents
- ✅ **Built-in CommunicationManager** — No need to create and manage separately
- ✅ **Optional intelligent routing** — Can enable AgentRouter for LLM-based message routing
- ✅ **Resource management** — Built-in GPU, memory, and custom resource tracking
- ✅ **Simple API** — Just set agents and call `start()`

### Architecture: HybridOrchestratorNode

```
┌─────────────────────────────────────────────────────────────┐
│                HybridOrchestratorNode                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    ORCHESTRATOR                     │    │
│  │  ┌─────────────┐                                    │    │
│  │  │ Main Agent  │ (Coordinator)                      │    │
│  │  └─────────────┘                                    │    │
│  │         │                                           │    │
│  │         ├─────────────────┬─────────────────┐       │    │
│  │         ▼                 ▼                 ▼       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ Sub-Agent 1 │  │ Sub-Agent 2 │  │ Sub-Agent N │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              NODE (Infrastructure Layer)            │    │
│  │  • Resource management (GPU, memory, etc.)          │    │
│  │  • Agent hosting                                    │    │
│  │  • P2P connections to other nodes                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         CommunicationManager (P2P + A2A)            │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         AgentRouter (Optional, LLM-based)           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Quick Start: Single Hybrid Node

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.core.hybrid import HybridOrchestratorNode

# Configure LLM
set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create hybrid system (one line!)
hybrid = HybridOrchestratorNode(
    node_id="research-lab",
    node_name="AI Research Lab",
    context_name="Research Lab",
    main_role="Professor",
    sub_role="Researcher",
    enable_router=True,  # Enable intelligent routing
    resources={
        "gpu_count": 4,
        "memory_gb": 32,
        "model_cache": {"llama3.2": True}
    }
)

# Set main agent (orchestrator)
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate research projects."
))
hybrid.set_main_agent(professor)

# Add sub-agents
researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research and gather information."
))
hybrid.add_sub_agent(researcher)

analyst = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You analyze data and identify trends."
))
hybrid.add_sub_agent(analyst)

# Start and use
await hybrid.start()

# Execute task via orchestrator
result = await hybrid.execute_task("Research AI trends")

# Or route message to best agent (if router enabled)
response = await hybrid.route_message("Analyze market data")

# Or get collaborative response from all agents
collab = await hybrid.execute_collaborative_task("Research and analyze AI trends")

# Check status
status = hybrid.get_status()
print(f"Node: {status['node_name']}, Agents: {status['total_agents']}")

# Cleanup
await hybrid.stop()
```

### Multi-Node Hybrid System

For distributed systems with multiple hybrid nodes, use `MultiNodeHybridSystem`:

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.core.hybrid import MultiNodeHybridSystem

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create multi-node system
system = MultiNodeHybridSystem()

# Create research lab node
research_node = system.create_node(
    node_id="research-lab",
    node_name="Research Lab",
    context_name="Research Lab"
)

# Configure research team
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate research projects."
))
research_node.set_main_agent(professor)

researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research."
))
research_node.add_sub_agent(researcher)

# Create content creation node
content_node = system.create_node(
    node_id="content-creation",
    node_name="Content Creation",
    context_name="Content Creation"
)

# Configure content team
editor = Agent(config=AgentConfig(
    name="Editor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate content creation."
))
content_node.set_main_agent(editor)

writer = Agent(config=AgentConfig(
    name="Writer",
    role=AgentRole.SPECIALIZED,
    system_prompt="You write clear content."
))
content_node.add_sub_agent(writer)

# Connect nodes for P2P communication
system.connect_nodes("research-lab", "content-creation")

# Start all nodes
await system.start_all()

# Execute task on specific node
result = await system.execute_task("research-lab", "Research AI trends")

# Broadcast task to all nodes
results = await system.broadcast_task("Analyze market impact")

# Check system status
status = system.get_system_status()
print(f"Total nodes: {status['total_nodes']}")

# Cleanup
await system.stop_all()
```

### HybridOrchestratorNode API Reference

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_id` | `str` | Required | Unique identifier for the node |
| `node_name` | `str` | `"Hybrid Node"` | Display name for the node |
| `context_name` | `str` | `"Hybrid System"` | Name of the orchestration context |
| `main_role` | `str` | `"Coordinator"` | Role name for the main agent |
| `sub_role` | `str` | `"Specialist"` | Role name for sub-agents |
| `enable_router` | `bool` | `True` | Enable intelligent AgentRouter |
| `comm_manager` | `CommunicationManager` | `None` | Optional communication manager |
| `resources` | `Dict[str, Any]` | `None` | Initial node resources |

#### Key Methods

| Method | Description |
|--------|-------------|
| `set_main_agent(agent)` | Set the main agent (orchestrator) |
| `add_sub_agent(agent)` | Add a sub-agent to the system |
| `add_resource(name, value)` | Add a resource to the node |
| `connect_to_node(peer_node_id)` | Connect to another node |
| `start()` | Start the hybrid system |
| `execute_task(task)` | Execute task via orchestrator |
| `route_message(message)` | Route message to best agent |
| `execute_collaborative_task(task)` | Get response from all agents |
| `get_status()` | Get system status |
| `stop()` | Stop the hybrid system |

### Comparison: Manual vs HybridOrchestratorNode

| Aspect | Manual Approach | HybridOrchestratorNode |
|--------|----------------|------------------------|
| **Setup Complexity** | High (50+ lines) | Low (10-15 lines) |
| **Boilerplate** | Significant | Minimal |
| **Control** | Full | Full (same API) |
| **Flexibility** | Maximum | High |
| **Learning Curve** | Steeper | Gentler |
| **Best For** | Custom architectures | Standard hybrid setups |

### When to Use HybridOrchestratorNode

✅ **Use HybridOrchestratorNode when:**
- You want a quick, simple hybrid setup
- You need standard Node + Orchestrator integration
- You want built-in resource management
- You prefer less boilerplate code
- You're building a standard multi-agent system

❌ **Use manual approach when:**
- You need custom Node/Orchestrator configurations
- You want to mix multiple Orchestrators on one Node
- You need fine-grained control over component lifecycle
- You're building a highly specialized architecture

---

## Intelligent Agent Router

The **AgentRouter** is an intelligent routing layer that uses LLM to automatically select the most appropriate agent for each message based on content analysis. It works seamlessly with both Node and Orchestrator architectures.

### What is AgentRouter?

The `AgentRouter` is a dynamic routing component that:
- **Analyzes message content** using LLM to understand intent
- **Discovers agent capabilities** automatically from agent configs
- **Routes messages** to the best-matched agent
- **Tracks routing history** for debugging and analysis
- **Works with any agent types** (no hardcoded agent names)

### Architecture: AgentRouter Layer

```
┌─────────────────────────────────────────────────────────────┐
│                    USER / APPLICATION                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AGENT ROUTER (Intelligent Layer)         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  • Analyzes message content                         │    │
│  │  • Discovers agent capabilities                     │    │
│  │  • Selects best agent                               │    │
│  │  • Routes message                                   │    │
│  │  • Logs routing decision                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│   NODE ARCHITECTURE │         │ ORCHESTRATOR PATTERN│
│                     │         │                     │
│  ┌─────────────┐    │         │  ┌─────────────┐    │
│  │   Agent 1   │    │         │  │ Main Agent  │    │
│  └─────────────┘    │         │  └─────────────┘    │
│  ┌─────────────┐    │         │  ┌─────────────┐    │
│  │   Agent 2   │    │         │  │ Sub-Agent 1 │    │
│  └─────────────┘    │         │  └─────────────┘    │
│  ┌─────────────┐    │         │  ┌─────────────┐    │
│  │   Agent 3   │    │         │  │ Sub-Agent 2 │    │
│  └─────────────┘    │         │  └─────────────┘    │
└─────────────────────┘         └─────────────────────┘
```

### How It Works

1. **Agent Discovery** — Router extracts agent names, roles, system prompts, and personality traits from configs
2. **Prompt Generation** — Creates a routing prompt listing all agents with their specialties
3. **LLM Decision** — Sends the routing prompt to the router agent (first agent by default)
4. **Decision Parsing** — Parses the LLM response to identify the selected agent
5. **Fallback** — If routing fails, falls back to the first available agent

### Key Features

| Feature | Description |
|---------|-------------|
| **Dynamic Discovery** | Automatically extracts agent capabilities from configs |
| **Auto-generated Prompts** | Creates routing prompts based on agent specialties |
| **Flexible Handling** | Works with any agent names and types |
| **History Tracking** | Logs all routing decisions for debugging |
| **Manual Override** | Can force specific agent with `agent_type` parameter |
| **Description Updates** | Manually update agent descriptions for better routing |

### Creating a Router

#### From a List of Agents

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole, AgentRouter

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create specialized agents
assistant = Agent(config=AgentConfig(
    name="Assistant",
    role=AgentRole.GENERAL_PURPOSE,
    system_prompt="You are a helpful general-purpose assistant."
))

coder = Agent(config=AgentConfig(
    name="Coder",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are an expert programmer. Write clean, efficient code."
))

researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You are a research specialist. Analyze and summarize information."
))

# Create router from agents list
router = AgentRouter.from_agents([assistant, coder, researcher])
```

#### From a Dictionary

```python
from daie.agents.router import create_router

router = create_router({
    "assistant": assistant,
    "coder": coder,
    "researcher": researcher,
})
```

### Using the Router

```python
# Route a message to the best agent
agent_type = await router.route("Write a Python function to sort a list")
# Returns: "coder"

agent_type = await router.route("Explain quantum computing")
# Returns: "researcher"

agent_type = await router.route("What's the weather like?")
# Returns: "assistant"

# Force a specific agent (bypass routing)
agent_type = await router.route("Hello", agent_type="assistant")
# Returns: "assistant"
```

### Router Methods

```python
# Get routing history
history = router.get_routing_history()
print(f"Routed {len(history)} messages")
# Returns: [
#   {"message_preview": "Write a Python...", "selected_agent": "coder", "llm_decision": "coder"},
#   ...
# ]

# Get auto-generated agent descriptions
descriptions = router.get_agent_descriptions()
print(descriptions)
# Returns: {"assistant": "Assistant | Role: general-purpose | ...", ...}

# Manually update an agent description
router.update_agent_description("coder", "Expert Python developer")

# Clear routing history
router.clear_routing_history()
```

### Integration with Node

In a Node architecture, the AgentRouter can be used to route messages to the most appropriate agent within a node:

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole, AgentRouter
from daie.core.node import Node

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create a node
node = Node(node_id="research-lab", name="Research Lab")
await node.start()

# Create agents
assistant = Agent(config=AgentConfig(name="Assistant", role=AgentRole.GENERAL_PURPOSE))
coder = Agent(config=AgentConfig(name="Coder", role=AgentRole.SPECIALIZED))
researcher = Agent(config=AgentConfig(name="Researcher", role=AgentRole.SPECIALIZED))

# Start agents
await assistant.start()
await coder.start()
await researcher.start()

# Add agents to node
node.add_agent(assistant.id)
node.add_agent(coder.id)
node.add_agent(researcher.id)

# Create router for this node
router = AgentRouter.from_agents([assistant, coder, researcher])

# Route messages to appropriate agents
message = "Write a Python function to calculate fibonacci"
agent_type = await router.route(message)
print(f"Routed to: {agent_type}")  # Returns: "coder"
```

### Integration with Orchestrator

In an Orchestrator architecture, the AgentRouter can be used to intelligently route tasks to the most appropriate sub-agent:

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole, AgentRouter

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create main agent (coordinator)
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate research projects."
))

# Create sub-agents
researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research and gather information."
))

analyst = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You analyze data and identify trends."
))

writer = Agent(config=AgentConfig(
    name="Writer",
    role=AgentRole.SPECIALIZED,
    system_prompt="You write clear and engaging content."
))

# Start agents
await professor.start()
await researcher.start()
await analyst.start()
await writer.start()

# Create router for intelligent task routing
router = AgentRouter.from_agents([professor, researcher, analyst, writer])

# Create orchestrator
orchestrator = Orchestrator(
    main_agent=professor,
    sub_agents=[researcher, analyst, writer],
    context_name="research_lab"
)
await orchestrator.start()

# Use router to determine which agent should handle specific tasks
task = "Analyze the market trends in AI"
agent_type = await router.route(task)
print(f"Best agent for this task: {agent_type}")  # Returns: "analyst"

# Execute task through orchestrator
result = await orchestrator.execute_task(task)
```

### Integration with Hybrid (Node + Orchestrator)

In a Hybrid architecture, the AgentRouter provides intelligent routing across multiple nodes and orchestrators:

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole, AgentRouter
from daie.communication import CommunicationManager
from daie.core.node import Node

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create communication manager
comm = CommunicationManager()
await comm.start()

# ──────────────────────────────────────────────
# Node 1: Research Lab (with Orchestrator)
# ──────────────────────────────────────────────
research_node = Node(node_id="research-lab", name="Research Lab")
await research_node.start()

# Create research team
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate research projects."
))
researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research and gather information."
))
analyst = Agent(config=AgentConfig(
    name="Analyst",
    role=AgentRole.SPECIALIZED,
    system_prompt="You analyze data and identify trends."
))

# Start agents
await professor.start(communication_manager=comm)
await researcher.start(communication_manager=comm)
await analyst.start(communication_manager=comm)

# Add agents to node
research_node.add_agent(professor.id)
research_node.add_agent(researcher.id)
research_node.add_agent(analyst.id)

# Create orchestrator on this node
research_orchestrator = Orchestrator(
    main_agent=professor,
    sub_agents=[researcher, analyst],
    context_name="research_lab"
)
await research_orchestrator.start()

# ──────────────────────────────────────────────
# Node 2: Content Creation (with Orchestrator)
# ──────────────────────────────────────────────
content_node = Node(node_id="content-creation", name="Content Creation")
await content_node.start()

# Create content team
editor = Agent(config=AgentConfig(
    name="Editor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate content creation."
))
writer = Agent(config=AgentConfig(
    name="Writer",
    role=AgentRole.SPECIALIZED,
    system_prompt="You write clear and engaging content."
))
designer = Agent(config=AgentConfig(
    name="Designer",
    role=AgentRole.SPECIALIZED,
    system_prompt="You create visual designs and graphics."
))

# Start agents
await editor.start(communication_manager=comm)
await writer.start(communication_manager=comm)
await designer.start(communication_manager=comm)

# Add agents to node
content_node.add_agent(editor.id)
content_node.add_agent(writer.id)
content_node.add_agent(designer.id)

# Create orchestrator on this node
content_orchestrator = Orchestrator(
    main_agent=editor,
    sub_agents=[writer, designer],
    context_name="content_creation"
)
await content_orchestrator.start()

# ──────────────────────────────────────────────
# Create global router across all agents
# ──────────────────────────────────────────────
all_agents = [professor, researcher, analyst, editor, writer, designer]
global_router = AgentRouter.from_agents(all_agents)

# ──────────────────────────────────────────────
# Route messages to appropriate agents
# ──────────────────────────────────────────────
message1 = "Analyze the market trends in AI"
agent_type1 = await global_router.route(message1)
print(f"Message 1 routed to: {agent_type1}")  # Returns: "analyst"

message2 = "Write a blog post about AI trends"
agent_type2 = await global_router.route(message2)
print(f"Message 2 routed to: {agent_type2}")  # Returns: "writer"

message3 = "Coordinate a research project on AI"
agent_type3 = await global_router.route(message3)
print(f"Message 3 routed to: {agent_type3}")  # Returns: "professor"

# Get routing history
history = global_router.get_routing_history()
print(f"Total messages routed: {len(history)}")

# Cleanup
await research_orchestrator.stop()
await content_orchestrator.stop()
await research_node.stop()
await content_node.stop()
await comm.stop()
```

### Benefits of AgentRouter

| Benefit | Description |
|---------|-------------|
| **Automatic Routing** | No need to manually specify which agent handles each message |
| **Content-Aware** | LLM analyzes message content to select the best agent |
| **Flexible** | Works with any agent types and configurations |
| **Scalable** | Can route across multiple nodes and orchestrators |
| **Debuggable** | Routing history helps understand routing decisions |
| **Overridable** | Can force specific agent when needed |
| **Maintainable** | Agent descriptions can be updated without code changes |

### Use Cases

1. **Multi-Agent Chat Systems** — Route user messages to the most appropriate specialist agent
2. **Task Delegation** — Automatically assign tasks to the best-suited agent
3. **Load Balancing** — Distribute work across multiple agents based on capability
4. **Specialized Workflows** — Route different types of requests to different workflows
5. **Hybrid Architectures** — Coordinate routing across multiple nodes and orchestrators

---

## Real-World Use Cases

### 1. **Distributed Research Network**

**Problem:** A research organization has multiple labs across different locations, each with specialized equipment and expertise.

**Solution:** Use **Node** for each lab location + **Orchestrator** within each lab for task coordination.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Lab A (US)    │◄───►│  Lab B (Europe) │◄───►│  Lab C (Asia)   │
│                 │     │                 │     │                 │
│  Orchestrator   │     │  Orchestrator   │     │  Orchestrator   │
│  • Professor    │     │  • Director     │     │  • Lead         │
│  • Researcher   │     │  • Scientist    │     │  • Engineer     │
│  • Analyst      │     │  • Technician   │     │  • Analyst      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Benefits:**
- Each lab manages its own resources (GPU clusters, specialized hardware)
- Labs can collaborate on research projects
- Orchestrator within each lab coordinates local tasks
- P2P networking enables direct lab-to-lab communication

---

### 2. **Smart City Traffic Management**

**Problem:** A city needs to coordinate traffic management across multiple intersections and districts.

**Solution:** Use **Node** for each district + **Orchestrator** for traffic coordination.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  District A     │◄───►│  District B     │◄───►│  District C     │
│                 │     │                 │     │                 │
│  Orchestrator   │     │  Orchestrator   │     │  Orchestrator   │
│  • Traffic AI   │     │  • Traffic AI   │     │  • Traffic AI   │
│  • Camera Agent │     │  • Sensor Agent │     │  • Camera Agent │
│  • Signal Agent │     │  • Signal Agent │     │  • Sensor Agent │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Benefits:**
- Each district manages its own traffic cameras and sensors
- Orchestrator coordinates traffic signals within district
- Nodes share traffic data across districts
- Resource management tracks camera/sensor availability

---

### 3. **Multi-Location Customer Support**

**Problem:** A company has support centers in different time zones, each with specialized teams.

**Solution:** Use **Node** for each support center + **Orchestrator** for ticket routing.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  US Support     │◄───►│  EU Support     │◄───►│  APAC Support   │
│                 │     │                 │     │                 │
│  Orchestrator   │     │  Orchestrator   │     │  Orchestrator   │
│  • Manager      │     │  • Manager      │     │  • Manager      │
│  • Tech Support │     │  • Tech Support │     │  • Tech Support │
│  • Sales Agent  │     │  • Sales Agent  │     │  • Sales Agent  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Benefits:**
- 24/7 coverage across time zones
- Each center manages its own resources
- Orchestrator routes tickets to appropriate specialist
- Nodes share knowledge base and customer history

---

### 4. **Autonomous Vehicle Fleet**

**Problem:** A fleet of autonomous vehicles needs coordination for route planning and resource management.

**Solution:** Use **Node** for each vehicle + **Orchestrator** for route coordination.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Vehicle A      │◄───►│  Vehicle B      │◄───►│  Vehicle C      │
│                 │     │                 │     │                 │
│  Orchestrator   │     │  Orchestrator   │     │  Orchestrator   │
│  • Navigation   │     │  • Navigation   │     │  • Navigation   │
│  • Sensor Agent │     │  • Sensor Agent │     │  • Sensor Agent │
│  • Safety Agent │     │  • Safety Agent │     │  • Safety Agent │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Benefits:**
- Each vehicle manages its own sensors and compute
- Orchestrator coordinates navigation decisions
- Nodes share traffic and road condition data
- Resource management tracks battery, compute, sensors

---

### 5. **Distributed Content Creation**

**Problem:** A media company needs to coordinate content creation across multiple teams.

**Solution:** Use **Node** for each team + **Orchestrator** for content workflow.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Writing Team   │◄───►│  Design Team    │◄───►│  Video Team     │
│                 │     │                 │     │                 │
│  Orchestrator   │     │  Orchestrator   │     │  Orchestrator   │
│  • Editor       │     │  • Art Director │     │  • Producer     │
│  • Writer       │     │  • Designer     │     │  • Editor       │
│  • Researcher   │     │  • Illustrator  │     │  • Animator     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Benefits:**
- Each team manages its own tools and resources
- Orchestrator coordinates content workflow
- Nodes share assets and drafts
- Resource management tracks rendering capacity

---

## Project Ideas

### Beginner Projects

#### 1. **Personal AI Assistant Network**
**Architecture:** Node only
**Description:** Create a node with multiple specialized assistants (calendar, email, research, coding).

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.core.node import Node

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create personal assistant node
node = Node(node_id="personal-assistants", name="My AI Assistants")
await node.start()

# Create specialized assistants
calendar_agent = Agent(config=AgentConfig(
    name="Calendar",
    role=AgentRole.SPECIALIZED,
    system_prompt="You manage calendar and scheduling.",
))

email_agent = Agent(config=AgentConfig(
    name="Email",
    role=AgentRole.SPECIALIZED,
    system_prompt="You help with email management.",
))

research_agent = Agent(config=AgentConfig(
    name="Research",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct research and gather information.",
))

# Start and register agents
await calendar_agent.start()
await email_agent.start()
await research_agent.start()

node.add_agent(calendar_agent.id)
node.add_agent(email_agent.id)
node.add_agent(research_agent.id)

# Use the network
print(f"Node has {node.agent_count} assistants")
```

**Learning Outcomes:**
- Node creation and management
- Agent registration
- Resource tracking

---

#### 2. **Study Group Simulator**
**Architecture:** Orchestrator only
**Description:** Simulate a study group with a professor and students.

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole

set_llm(ollama_llm="llama3.2:1b", stream=True)

# Create study group
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You guide students through complex topics.",
))

math_student = Agent(config=AgentConfig(
    name="MathStudent",
    role=AgentRole.SPECIALIZED,
    system_prompt="You excel at mathematical problems.",
))

science_student = Agent(config=AgentConfig(
    name="ScienceStudent",
    role=AgentRole.SPECIALIZED,
    system_prompt="You excel at scientific concepts.",
))

# Create orchestrator
study_group = Orchestrator(
    main_agent=professor,
    sub_agents=[math_student, science_student],
    context_name="study_group",
    main_role="Professor",
    sub_role="Student"
)

await study_group.start()

# Study session
result = await study_group.execute_task(
    "Explain the relationship between calculus and physics"
)

await study_group.stop()
```

**Learning Outcomes:**
- Orchestrator setup
- Task delegation
- Result aggregation

---

### Intermediate Projects

#### 3. **Multi-Location News Network**
**Architecture:** Node + Orchestrator
**Description:** Create a distributed news network with editorial teams in different locations.

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.core.node import Node

set_llm(ollama_llm="llama3.2:1b", stream=True)

comm = CommunicationManager()
await comm.start()

# New York Office
ny_node = Node(node_id="ny-office", name="New York Office")
await ny_node.start()

ny_editor = Agent(config=AgentConfig(
    name="NY_Editor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate news coverage in New York.",
))
ny_reporter = Agent(config=AgentConfig(
    name="NY_Reporter",
    role=AgentRole.SPECIALIZED,
    system_prompt="You report on New York events.",
))

await ny_editor.start(communication_manager=comm)
await ny_reporter.start(communication_manager=comm)

ny_node.add_agent(ny_editor.id)
ny_node.add_agent(ny_reporter.id)

ny_orchestrator = Orchestrator(
    main_agent=ny_editor,
    sub_agents=[ny_reporter],
    context_name="ny_newsroom",
    main_role="Editor",
    sub_role="Reporter"
)
await ny_orchestrator.start()

# London Office
london_node = Node(node_id="london-office", name="London Office")
await london_node.start()

london_editor = Agent(config=AgentConfig(
    name="London_Editor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate news coverage in London.",
))
london_reporter = Agent(config=AgentConfig(
    name="London_Reporter",
    role=AgentRole.SPECIALIZED,
    system_prompt="You report on London events.",
))

await london_editor.start(communication_manager=comm)
await london_reporter.start(communication_manager=comm)

london_node.add_agent(london_editor.id)
london_node.add_agent(london_reporter.id)

london_orchestrator = Orchestrator(
    main_agent=london_editor,
    sub_agents=[london_reporter],
    context_name="london_newsroom",
    main_role="Editor",
    sub_role="Reporter"
)
await london_orchestrator.start()

# Connect offices
ny_node.connect("london-office")
london_node.connect("ny-office")

# Collaborative reporting
result = await ny_orchestrator.execute_task(
    "Cover the global impact of AI regulation"
)

# Cleanup
await ny_orchestrator.stop()
await london_orchestrator.stop()
await ny_node.stop()
await london_node.stop()
await comm.stop()
```

**Learning Outcomes:**
- Combining Node and Orchestrator
- Multi-location coordination
- Cross-node communication

---

#### 4. **E-commerce Support System**
**Architecture:** Node + Orchestrator
**Description:** Build a distributed customer support system with specialized teams.

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.core.node import Node

set_llm(ollama_llm="llama3.2:1b", stream=True)

comm = CommunicationManager()
await comm.start()

# Support Node
support_node = Node(node_id="support-center", name="Customer Support Center")
await support_node.start()

# Create support team
support_manager = Agent(config=AgentConfig(
    name="SupportManager",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate customer support and route tickets.",
))

tech_support = Agent(config=AgentConfig(
    name="TechSupport",
    role=AgentRole.SPECIALIZED,
    system_prompt="You handle technical issues and troubleshooting.",
))

billing_support = Agent(config=AgentConfig(
    name="BillingSupport",
    role=AgentRole.SPECIALIZED,
    system_prompt="You handle billing and payment inquiries.",
))

sales_support = Agent(config=AgentConfig(
    name="SalesSupport",
    role=AgentRole.SPECIALIZED,
    system_prompt="You handle sales inquiries and product questions.",
))

# Start agents
await support_manager.start(communication_manager=comm)
await tech_support.start(communication_manager=comm)
await billing_support.start(communication_manager=comm)
await sales_support.start(communication_manager=comm)

# Register agents
support_node.add_agent(support_manager.id)
support_node.add_agent(tech_support.id)
support_node.add_agent(billing_support.id)
support_node.add_agent(sales_support.id)

# Create orchestrator
support_orchestrator = Orchestrator(
    main_agent=support_manager,
    sub_agents=[tech_support, billing_support, sales_support],
    context_name="support_center",
    main_role="Manager",
    sub_role="Specialist"
)
await support_orchestrator.start()

# Handle customer inquiry
result = await support_orchestrator.execute_task(
    "Customer reports they can't log in and were charged twice"
)

# Cleanup
await support_orchestrator.stop()
await support_node.stop()
await comm.stop()
```

**Learning Outcomes:**
- Real-world application
- Ticket routing
- Multi-specialist coordination

---

### Advanced Projects

#### 5. **Distributed AI Research Lab**
**Architecture:** Multiple Nodes + Orchestrators
**Description:** Create a research network with multiple labs, each with specialized equipment and expertise.

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.core.node import Node

set_llm(ollama_llm="llama3.2:1b", stream=True)

comm = CommunicationManager()
await comm.start()

# ──────────────────────────────────────────────
# Lab A: Machine Learning Research
# ──────────────────────────────────────────────
ml_node = Node(node_id="ml-lab", name="Machine Learning Lab")
await ml_node.start()
ml_node.set_resource("gpu_count", 8)
ml_node.set_resource("model_cache", {"gpt2": True, "bert": True})

ml_director = Agent(config=AgentConfig(
    name="ML_Director",
    role=AgentRole.COORDINATOR,
    system_prompt="You direct machine learning research projects.",
))
ml_researcher = Agent(config=AgentConfig(
    name="ML_Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct ML experiments and analysis.",
))
ml_engineer = Agent(config=AgentConfig(
    name="ML_Engineer",
    role=AgentRole.SPECIALIZED,
    system_prompt="You implement and optimize ML models.",
))

await ml_director.start(communication_manager=comm)
await ml_researcher.start(communication_manager=comm)
await ml_engineer.start(communication_manager=comm)

ml_node.add_agent(ml_director.id)
ml_node.add_agent(ml_researcher.id)
ml_node.add_agent(ml_engineer.id)

ml_orchestrator = Orchestrator(
    main_agent=ml_director,
    sub_agents=[ml_researcher, ml_engineer],
    context_name="ml_lab",
    main_role="Director",
    sub_role="Researcher"
)
await ml_orchestrator.start()

# ──────────────────────────────────────────────
# Lab B: Natural Language Processing
# ──────────────────────────────────────────────
nlp_node = Node(node_id="nlp-lab", name="NLP Lab")
await nlp_node.start()
nlp_node.set_resource("gpu_count", 4)
nlp_node.set_resource("model_cache", {"llama": True, "bert": True})

nlp_director = Agent(config=AgentConfig(
    name="NLP_Director",
    role=AgentRole.COORDINATOR,
    system_prompt="You direct NLP research projects.",
))
nlp_researcher = Agent(config=AgentConfig(
    name="NLP_Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You conduct NLP experiments and analysis.",
))

await nlp_director.start(communication_manager=comm)
await nlp_researcher.start(communication_manager=comm)

nlp_node.add_agent(nlp_director.id)
nlp_node.add_agent(nlp_researcher.id)

nlp_orchestrator = Orchestrator(
    main_agent=nlp_director,
    sub_agents=[nlp_researcher],
    context_name="nlp_lab",
    main_role="Director",
    sub_role="Researcher"
)
await nlp_orchestrator.start()

# ──────────────────────────────────────────────
# Connect labs
# ──────────────────────────────────────────────
ml_node.connect("nlp-lab")
nlp_node.connect("ml-lab")

# ──────────────────────────────────────────────
# Collaborative research
# ──────────────────────────────────────────────
result = await ml_orchestrator.execute_task(
    "Collaborate with NLP lab on transformer architecture improvements"
)

# Check resources
print(f"ML Lab GPUs: {ml_node.get_resource('gpu_count')}")
print(f"NLP Lab GPUs: {nlp_node.get_resource('gpu_count')}")

# Cleanup
await ml_orchestrator.stop()
await nlp_orchestrator.stop()
    finally:
        await agent2.stop()
        await comm.stop()
```

**Learning Outcomes:**
- Multi-node architecture
- Resource management
- Cross-lab collaboration
- Complex orchestration

---

#### 6. **Smart Factory Automation**
**Architecture:** Multiple Nodes + Orchestrators
**Description:** Build an automated factory system with multiple production lines.

```python
from daie import Agent, AgentConfig, Orchestrator, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.core.node import Node

set_llm(ollama_llm="llama3.2:1b", stream=True)

comm = CommunicationManager()
await comm.start()

# ──────────────────────────────────────────────
# Production Line A: Assembly
# ──────────────────────────────────────────────
assembly_node = Node(node_id="assembly-line", name="Assembly Line")
await assembly_node.start()
assembly_node.set_resource("robot_count", 10)
assembly_node.set_resource("conveyor_speed", "fast")

assembly_manager = Agent(config=AgentConfig(
    name="AssemblyManager",
    role=AgentRole.COORDINATOR,
    system_prompt="You manage assembly line operations.",
))
robot_agent = Agent(config=AgentConfig(
    name="RobotAgent",
    role=AgentRole.SPECIALIZED,
    system_prompt="You control assembly robots.",
))
quality_agent = Agent(config=AgentConfig(
    name="QualityAgent",
    role=AgentRole.SPECIALIZED,
    system_prompt="You perform quality control checks.",
))

await assembly_manager.start(communication_manager=comm)
await robot_agent.start(communication_manager=comm)
await quality_agent.start(communication_manager=comm)

assembly_node.add_agent(assembly_manager.id)
assembly_node.add_agent(robot_agent.id)
assembly_node.add_agent(quality_agent.id)

assembly_orchestrator = Orchestrator(
    main_agent=assembly_manager,
    sub_agents=[robot_agent, quality_agent],
    context_name="assembly_line",
    main_role="Manager",
    sub_role="Worker"
)
await assembly_orchestrator.start()

# ──────────────────────────────────────────────
# Production Line B: Packaging
# ──────────────────────────────────────────────
packaging_node = Node(node_id="packaging-line", name="Packaging Line")
await packaging_node.start()
packaging_node.set_resource("packaging_machines", 5)

packaging_manager = Agent(config=AgentConfig(
    name="PackagingManager",
    role=AgentRole.COORDINATOR,
    system_prompt="You manage packaging operations.",
))
packaging_agent = Agent(config=AgentConfig(
    name="PackagingAgent",
    role=AgentRole.SPECIALIZED,
    system_prompt="You operate packaging machines.",
))

await packaging_manager.start(communication_manager=comm)
await packaging_agent.start(communication_manager=comm)

packaging_node.add_agent(packaging_manager.id)
packaging_node.add_agent(packaging_agent.id)

packaging_orchestrator = Orchestrator(
    main_agent=packaging_manager,
    sub_agents=[packaging_agent],
    context_name="packaging_line",
    main_role="Manager",
    sub_role="Operator"
)
await packaging_orchestrator.start()

# ──────────────────────────────────────────────
# Connect production lines
# ──────────────────────────────────────────────
assembly_node.connect("packaging-line")
packaging_node.connect("assembly-line")

# ──────────────────────────────────────────────
# Coordinate production
# ──────────────────────────────────────────────
result = await assembly_orchestrator.execute_task(
    "Produce 100 units and coordinate with packaging line"
)

# Check resources
print(f"Assembly robots: {assembly_node.get_resource('robot_count')}")
print(f"Packaging machines: {packaging_node.get_resource('packaging_machines')}")

# Cleanup
await assembly_orchestrator.stop()
await packaging_orchestrator.stop()
await assembly_node.stop()
await packaging_node.stop()
await comm.stop()
```

**Learning Outcomes:**
- Industrial automation
- Resource tracking
- Production coordination
- Multi-line synchronization

---

## Pros and Cons

### Node

#### ✅ Pros

| Advantage | Description |
|-----------|-------------|
| **Scalability** | Add nodes horizontally to increase capacity |
| **Resource Management** | Track GPU, memory, model cache per node |
| **Decentralization** | No single point of failure |
| **P2P Networking** | Direct node-to-node communication |
| **Flexibility** | Each node can have different configurations |
| **Isolation** | Resources and agents isolated per node |
| **Geographic Distribution** | Deploy across multiple locations |

#### ❌ Cons

| Disadvantage | Description |
|--------------|-------------|
| **Complexity** | More complex to set up and manage |
| **No Task Delegation** | Manual coordination required |
| **No Result Aggregation** | Must combine results manually |
| **Overhead** | Additional layer for simple use cases |
| **Learning Curve** | Requires understanding of distributed systems |

---

### Orchestrator

#### ✅ Pros

| Advantage | Description |
|-----------|-------------|
| **Task Delegation** | Automatic task decomposition and delegation |
| **Result Aggregation** | Automatic combination of sub-agent outputs |
| **Clear Structure** | Hierarchical organization is easy to understand |
| **Workflow Control** | Main agent controls the workflow |
| **Specialization** | Sub-agents can be highly specialized |
| **Context Awareness** | Different contexts for different scenarios |
| **Simplicity** | Easier to set up for task coordination |

#### ❌ Cons

| Disadvantage | Description |
|--------------|-------------|
| **Centralization** | Main agent is a single point of failure |
| **Limited Scalability** | Vertical scaling only (add sub-agents) |
| **No Resource Management** | Doesn't track hardware resources |
| **Rigid Structure** | Hierarchical structure may not fit all use cases |
| **Main Agent Bottleneck** | Main agent can become a bottleneck |

---

### Hybrid (Node + Orchestrator)

#### ✅ Pros

| Advantage | Description |
|-----------|-------------|
| **Best of Both Worlds** | Combines infrastructure management with workflow coordination |
| **Maximum Scalability** | Both horizontal (nodes) and vertical (sub-agents) scaling |
| **Resource Efficiency** | Per-node resource tracking + task allocation |
| **Fault Tolerance** | Distributed + orchestrator backup |
| **Flexibility** | Can use Node-only, Orchestrator-only, or both as needed |
| **Enterprise-Ready** | Suitable for large-scale, complex systems |
| **Geographic Distribution** | Deploy across multiple locations with local coordination |
| **Load Balancing** | Distribute orchestrators across nodes |

#### ❌ Cons

| Disadvantage | Description |
|--------------|-------------|
| **Highest Complexity** | Most complex to set up and manage |
| **Steepest Learning Curve** | Requires both distributed systems and workflow design knowledge |
| **Highest Cost** | More infrastructure and maintenance overhead |
| **Hardest Debugging** | Distributed + centralized debugging challenges |
| **Most Overhead** | Network + coordination overhead |
| **Requires Both Skill Sets** | Need expertise in both Node and Orchestrator |

---

## Performance Comparison

### Node Performance

| Metric | Rating | Notes |
|--------|--------|-------|
| **Setup Time** | ⭐⭐⭐ | More initial setup required |
| **Scalability** | ⭐⭐⭐⭐⭐ | Excellent horizontal scaling |
| **Resource Efficiency** | ⭐⭐⭐⭐⭐ | Built-in resource tracking |
| **Communication Speed** | ⭐⭐⭐⭐⭐ | Direct P2P communication |
| **Fault Tolerance** | ⭐⭐⭐⭐⭐ | No single point of failure |
| **Complexity** | ⭐⭐ | Higher complexity |

### Orchestrator Performance

| Metric | Rating | Notes |
|--------|--------|-------|
| **Setup Time** | ⭐⭐⭐⭐⭐ | Quick to set up |
| **Scalability** | ⭐⭐⭐ | Limited to vertical scaling |
| **Resource Efficiency** | ⭐⭐ | No resource tracking |
| **Communication Speed** | ⭐⭐⭐⭐ | Via CommunicationManager |
| **Fault Tolerance** | ⭐⭐ | Main agent is single point of failure |
| **Complexity** | ⭐⭐⭐⭐⭐ | Simple and straightforward |

### Hybrid (Node + Orchestrator) Performance

| Metric | Rating | Notes |
|--------|--------|-------|
| **Setup Time** | ⭐⭐ | Most complex setup |
| **Scalability** | ⭐⭐⭐⭐⭐ | Both horizontal and vertical scaling |
| **Resource Efficiency** | ⭐⭐⭐⭐⭐ | Per-node resource tracking + task allocation |
| **Communication Speed** | ⭐⭐⭐⭐ | P2P + A2A messaging |
| **Fault Tolerance** | ⭐⭐⭐⭐ | Distributed + orchestrator backup |
| **Complexity** | ⭐ | Most complex (requires both skill sets) |

---

## Network Configuration

Both Node and Orchestrator architectures use the same underlying network configuration parameters for agents. Understanding these parameters is crucial for building distributed multi-agent systems.

### `network_url`

The `network_url` parameter defines the URL where an agent is hosted. This is the address that other agents use to communicate with this agent over the network.

**Key Points:**
- **Required for P2P communication** — Agents need to know each other's URLs to communicate directly
- **Unique per agent** — Each agent should have its own unique `network_url`
- **Accessible address** — The URL must be reachable by other agents in the network

**Examples:**

```python
# Local development
agent = Agent(config=AgentConfig(
    name="LocalAgent",
    network_url="http://localhost:8000"
))

# LAN deployment
agent = Agent(config=AgentConfig(
    name="LANAgent",
    network_url="http://192.168.1.100:8000"
))

# Internet deployment
agent = Agent(config=AgentConfig(
    name="CloudAgent",
    network_url="https://my-agent.example.com:8000"
))
```

### `network_connections`

The `network_connections` parameter is a dictionary that maps peer agent IDs to their network URLs. This allows an agent to know which other agents it can directly communicate with.

**Key Points:**
- **Bidirectional communication** — Both agents should have each other in their `network_connections`
- **Direct messaging** — Enables direct agent-to-agent communication without routing
- **Network topology** — Defines the structure of your agent network

**Examples:**

```python
# Agent A knows about Agent B
agent_a = Agent(config=AgentConfig(
    name="AgentA",
    network_url="http://localhost:8000",
    network_connections={
        "agent-b-id": "http://localhost:8001"
    }
))

# Agent B knows about Agent A
agent_b = Agent(config=AgentConfig(
    name="AgentB",
    network_url="http://localhost:8001",
    network_connections={
        "agent-a-id": "http://localhost:8000"
    }
))
```

### Network Configuration in Node Architecture

In Node architecture, agents within the same node can communicate directly. The `network_url` and `network_connections` are used to enable P2P communication between agents across different nodes.

```python
from daie import Agent, AgentConfig
from daie.core.node import Node

# Create a node
node = Node(node_id="research-lab", name="Research Lab")
node.start()

# Create agents with network configuration
agent = Agent(config=AgentConfig(
    name="Researcher",
    network_url="http://localhost:8000",
    network_connections={
        "analyst-id": "http://localhost:8001",
        "writer-id": "http://localhost:8002"
    }
))

await agent.start()
node.add_agent(agent.id)
```

### Network Configuration in Orchestrator Architecture

In Orchestrator architecture, the main agent and sub-agents can be configured with `network_url` and `network_connections` to enable distributed communication.

```python
from daie import Agent, AgentConfig, Orchestrator

# Create main agent
professor = Agent(config=AgentConfig(
    name="Professor",
    network_url="http://localhost:8000",
    network_connections={
        "researcher-id": "http://localhost:8001",
        "analyst-id": "http://localhost:8002"
    }
))

# Create sub-agents
researcher = Agent(config=AgentConfig(
    name="Researcher",
    network_url="http://localhost:8001",
    network_connections={
        "professor-id": "http://localhost:8000"
    }
))

analyst = Agent(config=AgentConfig(
    name="Analyst",
    network_url="http://localhost:8002",
    network_connections={
        "professor-id": "http://localhost:8000"
    }
))

# Create orchestrator
orchestrator = Orchestrator(
    main_agent=professor,
    sub_agents=[researcher, analyst],
    context_name="research_lab"
)
```

### Network Configuration in Hybrid Architecture

In Hybrid architecture, you can use `network_url` and `network_connections` to enable communication across multiple nodes and orchestrators.

```python
from daie import Agent, AgentConfig, Orchestrator
from daie.core.node import Node
from daie.communication import CommunicationManager

# Create communication manager
comm = CommunicationManager()
await comm.start()

# Node 1: Research Lab
research_node = Node(node_id="research-lab", name="Research Lab")
research_node.start()

professor = Agent(config=AgentConfig(
    name="Professor",
    network_url="http://localhost:8000",
    network_connections={
        "analyst-id": "http://localhost:8001",
    }
))

await professor.start(communication_manager=comm)
research_node.add_agent(professor.id)

# Node 2: Analysis Center
analysis_node = Node(node_id="analysis-center", name="Analysis Center")
analysis_node.start()

analyst = Agent(config=AgentConfig(
    name="Analyst",
    network_url="http://localhost:8001",
    network_connections={
        "professor-id": "http://localhost:8000",
    }
))

await analyst.start(communication_manager=comm)
analysis_node.add_agent(analyst.id)

# Connect nodes
research_node.connect("analysis-center")
analysis_node.connect("research-lab")
```

### Best Practices for Network Configuration

1. **Always set `network_url`** — Every agent that needs to communicate over the network should have a `network_url`
2. **Use consistent URLs** — Use the same URL format across all agents (e.g., all HTTP or all HTTPS)
3. **Ensure accessibility** — Make sure the URLs are reachable by all agents in the network
4. **Document your topology** — Keep a record of which agents connect to which
5. **Use meaningful IDs** — Use descriptive agent IDs that make it easy to identify agents
6. **Test connectivity** — Verify that agents can reach each other's URLs before deploying
7. **Handle failures** — Implement retry logic for network communication failures
8. **Use HTTPS for production** — Always use HTTPS for production deployments
9. **Consider firewall rules** — Ensure firewall rules allow communication between agents
10. **Monitor network health** — Monitor network connectivity and latency between agents

---

## Best Practices

### Node Best Practices

1. **Plan your network topology** — Design node connections before implementation
2. **Use meaningful node IDs** — Make IDs descriptive (e.g., "us-east-gpu-cluster")
3. **Track resources** — Always set and monitor node resources
4. **Implement health checks** — Monitor node status regularly
5. **Handle node failures** — Implement retry logic and failover
6. **Document connections** — Keep track of which nodes connect to which
7. **Use method chaining** — Leverage fluent API for cleaner code

### Orchestrator Best Practices

1. **Clear role definitions** — Define clear roles for main and sub-agents
2. **Specialized prompts** — Provide detailed system prompts for each agent
3. **Appropriate context** — Choose meaningful context names
4. **Task decomposition** — Break complex tasks into clear sub-tasks
5. **Result validation** — Ensure main agent validates sub-agent results
6. **Error handling** — Handle sub-agent failures gracefully
7. **Monitor performance** — Track task execution times

### Hybrid (Node + Orchestrator) Best Practices

1. **Separate concerns** — Use Node for infrastructure, Orchestrator for workflows
2. **Resource allocation** — Allocate resources based on orchestrator needs
3. **Cross-node communication** — Use P2P for node-to-node, A2A for agent-to-agent
4. **Load balancing** — Distribute orchestrators across nodes
5. **Monitoring** — Monitor both node health and orchestrator performance
6. **Documentation** — Document the overall architecture clearly
7. **Plan topology first** — Design node and orchestrator placement before implementation
8. **Use meaningful IDs** — Make node and orchestrator IDs descriptive
9. **Implement health checks** — Monitor both node and orchestrator status
10. **Handle failures gracefully** — Implement retry logic and failover at both levels

---

## Summary

### Choose Node When:
- Building distributed networks
- Managing hardware resources
- Need horizontal scalability
- Require P2P communication
- Multiple locations/machines

### Choose Orchestrator When:
- Coordinating complex tasks
- Need task delegation
- Require result aggregation
- Clear hierarchical workflow
- Specialized agent teams

### Use Hybrid (Node + Orchestrator) When:
- Building enterprise-scale systems
- Need both infrastructure and workflow management
- Distributed teams with local coordination
- Resource-aware task execution
- Complex distributed workflows
- Multi-location with specialized teams
- Edge computing with central coordination
- Maximum scalability and flexibility
- Large-scale, complex multi-agent systems

---

## Related Documentation

- [Node Documentation](node.md) — Complete Node API reference
- [Orchestrator Documentation](orchestrator.md) — Complete Orchestrator API reference
- [Agents Documentation](agents.md) — Agent configuration and the ReAct loop
- [Communication Documentation](communication.md) — P2P networking and messaging
- [P2P Networking](p2p.md) — Peer-to-peer communication protocol
- [Examples](../examples/) — Working code examples

---

## Examples

- [`examples/07_node_agents_interactive.py`](../examples/07_node_agents_interactive.py) — Interactive Node-based chat system
- [`examples/08_node_agents_demo.py`](../examples/08_node_agents_demo.py) — Automated Node demonstration
- [`examples/classroom_demo.py`](../examples/classroom_demo.py) — Orchestrator classroom example
- [`examples/courtroom_demo.py`](../examples/courtroom_demo.py) — Orchestrator courtroom example
- [`examples/03_p2p_networking.py`](../examples/03_p2p_networking.py) — P2P networking with agents
---

## Advanced Scalable Architectures

For production-grade decentralized AI, DAIE supports advanced multi-node patterns optimized for high availability, observability, and scale.

### 1. High-Availability Research Cluster (5 Nodes)

This pattern uses NATS JetStream for persistent messaging and automated heartbeats for health monitoring.

```python
from daie import Agent, AgentConfig, SystemConfig
from daie.core.hybrid import HybridOrchestratorNode

# Distributed configuration with NATS
config = SystemConfig(
    nats_url="nats://coordinator:4222",
    heartbeat_interval=5.0,
    enable_e2e_encryption=True
)

# 1. Orchestrator Node (The Brain)
brain_node = HybridOrchestratorNode(
    node_id="brain-01", 
    node_name="Central Coordinator",
    config=config
)

# 2. Compute Nodes (The Brawn) x 3
worker_nodes = []
for i in range(3):
    node = HybridOrchestratorNode(
        node_id=f"worker-{i:02d}",
        node_name=f"GPU Worker {i+1}",
        config=config
    )
    worker_nodes.append(node)

# 3. Discovery & Registry Node
# (Nodes automatically find each other via NATS and Kademlia DHT)

# Start all nodes
await brain_node.start()
for w in worker_nodes:
    await w.start()

# Health check (Stale nodes are automatically pruned after 300s)
topology = brain_node.comm_manager.get_network_topology()
print(f"Active Nodes in Cluster: {len(topology['nodes'])}")
```

### 2. Distributed Enterprise AI Ecosystem (10+ Nodes)

In a large-scale setup, nodes are partitioned by domain (e.g., Sales, Engineering, Legal) and use a shared **Identity & Registry Backbone**.

| Node Type | Count | Responsibility |
|-----------|-------|----------------|
| **Gateway Node** | 2 | Handles external requests, rate limiting, and global routing. |
| **Domain Nodes** | 6 | Specialized clusters for specific departments (Marketing, Finance). |
| **Storage Nodes** | 2 | RAG-specific nodes with high-speed vector database access. |

#### Observability & Tracing
Every request in an enterprise cluster is traced using `trace_id` propagated across nodes.

```python
from daie.core.tracing import TracerManager

# In an enterprise environment, enable full tracing
TracerManager().setup(service_name="daie-cluster", enabled=True)

# Every agent execution now logs structured context:
# [agent-id | trace-id] Performing task...
```

#### Metrics Monitoring
Expose a `/metrics` endpoint for Prometheus to monitor cluster health in real-time.

```python
from daie.core.metrics import metrics

# Automatically tracked:
# - agent_task_started_total
# - agent_tool_calls_total
# - llm_invocation_errors_total
```

### Summary of Scalability Best Practices

1. **Use NATS for Backbone**: Reliable, persistent, and supports offline queueing.
2. **Enable Heartbeats**: Crucial for detecting node failures in P2P networks.
3. **Structured Tracing**: Essential for debugging distributed agent workflows.
4. **Domain Partitioning**: Group agents into domain-specific hybrid nodes for better resource management.
