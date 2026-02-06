"""
Central Core System - Configuration Settings
Decentralized AI Ecosystem

This module provides configuration management for the Central Core System.
It loads configuration from environment variables and configuration files.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import os
import sys
from typing import Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings:
    """
    Configuration class for the Central Core System
    
    This class loads configuration from environment variables with sensible defaults.
    Environment variables can override the default values.
    """
    
    # API Configuration
    API_HOST: str = os.environ.get("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.environ.get("API_PORT", 8000))
    API_DEBUG: bool = os.environ.get("API_DEBUG", "False").lower() in ["true", "1", "yes"]
    API_RELOAD: bool = os.environ.get("API_RELOAD", "False").lower() in ["true", "1", "yes"]
    API_WORKERS: int = int(os.environ.get("API_WORKERS", 4))
    
    # Security Configuration
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    # Database Configuration
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./central_core.db")
    DATABASE_ECHO: bool = os.environ.get("DATABASE_ECHO", "False").lower() in ["true", "1", "yes"]
    
    # Redis Configuration
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: str = os.environ.get("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.environ.get("REDIS_DB", 0))
    
    # CORS Configuration
    CORS_ORIGINS: list = os.environ.get("CORS_ORIGINS", ["*"]).split(",")
    
    # Logging Configuration
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.environ.get("LOG_FILE", "central_core.log")
    LOG_MAX_SIZE: int = int(os.environ.get("LOG_MAX_SIZE", 10485760))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.environ.get("LOG_BACKUP_COUNT", 5))
    
    # Agent Coordination Configuration
    MAX_AGENTS: int = int(os.environ.get("MAX_AGENTS", 1000))
    HEARTBEAT_INTERVAL: int = int(os.environ.get("HEARTBEAT_INTERVAL", 60))
    HEARTBEAT_TIMEOUT: int = int(os.environ.get("HEARTBEAT_TIMEOUT", 300))
    TASK_TIMEOUT: int = int(os.environ.get("TASK_TIMEOUT", 300))
    
    # LLM Configuration
    OLLAMA_HOST: str = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4-turbo-preview")
    EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Tool Configuration
    TOOL_EXECUTION_TIMEOUT: int = int(os.environ.get("TOOL_EXECUTION_TIMEOUT", 60))
    SANDBOX_ENABLED: bool = os.environ.get("SANDBOX_ENABLED", "True").lower() in ["true", "1", "yes"]
    MAX_CONCURRENT_TOOLS: int = int(os.environ.get("MAX_CONCURRENT_TOOLS", 5))
    
    # Memory Configuration
    CHROMA_DB_PATH: str = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
    MAX_KNOWLEDGE_SIZE: int = int(os.environ.get("MAX_KNOWLEDGE_SIZE", 100000))
    VECTOR_DIMENSION: int = int(os.environ.get("VECTOR_DIMENSION", 384))
    
    # Performance Configuration
    MAX_CONCURRENT_TASKS: int = int(os.environ.get("MAX_CONCURRENT_TASKS", 100))
    QUEUE_SIZE: int = int(os.environ.get("QUEUE_SIZE", 1000))
    PROCESSING_DELAY: float = float(os.environ.get("PROCESSING_DELAY", 0.1))
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = os.environ.get("ENABLE_METRICS", "True").lower() in ["true", "1", "yes"]
    METRICS_PORT: int = int(os.environ.get("METRICS_PORT", 9090))
    HEALTH_CHECK_INTERVAL: int = int(os.environ.get("HEALTH_CHECK_INTERVAL", 30))
    
    # Message Routing Configuration
    MESSAGE_ROUTER_TYPE: str = os.environ.get("MESSAGE_ROUTER_TYPE", "redis")
    ROUTER_CACHE_SIZE: int = int(os.environ.get("ROUTER_CACHE_SIZE", 1000))
    ROUTER_TTL: int = int(os.environ.get("ROUTER_TTL", 3600))
    
    # Task Dispatcher Configuration
    TASK_DISPATCHER_TYPE: str = os.environ.get("TASK_DISPATCHER_TYPE", "simple")
    DISPATCHER_PARALLELISM: int = int(os.environ.get("DISPATCHER_PARALLELISM", 10))
    
    # WebSocket Configuration
    WEBSOCKET_MAX_SIZE: int = int(os.environ.get("WEBSOCKET_MAX_SIZE", 1024 * 1024))  # 1MB
    WEBSOCKET_TIMEOUT: int = int(os.environ.get("WEBSOCKET_TIMEOUT", 600))
    
    @classmethod
    def get_config_dict(cls) -> dict:
        """Return all configuration settings as a dictionary"""
        return {
            "api_host": cls.API_HOST,
            "api_port": cls.API_PORT,
            "api_debug": cls.API_DEBUG,
            "api_reload": cls.API_RELOAD,
            "api_workers": cls.API_WORKERS,
            "secret_key": "[REDACTED]",
            "algorithm": cls.ALGORITHM,
            "access_token_expire_minutes": cls.ACCESS_TOKEN_EXPIRE_MINUTES,
            "database_url": cls.DATABASE_URL,
            "database_echo": cls.DATABASE_ECHO,
            "redis_url": cls.REDIS_URL,
            "cors_origins": cls.CORS_ORIGINS,
            "log_level": cls.LOG_LEVEL,
            "log_file": cls.LOG_FILE,
            "log_max_size": cls.LOG_MAX_SIZE,
            "log_backup_count": cls.LOG_BACKUP_COUNT,
            "max_agents": cls.MAX_AGENTS,
            "heartbeat_interval": cls.HEARTBEAT_INTERVAL,
            "heartbeat_timeout": cls.HEARTBEAT_TIMEOUT,
            "task_timeout": cls.TASK_TIMEOUT,
            "ollama_host": cls.OLLAMA_HOST,
            "openai_api_key": "[REDACTED]" if cls.OPENAI_API_KEY else "",
            "openai_model": cls.OPENAI_MODEL,
            "embedding_model": cls.EMBEDDING_MODEL,
            "tool_execution_timeout": cls.TOOL_EXECUTION_TIMEOUT,
            "sandbox_enabled": cls.SANDBOX_ENABLED,
            "max_concurrent_tools": cls.MAX_CONCURRENT_TOOLS,
            "chroma_db_path": cls.CHROMA_DB_PATH,
            "max_knowledge_size": cls.MAX_KNOWLEDGE_SIZE,
            "vector_dimension": cls.VECTOR_DIMENSION,
            "max_concurrent_tasks": cls.MAX_CONCURRENT_TASKS,
            "queue_size": cls.QUEUE_SIZE,
            "processing_delay": cls.PROCESSING_DELAY,
            "enable_metrics": cls.ENABLE_METRICS,
            "metrics_port": cls.METRICS_PORT,
            "health_check_interval": cls.HEALTH_CHECK_INTERVAL,
            "message_router_type": cls.MESSAGE_ROUTER_TYPE,
            "router_cache_size": cls.ROUTER_CACHE_SIZE,
            "router_ttl": cls.ROUTER_TTL,
            "task_dispatcher_type": cls.TASK_DISPATCHER_TYPE,
            "dispatcher_parallelism": cls.DISPATCHER_PARALLELISM,
            "websocket_max_size": cls.WEBSOCKET_MAX_SIZE,
            "websocket_timeout": cls.WEBSOCKET_TIMEOUT
        }
    
    @classmethod
    def validate_config(cls) -> list[str]:
        """Validate configuration settings and return any errors"""
        errors = []
        
        # Validate required fields
        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY is required")
        
        if len(cls.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")
        
        # Validate numeric values
        if cls.API_PORT < 1024 or cls.API_PORT > 65535:
            errors.append("API_PORT must be between 1024 and 65535")
        
        if cls.API_WORKERS < 1 or cls.API_WORKERS > 32:
            errors.append("API_WORKERS must be between 1 and 32")
        
        if cls.MAX_AGENTS < 1 or cls.MAX_AGENTS > 10000:
            errors.append("MAX_AGENTS must be between 1 and 10000")
        
        if cls.HEARTBEAT_INTERVAL < 10 or cls.HEARTBEAT_INTERVAL > 300:
            errors.append("HEARTBEAT_INTERVAL must be between 10 and 300 seconds")
        
        if cls.TASK_TIMEOUT < 60 or cls.TASK_TIMEOUT > 3600:
            errors.append("TASK_TIMEOUT must be between 60 and 3600 seconds")
        
        # Validate LLM configuration
        if not cls.OLLAMA_HOST and not cls.OPENAI_API_KEY:
            errors.append("Either OLLAMA_HOST or OPENAI_API_KEY must be configured")
        
        # Validate paths
        if cls.CHROMA_DB_PATH:
            try:
                if not os.path.exists(cls.CHROMA_DB_PATH):
                    os.makedirs(cls.CHROMA_DB_PATH, exist_ok=True)
            except Exception as e:
                errors.append(f"Invalid CHROMA_DB_PATH: {e}")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print configuration settings"""
        print("=" * 60)
        print("Central Core System Configuration")
        print("=" * 60)
        
        for key, value in cls.get_config_dict().items():
            print(f"{key:30} = {value}")
        
        print("=" * 60)
        
        errors = cls.validate_config()
        if errors:
            print("\nConfiguration Errors:")
            for error in errors:
                print(f"  - {error}")
        
        print(f"\nConfiguration Valid: {len(errors) == 0}")

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded configuration from .env file")
except ImportError:
    print("python-dotenv not installed, using environment variables only")

# Validate configuration on import
config_errors = Settings.validate_config()
if config_errors:
    print("Configuration Errors:")
    for error in config_errors:
        print(f"  - {error}")
    sys.exit(1)

if __name__ == "__main__":
    Settings.print_config()
