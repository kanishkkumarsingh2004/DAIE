"""
Architecture Container (Block) Module
"""

import logging
import asyncio
from typing import Any, List, Optional, Union
from daie.chat import ChatLoopConfig
from daie.core.tracing import get_logger

logger = get_logger(__name__)

class BlockChatWrapper:
    """Internal wrapper to make any architecture compatible with ChatLoopConfig."""
    def __init__(self, architecture):
        self.architecture = architecture
        # Proxy attributes that ChatLoopConfig might need
        if hasattr(architecture, "config"):
            self.config = architecture.config
        elif hasattr(architecture, "node_name"):
            # For HybridOrchestratorNode
            from dataclasses import dataclass
            @dataclass
            class DummyConfig:
                name: str
            self.config = DummyConfig(name=architecture.node_name)
        else:
            from dataclasses import dataclass
            @dataclass
            class DummyConfig:
                name: str
            self.config = DummyConfig(name="Architecture")

    async def start(self, *args, **kwargs):
        if hasattr(self.architecture, "start"):
            return await self.architecture.start(*args, **kwargs)

    async def stop(self, *args, **kwargs):
        if hasattr(self.architecture, "stop"):
            return await self.architecture.stop(*args, **kwargs)

    async def send_message(self, message: str) -> str:
        func = None
        if hasattr(self.architecture, "send_message"):
            func = self.architecture.send_message
        elif hasattr(self.architecture, "execute_task"):
            func = self.architecture.execute_task
        elif hasattr(self.architecture, "arun"):
            func = self.architecture.arun
        elif callable(self.architecture):
            func = self.architecture
            
        if func:
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(message)
                else:
                    result = func(message)
                    if asyncio.iscoroutine(result):
                        result = await result
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
                
        return "Error: Architecture is not executable"

class Block:
    """
    A container that wraps any AI architecture and provides interaction modes.
    
    This class serves as a "block" in the decentralized AI ecosystem, capable of
    running in either a terminal-based chat loop or as a network-hosted API server.
    It supports graph-like connectivity through 'edges'.
    
    Attributes:
        architecture: The AI logic or agent to wrap.
        host: The host address to bind the server to.
        port: The port to bind the server to.
        chat: If True, runs an interactive terminal chat loop.
        logs: If True, enables detailed logging (forced to False if chat is True).
        edges: A list of endpoints (URLs/ports) this block is connected to.
    """

    def __init__(
        self,
        architecture: Any,
        host: str = "0.0.0.0",
        port: int = 8000,
        chat: bool = False,
        logs: Optional[bool] = None,
        edges: Optional[List[str]] = None,
        stream: bool = True
    ):
        self.architecture = architecture
        self.host = host
        self.port = port
        self.chat = chat
        self.edges = edges or []
        self.stream = stream

        # Mutually exclusive logic: if chat is on, logs is off and vice versa
        if self.chat:
            self.logs = False
        else:
            # If logs not specified, default to True for network mode
            self.logs = True if logs is None else logs

        # Configure logging based on self.logs
        if self.logs:
            logging.basicConfig(level=logging.INFO)
        else:
            # If chat is active, we don't want noisy logs in the same terminal
            logging.basicConfig(level=logging.WARNING)

        # Inject edges/connections into architecture if it's an Agent
        self._setup_connectivity()

        # Set streaming preference
        self._setup_streaming()

        # Inject network and architecture knowledge into system prompt
        self._inject_knowledge()

        logger.info(f"Block initialized (host={self.host}, port={self.port}, chat={self.chat}, edges={len(self.edges)}, stream={self.stream})")

    def _inject_knowledge(self):
        """Inject network and architecture knowledge into the system prompt."""
        from daie.agents import Agent
        from daie.core.hybrid import HybridOrchestratorNode

        knowledge = [
            "\n\n[System Knowledge: Network & Architecture]",
            f"- Deployment Mode: {'Interactive Chat' if self.chat else 'Network Server'}",
            f"- Local Endpoint: http://{self.host}:{self.port}",
            f"- Network Edges (Connections): {', '.join(self.edges) if self.edges else 'No external edges'}"
        ]
        
        if isinstance(self.architecture, HybridOrchestratorNode):
            knowledge.append(f"- Node Type: Hybrid Orchestrator ('{self.architecture.node_name}')")
            sub_agents = [a.config.name for a in self.architecture.sub_agents]
            knowledge.append(f"- Internal Agents Count: {len(sub_agents) + 1} (1 Main + {len(sub_agents)} Sub-agents)")
            knowledge.append(f"- Managed Agents: {', '.join(sub_agents)}")
        elif isinstance(self.architecture, Agent):
            knowledge.append(f"- Node Type: Standalone Agent ('{self.architecture.config.name}')")
            knowledge.append("- Internal Agents Count: 1")
            
            # List known peer IDs if any
            conns = self.architecture.config.network_connections
            if conns:
                knowledge.append(f"- Known Peer Agents (Direct IDs): {', '.join(conns.keys())}")
        
        # Explicit reminder about A2A tools if edges exist
        if self.edges:
            knowledge.append("- Communication: You have A2A tools ('a2a_send_message', 'a2a_delegate_task') to interact with the peers/edges listed above.")
            
        knowledge_str = "\n".join(knowledge)
        
        # Inject into system prompt
        target_agent = None
        if isinstance(self.architecture, Agent):
            target_agent = self.architecture
        elif isinstance(self.architecture, HybridOrchestratorNode):
            target_agent = self.architecture.main_agent
            
        if target_agent and hasattr(target_agent.config, "system_prompt"):
            # Append if not already there
            if knowledge_str not in target_agent.config.system_prompt:
                target_agent.config.system_prompt += knowledge_str
                
        # Auto-equip communication tools
        self._equip_communication_tools()

    def _equip_communication_tools(self):
        """Add A2A communication tools to the agent if they are not already present."""
        if not self.edges:
            return
            
        from daie.agents import Agent
        from daie.core.hybrid import HybridOrchestratorNode
        from daie.tools.a2a import A2ASendMessageTool, A2ADelegateTaskTool

        target_agents = []
        if isinstance(self.architecture, Agent):
            target_agents.append(self.architecture)
        elif isinstance(self.architecture, HybridOrchestratorNode):
            target_agents.append(self.architecture.main_agent)
            
        for agent in target_agents:
            if not agent: continue
            
            # Check if tools already exist
            tool_names = list(agent.tools.keys())
            
            if "a2a_send_message" not in tool_names:
                agent.add_tool(A2ASendMessageTool())
            if "a2a_delegate_task" not in tool_names:
                agent.add_tool(A2ADelegateTaskTool())
                
            # Remind the agent about these tools in system prompt
            tool_reminder = "\n- You have A2A tools ('a2a_send_message', 'a2a_delegate_task') to communicate with the edges listed above."
            if tool_reminder not in agent.config.system_prompt:
                agent.config.system_prompt += tool_reminder

    def _setup_streaming(self):
        """Configure streaming for the wrapped architecture."""
        from daie.agents import Agent
        
        if isinstance(self.architecture, Agent):
            self.architecture.config.stream = self.stream
        elif hasattr(self.architecture, "config") and hasattr(self.architecture.config, "stream"):
            self.architecture.config.stream = self.stream

    def _setup_connectivity(self):
        """Inject network topology information into the wrapped architecture."""
        from daie.agents import Agent
        from daie.core.hybrid import HybridOrchestratorNode

        # If architecture is an Agent, update its config
        if isinstance(self.architecture, Agent):
            if not self.architecture.config.network_connections:
                self.architecture.config.network_connections = {}
            
            for edge in self.edges:
                # Use the edge URL as a temporary key if ID is unknown
                # The communication manager will handle discovery if needed
                self.architecture.config.network_connections[edge] = edge
                
            # Also set the local network URL for this agent
            if not self.architecture.config.network_url:
                self.architecture.config.network_url = f"http://{self.host}:{self.port}"

        # If architecture is a Hybrid node, update its nodes
        elif isinstance(self.architecture, HybridOrchestratorNode):
            for edge in self.edges:
                # Hybrid nodes can connect to other node IDs
                # Here we assume the edge might be a URL or a node_id
                self.architecture.connect_to_node(edge)
            
            # Also set the local network URL for the main agent
            if self.architecture.main_agent and not self.architecture.main_agent.config.network_url:
                self.architecture.main_agent.config.network_url = f"http://{self.host}:{self.port}"

    def run(self):
        """Run the block in the configured mode."""
        if self.chat:
            self._run_chat_mode()
        else:
            self._run_network_mode()

    def _run_chat_mode(self):
        """Run interactive terminal chat loop."""
        from daie.agents import Agent
        
        # Wrap the architecture to ensure compatibility with ChatLoopConfig
        wrapped_arch = BlockChatWrapper(self.architecture)
        
        chat_loop = ChatLoopConfig(agent=wrapped_arch)
        chat_loop.run()

    def _run_network_mode(self):
        """Start FastAPI server to host the architecture."""
        try:
            import uvicorn
            from fastapi import FastAPI, HTTPException
            from pydantic import BaseModel

            app = FastAPI(title=f"DAIE Block Server ({self.port})")

            class TaskRequest(BaseModel):
                task: str
                context: Optional[dict] = None

            @app.get("/")
            async def root():
                return {
                    "status": "online",
                    "port": self.port,
                    "edges": self.edges,
                    "architecture": str(type(self.architecture).__name__)
                }

            @app.post("/execute")
            async def execute(request: TaskRequest):
                try:
                    # Generic execution logic
                    if hasattr(self.architecture, "execute_task"):
                        result = await self.architecture.execute_task(request.task)
                    elif hasattr(self.architecture, "arun"):
                        result = await self.architecture.arun(request.task)
                    elif hasattr(self.architecture, "send_message"):
                        result = await self.architecture.send_message(request.task)
                    elif callable(self.architecture):
                        if asyncio.iscoroutinefunction(self.architecture):
                            result = await self.architecture(request.task)
                        else:
                            result = self.architecture(request.task)
                    else:
                        raise HTTPException(status_code=500, detail="Architecture is not executable via known methods")
                    
                    return {"result": result}
                except Exception as e:
                    logger.error(f"Execution error: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail=str(e))

            # Start the server
            logger.info(f"Starting Block server on http://{self.host}:{self.port}")
            uvicorn.run(app, host=self.host, port=self.port, log_level="info" if self.logs else "warning")
            
        except ImportError:
            logger.error("FastAPI or Uvicorn not installed. Please install with: pip install 'daie[server]'")
            raise ImportError("Server requirements missing: fastapi, uvicorn")
