"""Test configuration and shared fixtures for all tests."""

import pytest
from unittest.mock import Mock, patch
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
