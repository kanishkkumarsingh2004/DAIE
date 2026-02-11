"""
System configuration module
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv


class LogLevel(Enum):
    """Logging levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SystemConfig:
    """
    System configuration for the Decentralized AI Ecosystem

    This dataclass holds all system-wide configuration parameters.

    Example:
    >>> from daie.config import SystemConfig

    >>> # Create default configuration
    >>> config = SystemConfig()

    >>> # Create custom configuration
    >>> config = SystemConfig(
    ...     log_level=LogLevel.DEBUG,
    ...     nats_url="nats://localhost:4222",
    ...     central_core_url="http://localhost:8000"
    ... )
    """

    # Logging configuration
    log_level: LogLevel = LogLevel.INFO
    """Logging level for the system"""

    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    """Logging format string"""

    log_file: Optional[str] = None
    """Path to log file (if None, logs to console)"""

    # Communication configuration
    nats_url: str = "nats://localhost:4222"
    """NATS JetStream server URL"""

    central_core_url: str = "http://localhost:3333"
    """Central core API URL"""

    websocket_url: str = "ws://localhost:3333/ws"
    """Websocket communication URL"""

    communication_timeout: int = 30
    """Communication timeout in seconds"""

    heartbeat_interval: int = 10
    """Heartbeat interval in seconds"""

    # Memory configuration
    memory_root_path: str = "./agent_memory"
    """Root directory for agent memory storage"""

    max_memory_items: int = 1000
    """Maximum number of memory items to store per agent"""

    memory_retention_days: int = 30
    """Memory retention period in days"""

    memory_storage_type: str = "file"
    """Type of memory storage (file, in-memory, redis, postgres)"""

    # Logging configuration
    enable_logging: bool = False
    """Whether to enable file logging (default: False)"""

    log_directory: str = "./logs"
    """Directory for log files"""

    # LLM configuration
    default_llm_model: str = "llama3"
    """Default LLM model to use"""

    llm_temperature: float = 0.7
    """LLM temperature parameter (0.0 to 1.0)"""

    llm_max_tokens: int = 1000
    """Maximum tokens per LLM response"""

    # Security configuration
    enable_encryption: bool = True
    """Whether to enable message encryption"""

    enable_signatures: bool = True
    """Whether to enable message signatures"""

    require_verification: bool = True
    """Whether to require agent verification"""

    # Performance configuration
    enable_caching: bool = True
    """Whether to enable response caching"""

    cache_ttl: int = 3600
    """Cache TTL in seconds"""

    max_concurrent_tasks: int = 10
    """Maximum number of concurrent tasks"""

    task_timeout: int = 60
    """Task timeout in seconds"""

    # Network configuration
    enable_p2p: bool = False
    """Whether to enable peer-to-peer communication"""

    discovery_interval: int = 60
    """Peer discovery interval in seconds"""

    connection_retries: int = 5
    """Maximum number of connection retries"""

    # Database configuration
    database_url: str = "sqlite:///:memory:"
    """Database connection URL"""

    redis_url: str = "redis://localhost:6379/0"
    """Redis connection URL"""

    # RAG (Retrieval-Augmented Generation) configuration
    rag_document_path: Optional[str] = None
    """Path to directory containing documents (PDF, TXT files) for RAG"""

    enable_rag: bool = False
    """Whether to enable RAG functionality"""

    # Monitoring configuration
    enable_metrics: bool = True
    """Whether to enable metrics collection"""

    prometheus_port: int = 3333
    """Prometheus metrics port"""

    enable_tracing: bool = False
    """Whether to enable distributed tracing"""

    @classmethod
    def from_env(cls) -> "SystemConfig":
        """
        Create a SystemConfig instance from environment variables

        Returns:
            SystemConfig instance initialized from environment variables
        """
        load_dotenv()

        config = cls()

        # Load from environment variables
        if os.getenv("LOG_LEVEL"):
            try:
                config.log_level = LogLevel(os.getenv("LOG_LEVEL").upper())
            except ValueError:
                pass

        if os.getenv("LOG_FORMAT"):
            config.log_format = os.getenv("LOG_FORMAT")

        if os.getenv("LOG_FILE"):
            config.log_file = os.getenv("LOG_FILE")

        if os.getenv("NATS_URL"):
            config.nats_url = os.getenv("NATS_URL")

        if os.getenv("CENTRAL_CORE_URL"):
            config.central_core_url = os.getenv("CENTRAL_CORE_URL")

        if os.getenv("WEBSOCKET_URL"):
            config.websocket_url = os.getenv("WEBSOCKET_URL")

        if os.getenv("COMMUNICATION_TIMEOUT"):
            try:
                config.communication_timeout = int(os.getenv("COMMUNICATION_TIMEOUT"))
            except ValueError:
                pass

        if os.getenv("HEARTBEAT_INTERVAL"):
            try:
                config.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL"))
            except ValueError:
                pass

        if os.getenv("MAX_MEMORY_ITEMS"):
            try:
                config.max_memory_items = int(os.getenv("MAX_MEMORY_ITEMS"))
            except ValueError:
                pass

        if os.getenv("MEMORY_RETENTION_DAYS"):
            try:
                config.memory_retention_days = int(os.getenv("MEMORY_RETENTION_DAYS"))
            except ValueError:
                pass

        if os.getenv("MEMORY_STORAGE_TYPE"):
            config.memory_storage_type = os.getenv("MEMORY_STORAGE_TYPE")

        if os.getenv("DEFAULT_LLM_MODEL"):
            config.default_llm_model = os.getenv("DEFAULT_LLM_MODEL")

        if os.getenv("LLM_TEMPERATURE"):
            try:
                config.llm_temperature = float(os.getenv("LLM_TEMPERATURE"))
            except ValueError:
                pass

        if os.getenv("LLM_MAX_TOKENS"):
            try:
                config.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS"))
            except ValueError:
                pass

        if os.getenv("ENABLE_ENCRYPTION"):
            config.enable_encryption = os.getenv("ENABLE_ENCRYPTION").lower() == "true"

        if os.getenv("ENABLE_SIGNATURES"):
            config.enable_signatures = os.getenv("ENABLE_SIGNATURES").lower() == "true"

        if os.getenv("REQUIRE_VERIFICATION"):
            config.require_verification = (
                os.getenv("REQUIRE_VERIFICATION").lower() == "true"
            )

        if os.getenv("ENABLE_CACHING"):
            config.enable_caching = os.getenv("ENABLE_CACHING").lower() == "true"

        if os.getenv("CACHE_TTL"):
            try:
                config.cache_ttl = int(os.getenv("CACHE_TTL"))
            except ValueError:
                pass

        if os.getenv("MAX_CONCURRENT_TASKS"):
            try:
                config.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS"))
            except ValueError:
                pass

        if os.getenv("TASK_TIMEOUT"):
            try:
                config.task_timeout = int(os.getenv("TASK_TIMEOUT"))
            except ValueError:
                pass

        if os.getenv("ENABLE_P2P"):
            config.enable_p2p = os.getenv("ENABLE_P2P").lower() == "true"

        if os.getenv("DISCOVERY_INTERVAL"):
            try:
                config.discovery_interval = int(os.getenv("DISCOVERY_INTERVAL"))
            except ValueError:
                pass

        if os.getenv("CONNECTION_RETRIES"):
            try:
                config.connection_retries = int(os.getenv("CONNECTION_RETRIES"))
            except ValueError:
                pass

        if os.getenv("DATABASE_URL"):
            config.database_url = os.getenv("DATABASE_URL")

        if os.getenv("REDIS_URL"):
            config.redis_url = os.getenv("REDIS_URL")

        if os.getenv("ENABLE_METRICS"):
            config.enable_metrics = os.getenv("ENABLE_METRICS").lower() == "true"

        if os.getenv("PROMETHEUS_PORT"):
            try:
                config.prometheus_port = int(os.getenv("PROMETHEUS_PORT"))
            except ValueError:
                pass

        if os.getenv("ENABLE_TRACING"):
            config.enable_tracing = os.getenv("ENABLE_TRACING").lower() == "true"

        if os.getenv("RAG_DOCUMENT_PATH"):
            config.rag_document_path = os.getenv("RAG_DOCUMENT_PATH")

        if os.getenv("ENABLE_RAG"):
            config.enable_rag = os.getenv("ENABLE_RAG").lower() == "true"

        return config

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemConfig":
        """
        Create a SystemConfig instance from a dictionary

        Args:
            data: Dictionary containing configuration values

        Returns:
            SystemConfig instance
        """
        config = cls()

        for key, value in data.items():
            if hasattr(config, key):
                if key == "log_level" and isinstance(value, str):
                    try:
                        value = LogLevel(value.upper())
                    except ValueError:
                        continue
                setattr(config, key, value)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format

        Returns:
            Dictionary representation of configuration
        """
        from dataclasses import fields

        data = {}

        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, LogLevel):
                data[field.name] = value.value
            elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
                data[field.name] = value

        return data

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the configuration

        Returns:
            Dictionary of validation errors
        """
        errors = {}

        # Validate log level
        if not isinstance(self.log_level, LogLevel):
            errors.setdefault("log_level", []).append("Must be a LogLevel enum")

        # Validate communication timeout
        if self.communication_timeout <= 0:
            errors.setdefault("communication_timeout", []).append("Must be positive")

        if self.heartbeat_interval <= 0:
            errors.setdefault("heartbeat_interval", []).append("Must be positive")

        # Validate memory settings
        if self.max_memory_items <= 0:
            errors.setdefault("max_memory_items", []).append("Must be positive")

        if self.memory_retention_days <= 0:
            errors.setdefault("memory_retention_days", []).append("Must be positive")

        # Validate LLM settings
        if self.llm_temperature < 0.0 or self.llm_temperature > 1.0:
            errors.setdefault("llm_temperature", []).append(
                "Must be between 0.0 and 1.0"
            )

        if self.llm_max_tokens <= 0:
            errors.setdefault("llm_max_tokens", []).append("Must be positive")

        # Validate performance settings
        if self.cache_ttl <= 0 and self.enable_caching:
            errors.setdefault("cache_ttl", []).append(
                "Must be positive when caching is enabled"
            )

        if self.max_concurrent_tasks <= 0:
            errors.setdefault("max_concurrent_tasks", []).append("Must be positive")

        if self.task_timeout <= 0:
            errors.setdefault("task_timeout", []).append("Must be positive")

        # Validate network settings
        if self.discovery_interval <= 0:
            errors.setdefault("discovery_interval", []).append("Must be positive")

        if self.connection_retries < 0:
            errors.setdefault("connection_retries", []).append("Cannot be negative")

        # Validate RAG settings
        if self.rag_document_path is not None:
            import os

            if not os.path.isdir(self.rag_document_path):
                errors.setdefault("rag_document_path", []).append(
                    "Must be a valid directory path"
                )
            elif not os.path.exists(self.rag_document_path):
                errors.setdefault("rag_document_path", []).append(
                    "Directory does not exist"
                )

        return errors

    def is_valid(self) -> bool:
        """
        Check if configuration is valid

        Returns:
            True if configuration is valid, False otherwise
        """
        return len(self.validate()) == 0
