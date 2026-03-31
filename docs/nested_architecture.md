# Nested Architecture

This document explains the nested architecture used by the Decentralized AI Ecosystem.
It describes how `Orchestrator`, `HybridOrchestratorNode`, and `MultiNodeHybridSystem` combine to create nested coordination layers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER / APPLICATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    MAIN AGENT (Coordinator)                         │    │
│  │  • Receives user tasks                                              │    │
│  │  • Decomposes work                                                  │    │
│  │  • Delegates to sub-agents                                          │    │
│  │  • Aggregates results                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                        │
│                    ▼               ▼               ▼                        │
│  ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐    │
│  │     SUB-AGENT 1     │ │     SUB-AGENT 2     │ │     SUB-AGENT N     │    │
│  │  • Receives task    │ │  • Receives task    │ │  • Receives task    │    │
│  │  • Executes work    │ │  • Executes work    │ │  • Executes work    │    │
│  │  • Returns result   │ │  • Returns result   │ │  • Returns result   │    │
│  └─────────────────────┘ └─────────────────────┘ └─────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    COMMUNICATION MANAGER                            │    │
│  │  • A2A messaging (a2a_send_message)                                 │    │
│  │  • Task delegation (a2a_delegate_task)                              │    │
│  │  • P2P routing and peer discovery                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     HYBRID ORCHESTRATOR NODE                                │
│  • Combines node infrastructure with local orchestration                    │
│  • Hosts agents, resources, and local communication                         │
│  • Supports parent/child hybrid node structure                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MULTI-NODE HYBRID SYSTEM                              │
│  • Connects hybrid nodes across devices                                     │
│  • Enables cross-node P2P mesh and hierarchical relationships               │
│  • Supports N-layer nested ecosystems                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

- `Agent` layer: individual agents that run tasks and communicate.
- `Orchestrator` layer: main coordinator agent delegates to sub-agents.
- `HybridOrchestratorNode` layer: combines node infrastructure with local orchestration.
- `MultiNodeHybridSystem` layer: connects multiple hybrid nodes across devices.

## Core Concepts

- `Orchestrator`:
  - Coordinates one main agent and multiple sub-agents.
  - Main agent delegates work to sub-agents using A2A tools.
  - Supports nested orchestration through parent/child orchestrator relationships.

- `HybridOrchestratorNode`:
  - Combines the `Node` and `Orchestrator` architectures into a single hybrid component.
  - Manages local resources, agent lifecycle, communication, and orchestration.
  - Supports nested node relationships with parent/child hybrid nodes.

- `MultiNodeHybridSystem`:
  - Manages many `HybridOrchestratorNode` instances.
  - Connects nodes via P2P networking.
  - Supports parent/child node hierarchies for nested orchestration domains.

## Nested Layers

The architecture is built in layers:

1. `Agent` layer:
   - Individual agents with a configuration, system prompt, and task execution methods.

2. `Orchestrator` layer:
   - One main agent and multiple sub-agents.
   - The main agent becomes the coordinator for a specific context.
   - Sub-agents are specialized workers.

3. `HybridOrchestratorNode` layer:
   - A node that owns a local `Orchestrator`.
   - It also owns a local `Node` structure for resources and connectivity.
   - Agents in the node can participate in both workflow coordination and P2P communication.

4. `MultiNodeHybridSystem` layer:
   - A network of hybrid nodes.
   - Nodes can be connected, parented, and orchestrated together.

## Parent/Child Relationships

### Orchestrator-level nesting

`Orchestrator` exposes methods for nested orchestration:

- `set_parent(parent_orchestrator_id)`
- `add_child_orchestrator(child_orchestrator_id)`
- `remove_child_orchestrator(child_orchestrator_id)`
- `child_orchestrator_ids`
- `parent_orchestrator_id`

This allows orchestrators to form a nested tree of coordination contexts.
A child orchestrator can represent a specialized sub-domain, while the parent orchestrator oversees higher-level coordination.

### Hybrid node nesting

`HybridOrchestratorNode` supports nested node hierarchies:

- `set_parent_hybrid_node(parent_node_id)`
- `add_child_hybrid_node(child_node_id)`
- `remove_child_hybrid_node(child_node_id)`
- `child_hybrid_node_ids`
- `parent_hybrid_node_id`

These methods establish structural relationships between nodes and enable nested multi-agent ecosystems.

### Multi-node system membership

`MultiNodeHybridSystem` manages node relationships across the system:

- `create_node(...)`
- `connect_nodes(node_id1, node_id2)`
- `set_parent_child(parent_node_id, child_node_id)`
- `remove_parent_child(parent_node_id, child_node_id)`
- `get_child_nodes(node_id)`
- `get_parent_node(node_id)`

A parent node can contain child nodes, each with its own orchestrator and agents.

## Communication and Coordination

Nested architectures use a shared communication manager to bridge coordination and networking:

- `CommunicationManager` handles A2A messaging and task delegation.
- `HybridOrchestratorNode` and `MultiNodeHybridSystem` can share the same communication manager.
- Agents in nested orchestrators may still communicate directly through A2A tools.

## Multi-Device P2P Connectivity

The code supports multiple devices and layered P2P connectivity by synchronizing network metadata across nodes and agents.

- `connect_nodes(node_a, node_b)` now links the two hybrid nodes at the node layer.
- Each agent in the connected nodes receives direct peer network URLs for every agent in the opposite node.
- This ensures P2P routing can traverse multiple device endpoints even when the orchestrator and node layers are nested.
- For cross-device setups, configure each agent with `network_url` and optionally `network_connections`.

Example:

```python
# Set direct network URLs for device-hosted agents
agent_a.config.network_url = "http://device-a.local:8000"
agent_b.config.network_url = "http://device-b.local:8000"

system.connect_nodes("node-a", "node-b")
```

This allows the underlying `CommunicationManager` to route messages from one device's agents to another device's agents, giving you a functional multi-node P2P mesh across nested layers.

## ASC AI Nested Architecture

The ASC AI architecture is a nested, heterogeneous design that supports an "all different" approach across multiple layers.
It combines `Orchestrator` workflow coordination with `HybridOrchestratorNode` infrastructure for N-layer parent/child systems.

### Key principles

- `All different` means each layer can use different domain roles, policies, and communication behavior.
- `Parent` layers provide governance, strategy, and cross-domain coordination.
- `Child` layers execute specialized tasks, local decision-making, and resource management.
- `N-layer nesting` means a parent orchestrator can manage child orchestrators or child hybrid nodes, and those children can in turn manage deeper layers.

### Layer combination model

1. Parent orchestration layer
   - High-level coordination
   - Global policies and delegation rules
   - Routes tasks to child domains

2. Hybrid node layer
   - Local orchestration plus node resource management
   - Connects agents, routers, and communication services
   - Provides a compact execution domain for child tasks

3. Leaf agent layer
   - Specialized agents performing concrete work
   - Use system prompts and A2A tools for collaboration

### Brief data model

- `L0`: top-level parent orchestrator or multi-node system
- `L1..Ln`: nested child orchestrators, hybrid nodes, and leaf agents
- `parent_id`: identifier for the parent orchestrator/node
- `child_ids`: list of nested child orchestrator/node identifiers
- `context_name`: domain name for each nested layer
- `main_role` / `sub_role`: role semantics for each orchestration layer

### What this enables

- A parent layer can enforce a common workflow while child layers adapt to local requirements.
- Hybrid nodes act as the glue between orchestration logic and node-level connectivity.
- N layers of nesting support both wide ecosystems and deep hierarchical control.

### ASC AI nested architecture example

- Global orchestrator manages multiple regional hybrid nodes.
- Each hybrid node manages a local orchestrator plus agents for specific workflows.
- Child hybrid nodes may themselves be parents for more granular sub-domains.

## Example: Nested Hybrid System

```python
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.core.hybrid import MultiNodeHybridSystem

set_llm(ollama_llm="llama3.2:1b", stream=True)

system = MultiNodeHybridSystem()

research_node = system.create_node(
    node_id="research-lab",
    node_name="Research Lab",
    context_name="Research Lab",
    main_role="Professor",
    sub_role="Researcher"
)

content_node = system.create_node(
    node_id="content-creation",
    node_name="Content Creation",
    context_name="Content Creation",
    main_role="Director",
    sub_role="Creator"
)

# Create main and sub-agents for research node
professor = Agent(config=AgentConfig(
    name="Professor",
    role=AgentRole.COORDINATOR,
    system_prompt="You coordinate the research lab."
))
researcher = Agent(config=AgentConfig(
    name="Researcher",
    role=AgentRole.SPECIALIZED,
    system_prompt="You gather and summarize research."
))

research_node.set_main_agent(professor)
research_node.add_sub_agent(researcher)

# Create main and sub-agents for content node
director = Agent(config=AgentConfig(
    name="Director",
    role=AgentRole.COORDINATOR,
    system_prompt="You manage content creation."
))
creator = Agent(config=AgentConfig(
    name="Creator",
    role=AgentRole.SPECIALIZED,
    system_prompt="You generate and refine content."
))

content_node.set_main_agent(director)
content_node.add_sub_agent(creator)

# Nest nodes and connect them
system.set_parent_child("research-lab", "content-creation")
system.connect_nodes("research-lab", "content-creation")

await system.start_all()

result = await system.execute_task("research-lab", "Research the latest AI trends")

await system.stop_all()
```

## When to use nested architecture

- Use `Orchestrator` when you need a single coordination domain with one main agent and several sub-agents.
- Use `HybridOrchestratorNode` when you want a self-contained node that manages both resources and orchestration.
- Use `MultiNodeHybridSystem` when you need a distributed system of multiple hybrid nodes that can communicate and coordinate with each other.

## Benefits of nesting

- modular separation of domains
- scalable multi-agent systems
- hierarchical coordination and delegation
- flexible P2P networking across nodes
- re-use of the same `Orchestrator` and `Node` concepts at multiple levels

## 200 Real-Life Implementation Examples

1. Customer support routing with a main agent coordinating product, billing, and technical sub-agents.
2. Legal case preparation where the main agent delegates research, contract review, and precedent analysis.
3. Healthcare triage where the orchestrator sends symptoms to diagnosis, prescription, and scheduling agents.
4. Retail inventory planning with sub-agents for demand forecasting, purchase orders, and warehouse allocation.
5. Supply chain monitoring with main coordination between sourcing, manufacturing, and delivery agents.
6. Smart building management with main coordinator controlling climate, lighting, and security subsystems.
7. Financial advisory with a main advisor agent delegating tax, investment, and budgeting tasks.
8. Travel planning where the orchestrator manages itinerary, ticketing, and hotel booking agents.
9. Manufacturing quality control with sub-agents for inspection, defect analysis, and process optimization.
10. Educational tutoring where a main coach delegates math, writing, and exam-prep agents.
11. Research lab organization where the orchestrator assigns literature review, experiment design, and data analysis.
12. Marketing campaign orchestration with separate sub-agents for copywriting, design, and analytics.
13. Emergency response coordination among dispatch, field assessment, and logistics agents.
14. Event planning with main agent handling venue, catering, and attendee communication.
15. Human resources onboarding with sub-agents for paperwork, training, and benefits enrollment.
16. Insurance claims processing with main agent routing to verification, assessment, and payment sub-agents.
17. Public policy development with sub-agents for research, stakeholder outreach, and regulatory drafting.
18. E-commerce order processing with orchestrator assigning payment, fulfillment, and shipment tracking.
19. Environmental monitoring coordinating air quality, water quality, and wildlife tracking agents.
20. Cybersecurity incident response with main coordinator delegating triage, containment, and forensics.
21. Pharmaceutical drug development with sub-agents for chemistry, clinical design, and regulatory filing.
22. Automotive design workflow with main agent coordinating aerodynamics, materials, and simulation teams.
23. Energy grid optimization with sub-agents for demand forecasting, generation scheduling, and outage response.
24. Real estate property management with orchestrator managing leasing, maintenance, and tenant communications.
25. Content production with main coordinator delegating writing, editing, and publishing agents.
26. Restaurant operations with sub-agents for menu planning, supply ordering, and staffing.
27. Construction project management with main agent overseeing scheduling, procurement, and safety.
28. Clinical trial administration with sub-agents for recruitment, compliance, and data collection.
29. Robotics fleet coordination with main agent assigning tasks to cleaning, inspection, and delivery robots.
30. Smart agriculture with orchestrator managing irrigation, pest control, and harvest scheduling.
31. Retail customer personalization with sub-agents for recommendation, discounting, and feedback.
32. Telecommunications network troubleshooting with main agent coordinating routing, bandwidth, and hardware checks.
33. Automotive service scheduling with orchestrator dispatching diagnostics, repair, and parts agents.
34. Financial risk management with sub-agents for credit, market, and operational risk analysis.
35. Museum visitor experience with main agent delegating tour planning, exhibit information, and accessibility.
36. Media rights management with sub-agents for licensing, royalty accounting, and content clearance.
37. Airline operations with orchestrator coordinating crew scheduling, ground services, and maintenance.
38. City traffic optimization with main agent managing signals, incident response, and route planning.
39. Academic administration with sub-agents for admissions, advising, and records management.
40. Personal wellness coaching with orchestrator coordinating nutrition, fitness, and mental health agents.
41. Warehouse robotics coordination with main agent delegating picking, packing, and restocking.
42. Autonomous vehicle supervision with sub-agents for perception, planning, and communication.
43. Climate adaptation planning with orchestrator coordinating flood mitigation, heat response, and agriculture.
44. Mining operation safety with sub-agents for monitoring, evacuation planning, and environmental compliance.
45. Film production scheduling with main agent managing casting, locations, and post-production.
46. SaaS customer success with orchestrator tracking onboarding, retention, and escalation workflows.
47. Sports team strategy planning with main agent assigning scouting, training, and performance analysis.
48. Blockchain network governance with sub-agents for validation, proposal review, and rewards distribution.
49. Retail loss prevention with orchestrator coordinating surveillance, auditing, and incident investigation.
50. Hospitality guest services with main agent managing check-in, maintenance requests, and concierge.
51. Laboratory sample tracking with sub-agents for collection, testing, and reporting.
52. Nonprofit campaign coordination with orchestrator managing fundraising, volunteer logistics, and outreach.
53. Agricultural supply forecasting with sub-agents for weather, crop yields, and distribution.
54. Smart grid demand response with main agent adjusting pricing, load control, and storage.
55. Fleet maintenance planning with sub-agents for inspections, repairs, and replacement parts.
56. Translation workflow with orchestrator coordinating translation, editing, and localization reviewers.
57. Insurance underwriting with main agent distributing property, liability, and actuarial analysis.
58. Disaster recovery planning with sub-agents for backup, restoration, and communications.
59. Pharmaceutical supply chain tracking with orchestrator managing raw materials, production, and distribution.
60. Legal discovery management with sub-agents for document review, privilege checks, and deposition prep.
61. Airport ground handling with main agent coordinating baggage, fueling, and gate operations.
62. Renewable energy projects with sub-agents for permitting, construction, and community outreach.
63. Waste management with orchestrator managing collection routes, recycling, and hazardous disposal.
64. Food safety audits with main agent assigning inspections, lab tests, and corrective actions.
65. Smart classroom facilitation with sub-agents for lesson plans, student assessment, and teacher support.
66. Ports logistics with orchestrator coordinating docking, customs clearance, and cargo handling.
67. Digital marketing optimization with main agent dispatching SEO, paid media, and analytics teams.
68. Pharmaceutical adverse event monitoring with sub-agents for case intake, follow-up, and regulatory reporting.
69. Personal finance management with orchestrator delegating budget, savings, and investment planning.
70. Healthcare referral coordination with sub-agents for specialist scheduling, records transfer, and follow-up.
71. Construction safety oversight with main agent managing inspections, training, and compliance.
72. Retail merchandising with orchestrator coordinating pricing, display, and inventory replenishment.
73. Government service delivery with sub-agents for permit processing, benefits enrollment, and citizen communication.
74. Automotive supply chain validation with main agent overseeing supplier audit, inventory, and quality.
75. Cyber threat intelligence with sub-agents for sensor data, malware analysis, and threat reporting.
76. Academic curriculum development with orchestrator coordinating subject matter experts, materials, and accreditation.
77. Film distribution planning with main agent assigning regional release, streaming, and promotion.
78. Sports event operations with sub-agents for ticketing, security, and hospitality.
79. Real-time translation services with orchestrator coordinating speech, text, and context agents.
80. Energy project finance with sub-agents for modeling, due diligence, and investor reporting.
81. Biotech lab workflow with main agent coordinating experiment setup, data capture, and audit trails.
82. Retail returns handling with sub-agents for customer service, reverse logistics, and refunds.
83. Mental health support with orchestrator managing intake, therapy matching, and resource referrals.
84. Pharmaceutical cold chain monitoring with sub-agents for temperature, location, and compliance reporting.
85. Construction procurement with main agent overseeing bid evaluation, vendor onboarding, and contract management.
86. Smart factory coordination with orchestrator managing production lines, quality, and maintenance.
87. Drone delivery orchestration with main agent delegating route planning, payload handling, and airspace clearance.
88. Forest fire management with sub-agents for detection, containment, and evacuation.
89. Election operations with orchestrator coordinating voter outreach, logistics, and ballot counting.
90. Sports analytics services with main agent assigning opponent scouting, player metrics, and game-planning.
91. Environmental compliance auditing with sub-agents for sampling, reporting, and remediation.
92. Clinical documentation improvement with orchestrator managing chart review, coder feedback, and physician outreach.
93. Retail loyalty programs with main agent coordinating acquisition, retention, and reward fulfillment.
94. Manufacturing change control with sub-agents for design review, approval, and implementation tracking.
95. Corporate training programs with orchestrator managing content creation, delivery, and assessments.
96. Smart campus operations with main agent coordinating security, transport, and facility services.
97. Personal concierge services with sub-agents for reservations, errand support, and itinerary updates.
98. Logistics network planning with orchestrator coordinating warehouses, carriers, and customs.
99. Water treatment operations with sub-agents for intake, filtration, and waste disposal.
100. Collaborative product development with main agent guiding ideation, prototyping, and launch readiness.
101. Remote education platforms with orchestrator coordinating teachers, graders, and student feedback.
102. Industrial maintenance scheduling with sub-agents for inspection, repair, and parts logistics.
103. Video game development pipelines with orchestrator managing design, art, and QA teams.
104. Smart parking systems with sub-agents for occupancy detection, pricing, and navigation.
105. Wholesale purchasing with main agent coordinating supplier bids, inventory, and delivery.
106. Carbon footprint tracking with sub-agents for energy, travel, and procurement data.
107. Construction bidding coordination with orchestrator matching contractors, materials, and timelines.
108. Food delivery dispatching with main agent delegating orders, routing, and rider assignments.
109. Healthcare claims adjudication with sub-agents for eligibility, billing, and fraud detection.
110. IT incident management with orchestrator assigning monitoring, diagnostics, and remediation agents.
111. Architecture design review with sub-agents for code compliance, structural analysis, and sustainability.
112. Event marketing coordination with main agent managing promotions, registrations, and vendor services.
113. Vehicle leasing management with sub-agents for contracts, maintenance, and customer support.
114. Predictive maintenance for heavy machinery with orchestrator delegating sensors, alerts, and repair planning.
115. Legal contract automation with main agent overseeing clause generation, review, and negotiation.
116. Smart home ecosystems with sub-agents for energy, security, and comfort optimization.
117. Scientific publication workflows with orchestrator coordinating authors, reviewers, and editors.
118. Patient care coordination with sub-agents for diagnosis, therapy scheduling, and follow-up.
119. Retail shelf optimization with main agent assigning planograms, pricing, and inventory replenishment.
120. Public transit planning with sub-agents for schedules, real-time updates, and capacity control.
121. Translation quality assurance with orchestrator managing linguistic, cultural, and format checks.
122. Water distribution control with sub-agents for pressure, leak detection, and consumption forecasting.
123. Sports coaching platforms with main agent coordinating training plans, nutrition, and performance analysis.
124. Energy procurement with orchestrator delegating market analysis, contract negotiation, and portfolio balancing.
125. Insurance fraud detection with sub-agents for claims scoring, patterns, and investigator alerts.
126. Online marketplace moderation with main agent assigning review, compliance, and appeal handling.
127. Cybersecurity awareness training with orchestrator coordinating simulations, reporting, and remediation.
128. City emergency planning with sub-agents for evacuation, sheltering, and communications.
129. Educational content personalization with main agent using learner profiles, progress, and recommendations.
130. Pharmaceutical inventory management with sub-agents for batch tracking, expiry alerts, and resupply.
131. Recruitment workflow automation with orchestrator managing sourcing, screening, and interviewing.
132. Warehouse order consolidation with main agent coordinating packing, routing, and carrier selection.
133. Renewable energy asset management with sub-agents for performance, maintenance, and compliance.
134. Personal data privacy orchestration with main agent managing consent, access, and reporting.
135. Agriculture disease monitoring with sub-agents for field sensors, forecasting, and mitigation actions.
136. Building restoration planning with orchestrator assigning assessment, design, and contractor coordination.
137. Fleet telematics management with main agent delegating routing, safety, and compliance data.
138. Entertainment production budgeting with sub-agents for creative, technical, and distribution costs.
139. Urban planning engagement with main agent coordinating feedback, zoning, and sustainability considerations.
140. Medical device lifecycle management with sub-agents for approvals, manufacturing, and post-market surveillance.
141. Subscription service retention with orchestrator assigning offers, support, and renewal reminders.
142. Smart waste collection with main agent coordinating pickup, route optimization, and recycling sorting.
143. Retail promotions planning with sub-agents for pricing, merchandising, and customer targeting.
144. Fleet electrification rollout with orchestrator managing charging, vehicle selection, and incentives.
145. Manufacturing compliance audits with sub-agents for safety, quality, and documentation.
146. Sports facility scheduling with main agent coordinating booking, staffing, and maintenance.
147. Disaster relief logistics with sub-agents for supply staging, transport, and distribution.
148. Digital twin synchronization with main agent coordinating simulation, data feeds, and scenario planning.
149. Autonomous drone operation with sub-agents for navigation, payload management, and monitoring.
150. Clinical decision support with orchestrator delegating diagnostics, treatment options, and care coordination.
151. Retail checkout automation with main agent coordinating payment, inventory, and customer communication.
152. Smart city lighting with sub-agents for occupancy, energy, and maintenance control.
153. Insurance renewal orchestration with main agent managing policy review, risk assessment, and pricing.
154. Hospitality revenue management with sub-agents for demand forecasting, pricing, and inventory control.
155. Healthcare patient flow optimization with orchestrator delegating admissions, diagnostics, and discharge planning.
156. Construction site safety monitoring with sub-agents for sensors, inspections, and alerts.
157. Financial compliance reporting with main agent coordinating transaction monitoring, analytics, and submissions.
158. E-learning curriculum management with sub-agents for content creation, assessment, and feedback.
159. Smart retail window displays with orchestrator controlling promotions, inventory, and customer interaction.
160. Transportation demand forecasting with sub-agents for ridership, weather, and event impact.
161. Renewable hydrogen plant coordination with main agent assigning production, storage, and distribution.
162. Gaming community moderation with sub-agents for reports, enforcement, and appeals.
163. Clinical pathway orchestration with main agent coordinating specialists, tests, and treatment plans.
164. Manufacturing capacity planning with sub-agents for orders, labor, and equipment availability.
165. Food safety traceability with main agent managing source data, inspection, and compliance reporting.
166. Retail customer journey orchestration with sub-agents for acquisition, engagement, and loyalty.
167. Logistics customs clearance with main agent coordinating documentation, routing, and duty payment.
168. Waste-to-energy project management with sub-agents for collection, conversion, and emission control.
169. Digital asset management with orchestrator delegating tagging, approval, and publishing workflows.
170. Workforce scheduling with main agent assigning shifts, skills, and availability.
171. Autonomous shipping coordination with sub-agents for navigation, cargo handling, and port operations.
172. Pharmaceutical pharmacovigilance with main agent managing adverse event reporting, analysis, and response.
173. Smart irrigation planning with sub-agents for weather, soil moisture, and crop needs.
174. Metaverse event coordination with main agent managing venue, content, and participant engagement.
175. Building energy retrofits with sub-agents for audit, financing, and contractor management.
176. Digital onboarding workflows with main agent coordinating account setup, verification, and training.
177. Advanced manufacturing scheduling with sub-agents for machine loading, material flow, and quality checks.
178. Retail assortment optimization with main agent balancing demand, space, and supplier availability.
179. Telehealth care coordination with sub-agents for intake, triage, and specialist referrals.
180. Supply chain sustainability tracking with orchestrator managing carbon, waste, and supplier audits.
181. Financial wellness coaching with sub-agents for saving, investing, and debt reduction.
182. Smart campus security with main agent coordinating access control, surveillance, and incident response.
183. Agricultural yield prediction with sub-agents for sensor data, weather, and fertilizer management.
184. Insurance customer service with main agent routing policy, claims, and billing support.
185. Construction materials logistics with sub-agents for ordering, delivery, and inventory staging.
186. Digital product launch management with main agent coordinating design, testing, and marketing.
187. Environmental remediation projects with sub-agents for assessment, cleanup, and compliance.
188. Fleet telehealth support with main agent dispatching care, monitoring, and logistics.
189. Smart retail checkout with sub-agents for scanning, payment, and receipt delivery.
190. AI research coordination with main agent managing experiments, datasets, and result summarization.
191. Urban flood management with sub-agents for forecasting, infrastructure, and emergency response.
192. Aerospace mission planning with main agent coordinating payload, trajectory, and ground support.
193. Smart manufacturing line balancing with sub-agents for throughput, quality, and changeovers.
194. Personalized nutrition planning with main agent coordinating diet, preferences, and health goals.
195. Connected vehicle services with sub-agents for navigation, diagnostics, and passenger assistance.
196. Retail returns optimization with main agent managing inspection, disposition, and resale.
197. Supply chain resilience planning with sub-agents for risk, redundancy, and recovery readiness.
198. Sustainable packaging design with main agent coordinating materials, cost, and recyclability.
199. Healthcare population health management with sub-agents for screening, outreach, and intervention.
200. Distributed research collaboration with main agent coordinating experiments, sharing, and publication workflows.

## Summary

The nested architecture in this project builds from simple agent orchestration up to distributed hybrid nodes.
It enables clean layering:

- `Agent` → `Orchestrator` → `HybridOrchestratorNode` → `MultiNodeHybridSystem`

Each layer adds structure, connectivity, and nested control for complex decentralized AI applications.
