"""Test configuration and shared fixtures for all tests."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic_settings import BaseSettings


@pytest.fixture
def mock_settings():
    """Mock system settings for testing."""

    class MockSettings(BaseSettings):
        NATS_URL: str = "nats://localhost:4222"
        NATS_USERNAME: str = "test_user"
        NATS_PASSWORD: str = "test_password"
        LOG_LEVEL: str = "DEBUG"
        ENCRYPTION_KEY: str = "test_encryption_key_1234"

    return MockSettings()


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch("daie.utils.logger.setup_logger") as mock:
        logger = Mock()
        logger.info = Mock()
        logger.debug = Mock()
        logger.warning = Mock()
        logger.error = Mock()
        logger.critical = Mock()
        mock.return_value = logger
        yield logger


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager for testing."""
    with patch("daie.core.llm_manager.LLMManager") as mock:
        llm_manager = Mock()
        llm_manager.generate_response = Mock(return_value="Mock LLM response")
        mock.return_value = llm_manager
        yield llm_manager


@pytest.fixture
def mock_node():
    """Mock node for testing."""
    with patch("daie.core.node.Node") as mock:
        node = Mock()
        node.id = "test-node-1"
        node.name = "Test Node"
        node.start = Mock()
        node.stop = Mock()
        node.send_message = Mock()
        mock.return_value = node
        yield node


# ─── Async Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_communication_manager():
    """Mock CommunicationManager with async methods."""
    with patch("daie.communication.manager.CommunicationManager") as mock:
        comm = AsyncMock()
        comm._is_running = True
        comm.start = AsyncMock()
        comm.stop = AsyncMock()
        comm.send_message = AsyncMock(return_value=True)
        comm.broadcast_message = AsyncMock(return_value=1)
        comm.register_agent = Mock()
        comm.deregister_agent = Mock()
        comm.get_agent = Mock(return_value=None)
        comm.get_peer_info = Mock(return_value=None)
        comm.get_peers = Mock(return_value=[])
        comm.get_peer_count = Mock(return_value=0)
        comm.registry = Mock()
        comm.registry.get_network_topology = Mock(return_value={"nodes": {}, "connections": {}})
        comm.registry.get_connected_peers = Mock(return_value={})
        comm.registry.find_route = Mock(return_value=None)
        comm.registry.register_node = Mock()
        comm.registry.update_connections = Mock()
        comm.registry.start = AsyncMock()
        comm.registry.stop = AsyncMock()
        comm.nats = Mock()
        comm.nats.is_connected = True
        comm.nats.connect = AsyncMock()
        comm.nats.disconnect = AsyncMock()
        comm.nats.publish = AsyncMock(return_value=True)
        comm.nats.subscribe_agent = AsyncMock()
        mock.return_value = comm
        yield comm


@pytest.fixture
def mock_memory_manager():
    """Mock MemoryManager."""
    with patch("daie.memory.manager.MemoryManager") as mock:
        mem = Mock()
        mem.start = Mock()
        mem.stop = Mock()
        mem.initialize_agent_memory = Mock()
        mem.store_memory = Mock()
        mem.retrieve_memories = Mock(return_value=[])
        mem.search_similar = Mock(return_value=[])
        mem.clear_agent_memory = Mock()
        mem.get_memory_count = Mock(return_value=0)
        mem.log_chat_history = Mock()
        mock.return_value = mem
        yield mem


@pytest.fixture
def mock_tool_registry():
    """Mock ToolRegistry."""
    with patch("daie.tools.registry.ToolRegistry") as mock:
        reg = Mock()
        reg.register = Mock()
        reg.list_tools = Mock(return_value=[])
        reg.get_tool = Mock(return_value=None)
        mock.return_value = reg
        yield reg


@pytest.fixture
async def agent_with_mocks(mock_communication_manager, mock_memory_manager, mock_tool_registry):
    """Create an Agent with all mocks for testing."""
    from daie import Agent, AgentConfig
    from daie.agents import AgentRole

    config = AgentConfig(name="TestAgent", role=AgentRole.GENERAL_PURPOSE)
    agent = Agent(config=config)

    # Start with mocks
    await agent.start(
        communication_manager=mock_communication_manager,
        memory_manager=mock_memory_manager,
        tool_registry=mock_tool_registry,
    )

    yield agent

    # Cleanup
    await agent.stop()


@pytest.fixture
def mock_llm():
    """Mock LLM with invoke method."""
    with patch("daie.core.llm_manager.LLMManager.get_llm") as mock_get:
        llm = Mock()
        llm.invoke = Mock(return_value='{"thought": "test", "answer": "test answer"}')
        llm.last_usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        mock_get.return_value = llm
        yield llm


@pytest.fixture
def concrete_tool():
    """Concrete tool implementation for testing."""

    class ConcreteTool:
        def __init__(self, name="test-tool"):
            self.name = name
            self.description = f"Test tool: {name}"

        async def execute(self, params):
            return {"result": f"Executed {self.name} with {params}"}

    return ConcreteTool()


@pytest.fixture
def agent_config():
    """Basic agent config for testing."""
    from daie.agents.config import AgentConfig, AgentRole
    return AgentConfig(
        name="TestAgent",
        role=AgentRole.GENERAL_PURPOSE,
        goal="Test goal",
        backstory="Test backstory",
        system_prompt="You are a test agent.",
    )