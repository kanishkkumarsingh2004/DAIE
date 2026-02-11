"""
AI Agent implementation module
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Callable, Union

from daie.agents.config import AgentConfig, AgentRole
from daie.agents.message import AgentMessage
from daie.tools import ToolRegistry
from daie.utils import generate_id

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
    >>> from daie import Agent
    >>> from daie.tools import WebSearchTool
    >>> from daie.agents.config import AgentConfig, AgentRole

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
        tools: Optional[List[Any]] = None,
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
                system_prompt=system_prompt
                or "You are a helpful AI agent that can assist with various tasks.",
            )

        self.id = generate_id()
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
        """Get LLM instance from core, configured with agent's LLM settings"""
        if self._llm is None:
            from daie.core.llm_manager import get_llm_manager, LLMType

            llm_manager = get_llm_manager()

            # Configure LLM with agent's settings
            llm_manager.set_llm(
                llm_type=LLMType(self.config.llm_provider),
                model_name=self.config.llm_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            from daie.core.llm_manager import get_llm

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
                message_type=message.message_type,
            )
            await self.send_message(response)

    async def _handle_task(self, task: Dict[str, Any]):
        """Internal task handler"""
        logger.info(f"Agent {self.name} received task: {task.get('name', 'Unknown')}")

        try:
            if self._task_handler:
                result = await self._task_handler(task)
            else:
                result = await self._default_task_handler(task)

            # If task has result future, set the result
            if "_result_future" in task and not task["_result_future"].done():
                task["_result_future"].set_result(result)

        except Exception as e:
            logger.error(f"Error handling task: {e}")
            # If task has result future, set the exception
            if "_result_future" in task and not task["_result_future"].done():
                task["_result_future"].set_exception(e)

    async def _default_task_handler(self, task: Dict[str, Any]):
        """Default task handler"""
        logger.debug(f"Default task handler called for agent {self.name}")

        # Execute task using available tools
        task_name = task.get("name")
        task_params = task.get("params", {})

        if task_name in self.tools:
            tool = self.tools[task_name]
            
            # Handle different tool types
            if hasattr(tool, "execute"):
                # Tool with execute method
                result = await tool.execute(task_params)
            elif callable(tool):
                # Direct callable (function)
                import inspect
                if inspect.iscoroutinefunction(tool):
                    result = await tool(**task_params)
                else:
                    result = tool(**task_params)
            else:
                logger.error(f"Tool {task_name} is not callable or executable")
                return {"success": False, "error": f"Tool '{task_name}' is not executable"}
            
            logger.info(f"Task {task_name} completed with result: {result}")
            return result
        else:
            logger.warning(f"Agent {self.name} doesn't have tool for task: {task_name}")
            return {"success": False, "error": f"Tool '{task_name}' not found"}

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

    async def send_message(self, message: Union[str, AgentMessage]) -> Union[str, bool]:
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
            metadata={"task": task},
        )

        return await self.send_message(message)

    async def execute_task(self, task_input: Union[str, Dict[str, Any]]) -> Any:
        """
        Execute a task locally - the agent acts like a human using tools

        Args:
            task_input: Task to execute (can be a task description string or dict with name/params)

        Returns:
            Task result
        """
        # Ensure agent is running
        if not self._is_running:
            await self.start()
        
        # If task is a string, analyze it using LLM to determine appropriate tool and parameters
        if isinstance(task_input, str):
            task_description = task_input
            logger.info(f"Agent analyzing task: {task_description}")

            # Get available tools information
            available_tools = self.list_tools()

            # If no tools available, respond conversationally
            if not available_tools:
                logger.info("No tools available - responding conversationally")
                return await self.send_message(task_description)

            # Build a clear tool description for the LLM
            tools_description = self._build_tools_description(available_tools)

            # Create a structured prompt for the LLM
            prompt = self._create_tool_selection_prompt(task_description, tools_description)

            try:
                llm = self.llm
                response = llm.invoke(prompt)
                logger.debug(f"LLM response: {response[:200]}...")

                # Parse the LLM response
                tool_call = self._parse_tool_response(response)

                # If no tool needed, respond conversationally
                if tool_call is None or tool_call.get("tool_name") == "none":
                    logger.info("No tool needed - responding conversationally")
                    return await self.send_message(task_description)

                # Validate and execute the tool
                tool_name = tool_call.get("tool_name")
                params = tool_call.get("params", {})

                # Check if tool exists
                if tool_name not in [t.name for t in available_tools]:
                    logger.warning(f"Tool '{tool_name}' not found - responding conversationally")
                    return await self.send_message(task_description)

                # Validate and fix parameters
                params = self._validate_and_fix_params(tool_name, params, task_description)
                if params is None:
                    # Parameters couldn't be fixed, respond conversationally
                    return await self.send_message(
                        f"I understand you want to use {tool_name}, but I need more information. {task_description}"
                    )

                task = {"name": tool_name, "params": params}
                logger.info(f"Executing tool '{tool_name}' with params: {params}")

            except Exception as e:
                logger.error(f"Error analyzing task with LLM: {e}", exc_info=True)
                logger.info("Falling back to conversational response")
                return await self.send_message(task_description)
        else:
            task = task_input

        # Execute the task
        loop = asyncio.get_event_loop()
        result_future = loop.create_future()

        task_with_result = task.copy()
        task_with_result["_result_future"] = result_future

        await self._task_queue.put(task_with_result)

        try:
            result = await asyncio.wait_for(result_future, timeout=60.0)
            return result
        except asyncio.TimeoutError:
            logger.error(f"Task execution timed out: {task.get('name')}")
            raise

    def _build_tools_description(self, tools: List) -> str:
        """Build a clear description of available tools"""
        descriptions = []
        for tool in tools:
            tool_desc = f"Tool: {tool.name}\nDescription: {tool.description}"
            
            # Add parameter information
            if hasattr(tool, "metadata") and hasattr(tool.metadata, "parameters"):
                params_desc = []
                for param in tool.metadata.parameters:
                    param_info = f"  - {param.name} ({param.type})"
                    if param.required:
                        param_info += " [REQUIRED]"
                    if param.choices:
                        param_info += f" [choices: {', '.join(map(str, param.choices))}]"
                    if param.description:
                        param_info += f": {param.description}"
                    params_desc.append(param_info)
                
                if params_desc:
                    tool_desc += "\nParameters:\n" + "\n".join(params_desc)
            
            descriptions.append(tool_desc)
        
        return "\n\n".join(descriptions)

    def _create_tool_selection_prompt(self, task: str, tools_description: str) -> str:
        """Create a structured prompt for tool selection"""
        return f"""{self.config.system_prompt}

You are an AI agent with access to tools. Your job is to analyze the user's request and decide:
1. If you need to use a tool to complete the task
2. If so, which tool and what parameters

Available Tools:
{tools_description}

User Request: "{task}"

Instructions:
- If the request is conversational (greeting, question, chat), respond with: {{"tool_name": "none", "response": "your conversational response"}}
- If you need to use a tool, respond with: {{"tool_name": "tool_name", "params": {{"param1": "value1", "param2": "value2"}}}}
- Be precise with parameter names and values
- Extract specific values from the user's request (file names, URLs, content, etc.)
- If a required parameter is missing, respond with: {{"tool_name": "none", "response": "ask for the missing information"}}

Respond ONLY with a valid JSON object, nothing else."""

    def _parse_tool_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response to extract tool call information"""
        import json
        import re

        # Try to extract JSON from the response
        tool_call = None

        # Method 1: Look for JSON in code blocks
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    tool_call = json.loads(match)
                    if isinstance(tool_call, dict):
                        break
                except json.JSONDecodeError:
                    continue

        # Method 2: Look for JSON object in the text
        if tool_call is None:
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            for match in matches:
                try:
                    tool_call = json.loads(match)
                    if isinstance(tool_call, dict) and "tool_name" in tool_call:
                        break
                except json.JSONDecodeError:
                    continue

        # Method 3: Try parsing the entire response
        if tool_call is None:
            try:
                tool_call = json.loads(response.strip())
            except json.JSONDecodeError:
                pass

        return tool_call

    def _validate_and_fix_params(
        self, tool_name: str, params: Dict[str, Any], task_description: str
    ) -> Optional[Dict[str, Any]]:
        """Validate and fix tool parameters"""
        
        # Get the tool
        tool = self.get_tool(tool_name)
        if not tool:
            return None

        # Tool-specific parameter validation and fixing
        if tool_name == "file_manager":
            return self._fix_file_manager_params(params, task_description)
        elif tool_name == "selenium_chrome":
            return self._fix_selenium_params(params, task_description)
        elif tool_name == "api_call" or "http" in tool_name.lower():
            return self._fix_api_params(params, task_description)
        
        # For other tools, just return the params as-is
        return params

    def _fix_file_manager_params(
        self, params: Dict[str, Any], task_description: str
    ) -> Optional[Dict[str, Any]]:
        """Fix file manager tool parameters"""
        
        # Ensure action is specified
        if "action" not in params:
            logger.warning("File manager action not specified")
            return None

        action = params["action"]

        # Actions that require a path
        path_required_actions = [
            "read_file", "write_file", "append_file", "delete_file",
            "create_file", "create_directory", "delete_directory",
            "file_exists", "directory_exists", "get_file_info", "get_directory_info"
        ]

        if action in path_required_actions:
            if "path" not in params or not params["path"]:
                logger.warning(f"File manager action '{action}' requires a path")
                return None

        # Default path for list operations
        if action in ["list_contents", "list"]:
            if "path" not in params or not params["path"]:
                params["path"] = "."

        # For write/create operations, ensure content is provided
        if action in ["write_file", "create_file", "append_file"]:
            if "content" not in params:
                logger.warning(f"File manager action '{action}' requires content")
                return None

        return params

    def _fix_selenium_params(
        self, params: Dict[str, Any], task_description: str
    ) -> Optional[Dict[str, Any]]:
        """Fix selenium tool parameters"""
        
        # Fix parameter name mismatch
        if "actions" in params and "action" not in params:
            params["action"] = params.pop("actions")

        # Default action
        if "action" not in params:
            params["action"] = "open_url"

        # Ensure URL is provided for open_url action
        if params.get("action") == "open_url" and "url" not in params:
            logger.warning("Selenium open_url action requires a URL")
            return None

        return params

    def _fix_api_params(
        self, params: Dict[str, Any], task_description: str
    ) -> Optional[Dict[str, Any]]:
        """Fix API tool parameters"""
        
        # Ensure URL is provided
        if "url" not in params:
            logger.warning("API tool requires a URL")
            return None

        # Default method
        if "method" not in params:
            params["method"] = "GET"

        return params

    async def start(
        self, communication_manager=None, memory_manager=None, tool_registry=None
    ) -> None:
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
