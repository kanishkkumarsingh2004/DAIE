import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, PropertyMock
from daie.core.resilience import CircuitBreaker, RetryPolicy, CircuitState
from daie.core.tracing import TracerManager, trace_span
from daie.agents.agent import Agent
from daie.agents.config import AgentConfig
from daie.agents.exceptions import TokenLimitExceeded, ToolCallLimitExceeded


@pytest.mark.asyncio
async def test_circuit_breaker():
    cb = CircuitBreaker("test_cb", failure_threshold=2, recovery_timeout=0.1)

    assert cb.state == CircuitState.CLOSED

    # First failure
    with pytest.raises(ValueError):
        await cb.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # Second failure -> OPEN
    with pytest.raises(ValueError):
        await cb.call(lambda: (_ for _ in ()).throw(ValueError("Error")))
    assert cb.state == CircuitState.OPEN

    # Rejects while open
    with pytest.raises(RuntimeError) as exc:
        await cb.call(lambda: "success")
    assert "is OPEN" in str(exc.value)

    # Wait for recovery
    await asyncio.sleep(0.15)

    # Try call -> HALF_OPEN then CLOSED
    result = await cb.call(lambda: "success")
    assert result == "success"
    # Note: recovery requires half_open_max_calls (default 3)
    assert cb.state == CircuitState.HALF_OPEN

    await cb.call(lambda: "success")
    await cb.call(lambda: "success")
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_retry_policy():
    rp = RetryPolicy(max_retries=2, base_delay=0.01)

    attempts = 0

    async def failing_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Fail")
        return "Success"

    result = await rp.execute(failing_func)
    assert result == "Success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_agent_token_guardrail():
    config = AgentConfig(name="GuardrailBot", max_tokens_per_task=10)
    agent = Agent(config=config)

    # Mock LLM to return many tokens
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Response"
    # Use PropertyMock to ensure last_usage works as a property
    type(mock_llm).last_usage = PropertyMock(return_value={"total_tokens": 100})
    agent._llm = mock_llm

    agent._is_running = True
    with pytest.raises(TokenLimitExceeded):
        await agent.execute_task("Do something")


@pytest.mark.asyncio
async def test_agent_tool_call_guardrail():
    config = AgentConfig(name="ToolLimiter", max_tool_calls_per_task=1)
    agent = Agent(config=config)

    # Add a dummy tool via mock object
    mock_tool = MagicMock()
    mock_tool.name = "dummy"
    mock_tool.description = "test tool"
    mock_tool.parameters = {}
    mock_tool.execute = AsyncMock(return_value="done")

    agent.add_tool(mock_tool)

    agent._is_running = True
    agent._current_task_tool_calls = 0

    # First call succeeds
    res1 = await agent._run_tool("dummy", {})
    assert res1 == "done"

    # Second call fails
    with pytest.raises(ToolCallLimitExceeded):
        await agent._run_tool("dummy", {})


def test_tracing_graceful_failure():
    # Verify tracing doesn't break
    TracerManager().setup(enabled=True)

    @trace_span("test")
    def sync_func():
        return "ok"

    assert sync_func() == "ok"
