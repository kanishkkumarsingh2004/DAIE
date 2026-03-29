# 🔴 Advanced - Node-Based Multi-Agent System
# Difficulty: Advanced
# This example demonstrates the Node class with real agents.

"""
Example 07: Node-Based Multi-Agent System

Demonstrates:
  - Creating and managing a Node
  - Hosting multiple agents on a single node
  - Resource management on nodes
  - Agent coordination within a node
"""

import asyncio
import logging

from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole, AgentRouter
from daie.communication import CommunicationManager
from daie.core.node import Node

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='node_agents.log',
    filemode='w'
)


class NodeChatSystem:
    """A simple chat system built on the Node architecture."""
    
    def __init__(self, node_id: str, node_name: str):
        """Initialize the Node-based chat system."""
        self.node = Node(node_id=node_id, name=node_name)
        self.comm = CommunicationManager()
        self.agents = {}
        self.router = None
        self._initialized = False
    
    async def initialize(self, use_streaming: bool = True):
        """Initialize the chat system with agents and resources."""
        if self._initialized:
            return
        
        # Configure LLM
        set_llm(ollama_llm="llama3.2:1b", stream=use_streaming)
        
        # Start communication manager
        await self.comm.start()
        
        # Start the node
        self.node.start()
        
        # Set node resources
        self.node.set_resource("gpu_count", 2)
        self.node.set_resource("memory_gb", 16)
        self.node.set_resource("model_cache", {"llama3.2": True})
        self.node.set_resource("max_concurrent_tasks", 5)
        
        # Create and register agents
        await self._create_agents()
        
        self._initialized = True
    
    async def _create_agents(self):
        """Create and register specialized agents on the node."""
        
        # Agent 1: General Assistant
        assistant_config = AgentConfig(
            name="Assistant",
            role=AgentRole.GENERAL_PURPOSE,
            system_prompt="You are a helpful general-purpose assistant.",
            personality="friendly and thorough"
        )
        assistant = Agent(config=assistant_config)
        await assistant.start(communication_manager=self.comm)
        self.agents["assistant"] = assistant
        self.node.add_agent(assistant.id)
        
        # Agent 2: Coding Specialist
        coder_config = AgentConfig(
            name="Coder",
            role=AgentRole.SPECIALIZED,
            system_prompt="You are an expert programming assistant.",
            personality="precise and logical"
        )
        coder = Agent(config=coder_config)
        await coder.start(communication_manager=self.comm)
        self.agents["coder"] = coder
        self.node.add_agent(coder.id)
        
        # Agent 3: Research Specialist
        researcher_config = AgentConfig(
            name="Researcher",
            role=AgentRole.SPECIALIZED,
            system_prompt="You are a research specialist.",
            personality="analytical and thorough"
        )
        researcher = Agent(config=researcher_config)
        await researcher.start(communication_manager=self.comm)
        self.agents["researcher"] = researcher
        self.node.add_agent(researcher.id)
        
        # Initialize the intelligent router
        agents_list = [assistant, coder, researcher]
        self.router = AgentRouter.from_agents(agents_list)
    
    async def route_message(self, message: str, agent_type: str = "auto") -> str:
        """Route a message to the appropriate agent."""
        try:
            selected_agent_type = await self.router.route(message, agent_type)
            agent = self.agents.get(selected_agent_type)
            
            if not agent:
                return f"Error: Agent type '{selected_agent_type}' not found"
            
            response = await agent.send_message(message)
            return response
            
        except Exception as e:
            return f"Error routing message: {e}"
    
    async def execute_collaborative_task(self, task: str) -> str:
        """Execute a task that requires collaboration between multiple agents."""
        results = []
        for agent_name, agent in self.agents.items():
            prompt = f"As a {agent.name}, contribute your expertise to this task: {task}"
            response = await agent.send_message(prompt)
            results.append(f"**{agent.name}:**\n{response}")
        
        combined = "\n\n" + "="*50 + "\n"
        combined += "COLLABORATIVE RESPONSE\n"
        combined += "="*50 + "\n\n"
        combined += "\n\n---\n\n".join(results)
        
        return combined
    
    async def shutdown(self):
        """Shutdown the chat system gracefully."""
        # Stop all agents
        for name, agent in self.agents.items():
            await agent.stop()
        
        # Stop the node
        self.node.stop()
        
        # Stop communication manager
        self.comm.stop()


async def interactive_chat_loop(system: NodeChatSystem):
    """Run an interactive chat loop with the node-based system."""
    print("\n" + "="*60)
    print("   INTERACTIVE CHAT MODE")
    print("="*60)
    print("\nType your message to chat with agents (or 'exit' to quit)")
    print("\n" + "="*60 + "\n")
    
    while True:
        try:
            # Get user input
            user_input = input("\033[94mYou:\033[0m ").strip()
            
            if not user_input:
                continue
            
            # Handle exit command
            if user_input.lower() in ['exit', 'quit']:
                print("\n[*] Ending chat session...")
                break
            
            # Route message to appropriate agent
            print("\n\033[92mAgent Response:\033[0m")
            response = await system.route_message(user_input)
            
        except KeyboardInterrupt:
            print("\n\n[*] Chat interrupted. Type 'exit' to quit.")
            continue
        except EOFError:
            print("\n\n[*] EOF received. Exiting...")
            break
        except Exception as e:
            print(f"\n\033[91mError:\033[0m {e}")
            logging.error(f"Error in chat loop: {e}", exc_info=True)


async def main():
    """Main entry point for the example."""
    # Create the chat system
    system = NodeChatSystem(
        node_id="production-node-001",
        node_name="Production Server Node"
    )
    
    try:
        # Initialize the system
        await system.initialize(use_streaming=True)
        
        # Run interactive chat loop
        await interactive_chat_loop(system)
        
    except Exception as e:
        print(f"\n[!] Fatal Error: {e}")
        logging.error(f"Fatal error in main: {e}", exc_info=True)
    
    finally:
        # Always shutdown gracefully
        await system.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[*] Program interrupted. Goodbye!")
