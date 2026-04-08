"""
Exception hierarchy for the DAIE agent framework.

Provides structured, catchable exceptions for the ReAct loop,
tool execution, and agent lifecycle.
"""


class DAIEError(Exception):
    """Base exception for all DAIE errors."""


class AgentError(DAIEError):
    """Base exception for agent-related errors."""


class ToolExecutionError(AgentError):
    """Raised when a tool fails during execution."""

    def __init__(self, tool_name: str, message: str, original_error: Exception = None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class ToolNotFoundError(AgentError):
    """Raised when a requested tool is not registered."""

    def __init__(self, tool_name: str, available_tools: list = None):
        self.tool_name = tool_name
        self.available_tools = available_tools or []
        tools_str = ", ".join(self.available_tools) if self.available_tools else "(none)"
        super().__init__(
            f"Tool '{tool_name}' not found. Available tools: {tools_str}"
        )


class ReActLoopError(AgentError):
    """Raised when the ReAct reasoning loop encounters an unrecoverable error."""

    def __init__(self, message: str, iteration: int = 0):
        self.iteration = iteration
        super().__init__(f"ReAct loop error (iteration {iteration}): {message}")


class TokenLimitExceeded(AgentError):
    """Raised when a task exceeds its token budget."""

    def __init__(self, used_tokens: int, max_tokens: int):
        self.used_tokens = used_tokens
        self.max_tokens = max_tokens
        super().__init__(
            f"Token limit exceeded: {used_tokens} used, {max_tokens} allowed"
        )


class ToolCallLimitExceeded(AgentError):
    """Raised when a task exceeds its tool call budget."""

    def __init__(self, used_calls: int, max_calls: int):
        self.used_calls = used_calls
        self.max_calls = max_calls
        super().__init__(
            f"Tool call limit exceeded: {used_calls} used, {max_calls} allowed"
        )


class AgentNotRunningError(AgentError):
    """Raised when an operation is attempted on a stopped agent."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        super().__init__(f"Agent '{agent_name}' is not running")


class LLMInvocationError(DAIEError):
    """Raised when the LLM invocation fails."""

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(f"LLM invocation failed: {message}")
