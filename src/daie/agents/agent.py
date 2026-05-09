"""
AI Agent implementation module
"""

import asyncio
import datetime
import json
import re
from typing import Any, Callable, Dict, List, Optional, Union

from daie.agents.config import AgentConfig, AgentRole
from daie.agents.exceptions import (
    LLMInvocationError,
    TokenLimitExceeded,
    ToolCallLimitExceeded,
    ToolExecutionError,
    ToolNotFoundError,
)
from daie.agents.message import AgentMessage
from daie.rag import RAGEngine
from daie.tools import ToolRegistry, WebSearchTool, CodeSandboxTool
from daie.utils import generate_id
from daie.utils.encryption.ciphers import generate_x25519_keypair
import base64
from daie.core.tracing import trace_span, get_logger, set_agent_context
from daie.core.metrics import metrics

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Prompt templates
# ─────────────────────────────────────────────────────────────────────────────

_TOOL_SYSTEM = """\
You are {name}, a professional AI assistant.

{system_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tools_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT — CRITICAL INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MUST respond with ONLY a single valid JSON object. No prose, no markdown, no explanation outside the JSON.

To call a tool:
{{"thought": "<your reasoning>", "tool": "<tool_name>", "params": {{<parameters>}}}}

To give a final answer:
{{"thought": "<your reasoning>", "answer": "<your complete response as a plain string>"}}

Rules:
- "answer" MUST be a plain text string. Never put JSON, lists, or objects inside "answer".
- Only call one tool per response.
- After seeing a tool result, reason about it and either call another tool or give your final "answer".
- If you cannot complete the task, explain why in the "answer" field.
"""

_TOOL_TURN = """\
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONVERSATION HISTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{history}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENT TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{user_input}

Your JSON response:"""

_TOOL_RESULT_TURN = """\
Tool "{tool_name}" returned the following result:
{result}

Analyze this result carefully. Now provide your next JSON response \
(either call another tool or give your final "answer"):"""

_NO_TOOL_SYSTEM = """\
You are {name}, a professional AI assistant.

{system_prompt}

Respond naturally and helpfully. Be concise, accurate, and professional.\
"""


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
        name: Optional[Union[str, AgentConfig]] = None,
        role: Optional[AgentRole] = None,
        goal: Optional[str] = None,
        backstory: Optional[str] = None,
        system_prompt: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        tools: Optional[List[Any]] = None,
    ):
        if isinstance(name, AgentConfig):
            self.config = name
        elif config is not None:
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

        # Use persistent agent_id from config if provided.
        # If persistent_memory is enabled and no explicit agent_id is provided,
        # fallback to the agent's name to ensure stable memory directory.
        if self.config.agent_id:
            self.id = self.config.agent_id
        elif self.config.persistent_memory:
            # Create a filesystem-friendly ID from the name
            self.id = self.config.name.lower().replace(" ", "_")
        else:
            self.id = generate_id()

        # Generate X25519 E2EE keypair if not provided
        if not self.config.public_key or not self.config.private_key:
            priv, pub = generate_x25519_keypair()
            self.config.private_key = base64.b64encode(priv).decode("utf-8")
            self.config.public_key = base64.b64encode(pub).decode("utf-8")
            logger.info(f"Generated new X25519 keypair for agent {self.id}")

        self.tools: Dict[str, Any] = {}
        self.tool_registry = ToolRegistry()
        self._is_running = False

        # Auto-load tools based on capabilities
        if "web_search" in self.config.capabilities:
            self.add_tool(WebSearchTool())
        if (
            "code_execution" in self.config.capabilities
            or "code_sandbox" in self.config.capabilities
        ):
            self.add_tool(CodeSandboxTool())

        self._task_queue: Optional[asyncio.Queue] = None
        self._message_handler: Optional[Callable] = None
        self._task_handler: Optional[Callable] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._llm = None
        self.rag_engine: Optional[RAGEngine] = None
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._cached_system_prompt: Optional[str] = None

        # Task-level usage tracking
        self._current_task_tokens = 0
        self._current_task_tool_calls = 0
        self._current_task_id: Optional[str] = None
        self._background_tasks: set[asyncio.Task] = set()

        # Attach the global usage tracker (singleton)
        from daie.core.usage_tracker import UsageTracker
        self._usage_tracker = UsageTracker()

        if tools:
            for t in tools:
                self.add_tool(t)

        logger.info(f"Agent {self.config.name} (ID: {self.id}) created")

    def _track_task(self, task_or_coro: Union[asyncio.Task, Any]) -> asyncio.Task:
        """Track a background task to ensure it is cancelled on stop."""
        if asyncio.iscoroutine(task_or_coro):
            task = asyncio.create_task(task_or_coro)
        else:
            task = task_or_coro

        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

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

    @property
    def usage_report(self) -> dict:
        """
        Per-agent usage summary with token counts and estimated cost.

        Returns a dict with keys: invocation_count, task_count,
        prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd.
        """
        return self._usage_tracker.get_agent_summary(self.id)

    # ── tool management ───────────────────────────────────────────────────────

    def add_tool(self, tool: Any) -> "Agent":
        if hasattr(tool, "name"):
            self.tools[tool.name] = tool
            self._cached_system_prompt = None  # Invalidate cache
            logger.info(f"Tool '{tool.name}' added to agent '{self.name}'")
        else:
            logger.warning("Tool must have a 'name' attribute")
        return self

    def remove_tool(self, tool_name: str) -> "Agent":
        if tool_name in self.tools:
            del self.tools[tool_name]
            self._cached_system_prompt = None  # Invalidate cache
            logger.info(f"Tool '{tool_name}' removed from agent '{self.name}'")
        return self

    def _track_task(self, task: asyncio.Task) -> None:
        """Track background task to ensure it gets cancelled on stop"""
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

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
                        opt_str += f" +{len(opt_params) - 5} more"
                    lines.append(f"  optional: {opt_str}")
        return "\n".join(lines)

    def _build_persona_context(self) -> str:
        """Construct a rich, professional persona block injected into the LLM system prompt."""
        parts = []

        if self.config.role:
            role_val = (
                self.config.role.value
                if hasattr(self.config.role, "value")
                else str(self.config.role)
            )
            parts.append(f"Professional Role : {role_val}")

        if self.config.goal:
            parts.append(f"Primary Objective : {self.config.goal}")

        if self.config.backstory:
            parts.append(f"Background        : {self.config.backstory}")

        if getattr(self.config, "gender", None):
            parts.append(f"Gender Identity   : {self.config.gender}")
            parts.append(
                f"Identity Directive: You MUST present yourself as {self.config.gender} at all times. "
                "Never describe yourself as neutral, genderless, or a generic AI assistant."
            )

        if getattr(self.config, "personality", None):
            parts.append(f"Personality Traits: {self.config.personality}")

        if getattr(self.config, "behavior", None):
            parts.append(f"Behavioral Style  : {self.config.behavior}")

        if not parts:
            return ""

        parts.append(
            "Persona Compliance: Remain fully in character at all times. "
            "Do not break persona, acknowledge being an AI, or deviate from the traits above "
            "unless explicitly instructed to do so as part of your backstory."
        )

        header = "╔══════════════════════════════════════╗\n║       AGENT PERSONA & IDENTITY       ║\n╚══════════════════════════════════════╝"
        footer = "═" * 42
        return f"\n{header}\n" + "\n".join(parts) + f"\n{footer}"

    def _build_system_info_block(self) -> str:
        """Construct a block containing current system information like date and time."""
        if not getattr(self.config, "include_datetime", True):
            return ""

        now = datetime.datetime.now()
        # Include timezone if available, otherwise just use local time
        tz_str = now.astimezone().tzname() if now.astimezone() else "Local Time"

        info_parts = [
            f"Current Date: {now.strftime('%Y-%m-%d')}",
            f"Current Time: {now.strftime('%H:%M:%S')}",
            f"Timezone    : {tz_str}",
            f"Day of Week : {now.strftime('%A')}",
        ]

        header = "╔══════════════════════════════════════╗\n║      SYSTEM CONTEXT & TEMPORAL       ║\n╚══════════════════════════════════════╝"
        footer = "═" * 42
        return f"\n{header}\n" + "\n".join(info_parts) + f"\n{footer}"

    def _build_system_prompt(self) -> str:
        """Assemble the full system prompt with persona, instructions, and tool schema."""
        persona_context = self._build_persona_context()
        system_info = self._build_system_info_block()

        base_sys_prompt = (
            f"{persona_context}\n"
            f"{system_info}\n\n"
            f"Core Instructions:\n{self.config.system_prompt}"
        )

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
        Also handles non-JSON Thought/Answer formats as a fallback.
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
        if res:
            return res

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
                        candidate = text[start: i + 1]
                        res = try_parse(candidate)
                        if res:
                            return res
                        break
            search_from = start + 1

        # Fallback: parse plain-text "Thought: ... Answer: ..." or "Answer: ..." formats
        # that some models emit instead of JSON
        answer_match = re.search(
            r"(?:^|\n)\s*(?:Answer|ANSWER|Response|RESPONSE)\s*[:\-]\s*(.+)", text, re.DOTALL
        )
        if answer_match:
            answer_text = answer_match.group(1).strip()
            thought_match = re.search(
                r"(?:^|\n)\s*(?:Thought|THOUGHT|Thinking)\s*[:\-]\s*(.+?)(?:\n\s*(?:Answer|ANSWER))",
                text,
                re.DOTALL,
            )
            thought_text = thought_match.group(1).strip() if thought_match else ""
            return {"thought": thought_text, "answer": answer_text}

        return None

    # ── tool execution ────────────────────────────────────────────────────────

    @trace_span("agent_run_tool")
    async def _run_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute a tool and return a string representation of the result."""

        # --- Tool usage guardrails ---
        max_calls = getattr(self.config, "max_tool_calls_per_task", None)
        if max_calls is None:
            from daie.config import SystemConfig

            max_calls = SystemConfig().max_tool_calls_per_task

        if self._current_task_tool_calls >= max_calls:
            logger.warning(f"Agent '{self.name}' reached max_tool_calls_per_task: {max_calls}")
            raise ToolCallLimitExceeded(self._current_task_tool_calls, max_calls)

        self._current_task_tool_calls += 1
        # -----------------------------
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ToolNotFoundError(tool_name, list(self.tools.keys()))

        try:
            if hasattr(tool, "execute"):
                result = await tool.execute(params)
            elif callable(tool):
                import inspect

                result = (
                    await tool(**params) if inspect.iscoroutinefunction(tool) else tool(**params)
                )
            else:
                raise ToolExecutionError(tool_name, "tool is not executable")

            # Compact JSON for the LLM context
            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False, default=str)
            return str(result)

        except (ToolExecutionError, ToolNotFoundError, ToolCallLimitExceeded):
            raise
        except Exception as exc:
            logger.error(f"Tool '{tool_name}' raised: {exc}", exc_info=True)
            raise ToolExecutionError(tool_name, str(exc), original_error=exc)

    def _stream_final_answer(self, answer: str) -> None:
        """
        Stream a final answer string to stdout word-by-word.
        Called after the ReAct loop has already computed the answer non-streaming.
        Gives the user a natural streaming experience for the final response.
        """
        import sys
        import time

        sys.stdout.write(f"\n{self.name}: ")
        sys.stdout.flush()
        words = answer.split(" ")
        for i, word in enumerate(words):
            sys.stdout.write(word)
            if i < len(words) - 1:
                sys.stdout.write(" ")
            sys.stdout.flush()
            time.sleep(0.03)
        sys.stdout.write("\n\n")
        sys.stdout.flush()

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

    async def execute_task(
        self,
        user_input: str,
        images: Optional[List[str]] = None,
        output_schema=None,
    ):
        """
        Execute a task using the multi-step agent loop.

        Args:
            user_input: The task description or query
            images: Optional list of base64 encoded images or image URLs
            output_schema: Optional Pydantic BaseModel subclass. When provided,
                the agent's final answer is validated against this schema and
                returned as a typed model instance instead of a raw string.

        Returns:
            ``str`` if ``output_schema`` is None, otherwise an instance of
            the provided Pydantic model.
        """
        # --- PHASE 3: MULTI-MODAL SUPPORT ---
        if images:
            logger.info(f"Agent '{self.name}' received {len(images)} images for task")

        return await self._execute_task_internal(user_input, images=images, output_schema=output_schema)

    async def arun(self, user_input: str, images: Optional[List[str]] = None, output_schema=None):
        """
        Convenience shorthand: auto-start + execute_task.

        Example:
            >>> result = await agent.arun("List files in /tmp")
        """
        if not self._is_running:
            await self.start()
        return await self.execute_task(user_input, images=images, output_schema=output_schema)

    def run(self, user_input: str, images: Optional[List[str]] = None, output_schema=None):
        """Synchronous wrapper around arun() for scripts and notebooks."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return asyncio.run(self.arun(user_input, images=images, output_schema=output_schema))

        return asyncio.run(self.arun(user_input, images=images, output_schema=output_schema))

    async def _execute_task_internal(
        self,
        task_input: Union[str, Dict[str, Any]],
        images: Optional[List[str]] = None,
        output_schema=None,
    ) -> Any:
        # Reset task-level tracking
        self._current_task_tokens = 0
        self._current_task_tool_calls = 0
        self._current_task_id = generate_id()

        # ... (rest of logic)

        # ── direct tool call (dict input) ──────────────────────────────────
        if isinstance(task_input, dict):
            return await self._direct_tool_call(task_input)

        # ── natural-language task ──────────────────────────────────────────
        user_input = task_input

        # Log task input to history.txt if memory manager is available
        if hasattr(self, "memory_manager") and self.memory_manager:
            self.memory_manager.log_chat_history(self.id, f"User (Task): {task_input}")

        # RAG context retrieval for reasoning loop
        if self.config.enable_rag and self.rag_engine:
            context = self._get_rag_context(user_input)
            if context:
                user_input = f"Context from documents:\n{context}\n\nTask: {user_input}"
                if getattr(self.config, "rag_strict_context", False):
                    user_input += "\n(Answer ONLY using the provided documents)"

        system_prompt = self._build_system_prompt()

        # Inject structured output schema into the system prompt if requested
        if output_schema is not None:
            from daie.agents.structured_output import build_schema_prompt
            system_prompt += build_schema_prompt(output_schema)
        history: List[str] = []

        # Set agent context for logging
        set_agent_context(self.id)
        metrics.increment("agent_task_started_total", labels={"agent_role": self.config.role.value})

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
                    + _TOOL_TURN.format(history="\n".join(history), user_input=user_input)
                )

            # Invoke LLM via asyncio.to_thread to avoid blocking the event loop.
            # Always non-streaming for the ReAct reasoning loop.
            try:
                from daie.core.tracing import TracerManager

                with TracerManager().start_span(
                    "agent_thought", {"agent_id": self.id, "iteration": iteration}
                ) as span:
                    # --- PHASE 3: MULTI-MODAL LLM INVOCATION ---
                    invoke_kwargs = {
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "stream": False,
                    }

                    # Pass images to the LLM on the first reasoning step if provided
                    if iteration == 0 and images:
                        invoke_kwargs["images"] = images

                    raw = await asyncio.to_thread(self.llm.invoke, full_prompt, **invoke_kwargs)
                    raw = raw.strip()
                    span.set_attribute("raw_length", len(raw))
            except Exception as exc:
                logger.error(f"LLM invocation failed at iteration {iteration}: {exc}")
                metrics.increment("llm_invocation_errors_total", labels={"agent_id": self.id})
                raise LLMInvocationError(str(exc), original_error=exc)

            # --- Usage Tracking & Guardrails ---
            if hasattr(self.llm, "last_usage"):
                usage = self.llm.last_usage
                if isinstance(usage, dict):
                    tok = usage.get("total_tokens", 0)
                    self._current_task_tokens += tok
                    # Record to usage tracker
                    self._usage_tracker.record(
                        task_id=self._current_task_id or "",
                        agent_id=self.id,
                        agent_name=self.name,
                        provider=self.config.llm_provider,
                        model=self.config.llm_model,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                    )
                metrics.increment(
                    "daie_agent_tokens_total",
                    labels={"agent_id": self.id},
                    value=float(self._current_task_tokens),
                )
            metrics.increment("daie_agent_steps_total", labels={"agent_id": self.id})

            # Use configured or system-default max tokens
            max_tokens = getattr(self.config, "max_tokens_per_task", None)
            if max_tokens is None:
                from daie.config import SystemConfig

                max_tokens = SystemConfig().max_tokens_per_task

            if self._current_task_tokens > max_tokens:
                logger.warning(
                    f"Agent '{self.name}' [ID: {self.id}] exceeded max_tokens_per_task: {self._current_task_tokens} > {max_tokens}"
                )
                raise TokenLimitExceeded(self._current_task_tokens, max_tokens)
            # ------------------------------------

            logger.debug(f"[iter {iteration}] LLM raw: {raw[:300]}")

            parsed = self._parse_llm_json(raw)

            # ── final answer ───────────────────────────────────────────────
            if parsed is None:
                # LLM returned plain text — treat as final answer
                from daie.core.llm_manager import get_llm_config as _get_cfg

                if _get_cfg().stream or self.config.stream:
                    self._stream_final_answer(raw)
                return self._finalize_task(raw, output_schema=output_schema)

            if "answer" in parsed:
                answer = parsed["answer"]
                # When output_schema is set and answer is a dict, keep it as
                # JSON for structured validation rather than stringifying
                if output_schema is not None and isinstance(answer, dict):
                    answer = json.dumps(answer, ensure_ascii=False)
                elif not isinstance(answer, str):
                    answer = json.dumps(answer, ensure_ascii=False)
                # Log final answer to history.txt
                if hasattr(self, "memory_manager") and self.memory_manager:
                    self.memory_manager.log_chat_history(self.id, f"{self.name}: {answer}")
                # If streaming is enabled, re-deliver the answer via the LLM
                # so the user sees real token-by-token output
                from daie.core.llm_manager import get_llm_config as _get_cfg

                if _get_cfg().stream or self.config.stream:
                    self._stream_final_answer(answer)
                return self._finalize_task(answer, output_schema=output_schema)

            # ── tool call ─────────────────────────────────────────────────
            tool_name = parsed.get("tool")
            params = parsed.get("params", {})
            thought = parsed.get("thought", "")

            if not tool_name:
                # LLM gave JSON but no tool/answer key — treat as answer
                from daie.core.llm_manager import get_llm_config as _get_cfg

                if _get_cfg().stream or self.config.stream:
                    self._stream_final_answer(raw)
                return self._finalize_task(raw)

            logger.info(f"Agent '{self.name}' → tool '{tool_name}' | thought: {thought}")
            history.append(f"Assistant thought: {thought}")
            history.append(f"Called tool: {tool_name}({json.dumps(params)})")

            try:
                from daie.core.tracing import TracerManager

                with TracerManager().start_span("agent_action", {"tool": tool_name}) as span:
                    try:
                        tool_result = await self._run_tool(tool_name, params)
                        logger.info(f"Tool '{tool_name}' result: {tool_result[:200]}")
                        history.append(
                            _TOOL_RESULT_TURN.format(tool_name=tool_name, result=tool_result)
                        )
                        metrics.increment(
                            "agent_tool_calls_total",
                            labels={"agent_id": self.id, "tool": tool_name},
                        )
                    except ToolNotFoundError as e:
                        # --- PHASE 3: DYNAMIC TOOL DISCOVERY ---
                        discovered_agents = []
                        if hasattr(self, "registry") and self.registry:
                            logger.info(
                                f"Tool '{tool_name}' not found locally. Attempting DHT discovery..."
                            )
                            discovered_agents = await self.registry.search_by_capability_dht(
                                tool_name
                            )

                        if discovered_agents:
                            target_agent = discovered_agents[0]
                            target_id = target_agent["agent_id"]
                            logger.info(
                                f"Discovered specialist for '{tool_name}': {target_id}. Delegating..."
                            )

                            # Use delegation logic
                            delegate_result = await self._delegate_to_specialist(
                                target_id, tool_name, params
                            )
                            history.append(
                                f"Delegated to specialist {target_id} for tool '{tool_name}'. Result: {delegate_result}"
                            )
                        else:
                            raise e
            except ToolCallLimitExceeded:
                history.append("Tool call limit reached. Cannot call more tools.")
                break
            except ToolNotFoundError as e:
                error_msg = str(e)
                logger.warning(error_msg)
                # --- PHASE 3: SELF-CORRECTION ---
                history.append(
                    f"Tool error: {error_msg}. Please check the tool name or params and try again or use a different tool."
                )
            except ToolExecutionError as e:
                error_msg = str(e)
                logger.warning(f"Tool execution failed: {error_msg}")
                # --- PHASE 3: SELF-CORRECTION ---
                history.append(
                    _TOOL_RESULT_TURN.format(
                        tool_name=tool_name,
                        result=f"Error: {error_msg}. Please correct your parameters and retry.",
                    )
                )

        # Iteration limit reached — ask LLM for a final answer with what we have
        try:
            summary_prompt = (
                system_prompt
                + "\n\n"
                + _TOOL_TURN.format(history="\n".join(history), user_input=user_input)
                + "\n\nNote: You have reached the maximum number of tool calls allowed for this task. "
                "Based on all the information gathered so far, provide a comprehensive final answer. "
                "Summarise what was accomplished and what the outcome is."
            )
            raw = await asyncio.to_thread(
                self.llm.invoke,
                summary_prompt,
                stream=False,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            raw = raw.strip()
        except Exception as exc:
            logger.error(f"LLM summary invocation failed: {exc}")
            raise LLMInvocationError(str(exc), original_error=exc)

        # Record summary invocation usage
        if hasattr(self.llm, "last_usage"):
            usage = self.llm.last_usage
            if isinstance(usage, dict):
                self._usage_tracker.record(
                    task_id=self._current_task_id or "",
                    agent_id=self.id,
                    agent_name=self.name,
                    provider=self.config.llm_provider,
                    model=self.config.llm_model,
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                )

        parsed = self._parse_llm_json(raw)
        answer = (parsed or {}).get("answer", raw)
        if not isinstance(answer, str):
            answer = json.dumps(answer, ensure_ascii=False)

        return self._finalize_task(answer, output_schema=output_schema)

    def _finalize_task(self, answer: str, output_schema=None):
        """Post-process final answer, validate against output schema, and record metrics."""
        metrics.increment(
            "agent_task_completed_total", labels={"agent_role": self.config.role.value}
        )
        # Reset context
        from daie.core.tracing import set_agent_context

        set_agent_context(None)

        # Trigger periodic memory maintenance
        if hasattr(self, "memory_manager") and self.memory_manager:
            self._track_task(self._maybe_summarize_memory())

        # Structured output validation
        if output_schema is not None:
            from daie.agents.structured_output import (
                OutputValidationError,
                parse_and_validate,
            )

            try:
                return parse_and_validate(answer, output_schema)
            except OutputValidationError:
                logger.warning(
                    f"Structured output validation failed for schema "
                    f"{output_schema.__name__}. Raising error."
                )
                raise

        return answer

    async def _maybe_summarize_memory(self):
        """Check if memory needs summarization based on threshold"""
        try:
            if not self.memory_manager:
                return

            threshold = getattr(self.config, "memory_summarization_threshold", 20)
            memories = self.memory_manager.retrieve_memories(self.id, limit=threshold + 1)

            if len(memories) > threshold:
                logger.info(
                    f"Memory threshold reached ({len(memories)}). Triggering summarization..."
                )
                # In a real system, we'd call the LLM to summarize
                # For now, we use the memory manager's built-in summuarization hook
                if hasattr(self.memory_manager, "summarize_agent_history"):
                    await self.memory_manager.summarize_agent_history(self.id)
        except Exception as e:
            logger.error(f"Error during memory summarization: {e}")

    def _stream_final_answer(self, answer: str) -> None:
        """Re-stream the final answer if enabled"""
        import sys

        if not sys.stdout.isatty():
            # Avoid messing with non-interactive pipes
            pass
        # In a real system, we might push tokens to a callback or websocket
        # For CLI, we just ensure a newline
        sys.stdout.write("\n")
        sys.stdout.flush()

    async def _delegate_to_specialist(
        self, target_id: str, tool_name: str, params: Dict[str, Any]
    ) -> str:
        """
        Dynamically delegate a tool call to a remote specialist agent.
        Used as part of Phase 3 Intelligence (Tool Discovery).
        """
        # We leverage the existing A2ADelegateTaskTool logic
        # Construct the task payload
        task_payload = {
            "task": f"Please execute the tool '{tool_name}' with these parameters and return the result as a string.",
            "direct_tool_call": {"tool": tool_name, "params": params},
        }

        # Prepare delegation message
        from daie.utils import generate_id

        correlation_id = generate_id()

        # We manually build the message to avoid tool recursion
        msg = AgentMessage(
            sender_id=self.id,
            receiver_id=target_id,
            content=json.dumps({"task": task_payload}),
            message_type="task",
            metadata={"correlation_id": correlation_id},
        )

        # Create future for response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_responses[correlation_id] = future

        try:
            if not getattr(self, "communication_manager", None):
                return "Error: No communication manager to delegate task."

            success = await self.communication_manager.send_message(msg)
            if not success:
                self._pending_responses.pop(correlation_id, None)
                return f"Error: Failed to send delegation message to {target_id}."

            # Wait for specialist (60s timeout for complex tasks)
            response = await asyncio.wait_for(future, timeout=60.0)
            return str(response)
        except asyncio.TimeoutError:
            self._pending_responses.pop(correlation_id, None)
            return f"Error: Delegation to {target_id} for '{tool_name}' timed out after 60s."
        except Exception as e:
            self._pending_responses.pop(correlation_id, None)
            return f"Error during delegation: {e}"

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
            import sys

            from daie.core.llm_manager import get_llm_config

            persona_context = self._build_persona_context()
            base_sys_prompt = (
                f"You are {self.name}, a professional AI assistant.\n"
                f"{persona_context}\n\n"
                f"Core Instructions:\n{self.config.system_prompt}"
            )

            # Retrieve relevant memory context if memory manager is available
            memory_context = ""
            if hasattr(self, "memory_manager") and self.memory_manager:
                try:
                    similar_memories = self.memory_manager.search_similar(
                        self.id, message, memory_type="working", limit=10
                    )
                    recent_memories = self.memory_manager.retrieve_memories(
                        self.id, memory_type="working", limit=20
                    )

                    all_memories = {}
                    for mem in similar_memories + recent_memories:
                        if mem.id not in all_memories:
                            all_memories[mem.id] = mem

                    sorted_memories = sorted(
                        all_memories.values(), key=lambda x: x.timestamp, reverse=True
                    )[:15]

                    if sorted_memories:
                        memory_items = [f"  {mem.content}" for mem in sorted_memories]
                        memory_context = (
                            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "CONVERSATION HISTORY (most recent first)\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(memory_items)
                        )
                except Exception as e:
                    logger.warning(f"Failed to retrieve memory context: {e}")

            if memory_context:
                memory_instruction = (
                    "\n\nMemory Directive: Use the conversation history above to recall prior context, "
                    "user preferences, and previously shared information. Reference it naturally without "
                    "explicitly saying 'according to our history'."
                )
            else:
                memory_instruction = (
                    "\n\nMemory Directive: This is the beginning of the conversation. "
                    "Do not fabricate or reference any prior interactions that have not occurred."
                )

            prompt = (
                f"{base_sys_prompt}"
                f"{memory_context}"
                f"{memory_instruction}"
                f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"User: {message}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{self.name}:"
            )

            # Apply RAG augmentation
            prompt = self._augment_prompt_with_rag(prompt, message)

            cfg = get_llm_config()
            try:
                if cfg.stream:
                    sys.stdout.write(f"{self.name}: ")
                    sys.stdout.flush()
                response = self.llm.invoke(
                    prompt, temperature=self.config.temperature, max_tokens=self.config.max_tokens
                ).strip()

                # Store the conversation in memory if memory manager is available
                if hasattr(self, "memory_manager") and self.memory_manager:
                    try:
                        # Store user message
                        self.memory_manager.store_memory(
                            agent_id=self.id,
                            content=f"User: {message}",
                            memory_type="working",
                            tags=["conversation", "user_message"],
                            namespace=self.config.memory_namespace,
                        )
                        # Log user message to history.txt
                        self.memory_manager.log_chat_history(self.id, f"User: {message}")

                        # Store agent response
                        self.memory_manager.store_memory(
                            agent_id=self.id,
                            content=f"{self.name}: {response}",
                            memory_type="working",
                            tags=["conversation", "agent_response"],
                            namespace=self.config.memory_namespace,
                        )
                        # Log agent response to history.txt
                        self.memory_manager.log_chat_history(self.id, f"{self.name}: {response}")
                    except Exception as e:
                        logger.warning(f"Failed to store conversation in memory: {e}")

                return response
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
        from daie.core.tracing import inject_trace_context

        message = AgentMessage(
            sender_id=self.id,
            receiver_id=receiver_id,
            content=json.dumps(task),
            message_type="task",
            metadata={"task": task},
        )
        # Handle images if passed in metadata/config but normally tasks are text-based payloads
        # Images are better handled in conversational messages or specialized vision tools.

        # Inject trace context into outgoing message
        message.metadata = inject_trace_context(message.metadata)
        return await self.send_message(message)

    # ── message / task queue internals ────────────────────────────────────────

    def set_message_handler(self, handler: Callable[[AgentMessage], None]) -> "Agent":
        self._message_handler = handler
        return self

    def set_task_handler(self, handler: Callable[[Dict[str, Any]], Any]) -> "Agent":
        self._task_handler = handler
        return self

    async def _handle_message(self, message: AgentMessage):
        """
        Handle incoming messages asynchronously without blocking agent tasks.
        """
        from daie.core.tracing import TraceContextManager

        # Extract trace context from incoming message
        with TraceContextManager(message.metadata):
            try:
                # Check for correlation_id to resolve pending requests (reply to a delegation)
                correlation_id = message.metadata.get("correlation_id")
                if correlation_id and correlation_id in self._pending_responses:
                    future = self._pending_responses.pop(correlation_id)
                    if not future.done():
                        future.set_result(message.content)
                    return

                # For task messages, await directly so the reply is sent before
                # the delegation future times out
                if message.message_type == "task":
                    if self._message_handler:
                        await self._message_handler(message)
                    else:
                        await self._default_message_handler(message)
                else:
                    # For non-task messages, fire-and-forget is fine
                    if self._message_handler:
                        asyncio.create_task(self._message_handler(message))
                    else:
                        asyncio.create_task(self._default_message_handler(message))
            except Exception as exc:
                logger.error(f"Error handling message: {exc}")

    async def _default_message_handler(self, message: AgentMessage):
        if message.message_type == "task":
            # Handle task message and reply with result
            try:
                task_data = (
                    json.loads(message.content)
                    if isinstance(message.content, str)
                    else message.content
                )

                # Recursively unwrap nested {"task": ...} dicts until we get a plain string
                task_str = task_data
                while isinstance(task_str, dict):
                    task_str = (
                        task_str.get("task")
                        or task_str.get("description")
                        or task_str.get("content")
                        or str(task_str)
                    )

                task_str = str(task_str)
                logger.info(f"Agent '{self.name}' [ID: {self.id}] received task: {task_str}")

                # Log incoming task to this agent's history
                if hasattr(self, "memory_manager") and self.memory_manager:
                    self.memory_manager.log_chat_history(
                        self.id, f"[Delegated task from {message.sender_id}]: {task_str}"
                    )
                    self.memory_manager.store_memory(
                        agent_id=self.id,
                        content=f"Received task: {task_str}",
                        memory_type="episodic",
                        tags=["task", "delegated"],
                        namespace=self.config.memory_namespace,
                    )

                # If streaming, show that this agent is starting
                from daie.core.llm_manager import get_llm_config

                if self.config.stream or get_llm_config().stream:
                    print(f"\n\033[96m{self.name} is working on the task...\033[0m")

                result = await self.execute_task(task_str)

                # Log the result to this agent's history
                if hasattr(self, "memory_manager") and self.memory_manager:
                    self.memory_manager.log_chat_history(self.id, f"[Task result]: {result}")
                    self.memory_manager.store_memory(
                        agent_id=self.id,
                        content=f"Task completed: {result}",
                        memory_type="episodic",
                        tags=["task", "result"],
                        namespace=self.config.memory_namespace,
                    )

                reply = AgentMessage(
                    sender_id=self.id,
                    receiver_id=message.sender_id,
                    content=str(result),
                    message_type="text",
                    metadata={"correlation_id": message.metadata.get("correlation_id")},
                )
                comm_mgr = getattr(self, "communication_manager", None)
                if comm_mgr:
                    await comm_mgr.send_message(reply)
                else:
                    logger.error(
                        f"Agent '{self.name}' has no communication_manager — cannot send task reply"
                    )
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
                        metadata={"correlation_id": cid},
                    )
                    comm_mgr = getattr(self, "communication_manager", None)
                    if comm_mgr:
                        await comm_mgr.send_message(reply)
            return

        if message.message_type == "file":
            if not getattr(self.config, "allow_file_transfers", False):
                reply = AgentMessage(
                    sender_id=self.id,
                    receiver_id=message.sender_id,
                    content="File transfer rejected: receiver does not allow incoming files.",
                    message_type="text",
                )
                comm_mgr = getattr(self, "communication_manager", None)
                if comm_mgr:
                    await comm_mgr.send_message(reply)
                return

            try:
                import base64
                import os

                downloads_dir = os.path.join(os.getcwd(), "downloads")
                os.makedirs(downloads_dir, exist_ok=True)

                file_name = message.metadata.get("file_name", "received_file")
                file_path = os.path.join(downloads_dir, f"{self.id}_{file_name}")

                b64_data = message.metadata.get("base64_data", "")

                # Decrypt file payload if it was encrypted by the sender
                if message.metadata.get("file_encrypted", False):
                    try:
                        from daie.utils.encryption.ciphers import (
                            decrypt_data,
                            derive_shared_secret,
                        )

                        comm_mgr = getattr(self, "communication_manager", None)
                        if comm_mgr and self.config.private_key:
                            topology = comm_mgr.registry.get_network_topology()
                            sender_data = topology.get("nodes", {}).get(message.sender_id)
                            if sender_data and sender_data.get("public_key"):
                                priv = base64.b64decode(self.config.private_key)
                                pub = base64.b64decode(sender_data["public_key"])
                                shared_key = derive_shared_secret(priv, pub)
                                b64_data = decrypt_data(b64_data, shared_key)
                                logger.info(
                                    f"Decrypted file payload from {message.sender_id}"
                                )
                            else:
                                logger.warning(
                                    f"No public key for sender {message.sender_id}, "
                                    "cannot decrypt file payload"
                                )
                    except Exception as dec_err:
                        logger.error(f"File decryption failed: {dec_err}")
                        reply_content = f"Error decrypting file: {str(dec_err)}"
                        raise Exception(reply_content)

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
            comm_mgr = getattr(self, "communication_manager", None)
            if comm_mgr:
                await comm_mgr.send_message(reply)
            return

        if message.content.strip() and not message.content.startswith("I received your message:"):
            reply = AgentMessage(
                sender_id=self.id,
                receiver_id=message.sender_id,
                content=f"I received your message: {message.content}",
                message_type=message.message_type,
            )
            comm_mgr = getattr(self, "communication_manager", None)
            if comm_mgr:
                await comm_mgr.send_message(reply)

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

            # Handle memory manager based on persistent_memory config
            if memory_manager:
                # Use provided memory manager
                self.memory_manager = memory_manager
                self.memory_manager.initialize_agent_memory(self.id)
            elif self.config.persistent_memory:
                # Auto-create memory manager with persistent memory enabled
                from daie.config import SystemConfig
                from daie.memory import MemoryManager

                # Create system config with persistent memory enabled
                # Use default memory_root_path to ensure consistent storage location
                system_config = SystemConfig(
                    persistent_memory=True,
                    memory_storage_type="binary",
                    memory_root_path="./agent_memory",
                )
                self.memory_manager = MemoryManager(config=system_config)
                self.memory_manager.start()
                self.memory_manager.initialize_agent_memory(self.id)
                logger.info(
                    f"Auto-created persistent memory manager for agent '{self.name}' (ID: {self.id})"
                )

            if tool_registry:
                self.tool_registry = tool_registry

            # Register A2A tools if communication manager is available
            if hasattr(self, "communication_manager") and self.communication_manager:
                try:
                    from daie.tools.a2a import A2ADelegateTaskTool, A2ASendMessageTool

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
                    from daie.rag import VectorRAGEngine

                    self.rag_engine = VectorRAGEngine(self.config.rag_document_path)
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

            # Stop memory manager if it was auto-created (persistent_memory=True)
            if hasattr(self, "memory_manager") and self.memory_manager is not None:
                try:
                    self.memory_manager.stop()
                    logger.debug(f"Memory manager stopped for agent '{self.name}'")
                except Exception as mem_exc:
                    logger.error(
                        f"Error stopping memory manager for agent '{self.name}': {mem_exc}"
                    )

            # Cancel remaining background tasks
            if self._background_tasks:
                logger.debug(
                    f"Cancelling {len(self._background_tasks)} background tasks for {self.name}"
                )
                for task in list(self._background_tasks):
                    task.cancel()
                # Wait briefly for cancellation to propagate
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            logger.info(f"Agent '{self.name}' stopped successfully")
        except Exception as exc:
            logger.error(f"Error stopping agent '{self.name}': {exc}")

    # ── serialization & hot-reload ────────────────────────────────────────

    def snapshot(self, path: str = None) -> dict:
        """
        Capture the agent's current state as a serializable snapshot.

        If the agent is running, it will be stopped first (graceful pause).
        If ``path`` is provided, the snapshot is also written to that file.

        Args:
            path: Optional file path to save the JSON snapshot.

        Returns:
            The snapshot as a plain dictionary.

        Example::

            snapshot_dict = agent.snapshot("./checkpoint.json")
        """
        from daie.agents.serialization import serialize_agent

        snap = serialize_agent(self)

        if path:
            snap.save(path)

        return snap.to_dict()

    @classmethod
    def from_snapshot(
        cls,
        path_or_dict,
        tools=None,
    ) -> "Agent":
        """
        Reconstruct an agent from a previously saved snapshot.

        The agent is created in a **stopped** state. Call
        ``await agent.start()`` to resume execution.

        Args:
            path_or_dict: Path to a snapshot JSON file, or a dict returned
                by ``agent.snapshot()``.
            tools: Optional list of tool instances to register. Tools that
                were present in the snapshot but not provided here will
                trigger a warning (not an error).

        Returns:
            A new ``Agent`` with the original identity, config, and E2EE keys.

        Example::

            agent = Agent.from_snapshot("./checkpoint.json", tools=[FileManagerTool()])
            await agent.start()
            result = await agent.execute_task("Continue where we left off")
        """
        from daie.agents.serialization import AgentSnapshot, deserialize_agent

        if isinstance(path_or_dict, (str,)):
            snap = AgentSnapshot.load(path_or_dict)
        elif isinstance(path_or_dict, dict):
            snap = AgentSnapshot.from_dict(path_or_dict)
        else:
            # Try treating it as a Path-like object
            snap = AgentSnapshot.load(str(path_or_dict))

        return deserialize_agent(snap, tools=tools)

    async def pause(self) -> dict:
        """
        Gracefully stop the agent and return its snapshot.

        This is a convenience method combining ``stop()`` + ``snapshot()``.
        Use this when you intend to resume the agent later.

        Returns:
            The snapshot as a plain dictionary.

        Example::

            snapshot_dict = await agent.pause()
            # Save to file for transfer to another machine
            import json
            with open("agent_state.json", "w") as f:
                json.dump(snapshot_dict, f, indent=2)
        """
        if self._is_running:
            await self.stop()

        return self.snapshot()
