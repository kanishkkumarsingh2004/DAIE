"""
Agent Node System - Environment Configuration
Decentralized AI Ecosystem

This module provides configuration management for the Agent Node System.
It loads configuration from environment variables and configuration files.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import os
import sys
from typing import Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EnvironmentConfig:
    """
    Configuration class for the Agent Node System
    
    This class loads configuration from environment variables with sensible defaults.
    Environment variables can override the default values.
    """
    
    # Central Core Connection Configuration
    CENTRAL_CORE_URL: str = os.environ.get("CENTRAL_CORE_URL", "http://localhost:8000")
    WEBSOCKET_URL: str = os.environ.get("WEBSOCKET_URL", "ws://localhost:8000/ws")
    
    # Agent Identity Configuration
    AGENT_ID: str = os.environ.get("AGENT_ID", "agent-001")
    AGENT_NAME: str = os.environ.get("AGENT_NAME", "My AI Agent")
    AGENT_ROLE: str = os.environ.get("AGENT_ROLE", "general-purpose")
    
    # Communication Configuration
    RECONNECT_INTERVAL: int = int(os.environ.get("RECONNECT_INTERVAL", 5))
    MESSAGE_TIMEOUT: int = int(os.environ.get("MESSAGE_TIMEOUT", 30))
    HEARTBEAT_INTERVAL: int = int(os.environ.get("HEARTBEAT_INTERVAL", 60))
    MAX_RETRY_COUNT: int = int(os.environ.get("MAX_RETRY_COUNT", 5))
    
    # Storage Configuration
    LOCAL_STORAGE_PATH: str = os.environ.get("LOCAL_STORAGE_PATH", "./local_storage")
    MAX_STORAGE_SIZE: int = int(os.environ.get("MAX_STORAGE_SIZE", 1073741824))  # 1GB
    
    # Performance Configuration
    MAX_CONCURRENT_TASKS: int = int(os.environ.get("MAX_CONCURRENT_TASKS", 5))
    CPU_USAGE_LIMIT: int = int(os.environ.get("CPU_USAGE_LIMIT", 70))
    RAM_USAGE_LIMIT: int = int(os.environ.get("RAM_USAGE_LIMIT", 80))
    
    # Debug Configuration
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() in ["true", "1", "yes"]
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    
    # Security Configuration
    ENCRYPTION_ENABLED: bool = os.environ.get("ENCRYPTION_ENABLED", "True").lower() in ["true", "1", "yes"]
    VERIFICATION_ENABLED: bool = os.environ.get("VERIFICATION_ENABLED", "True").lower() in ["true", "1", "yes"]
    TRUST_SCORE_MIN: float = float(os.environ.get("TRUST_SCORE_MIN", 0.5))
    
    # Memory Configuration
    MAX_WORKING_MEMORY_SIZE: int = int(os.environ.get("MAX_WORKING_MEMORY_SIZE", 100))
    MAX_CHAT_HISTORY_SIZE: int = int(os.environ.get("MAX_CHAT_HISTORY_SIZE", 500))
    MEMORY_CLEANUP_INTERVAL: int = int(os.environ.get("MEMORY_CLEANUP_INTERVAL", 3600))
    
    # Tool Configuration
    TOOL_EXECUTION_TIMEOUT: int = int(os.environ.get("TOOL_EXECUTION_TIMEOUT", 60))
    SANDBOX_ENABLED: bool = os.environ.get("SANDBOX_ENABLED", "True").lower() in ["true", "1", "yes"]
    MAX_CONCURRENT_TOOLS: int = int(os.environ.get("MAX_CONCURRENT_TOOLS", 3))
    
    # Network Configuration
    CONNECTION_TIMEOUT: int = int(os.environ.get("CONNECTION_TIMEOUT", 10))
    REQUEST_RETRIES: int = int(os.environ.get("REQUEST_RETRIES", 3))
    RETRY_DELAY: int = int(os.environ.get("RETRY_DELAY", 2))
    
    # Advanced Configuration
    ENABLE_P2P_COMMUNICATION: bool = os.environ.get("ENABLE_P2P_COMMUNICATION", "False").lower() in ["true", "1", "yes"]
    P2P_PORT: int = int(os.environ.get("P2P_PORT", 8001))
    P2P_DISCOVERY_ENABLED: bool = os.environ.get("P2P_DISCOVERY_ENABLED", "False").lower() in ["true", "1", "yes"]
    
    # Logging Configuration
    LOG_FILE: str = os.environ.get("LOG_FILE", "agent_node.log")
    LOG_MAX_SIZE: int = int(os.environ.get("LOG_MAX_SIZE", 10485760))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.environ.get("LOG_BACKUP_COUNT", 5))
    
    # System Configuration
    CHECK_SYSTEM_RESOURCES: bool = os.environ.get("CHECK_SYSTEM_RESOURCES", "True").lower() in ["true", "1", "yes"]
    SYSTEM_CHECK_INTERVAL: int = int(os.environ.get("SYSTEM_CHECK_INTERVAL", 300))
    
    @classmethod
    def get_config_dict(cls) -> dict:
        """Return all configuration settings as a dictionary"""
        return {
            "central_core_url": cls.CENTRAL_CORE_URL,
            "websocket_url": cls.WEBSOCKET_URL,
            "agent_id": cls.AGENT_ID,
            "agent_name": cls.AGENT_NAME,
            "agent_role": cls.AGENT_ROLE,
            "reconnect_interval": cls.RECONNECT_INTERVAL,
            "message_timeout": cls.MESSAGE_TIMEOUT,
            "heartbeat_interval": cls.HEARTBEAT_INTERVAL,
            "max_retry_count": cls.MAX_RETRY_COUNT,
            "local_storage_path": cls.LOCAL_STORAGE_PATH,
            "max_storage_size": cls.MAX_STORAGE_SIZE,
            "max_concurrent_tasks": cls.MAX_CONCURRENT_TASKS,
            "cpu_usage_limit": cls.CPU_USAGE_LIMIT,
            "ram_usage_limit": cls.RAM_USAGE_LIMIT,
            "debug": cls.DEBUG,
            "log_level": cls.LOG_LEVEL,
            "encryption_enabled": cls.ENCRYPTION_ENABLED,
            "verification_enabled": cls.VERIFICATION_ENABLED,
            "trust_score_min": cls.TRUST_SCORE_MIN,
            "max_working_memory_size": cls.MAX_WORKING_MEMORY_SIZE,
            "max_chat_history_size": cls.MAX_CHAT_HISTORY_SIZE,
            "memory_cleanup_interval": cls.MEMORY_CLEANUP_INTERVAL,
            "tool_execution_timeout": cls.TOOL_EXECUTION_TIMEOUT,
            "sandbox_enabled": cls.SANDBOX_ENABLED,
            "max_concurrent_tools": cls.MAX_CONCURRENT_TOOLS,
            "connection_timeout": cls.CONNECTION_TIMEOUT,
            "request_retries": cls.REQUEST_RETRIES,
            "retry_delay": cls.RETRY_DELAY,
            "enable_p2p_communication": cls.ENABLE_P2P_COMMUNICATION,
            "p2p_port": cls.P2P_PORT,
            "p2p_discovery_enabled": cls.P2P_DISCOVERY_ENABLED,
            "log_file": cls.LOG_FILE,
            "log_max_size": cls.LOG_MAX_SIZE,
            "log_backup_count": cls.LOG_BACKUP_COUNT,
            "check_system_resources": cls.CHECK_SYSTEM_RESOURCES,
            "system_check_interval": cls.SYSTEM_CHECK_INTERVAL
        }
    
    @classmethod
    def validate_config(cls) -> list[str]:
        """Validate configuration settings and return any errors"""
        errors = []
        
        # Validate required fields
        if not cls.CENTRAL_CORE_URL:
            errors.append("CENTRAL_CORE_URL is required")
        
        if not cls.AGENT_ID:
            errors.append("AGENT_ID is required")
        
        # Validate numeric values
        if cls.RECONNECT_INTERVAL < 1 or cls.RECONNECT_INTERVAL > 60:
            errors.append("RECONNECT_INTERVAL must be between 1 and 60 seconds")
        
        if cls.HEARTBEAT_INTERVAL < 10 or cls.HEARTBEAT_INTERVAL > 300:
            errors.append("HEARTBEAT_INTERVAL must be between 10 and 300 seconds")
        
        if cls.MESSAGE_TIMEOUT < 10 or cls.MESSAGE_TIMEOUT > 300:
            errors.append("MESSAGE_TIMEOUT must be between 10 and 300 seconds")
        
        if cls.MAX_CONCURRENT_TASKS < 1 or cls.MAX_CONCURRENT_TASKS > 20:
            errors.append("MAX_CONCURRENT_TASKS must be between 1 and 20")
        
        if cls.CPU_USAGE_LIMIT < 10 or cls.CPU_USAGE_LIMIT > 100:
            errors.append("CPU_USAGE_LIMIT must be between 10 and 100 percent")
        
        if cls.RAM_USAGE_LIMIT < 10 or cls.RAM_USAGE_LIMIT > 100:
            errors.append("RAM_USAGE_LIMIT must be between 10 and 100 percent")
        
        # Validate paths
        if cls.LOCAL_STORAGE_PATH:
            try:
                if not os.path.exists(cls.LOCAL_STORAGE_PATH):
                    os.makedirs(cls.LOCAL_STORAGE_PATH, exist_ok=True)
            except Exception as e:
                errors.append(f"Invalid LOCAL_STORAGE_PATH: {e}")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print configuration settings"""
        print("=" * 60)
        print("Agent Node System Configuration")
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
config_errors = EnvironmentConfig.validate_config()
if config_errors:
    print("Configuration Errors:")
    for error in config_errors:
        print(f"  - {error}")
    sys.exit(1)

if __name__ == "__main__":
    EnvironmentConfig.print_config()
