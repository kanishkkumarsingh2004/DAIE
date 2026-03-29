# 🔴 Advanced - Node-Based Multi-Agent Demo
# Difficulty: Advanced
# This example demonstrates the Node class with real agents in an automated demo mode.

"""
Example 08: Node-Based Multi-Agent Demo

Demonstrates:
  - Creating and managing a Node
  - Hosting multiple agents on a single node
  - Automated demonstration of node capabilities
  - Resource management on nodes
  - Node status monitoring
  - Agent coordination within a node
  - Collaborative task execution

Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │                    Node (Production Server)                 │
  │                                                             │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
  │  │  Assistant  │  │   Coder     │  │  Researcher │          │
  │  │   Agent     │  │   Agent     │  │   Agent     │          │
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
"""

import asyncio
import logging

from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.core.node import Node

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='node_agents_demo.log',
    filemode='w'
)

# Console handler for warnings only
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logging.getLogger('').addHandler(console)


class NodeChatSystem:
    """
    A complete chat system built on the Node architecture.
    
    This class demonstrates how to:
    - Create and manage a Node
    - Host multiple specialized agents
    - Manage node resources
    - Connect to peer nodes
    """
    
    def __init__(self, node_id: str, node_name: str):
        """
        Initialize the Node-based chat system.
        
        Args:
            node_id: Unique identifier for the node
            node_name: Display name for the node
        """
        # Create the node
        self.node = Node(node_id=node_id, name=node_name)
        
        # Create communication manager for P2P networking
        self.comm = CommunicationManager()
        
        # Store agents for easy access
        self.agents = {}
        
        # Track if system is initialized
        self._initialized = False
    
    async def initialize(self, use_streaming: bool = True):
        """
        Initialize the chat system with agents and resources.
        
        Args:
            use_streaming: Whether to enable LLM streaming
        """
        if self._initialized:
            print("[!] System already initialized")
            return
        
        print("\n" + "="*60)
        print("   INITIALIZING NODE-BASED MULTI-AGENT SYSTEM")
        print("="*60)
        
        # 1. Configure LLM
        print("\n[*] Configuring LLM...")
        set_llm(ollama_llm="llama3.2:1b", stream=use_streaming)
        print(f"    Streaming: {'ENABLED' if use_streaming else 'DISABLED'}")
        
        # 2. Start the communication manager
        print("\n[*] Starting Communication Manager...")
        await self.comm.start()
        print("    ✓ P2P layer ready")
        
        # 3. Start the node
        print(f"\n[*] Starting Node: {self.node.name} (ID: {self.node.node_id})...")
        self.node.start()
        print("    ✓ Node active")
        
        # 4. Set node resources
        print("\n[*] Configuring node resources...")
        self.node.set_resource("gpu_count", 2)
        self.node.set_resource("memory_gb", 16)
        self.node.set_resource("model_cache", {"llama3.2": True})
        self.node.set_resource("max_concurrent_tasks", 5)
        print("    ✓ Resources configured")
        
        # 5. Create and register agents
        print("\n[*] Creating agents...")
        await self._create_agents()
        
        # 6. Display node status
        print("\n[*] Node Status:")
        status = self.node.get_status()
        self._print_status(status)
        
        self._initialized = True
        print("\n[+] System initialization complete!")
        print("="*60 + "\n")
    
    async def _create_agents(self):
        """Create and register specialized agents on the node."""
        
        # Agent 1: General Assistant
        assistant_config = AgentConfig(
            name="Assistant",
            role=AgentRole.GENERAL_PURPOSE,
            system_prompt=(
                "You are a helpful general-purpose assistant. "
                "You can answer questions, provide explanations, and help with various tasks. "
                "You work on a node with other specialized agents."
            ),
            personality="friendly, patient, and thorough",
            behavior="always provides clear explanations with examples"
        )
        assistant = Agent(config=assistant_config)
        await assistant.start(communication_manager=self.comm)
        self.agents["assistant"] = assistant
        self.node.add_agent(assistant.id)
        print(f"    ✓ Assistant Agent (ID: {assistant.id})")
        
        # Agent 2: Coding Specialist
        coder_config = AgentConfig(
            name="Coder",
            role=AgentRole.SPECIALIZED,
            system_prompt=(
                "You are an expert programming assistant. "
                "You specialize in writing, debugging, and explaining code. "
                "You can work with multiple programming languages and frameworks. "
                "Always provide working code examples when possible."
            ),
            personality="precise, logical, and detail-oriented",
            behavior="always includes code comments and best practices"
        )
        coder = Agent(config=coder_config)
        await coder.start(communication_manager=self.comm)
        self.agents["coder"] = coder
        self.node.add_agent(coder.id)
        print(f"    ✓ Coder Agent (ID: {coder.id})")
        
        # Agent 3: Research Specialist
        researcher_config = AgentConfig(
            name="Researcher",
            role=AgentRole.SPECIALIZED,
            system_prompt=(
                "You are a research specialist. "
                "You excel at gathering information, analyzing data, and providing "
                "well-researched answers. You cite sources when possible and "
                "present information in a structured manner."
            ),
            personality="analytical, thorough, and objective",
            behavior="always structures responses with clear sections and bullet points"
        )
        researcher = Agent(config=researcher_config)
        await researcher.start(communication_manager=self.comm)
        self.agents["researcher"] = researcher
        self.node.add_agent(researcher.id)
        print(f"    ✓ Researcher Agent (ID: {researcher.id})")
    
    def _print_status(self, status: dict):
        """Pretty print node status."""
        print(f"    Node ID: {status['node_id']}")
        print(f"    Name: {status['name']}")
        print(f"    Status: {status['status']}")
        print(f"    Agents: {status['agent_count']} active")
        for agent_id in status['agents']:
            agent_name = self._get_agent_name_by_id(agent_id)
            print(f"      - {agent_name} ({agent_id[:8]}...)")
        print(f"    Connections: {status['connection_count']} peers")
        print(f"    Resources: {len(status['resources'])} configured")
    
    def _get_agent_name_by_id(self, agent_id: str) -> str:
        """Get agent name from ID."""
        for name, agent in self.agents.items():
            if agent.id == agent_id:
                return agent.name
        return "Unknown"
    
    async def connect_to_peer(self, peer_node_id: str):
        """
        Connect this node to a peer node.
        
        Args:
            peer_node_id: ID of the peer node to connect to
        """
        self.node.connect(peer_node_id)
        print(f"[+] Connected to peer node: {peer_node_id}")
    
    async def execute_intelligent_task(self, task: str) -> str:
        """
        Execute a task using intelligent agent selection and collaboration.
        
        This method lets agents self-select based on their expertise,
        and collaborates on complex tasks that span multiple domains.
        
        Args:
            task: The task to execute
        
        Returns:
            Combined result from all participating agents
        """
        print(f"\n[*] Executing intelligent task: {task[:50]}...")
        
        # Step 1: Have each agent evaluate if they should participate
        participating_agents = []
        evaluation_results = []
        
        for agent_name, agent in self.agents.items():
            print(f"    → Evaluating {agent.name}...")
            evaluation_prompt = (
                f"Based on your expertise, should you participate in this task? "
                f"Task: {task}\n\n"
                f"Respond with ONLY 'YES' or 'NO' and a brief reason why."
            )
            response = await agent.send_message(evaluation_prompt)
            evaluation_results.append(f"{agent.name}: {response[:100]}...")
            
            # Simple check if agent wants to participate
            if "yes" in response.lower() or "participate" in response.lower():
                participating_agents.append((agent_name, agent))
        
        # Step 2: If no agents want to participate, use all agents
        if not participating_agents:
            print("    → No agents self-selected, using all agents...")
            participating_agents = [(name, agent) for name, agent in self.agents.items()]
        
        # Step 3: Execute task with participating agents
        results = []
        for agent_name, agent in participating_agents:
            print(f"    → Executing with {agent.name}...")
            prompt = f"As a {agent.name}, contribute your expertise to this task: {task}"
            response = await agent.send_message(prompt)
            results.append(f"**{agent.name}:**\n{response}")
        
        # Step 4: Combine results
        combined = "\n\n" + "="*50 + "\n"
        combined += "INTELLIGENT COLLABORATIVE RESPONSE\n"
        combined += "="*50 + "\n\n"
        combined += "\n\n---\n\n".join(results)
        
        return combined
    
    async def execute_collaborative_task(self, task: str) -> str:
        """
        Execute a task that requires collaboration between multiple agents.
        
        Args:
            task: The task to execute
        
        Returns:
            Combined result from all agents
        """
        print(f"\n[*] Executing collaborative task: {task[:50]}...")
        
        results = []
        
        # Have each agent contribute based on their specialty
        for agent_name, agent in self.agents.items():
            print(f"    → Consulting {agent.name}...")
            prompt = f"As a {agent.name}, contribute your expertise to this task: {task}"
            response = await agent.send_message(prompt)
            results.append(f"**{agent.name}:**\n{response}")
        
        # Combine results
        combined = "\n\n" + "="*50 + "\n"
        combined += "COLLABORATIVE RESPONSE\n"
        combined += "="*50 + "\n\n"
        combined += "\n\n---\n\n".join(results)
        
        return combined
    
    def get_node_info(self) -> dict:
        """Get comprehensive node information."""
        return {
            "node": self.node.get_status(),
            "agents": {
                name: {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "is_running": agent.is_running
                }
                for name, agent in self.agents.items()
            },
            "resources": self.node.get_resource_info()
        }
    
    async def shutdown(self):
        """Shutdown the chat system gracefully."""
        print("\n" + "="*60)
        print("   SHUTTING DOWN NODE SYSTEM")
        print("="*60)
        
        # Stop all agents
        print("\n[*] Stopping agents...")
        for name, agent in self.agents.items():
            await agent.stop()
            print(f"    ✓ {agent.name} stopped")
        
        # Stop the node
        print(f"\n[*] Stopping node: {self.node.name}...")
        self.node.stop()
        print("    ✓ Node stopped")
        
        # Stop communication manager
        print("\n[*] Stopping Communication Manager...")
        self.comm.stop()
        print("    ✓ P2P layer stopped")
        
        print("\n[+] Shutdown complete!")
        print("="*60 + "\n")


async def demo_mode(system: NodeChatSystem):
    """
    Run a demonstration of the node system capabilities.
    
    Args:
        system: The NodeChatSystem instance
    """
    print("\n" + "="*60)
    print("   DEMONSTRATION MODE")
    print("="*60)
    
    # Demo 1: Show node status
    print("\n[DEMO 1] Node Status")
    print("-" * 40)
    status = system.node.get_status()
    system._print_status(status)
    await asyncio.sleep(1)
    
    # Demo 2: Show resources
    print("\n[DEMO 2] Node Resources")
    print("-" * 40)
    resources = system.node.get_resource_info()
    for name, value in resources.items():
        print(f"  {name}: {value}")
    await asyncio.sleep(1)
    
    # Demo 3: Intelligent task execution (agents self-select)
    print("\n[DEMO 3] Intelligent Task Execution")
    print("-" * 40)
    result = await system.execute_intelligent_task(
        "Research the latest trends in AI and write a Python script to analyze the data"
    )
    print(result[:500] + "...")
    await asyncio.sleep(1)
    
    # Demo 4: Collaborative task (all agents participate)
    print("\n[DEMO 4] Collaborative Task Execution")
    print("-" * 40)
    result = await system.execute_collaborative_task(
        "Design a simple REST API for a todo application"
    )
    print(result[:500] + "...")
    
    # Demo 5: Peer node connection
    print("\n[DEMO 5] Peer Node Connection")
    print("-" * 40)
    await system.connect_to_peer("peer-node-002")
    await system.connect_to_peer("peer-node-003")
    print(f"  Connected peers: {system.node.connections}")
    
    # Demo 6: Final node status
    print("\n[DEMO 6] Final Node Status")
    print("-" * 40)
    status = system.node.get_status()
    system._print_status(status)
    
    print("\n" + "="*60)
    print("   DEMONSTRATION COMPLETE")
    print("="*60)


async def main():
    """Main entry point for the example."""
    print("\n" + "="*60)
    print("   NODE-BASED MULTI-AGENT DEMO")
    print("="*60)
    
    # Ask for streaming preference
    stream_input = input("\nEnable real-time streaming? [Y/n]: ").lower()
    use_streaming = stream_input != 'n'
    
    # Create the chat system
    system = NodeChatSystem(
        node_id="demo-node-001",
        node_name="Demo Server Node"
    )
    
    try:
        # Initialize the system
        await system.initialize(use_streaming=use_streaming)
        
        # Run demo mode
        await demo_mode(system)
    
    except Exception as e:
        print(f"\n\033[91mFatal Error:\033[0m {e}")
        logging.error(f"Fatal error in main: {e}", exc_info=True)
    
    finally:
        # Always shutdown gracefully
        await system.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[*] Program interrupted. Goodbye!")
