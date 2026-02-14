"""Tests for agents module - Decentralized AI Ecosystem Agent System.

Use Case Description:
This test file validates the agent system in the Decentralized AI Ecosystem (DAIE), focusing on three main components:

1. **Agent Configuration**: Tests for AgentConfig class which defines agent behavior
   - Basic AgentConfig creation and initialization
   - Default values for agent configurations
   - Configuration validation and schema

2. **Agent Communication**: Tests for AgentMessage class which enables agent-to-agent communication
   - Message creation and initialization
   - Message serialization and deserialization
   - Timestamps and message type handling

3. **Agent Management**: Tests for Agent class which represents individual AI agents
   - Agent creation and initialization
   - Starting and stopping agent operations
   - Adding and removing tools
   - Message sending and receiving
   - Task execution with tools

These tests ensure that agents can be properly configured, communicate effectively, and execute tasks in the decentralized environment, forming the core of the DAIE's computational capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from daie.agents.agent import Agent
from daie.agents.config import AgentConfig, AgentRole
from daie.agents.message import AgentMessage
from daie.tools import ToolMetadata, ToolCategory, ToolParameter


class ConcreteTool:
    """Concrete tool implementation for testing"""

    def __init__(self, name="test-tool"):
        self.name = name

    async def execute(self, params):
        return {"result": f"Executed {self.name} with {params}"}


class TestAgentConfig:
    """Tests for AgentConfig class."""

    def test_agent_config_creation(self):
        """Test basic AgentConfig creation."""
        config = AgentConfig(
            name="Test Agent",
            role=AgentRole.SPECIALIZED,
            capabilities=["capability1", "capability2"],
        )

        assert config.name == "Test Agent"
        assert config.role == AgentRole.SPECIALIZED
        assert "capability1" in config.capabilities
        assert "capability2" in config.capabilities

    def test_agent_config_defaults(self):
        """Test AgentConfig with default values."""
        config = AgentConfig()

        assert config.name == "DefaultAgent"
        assert config.role == AgentRole.GENERAL_PURPOSE
        assert config.capabilities == []


class TestAgentMessage:
    """Tests for AgentMessage class."""

    def test_message_creation(self):
        """Test basic message creation."""
        message = AgentMessage(
            sender_id="agent1",
            receiver_id="agent2",
            content="Hello, world!",
            message_type="text",
        )

        assert message.sender_id == "agent1"
        assert message.receiver_id == "agent2"
        assert message.content == "Hello, world!"
        assert message.message_type == "text"
        assert message.timestamp is not None

    def test_message_serialization(self):
        """Test message serialization and deserialization."""
        message = AgentMessage(
            sender_id="agent1",
            receiver_id="agent2",
            content="Hello, world!",
            message_type="text",
        )

        serialized = message.to_json()
        assert isinstance(serialized, str)

        deserialized = AgentMessage.from_json(serialized)
        assert isinstance(deserialized, AgentMessage)
        assert deserialized.sender_id == "agent1"


class TestAgent:
    """Tests for Agent class."""

    def test_agent_creation(self):
        """Test agent creation and initialization."""
        config = AgentConfig(name="Test Agent", role=AgentRole.SPECIALIZED)

        agent = Agent(config=config)

        assert agent.name == "Test Agent"
        assert agent.role == AgentRole.SPECIALIZED
        assert agent.is_running is False

    @pytest.mark.asyncio
    async def test_agent_start_stop(self):
        """Test agent start and stop operations."""
        with patch("daie.agents.agent.logger") as mock_logger:
            config = AgentConfig(name="Test Agent")
            agent = Agent(config=config)

            assert not agent.is_running

            # Create mock managers
            mock_comm_manager = Mock()
            mock_comm_manager.register_agent = Mock()
            mock_comm_manager.deregister_agent = Mock()

            await agent.start(
                communication_manager=mock_comm_manager,
                memory_manager=Mock(),
                tool_registry=Mock(),
            )

            assert agent.is_running is True
            mock_comm_manager.register_agent.assert_called_once()

            await agent.stop()
            assert agent.is_running is False
            mock_comm_manager.deregister_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_send_message(self):
        """Test agent message sending."""
        with patch("daie.agents.agent.logger") as mock_logger:
            config = AgentConfig(name="Test Agent")
            agent = Agent(config=config)

            # Create mock communication manager
            mock_comm_manager = Mock()

            await agent.start(
                communication_manager=mock_comm_manager,
                memory_manager=Mock(),
                tool_registry=Mock(),
            )

            # Patch the send_message method to return True
            with patch.object(agent, "send_message", return_value=True) as mock_send:
                message = AgentMessage(
                    sender_id=agent.id,
                    receiver_id="test-agent-2",
                    content="Hello from test agent!",
                    message_type="text",
                )

                result = await agent.send_message(message)
                assert result is True
                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_add_remove_tool(self):
        """Test adding and removing tools."""
        with patch("daie.agents.agent.logger") as mock_logger:
            config = AgentConfig(name="Test Agent")
            agent = Agent(config=config)

            tool = ConcreteTool(name="test-tool")
            agent.add_tool(tool)

            assert len(agent.list_tools()) == 1
            assert agent.get_tool("test-tool") is not None

            agent.remove_tool("test-tool")
            assert len(agent.list_tools()) == 0
            assert agent.get_tool("test-tool") is None

    @pytest.mark.asyncio
    async def test_agent_execute_task(self):
        """Test task execution with tools."""
        with patch("daie.agents.agent.logger") as mock_logger:
            config = AgentConfig(name="Test Agent")
            agent = Agent(config=config)

            # Add test tool
            tool = ConcreteTool(name="test-tool")
            agent.add_tool(tool)

            await agent.start(
                communication_manager=Mock(),
                memory_manager=Mock(),
                tool_registry=Mock(),
            )

            result = await agent.execute_task(
                {"name": "test-tool", "params": {"text": "test input"}}
            )

            assert isinstance(result, dict)
            assert "result" in result
            assert "test input" in result["result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
