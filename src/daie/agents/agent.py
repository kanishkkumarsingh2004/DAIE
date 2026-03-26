"""
AI Agent implementation module
"""

import asyncio
import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Union

from daie.agents.config import AgentConfig, AgentRole
from daie.agents.message import AgentMessage
from daie.tools import ToolRegistry
from daie.utils import generate_id
from daie.rag import RAGEngine

logger = logging.getLogger(__name__)

try:
    from daie.communication import CommunicationManager
    from daie.memory import MemoryManager
except ImportError:
    CommunicationManager = None  # type: ignore
    MemoryManager = None  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# Prompt templates
# ─────────────────────────────────────────────────────────────────────────────

_TOOL_SYSTEM = """\
You are {name}. {system_prompt}

Tools available:
{tools_block}

IMPORTANT: Respond with ONLY a single JSON object, no other text.
To call a tool:
{{"thought":"reason","tool":"tool_name","params":{{...}}}}
To give a final answer:
{{"thought":"reason","answer":"your response"}}
"""

_TOOL_TURN = """\
History: {history}
Task: {user_input}
JSON:"""

_TOOL_RESULT_TURN = 'Tool "{tool_name}" result: {result}\nNext JSON:'

_NO_TOOL_SYSTEM = "You are {name}. {system_prompt}"


class Agent:
    """
    AI Agent with a proper ReAct-style tool-use loop.

    The LLM is the brain: it reasons, picks tools, observes results, and
    iterates until it can give a final answer.  Both pre-built tools
    (SeleniumChromeTool, APICallTool, FileManagerTool, …) and user-defined
    @tool-decorated functions work identically.

    Example
    -------
    >>> from daie import Agent, AgentConfig, set_llm
    >>> from daie.agents import AgentRole
    >>> from daie.tools import FileManagerTool, APICallTool
    >>> from daie.tools import tool
    >>>
    >>> @tool(name="greet", description="Greet a person by name")
    >>> async def greet(name: str) -> str:
    ...     return f"Hello, {name}!"
    >>>
    >>> set_llm(ollama_llm="llama3.2:latest", stream=True)
    >>> agent = Agent(config=AgentConfig(name="Bob", role=AgentRole.GENERAL_PURPOSE))
    >>> agent.add_tool(greet)
    >>> agent.add_tool(FileManagerTool())
    >>> agent.add_tool(APICallTool())
    >>> await agent.start()
    >>> result = await agent.execute_task("List the files in the current directory")
    """

    # Maximum tool-call iterations per execute_task call
    MAX_TOOL_ITERATIONS = 8

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
        self._task_queue: Optional[asyncio.Queue] = None
        self._message_handler: Optional[Callable] = None
        self._task_handler: Optional[Callable] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._llm = None
        self.rag_engine: Optional[RAGEngine] = None
        self._pending_responses: Dict[str, asyncio.Future] = {}

        if tools:
            for t in tools:
                self.add_tool(t)

        logger.info(f"Agent {self.config.name} (ID: {self.id}) created")

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> AgentRole:
        return self.config.role

    @property
    def goal(self) -> str:
        return self.config.goal

    @property
    def backstory(self) -> str:
        return self.config.backstory

    @property
    def system_prompt(self) -> str:
        return self.config.system_prompt

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def llm(self):
        """Lazy-load the LLM, respecting any global set_llm() config."""
        if self._llm is None:
            from daie.core.llm_manager import LLMType, get_llm, get_llm_manager

            mgr = get_llm_manager()
            # Only override if the agent has non-default LLM settings
            if self.config.llm_model != "llama3":
                mgr.set_llm(
                    llm_type=LLMType(self.config.llm_provider),
                    model_name=self.config.llm_model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
            self._llm = get_llm()
        return self._llm

    # ── tool management ───────────────────────────────────────────────────────

    def add_tool(self, tool: Any) -> "Agent":
        if hasattr(tool, "name"):
            self.tools[tool.name] = tool
            logger.info(f"Tool '{tool.name}' added to agent '{self.name}'")
        else:
            logger.warning("Tool must have a 'name' attribute")
        return self

    def remove_tool(self, tool_name: str) -> "Agent":
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Tool '{tool_name}' removed from agent '{self.name}'")
        return self

    def get_tool(self, tool_name: str) -> Optional[Any]:
        return self.tools.get(tool_name)

    def list_tools(self) -> List[Any]:
        return list(self.tools.values())

    # ── prompt helpers ────────────────────────────────────────────────────────

    def _tools_block(self) -> str:
        """Render all tools as a compact schema block for the system prompt.

        Only required parameters are shown to keep the prompt small enough
        for lightweight models (e.g. gemma3:1b).
        """
        if not self.tools:
            return "(no tools available)"
        lines = []
        for t in self.tools.values():
            # Truncate long descriptions to keep prompt size manageable
            desc = t.description[:120] if len(t.description) > 120 else t.description
            lines.append(f"- {t.name}: {desc}")
            if hasattr(t, "metadata") and t.metadata.parameters:
                req_params = [p for p in t.metadata.parameters if p.required]
                opt_params = [p for p in t.metadata.parameters if not p.required]
                if req_params:
                    req_str = ", ".join(
                        f"{p.name}({p.type})" + (f" choices={p.choices}" if p.choices else "")
                        for p in req_params
                    )
                    lines.append(f"  required: {req_str}")
                if opt_params:
                    opt_str = ", ".join(f"{p.name}({p.type})" for p in opt_params[:5])
                    if len(opt_params) > 5:
                        opt_str += f" +{len(opt_params)-5} more"
                    lines.append(f"  optional: {opt_str}")
        return "\n".join(lines)

    def _build_system_prompt(self) -> str:
        prompt_extras = []
        if getattr(self.config, "gender", None):
            prompt_extras.append(f"Gender: {self.config.gender}")
        if getattr(self.config, "personality", None):
            prompt_extras.append(f"Personality: {self.config.personality}")
        if getattr(self.config, "behavior", None):
            prompt_extras.append(f"Behavior: {self.config.behavior}")
            
        extra_str = "\\n".join(prompt_extras)
        base_sys_prompt = f"{self.config.system_prompt}\\n\\nAgent Persona Traits:\\n{extra_str}" if extra_str else self.config.system_prompt

        if self.tools:
            return _TOOL_SYSTEM.format(
                name=self.name,
                system_prompt=base_sys_prompt,
                tools_block=self._tools_block(),
            )
        return _NO_TOOL_SYSTEM.format(
            name=self.name,
            system_prompt=base_sys_prompt,
        )

    # ── JSON parsing ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract the first valid JSON object from LLM output.
        Handles code fences, leading prose, and partial wrapping.
        """
        # Strip code fences
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

        def try_parse(s):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return None

        # Try the whole string first
        res = try_parse(text)
        if res: return res

        # Iteratively try to find and parse the first valid JSON object
        search_from = 0
        while True:
            start = text.find("{", search_from)
            if start == -1:
                break
            
            depth = 0
            for i in range(start, len(text)):
                ch = text[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        res = try_parse(candidate)
                        if res:
                            return res
                        break # Failed this one, look for next {
            search_from = start + 1
            
        return None

    # ── tool execution ────────────────────────────────────────────────────────

    async def _run_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute a tool and return a string representation of the result."""
        tool = self.get_tool(tool_name)
        if tool is None:
            return f"Error: tool '{tool_name}' not found. Available: {list(self.tools.keys())}"

        try:
            if hasattr(tool, "execute"):
                result = await tool.execute(params)
            elif callable(tool):
                import inspect
                result = await tool(**params) if inspect.iscoroutinefunction(tool) else tool(**params)
            else:
                return f"Error: tool '{tool_name}' is not executable"

            # Compact JSON for the LLM context
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False, default=str)
            return str(result)

        except Exception as exc:
            logger.error(f"Tool '{tool_name}' raised: {exc}", exc_info=True)
            return f"Error executing '{tool_name}': {exc}"

    # ── RAG helpers ──────────────────────────────────────────────────────────

    def _get_rag_context(self, query: str) -> str:
        """Retrieve context from RAG engine if enabled."""
        if not self.config.enable_rag or self.rag_engine is None:
            return ""
        
        return self.rag_engine.build_context(query)

    def _augment_prompt_with_rag(self, prompt: str, query: str) -> str:
        """Augment the prompt with retrieved RAG context."""
        context = self._get_rag_context(query)
        if not context:
            return prompt

        rag_block = f"\n\nAdditional Information:\n{context}\n"
        
        # If strict context is enabled, add enforcing instructions
        if getattr(self.config, "rag_strict_context", False):
            rag_block += (
                "\nInstruction: Only use the information provided above to answer. "
                "If the information is not there, say you don't know."
            )

        # Prepend context to the user query/task part of the prompt
        if "User: " in prompt:
            return prompt.replace("User: ", f"{rag_block}\nUser: ")
        elif "Task: " in prompt:
            return prompt.replace("Task: ", f"{rag_block}\nTask: ")
        
        return f"{rag_block}\n{prompt}"

    # ── ReAct loop ────────────────────────────────────────────────────────────

    async def execute_task(self, task_input: Union[str, Dict[str, Any]]) -> Any:
        """
        Execute a task using a ReAct-style loop.

        The LLM reasons → picks a tool → sees the result → reasons again,
        until it produces a final answer or the iteration limit is reached.

        Args:
            task_input: Natural-language task string, or a dict with
                        {"name": tool_name, "params": {...}} for direct execution.

        Returns:
            Final answer string, or raw tool result for direct dict calls.
        """
        if not self._is_running:
            await self.start()

        # ── direct tool call (dict input) ──────────────────────────────────
        if isinstance(task_input, dict):
            return await self._direct_tool_call(task_input)

        # ── natural-language task ──────────────────────────────────────────
        user_input = task_input
        
        # RAG context retrieval for reasoning loop
        if self.config.enable_rag and self.rag_engine:
            context = self._get_rag_context(user_input)
            if context:
                user_input = f"Context from documents:\n{context}\n\nTask: {user_input}"
                if getattr(self.config, "rag_strict_context", False):
                    user_input += "\n(Answer ONLY using the provided documents)"

        system_prompt = self._build_system_prompt()
        history: List[str] = []

        # Tool-use loop (stream=False for reasoning; streaming is for chat)
        for iteration in range(self.MAX_TOOL_ITERATIONS):
            if iteration == 0:
                full_prompt = (
                    system_prompt
                    + "\n\n"
                    + _TOOL_TURN.format(history="(none)", user_input=user_input)
                )
            else:
                full_prompt = (
                    system_prompt
                    + "\n\n"
                    + _TOOL_TURN.format(
                        history="\n".join(history), user_input=user_input
                    )
                )

            # Invoke LLM. If streaming is enabled, reasoning is shown too.
            from daie.core.llm_manager import get_llm_config
            raw = self.llm.invoke(
                full_prompt, 
                stream=self.config.stream or get_llm_config().stream, 
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            ).strip()
            logger.debug(f"[iter {iteration}] LLM raw: {raw[:300]}")

            parsed = self._parse_llm_json(raw)

            # ── final answer ───────────────────────────────────────────────
            if parsed is None:
                # LLM returned plain text — treat as final answer
                return raw

            if "answer" in parsed:
                return parsed["answer"]

            # ── tool call ─────────────────────────────────────────────────
            tool_name = parsed.get("tool")
            params = parsed.get("params", {})
            thought = parsed.get("thought", "")

            if not tool_name:
                # LLM gave JSON but no tool/answer key — treat as answer
                return raw

            logger.info(f"Agent '{self.name}' → tool '{tool_name}' | thought: {thought}")
            history.append(f"Assistant thought: {thought}")
            history.append(f"Called tool: {tool_name}({json.dumps(params)})")

            tool_result = await self._run_tool(tool_name, params)
            logger.info(f"Tool '{tool_name}' result: {tool_result[:200]}")
            history.append(
                _TOOL_RESULT_TURN.format(tool_name=tool_name, result=tool_result)
            )

        # Iteration limit reached — ask LLM for a final answer with what we have
        summary_prompt = (
            system_prompt
            + "\n\n"
            + _TOOL_TURN.format(history="\n".join(history), user_input=user_input)
            + "\nYou have reached the tool call limit. Summarise what you found and give a final answer."
        )
        raw = self.llm.invoke(
            summary_prompt, 
            stream=False,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        ).strip()
        parsed = self._parse_llm_json(raw)
        return (parsed or {}).get("answer", raw)

    async def _direct_tool_call(self, task: Dict[str, Any]) -> Any:
        """Execute a tool directly from a dict spec, via the task queue."""
        if self._task_queue is None:
            self._task_queue = asyncio.Queue()

        loop = asyncio.get_running_loop()
        result_future = loop.create_future()
        task_copy = task.copy()
        task_copy["_result_future"] = result_future
        await self._task_queue.put(task_copy)

        try:
            return await asyncio.wait_for(result_future, timeout=self.config.task_timeout)
        except asyncio.TimeoutError:
            logger.error(f"Direct tool call timed out: {task.get('name')}")
            raise

    # ── chat / send_message ───────────────────────────────────────────────────

    async def send_message(self, message: Union[str, AgentMessage]) -> Union[str, bool]:
        """
        Send a conversational message to the LLM (no tool loop).

        For tool-using tasks, prefer execute_task().
        Streaming is controlled by the global set_llm(stream=True) config.
        """
        if isinstance(message, str):
            from daie.core.llm_manager import get_llm_config
            import sys

            prompt_extras = []
            if getattr(self.config, "gender", None):
                prompt_extras.append(f"Gender: {self.config.gender}")
            if getattr(self.config, "personality", None):
                prompt_extras.append(f"Personality: {self.config.personality}")
            if getattr(self.config, "behavior", None):
                prompt_extras.append(f"Behavior: {self.config.behavior}")
                
            extra_str = "\n".join(prompt_extras)
            base_sys_prompt = f"You are {self.name}. {self.config.system_prompt}"
            base_sys_prompt = f"{base_sys_prompt}\n\nAgent Persona Traits:\n{extra_str}" if extra_str else base_sys_prompt

            prompt = f"{base_sys_prompt}\n\nUser: {message}\n\n{self.name}:"
            
            # Apply RAG augmentation
            prompt = self._augment_prompt_with_rag(prompt, message)
            
            cfg = get_llm_config()
            try:
                if cfg.stream:
                    sys.stdout.write(f"{self.name}: ")
                    sys.stdout.flush()
                return self.llm.invoke(
                    prompt, 
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                ).strip()
            except Exception as exc:
                logger.error(f"LLM invocation error: {exc}")
                return f"Error: Failed to get response from LLM - {exc}"

        # AgentMessage path
        logger.info(f"Agent '{self.name}' sending message to {message.receiver_id}")
        try:
            if not hasattr(self, "communication_manager"):
                logger.error("Communication manager not initialized")
                return False
            await self.communication_manager.send_message(message)
            return True
        except Exception as exc:
            logger.error(f"Error sending message: {exc}")
            return False

    async def send_task(self, task: Dict[str, Any], receiver_id: str) -> bool:
        message = AgentMessage(
            sender_id=self.id,
            receiver_id=receiver_id,
            content=str(task),
            message_type="task",
            metadata={"task": task},
        )
        return await self.send_message(message)

    # ── message / task queue internals ────────────────────────────────────────

    def set_message_handler(self, handler: Callable[[AgentMessage], None]) -> "Agent":
        self._message_handler = handler
        return self

    def set_task_handler(self, handler: Callable[[Dict[str, Any]], Any]) -> "Agent":
        self._task_handler = handler
        return self

    async def _handle_message(self, message: AgentMessage):
        try:
            # Check for correlation_id to resolve pending requests
            correlation_id = message.metadata.get("correlation_id")
            if correlation_id and correlation_id in self._pending_responses:
                future = self._pending_responses.pop(correlation_id)
                if not future.done():
                    future.set_result(message.content)
                return

            if self._message_handler:
                await self._message_handler(message)
            else:
                await self._default_message_handler(message)
        except Exception as exc:
            logger.error(f"Error handling message: {exc}")

    async def _default_message_handler(self, message: AgentMessage):
        if message.message_type == "task":
            # Handle task message and reply with result
            try:
                task_data = json.loads(message.content) if isinstance(message.content, str) else message.content
                task_str = task_data
                if isinstance(task_data, dict):
                    task_str = task_data.get("task") or task_data.get("description") or str(task_data)
                
                logger.info(f"Agent '{self.name}' [ID: {self.id}] received task: {task_str}")
                
                # If streaming, show that this agent is starting
                from daie.core.llm_manager import get_llm_config
                if self.config.stream or get_llm_config().stream:
                    print(f"\n\033[96m{self.name} is working on the task...\033[0m")

                result = await self.execute_task(str(task_str))
                
                reply = AgentMessage(
                    sender_id=self.id,
                    receiver_id=message.sender_id,
                    content=str(result),
                    message_type="text",
                    metadata={"correlation_id": message.metadata.get("correlation_id")}
                )
                await self.send_message(reply)
            except Exception as e:
                logger.error(f"Error handling task message: {e}")
                # Send error back if correlation_id exists
                cid = message.metadata.get("correlation_id")
                if cid:
                    reply = AgentMessage(
                        sender_id=self.id,
                        receiver_id=message.sender_id,
                        content=f"Error: {str(e)}",
                        message_type="text",
                        metadata={"correlation_id": cid}
                    )
                    await self.send_message(reply)
            return

        if message.message_type == "file":
            if not getattr(self.config, 'allow_file_transfers', False):
                reply = AgentMessage(
                    sender_id=self.id,
                    receiver_id=message.sender_id,
                    content="File transfer rejected: receiver does not allow incoming files.",
                    message_type="text",
                )
                await self.send_message(reply)
                return

            try:
                import os, base64
                downloads_dir = os.path.join(os.getcwd(), "downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                
                file_name = message.metadata.get("file_name", "received_file")
                file_path = os.path.join(downloads_dir, f"{self.id}_{file_name}")
                
                b64_data = message.metadata.get("base64_data", "")
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(b64_data))
                    
                reply_content = f"Successfully received and saved file: {file_name} at {file_path}"
                logger.info(f"Agent {self.name} received file {file_name}")
            except Exception as e:
                reply_content = f"Error saving file: {str(e)}"
                logger.error(reply_content)
                
            reply = AgentMessage(
                sender_id=self.id,
                receiver_id=message.sender_id,
                content=reply_content,
                message_type="text",
            )
            await self.send_message(reply)
            return

        if message.content.strip() and not message.content.startswith("I received your message:"):
            reply = AgentMessage(
                sender_id=self.id,
                receiver_id=message.sender_id,
                content=f"I received your message: {message.content}",
                message_type=message.message_type,
            )
            await self.send_message(reply)

    async def _handle_task(self, task: Dict[str, Any]):
        try:
            if self._task_handler:
                result = await self._task_handler(task)
            else:
                result = await self._default_task_handler(task)

            fut = task.get("_result_future")
            if fut and not fut.done():
                fut.set_result(result)
        except Exception as exc:
            logger.error(f"Error handling task: {exc}")
            fut = task.get("_result_future")
            if fut and not fut.done():
                fut.set_exception(exc)

    async def _default_task_handler(self, task: Dict[str, Any]) -> Any:
        tool_name = task.get("name")
        params = task.get("params", {})

        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}

        tool = self.tools[tool_name]
        if hasattr(tool, "execute"):
            return await tool.execute(params)
        elif callable(tool):
            import inspect
            return await tool(**params) if inspect.iscoroutinefunction(tool) else tool(**params)
        return {"success": False, "error": f"Tool '{tool_name}' is not executable"}

    async def _run_task_queue(self):
        while self._is_running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self._handle_task(task)
                self._task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as exc:
                logger.error(f"Error in task queue: {exc}")

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def start(
        self,
        communication_manager=None,
        memory_manager=None,
        tool_registry=None,
    ) -> None:
        if self._is_running:
            logger.warning(f"Agent '{self.name}' is already running")
            return

        logger.info(f"Starting agent: '{self.name}' (ID: {self.id})")
        try:
            if communication_manager:
                self.communication_manager = communication_manager
                self.communication_manager.register_agent(self)
            if memory_manager:
                self.memory_manager = memory_manager
                self.memory_manager.initialize_agent_memory(self.id)
            if tool_registry:
                self.tool_registry = tool_registry

            # Register A2A tools if communication manager is available
            if hasattr(self, "communication_manager") and self.communication_manager:
                try:
                    from daie.tools.a2a import A2ASendMessageTool, A2ADelegateTaskTool
                    send_msg_tool = A2ASendMessageTool()
                    send_msg_tool.set_agent(self)
                    self.add_tool(send_msg_tool)

                    delegate_tool = A2ADelegateTaskTool()
                    delegate_tool.set_agent(self)
                    self.add_tool(delegate_tool)
                    
                    try:
                        from daie.tools.a2a_file import A2ASendFileTool
                        file_tool = A2ASendFileTool()
                        file_tool.set_agent(self)
                        self.add_tool(file_tool)
                    except ImportError as e:
                        logger.warning(f"Could not load A2ASendFileTool: {e}")
                        
                    logger.debug(f"A2A communication tools dynamically mounted for {self.name}")
                except ImportError as e:
                    logger.warning(f"Could not load A2A tools: {e}")

            self._is_running = True
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)

            if self._task_queue is None:
                self._task_queue = asyncio.Queue()

            self._loop.create_task(self._run_task_queue())

            # Initialize RAG engine if enabled
            if self.config.enable_rag and self.config.rag_document_path:
                try:
                    self.rag_engine = RAGEngine(self.config.rag_document_path)
                    # Offload to thread to avoid blocking the event loop
                    await asyncio.to_thread(self.rag_engine.load)
                except Exception as e:
                    logger.error(f"Failed to initialize RAG engine: {e}")

            logger.info(f"Agent '{self.name}' started successfully")
        except Exception as exc:
            logger.error(f"Failed to start agent '{self.name}': {exc}")
            self._is_running = False
            raise

    async def stop(self) -> None:
        if not self._is_running:
            logger.warning(f"Agent '{self.name}' is already stopped")
            return

        logger.info(f"Stopping agent: '{self.name}'")
        try:
            self._is_running = False
            if hasattr(self, "communication_manager"):
                self.communication_manager.deregister_agent(self.id)
            logger.info(f"Agent '{self.name}' stopped successfully")
        except Exception as exc:
            logger.error(f"Error stopping agent '{self.name}': {exc}")
