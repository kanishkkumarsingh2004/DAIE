"""Tests for Agent ReAct loop, tool integration, and prompt helpers.

Covers:
- _tools_block() compact rendering
- _build_system_prompt() with/without tools
- _parse_llm_json() edge cases
- _run_tool() dispatch (Tool subclass + @tool decorator)
- execute_task() ReAct loop with mock LLM
- execute_task() direct dict call
- send_message() streaming prefix
- @tool decorated function through agent
"""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from daie.agents.agent import Agent
from daie.agents.config import AgentConfig, AgentRole
from daie.agents.exceptions import ToolExecutionError, ToolNotFoundError
from daie.tools.file_manager import FileManagerTool
from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter, tool

# ── helpers ───────────────────────────────────────────────────────────────────


def make_agent(name="Bot", tools=None) -> Agent:
    agent = Agent(config=AgentConfig(name=name, role=AgentRole.GENERAL_PURPOSE))
    if tools:
        for t in tools:
            agent.add_tool(t)
    return agent


class EchoTool(Tool):
    """Simple tool that echoes its input — no external deps."""

    def __init__(self):
        super().__init__(
            ToolMetadata(
                name="echo",
                description="Echo the input text back",
                category=ToolCategory.GENERAL,
                parameters=[
                    ToolParameter(
                        name="text", type="string", description="Text to echo", required=True
                    )
                ],
            )
        )

    async def _execute(self, params):
        return {"echoed": params["text"]}


class MockLLM:
    """Controllable mock LLM — returns responses from a queue."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def invoke(self, prompt, stream=None, **kw):
        self.calls.append(prompt)
        return self._responses.pop(0) if self._responses else '{"answer":"done"}'


# ── _tools_block ──────────────────────────────────────────────────────────────


class TestToolsBlock:
    def test_no_tools_returns_placeholder(self):
        agent = make_agent()
        assert agent._tools_block() == "(no tools available)"

    def test_tool_name_and_description_present(self):
        agent = make_agent(tools=[EchoTool()])
        block = agent._tools_block()
        assert "echo" in block
        assert "Echo" in block

    def test_description_truncated_at_120(self):
        class LongDescTool(Tool):
            def __init__(self):
                super().__init__(
                    ToolMetadata(name="long", description="x" * 200, category=ToolCategory.GENERAL)
                )

            async def _execute(self, p):
                return {}

        agent = make_agent(tools=[LongDescTool()])
        block = agent._tools_block()
        # description line should not exceed 120 chars for the desc portion
        desc_line = [line for line in block.splitlines() if "long" in line][0]
        assert len(desc_line) <= 130  # name + ": " + 120 chars

    def test_required_params_shown(self):
        agent = make_agent(tools=[EchoTool()])
        block = agent._tools_block()
        assert "required:" in block
        assert "text(string)" in block

    def test_optional_params_shown(self):
        agent = make_agent(tools=[FileManagerTool()])
        block = agent._tools_block()
        assert "optional:" in block

    def test_multiple_tools(self):
        agent = make_agent(tools=[EchoTool(), FileManagerTool()])
        block = agent._tools_block()
        assert "echo" in block
        assert "file_manager" in block


# ── _build_system_prompt ──────────────────────────────────────────────────────


class TestBuildSystemPrompt:
    def test_no_tools_uses_simple_template(self):
        agent = make_agent()
        prompt = agent._build_system_prompt()
        assert agent.name in prompt
        # Should NOT contain tool-use instructions
        assert "tool_name" not in prompt

    def test_with_tools_uses_tool_template(self):
        agent = make_agent(tools=[EchoTool()])
        prompt = agent._build_system_prompt()
        assert "tool_name" in prompt
        assert "echo" in prompt

    def test_agent_name_in_prompt(self):
        agent = make_agent(name="Aria")
        prompt = agent._build_system_prompt()
        assert "Aria" in prompt


# ── _parse_llm_json ───────────────────────────────────────────────────────────


class TestParseLlmJson:
    def test_clean_json(self):
        result = Agent._parse_llm_json('{"tool":"echo","params":{"text":"hi"}}')
        assert result["tool"] == "echo"

    def test_json_in_code_fence(self):
        text = '```json\n{"answer":"hello"}\n```'
        result = Agent._parse_llm_json(text)
        assert result["answer"] == "hello"

    def test_json_with_leading_prose(self):
        text = 'Sure, here you go:\n{"answer":"42"}'
        result = Agent._parse_llm_json(text)
        assert result["answer"] == "42"

    def test_plain_text_returns_none(self):
        result = Agent._parse_llm_json("This is just plain text with no JSON.")
        assert result is None

    def test_nested_json(self):
        text = '{"tool":"file_manager","params":{"action":"create_file","path":"/tmp/x.txt"}}'
        result = Agent._parse_llm_json(text)
        assert result["params"]["action"] == "create_file"

    def test_empty_string_returns_none(self):
        assert Agent._parse_llm_json("") is None


# ── _run_tool ─────────────────────────────────────────────────────────────────


class TestRunTool:
    @pytest.mark.asyncio
    async def test_run_known_tool(self):
        agent = make_agent(tools=[EchoTool()])
        result = await agent._run_tool("echo", {"text": "hello"})
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_run_unknown_tool_raises_error(self):
        agent = make_agent()
        with pytest.raises(ToolNotFoundError, match="not found"):
            await agent._run_tool("nonexistent", {})

    @pytest.mark.asyncio
    async def test_run_tool_decorator(self):
        @tool(name="add", description="Add two numbers")
        async def add(a: str, b: str) -> str:
            return str(int(a) + int(b))

        agent = make_agent(tools=[add])
        result = await agent._run_tool("add", {"a": "3", "b": "4"})
        assert "7" in result

    @pytest.mark.asyncio
    async def test_run_tool_exception_raises_tool_execution_error(self):
        class BrokenTool(Tool):
            def __init__(self):
                super().__init__(
                    ToolMetadata(
                        name="broken", description="always fails", category=ToolCategory.GENERAL
                    )
                )

            async def _execute(self, p):
                raise RuntimeError("boom")

        agent = make_agent(tools=[BrokenTool()])
        with pytest.raises(ToolExecutionError, match="boom"):
            await agent._run_tool("broken", {})


# ── execute_task — ReAct loop ─────────────────────────────────────────────────


class TestExecuteTaskReact:
    @pytest.mark.asyncio
    async def test_direct_answer_no_tool(self):
        """LLM returns answer immediately without calling any tool."""
        agent = make_agent()
        agent._llm = MockLLM(['{"thought":"easy","answer":"42"}'])
        agent._is_running = True

        result = await agent.execute_task("What is 6 times 7?")
        assert result == "42"

    @pytest.mark.asyncio
    async def test_plain_text_answer(self):
        """LLM returns plain text (no JSON) — treated as final answer."""
        agent = make_agent()
        agent._llm = MockLLM(["Just plain text response."])
        agent._is_running = True

        result = await agent.execute_task("Say something")
        assert result == "Just plain text response."

    @pytest.mark.asyncio
    async def test_one_tool_call_then_answer(self):
        """LLM calls echo tool once, then gives final answer."""
        agent = make_agent(tools=[EchoTool()])
        agent._llm = MockLLM(
            [
                '{"thought":"echo it","tool":"echo","params":{"text":"ping"}}',
                '{"thought":"got result","answer":"pong"}',
            ]
        )
        agent._is_running = True

        result = await agent.execute_task("Echo ping")
        assert result == "pong"
        assert len(agent._llm.calls) == 2

    @pytest.mark.asyncio
    async def test_tool_result_in_second_prompt(self):
        """Tool result should appear in the history passed to the second LLM call."""
        agent = make_agent(tools=[EchoTool()])
        agent._llm = MockLLM(
            [
                '{"thought":"echo","tool":"echo","params":{"text":"hello"}}',
                '{"answer":"done"}',
            ]
        )
        agent._is_running = True

        await agent.execute_task("Echo hello")
        # Second prompt should contain the tool result
        second_prompt = agent._llm.calls[1]
        assert "hello" in second_prompt

    @pytest.mark.asyncio
    async def test_file_creation_via_react(self, tmp_path):
        """Full ReAct loop creates a real file via FileManagerTool."""
        target = str(tmp_path / "react_output.txt")
        agent = make_agent(tools=[FileManagerTool()])
        agent._llm = MockLLM(
            [
                json.dumps(
                    {
                        "thought": "create file",
                        "tool": "file_manager",
                        "params": {"action": "create_file", "path": target, "content": "hello"},
                    }
                ),
                '{"answer":"File created"}',
            ]
        )
        agent._is_running = True

        result = await agent.execute_task(f"Create a file at {target}")
        assert result == "File created"
        assert (tmp_path / "react_output.txt").read_text() == "hello"

    @pytest.mark.asyncio
    async def test_unknown_tool_continues_loop(self):
        """If LLM calls a non-existent tool, loop continues and LLM gets error feedback."""
        agent = make_agent()
        agent._llm = MockLLM(
            [
                '{"thought":"try","tool":"ghost","params":{}}',
                '{"answer":"recovered"}',
            ]
        )
        agent._is_running = True

        result = await agent.execute_task("Do something")
        assert result == "recovered"
        # Second prompt should mention the error
        assert "not found" in agent._llm.calls[1].lower() or "ghost" in agent._llm.calls[1]

    @pytest.mark.asyncio
    async def test_json_no_tool_no_answer_treated_as_answer(self):
        """JSON with neither 'tool' nor 'answer' key returns raw text."""
        agent = make_agent()
        raw = '{"thought":"hmm"}'
        agent._llm = MockLLM([raw])
        agent._is_running = True

        result = await agent.execute_task("Think")
        assert result == raw


# ── execute_task — direct dict call ──────────────────────────────────────────


class TestExecuteTaskDirect:
    @pytest.mark.asyncio
    async def test_direct_tool_call_via_dict(self):
        """Dict input bypasses LLM and calls tool directly via task queue."""
        agent = make_agent(tools=[EchoTool()])
        await agent.start()

        result = await agent.execute_task({"name": "echo", "params": {"text": "direct"}})
        assert result["echoed"] == "direct"

        await agent.stop()

    @pytest.mark.asyncio
    async def test_direct_call_unknown_tool(self):
        """Direct dict call with unknown tool returns error dict."""
        agent = make_agent()
        await agent.start()

        result = await agent.execute_task({"name": "ghost", "params": {}})
        assert result["success"] is False

        await agent.stop()


# ── send_message streaming prefix ────────────────────────────────────────────


class TestSendMessageStreaming:
    @pytest.mark.asyncio
    async def test_streaming_prefix_printed(self):
        """When stream=True, send_message prints '<name>: ' before tokens."""
        agent = make_agent(name="ALEX")
        agent._llm = MockLLM(["Hello there"])

        captured = StringIO()
        with patch("daie.core.llm_manager.get_llm_config") as mock_cfg:
            cfg = MagicMock()
            cfg.stream = True
            mock_cfg.return_value = cfg

            with patch("sys.stdout", captured):
                await agent.send_message("hi")

        output = captured.getvalue()
        assert "ALEX:" in output

    @pytest.mark.asyncio
    async def test_no_streaming_no_prefix(self):
        """When stream=False, send_message does NOT print the prefix."""
        agent = make_agent(name="ALEX")
        agent._llm = MockLLM(["Hello there"])

        captured = StringIO()
        with patch("daie.core.llm_manager.get_llm_config") as mock_cfg:
            cfg = MagicMock()
            cfg.stream = False
            mock_cfg.return_value = cfg

            with patch("sys.stdout", captured):
                result = await agent.send_message("hi")

        assert captured.getvalue() == ""
        assert result == "Hello there"

    @pytest.mark.asyncio
    async def test_send_message_returns_response(self):
        """send_message returns the LLM response string."""
        agent = make_agent()
        agent._llm = MockLLM(["Test response"])

        with patch("daie.core.llm_manager.get_llm_config") as mock_cfg:
            cfg = MagicMock()
            cfg.stream = False
            mock_cfg.return_value = cfg

            result = await agent.send_message("hello")

        assert result == "Test response"

    @pytest.mark.asyncio
    async def test_send_message_llm_error_returns_error_string(self):
        """LLM exception is caught and returned as error string."""
        agent = make_agent()

        class ErrorLLM:
            def invoke(self, *a, **kw):
                raise RuntimeError("LLM down")

        agent._llm = ErrorLLM()

        with patch("daie.core.llm_manager.get_llm_config") as mock_cfg:
            cfg = MagicMock()
            cfg.stream = False
            mock_cfg.return_value = cfg

            result = await agent.send_message("hello")

        assert "Error" in result


# ── @tool decorator integration ───────────────────────────────────────────────


class TestToolDecoratorIntegration:
    def test_tool_decorator_has_name(self):
        @tool(name="ping", description="Ping tool")
        async def ping() -> str:
            return "pong"

        assert ping.name == "ping"

    @pytest.mark.asyncio
    async def test_tool_decorator_execute(self):
        @tool(name="double", description="Double a number")
        async def double(n: str) -> str:
            return str(int(n) * 2)

        result = await double.execute({"n": "5"})
        assert result == "10"

    @pytest.mark.asyncio
    async def test_tool_decorator_in_agent_react(self):
        """@tool function works end-to-end through the ReAct loop."""

        @tool(name="shout", description="Shout text in uppercase")
        async def shout(text: str) -> str:
            return text.upper()

        agent = make_agent(tools=[shout])
        agent._llm = MockLLM(
            [
                '{"thought":"shout it","tool":"shout","params":{"text":"hello"}}',
                '{"answer":"HELLO"}',
            ]
        )
        agent._is_running = True

        result = await agent.execute_task("Shout hello")
        assert result == "HELLO"

    def test_tool_in_tools_block(self):
        @tool(name="mytool", description="My custom tool")
        async def mytool(x: str) -> str:
            return x

        agent = make_agent(tools=[mytool])
        block = agent._tools_block()
        assert "mytool" in block
        assert "My custom tool" in block
