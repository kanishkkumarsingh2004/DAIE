"""
AI Agent implementation module
"""

import asyncio
import logging
import uuid
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from decentralized_ai.agents.config import AgentConfig, AgentRole
from decentralized_ai.agents.message import AgentMessage
from decentralized_ai.tools import Tool, ToolRegistry
from decentralized_ai.communication import CommunicationManager
from decentralized_ai.memory import MemoryManager
from decentralized_ai.utils import generate_id

logger = logging.getLogger(__name__)


class Agent:
    """
    AI Agent class for the Decentralized AI Ecosystem
    
    This class represents an individual AI agent that can:
    - Communicate with other agents
    - Execute tasks with tools
    - Maintain memory
    - Learn and adapt
    - Handle events
    
    Example:
    >>> from decentralized_ai import Agent
    >>> from decentralized_ai.tools import WebSearchTool
    >>> from decentralized_ai.agents.config import AgentConfig, AgentRole
    
    >>> # Create agent configuration
    >>> config = AgentConfig(
    ...     name="MyResearchAgent",
    ...     role=AgentRole.SPECIALIZED,
    ...     goal="Research information on given topics",
    ...     backstory="Created to assist with research and information gathering",
    ...     system_prompt="You are a research assistant that helps users find and analyze information.",
    ...     capabilities=["web_search"]
    ... )
    
    >>> # Create and configure agent
    >>> agent = Agent(config=config)
    >>> agent.add_tool(WebSearchTool())
    
    >>> # Start the agent
    >>> agent.start()
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        role: Optional[AgentRole] = None,
        goal: Optional[str] = None,
        backstory: Optional[str] = None,
        system_prompt: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[Any]] = None
    ):
        """
        Initialize an AI agent
        
        Args:
            name: Agent display name
            role: Agent role type
            goal: Agent's main purpose or goal
            backstory: Agent's backstory or origin story
            system_prompt: System prompt for the agent's behavior
            config: Agent configuration (if None, default is used)
            tools: List of tools to initialize with
        """
        if config is not None:
            self.config = config
        else:
            self.config = AgentConfig(
                name=name or "DefaultAgent",
                role=role or AgentRole.GENERAL_PURPOSE,
                goal=goal or "Perform general tasks",
                backstory=backstory or "Default AI agent",
                system_prompt=system_prompt or "You are a helpful AI agent that can assist with various tasks.",
            )
            
        self.id = str(uuid.uuid4())
        self.tools: Dict[str, Any] = {}
        self.tool_registry = ToolRegistry()
        self._is_running = False
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._message_handler: Optional[Callable] = None
        self._task_handler: Optional[Callable] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Initialize LLM from core
        self._llm = None
        
        # Add initial tools
        if tools:
            for tool in tools:
                self.add_tool(tool)
                
        logger.info(f"Agent {self.config.name} (ID: {self.id}) created")
        
    @property
    def name(self) -> str:
        """Get agent display name"""
        return self.config.name
        
    @property
    def role(self) -> AgentRole:
        """Get agent role"""
        return self.config.role
        
    @property
    def goal(self) -> str:
        """Get agent goal"""
        return self.config.goal
        
    @property
    def backstory(self) -> str:
        """Get agent backstory"""
        return self.config.backstory
        
    @property
    def system_prompt(self) -> str:
        """Get agent system prompt"""
        return self.config.system_prompt
        
    @property
    def is_running(self) -> bool:
        """Check if agent is currently running"""
        return self._is_running
        
    @property
    def llm(self):
        """Get LLM instance from core"""
        if self._llm is None:
            from decentralized_ai.core.llm_manager import get_llm
            self._llm = get_llm()
        return self._llm
        
    def add_tool(self, tool: Any) -> "Agent":
        """
        Add a tool to the agent's toolbox
        
        Args:
            tool: Tool instance to add
            
        Returns:
            self for method chaining
        """
        if hasattr(tool, "name"):
            self.tools[tool.name] = tool
            logger.info(f"Tool {tool.name} added to agent {self.name}")
        else:
            logger.warning("Tool must have a 'name' attribute")
            
        return self
        
    def remove_tool(self, tool_name: str) -> "Agent":
        """
        Remove a tool from the agent's toolbox
        
        Args:
            tool_name: Name of tool to remove
            
        Returns:
            self for method chaining
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Tool {tool_name} removed from agent {self.name}")
            
        return self
        
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """
        Get a tool by name
        
        Args:
            tool_name: Name of tool to get
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(tool_name)
        
    def list_tools(self) -> List[Any]:
        """
        List all tools available to the agent
        
        Returns:
            List of tool instances
        """
        return list(self.tools.values())
        
    def set_message_handler(self, handler: Callable[[AgentMessage], None]) -> "Agent":
        """
        Set a custom message handler
        
        Args:
            handler: Function to handle incoming messages
            
        Returns:
            self for method chaining
        """
        self._message_handler = handler
        logger.debug(f"Message handler set for agent {self.name}")
        
        return self
        
    def set_task_handler(self, handler: Callable[[Dict[str, Any]], Any]) -> "Agent":
        """
        Set a custom task handler
        
        Args:
            handler: Function to handle incoming tasks
            
        Returns:
            self for method chaining
        """
        self._task_handler = handler
        logger.debug(f"Task handler set for agent {self.name}")
        
        return self
        
    async def _handle_message(self, message: AgentMessage):
        """Internal message handler"""
        logger.info(f"Agent {self.name} received message from {message.sender_id}")
        
        try:
            if self._message_handler:
                await self._message_handler(message)
            else:
                await self._default_message_handler(message)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            
    async def _default_message_handler(self, message: AgentMessage):
        """Default message handler"""
        logger.debug(f"Default message handler called for agent {self.name}")
        
        # Simple default behavior: echo messages
        if message.content.strip():
            response = AgentMessage(
                sender_id=self.id,
                receiver_id=message.sender_id,
                content=f"I received your message: {message.content}",
                message_type=message.message_type
            )
            await self.send_message(response)
            
    async def _handle_task(self, task: Dict[str, Any]):
        """Internal task handler"""
        logger.info(f"Agent {self.name} received task: {task.get('name', 'Unknown')}")
        
        try:
            if self._task_handler:
                await self._task_handler(task)
            else:
                await self._default_task_handler(task)
        except Exception as e:
            logger.error(f"Error handling task: {e}")
            
    async def _default_task_handler(self, task: Dict[str, Any]):
        """Default task handler"""
        logger.debug(f"Default task handler called for agent {self.name}")
        
        # Execute task using available tools
        task_name = task.get("name")
        task_params = task.get("params", {})
        
        if task_name in self.tools:
            tool = self.tools[task_name]
            result = await tool.execute(task_params)
            logger.info(f"Task {task_name} completed with result: {result}")
        else:
            logger.warning(f"Agent {self.name} doesn't have tool for task: {task_name}")
            
    async def _run_task_queue(self):
        """Run task processing loop"""
        while self._is_running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self._handle_task(task)
                self._task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task queue: {e}")
                
    async def send_message(self, message: str or AgentMessage) -> str or bool:
        """
        Send a message - if string is provided, use LLM to generate response
        
        Args:
            message: Message to send (string or AgentMessage)
            
        Returns:
            If string message, returns LLM response. If AgentMessage, returns boolean success
        """
        if isinstance(message, str):
            # If string is provided, use LLM to generate response
            prompt = f"{self.config.system_prompt}\n\nUser: {message}\n\nAssistant:"
            
            try:
                llm = self.llm
                response = llm.invoke(prompt)
                return response.strip()
            except Exception as e:
                logger.error(f"LLM invocation error: {e}")
                return f"Error: Failed to get response from LLM - {e}"
                
        # If AgentMessage, proceed with normal sending
        logger.info(f"Agent {self.name} sending message to {message.receiver_id}")
        
        try:
            if not hasattr(self, "communication_manager"):
                logger.error("Communication manager not initialized")
                return False
                
            await self.communication_manager.send_message(message)
            logger.debug(f"Message sent from {self.name} to {message.receiver_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    async def send_task(self, task: Dict[str, Any], receiver_id: str) -> bool:
        """
        Send a task to another agent
        
        Args:
            task: Task to send
            receiver_id: Recipient agent ID
            
        Returns:
            True if task sent successfully, False otherwise
        """
        message = AgentMessage(
            sender_id=self.id,
            receiver_id=receiver_id,
            content=str(task),
            message_type="task",
            metadata={"task": task}
        )
        
        return await self.send_message(message)
        
    async def execute_task(self, task: Dict[str, Any]) -> Any:
        """
        Execute a task locally
        
        Args:
            task: Task to execute
            
        Returns:
            Task result
        """
        await self._task_queue.put(task)
        return True
        
    async def start(self, communication_manager=None, memory_manager=None, tool_registry=None) -> None:
        """
        Start the agent
        
        Args:
            communication_manager: Communication manager instance (optional)
            memory_manager: Memory manager instance (optional)
            tool_registry: Tool registry instance (optional)
        """
        if self._is_running:
            logger.warning(f"Agent {self.name} is already running")
            return
            
        logger.info(f"Starting agent: {self.name} (ID: {self.id})")
        
        try:
            # Initialize managers - use dummy managers if not provided
            if communication_manager:
                self.communication_manager = communication_manager
                self.communication_manager.register_agent(self)
                
            if memory_manager:
                self.memory_manager = memory_manager
                self.memory_manager.initialize_agent_memory(self.id)
                
            if tool_registry:
                self.tool_registry = tool_registry
                
            # Start task processing
            self._is_running = True
            self._loop = asyncio.get_event_loop()
            self._loop.create_task(self._run_task_queue())
            
            logger.info(f"Agent {self.name} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start agent {self.name}: {e}")
            self._is_running = False
            raise
            
    async def stop(self) -> None:
        """Stop the agent"""
        if not self._is_running:
            logger.warning(f"Agent {self.name} is already stopped")
            return
            
        logger.info(f"Stopping agent: {self.name}")
        
        try:
            self._is_running = False
            
            # Deregister from communication manager
            if hasattr(self, "communication_manager"):
                self.communication_manager.deregister_agent(self.id)
                
            logger.info(f"Agent {self.name} stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping agent {self.name}: {e}")
