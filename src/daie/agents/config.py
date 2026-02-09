"""
Agent configuration module
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class AgentRole(Enum):
    """Agent role types"""
    GENERAL_PURPOSE = "general-purpose"
    SPECIALIZED = "specialized"
    WORKER = "worker"
    COORDINATOR = "coordinator"
    ANALYZER = "analyzer"
    EXECUTOR = "executor"


@dataclass
class AgentConfig:
    """
    Configuration for an AI agent
    
    This dataclass defines all the parameters needed to configure an agent,
    including identity, capabilities, communication settings, and behavior.
    
    Example:
    >>> config = AgentConfig(
    ...     name="MyAgent",
    ...     role=AgentRole.GENERAL_PURPOSE,
    ...     goal="Help users with their questions",
    ...     backstory="Created to assist with general questions and provide information",
    ...     system_prompt="You are a helpful AI assistant that provides accurate and friendly answers.",
    ...     capabilities=["web_search", "file_management"]
    ... )
    """
    
    # Agent identity
    name: str = "DefaultAgent"
    """Agent display name"""
    
    role: AgentRole = AgentRole.GENERAL_PURPOSE
    """Agent role type"""
    
    goal: str = "Perform general tasks"
    """Agent's main purpose or goal"""
    
    backstory: str = "Default AI agent"
    """Agent's backstory or origin story"""
    
    system_prompt: str = "You are a helpful AI agent that can assist with various tasks."
    """System prompt for the agent's behavior"""
    
    capabilities: List[str] = field(default_factory=list)
    """List of capabilities this agent supports"""
    
    # LLM settings
    llm_provider: str = "ollama"
    """LLM provider (openai, anthropic, ollama, etc.)"""
    
    llm_model: str = "llama3"
    """Default LLM model to use"""
    
    temperature: float = 0.7
    """LLM temperature parameter (0.0 to 1.0)"""
    
    max_tokens: int = 1000
    """Maximum tokens per LLM response"""
    
    # Communication settings
    communication_timeout: int = 30
    """Communication timeout in seconds"""
    
    heartbeat_interval: int = 10
    """Heartbeat interval in seconds"""
    
    max_reconnect_attempts: int = 5
    """Maximum number of reconnection attempts"""
    
    # Memory settings
    memory_retention_days: int = 30
    """Memory retention period in days"""
    
    max_memory_size: int = 1000
    """Maximum number of memory items to store"""
    
    # Behavior settings
    response_delay: float = 0.5
    """Delay before responding to messages in seconds"""
    
    max_concurrent_tasks: int = 5
    """Maximum number of concurrent tasks the agent can handle"""
    
    task_timeout: int = 60
    """Task timeout in seconds"""
    
    # Security settings
    require_encryption: bool = True
    """Whether to require encrypted communication"""
    
    verify_signatures: bool = True
    """Whether to verify message signatures"""
    
     # Performance settings
    enable_caching: bool = True
    """Whether to enable response caching"""
    
    cache_ttl: int = 3600
    """Cache TTL in seconds"""
    
    # Audio settings
    enable_audio_input: bool = False
    """Whether to enable microphone access for audio input (default: False)"""
    
    enable_audio_output: bool = False
    """Whether to enable speaker access for audio output (default: False)"""
    
    audio_device_index: int = -1
    """Audio device index to use (-1 for default device)"""
    
    audio_sample_rate: int = 16000
    """Audio sampling rate in Hz (default: 16000)"""
    
    audio_chunk_size: int = 1024
    """Audio chunk size for processing (default: 1024)"""
    
    # Camera settings
    enable_camera: bool = False
    """Whether to enable camera access for vision input (default: False)"""
    
    camera_device_index: int = 0
    """Camera device index to use (0 for default camera)"""
    
    camera_resolution: str = "640x480"
    """Camera resolution (width x height, default: 640x480)"""
    
    camera_fps: int = 30
    """Camera frames per second (default: 30)"""
    
    # Debug settings
    enable_logging: bool = True
    """Whether to enable detailed logging"""
    
    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR)"""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """
        Create an AgentConfig instance from a dictionary
        
        Args:
            data: Dictionary containing configuration values
            
        Returns:
            AgentConfig instance
        """
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                if key == "role" and isinstance(value, str):
                    value = AgentRole(value.lower())
                setattr(config, key, value)
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format
        
        Returns:
            Dictionary representation of configuration
        """
        data = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if isinstance(value, AgentRole):
                data[field_name] = value.value
            elif isinstance(value, (list, dict, str, int, float, bool)):
                data[field_name] = value
        return data
    
    def validate(self) -> List[str]:
        """
        Validate the configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Agent name cannot be empty")
            
        if not self.goal or len(self.goal.strip()) == 0:
            errors.append("Agent goal cannot be empty")
            
        if not self.system_prompt or len(self.system_prompt.strip()) == 0:
            errors.append("Agent system prompt cannot be empty")
            
        if self.communication_timeout <= 0:
            errors.append("Communication timeout must be positive")
            
        if self.heartbeat_interval <= 0:
            errors.append("Heartbeat interval must be positive")
            
        if self.max_reconnect_attempts < 0:
            errors.append("Max reconnect attempts cannot be negative")
            
        if self.memory_retention_days < 0:
            errors.append("Memory retention days cannot be negative")
            
        if self.max_memory_size <= 0:
            errors.append("Max memory size must be positive")
            
        if self.response_delay < 0:
            errors.append("Response delay cannot be negative")
            
        if self.max_concurrent_tasks <= 0:
            errors.append("Max concurrent tasks must be positive")
            
        if self.task_timeout <= 0:
            errors.append("Task timeout must be positive")
            
        if self.temperature < 0.0 or self.temperature > 1.0:
            errors.append("Temperature must be between 0.0 and 1.0")
            
        if self.max_tokens <= 0:
            errors.append("Max tokens must be positive")
            
        if self.cache_ttl <= 0 and self.enable_caching:
            errors.append("Cache TTL must be positive when caching is enabled")
            
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if self.log_level not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}")
            
        # Audio settings validation
        if self.audio_sample_rate <= 0:
            errors.append("Audio sample rate must be positive")
            
        if self.audio_chunk_size <= 0:
            errors.append("Audio chunk size must be positive")
            
        # Camera settings validation
        if self.camera_device_index < 0:
            errors.append("Camera device index cannot be negative")
            
        if self.camera_fps <= 0:
            errors.append("Camera FPS must be positive")
            
        # Validate camera resolution format (width x height)
        if self.camera_resolution:
            parts = self.camera_resolution.split('x')
            if len(parts) != 2:
                errors.append("Camera resolution must be in format 'widthxheight' (e.g., '640x480')")
            else:
                try:
                    width = int(parts[0])
                    height = int(parts[1])
                    if width <= 0 or height <= 0:
                        errors.append("Camera resolution dimensions must be positive")
                except ValueError:
                    errors.append("Camera resolution must contain numeric dimensions")
                    
        return errors
    
    def is_valid(self) -> bool:
        """
        Check if configuration is valid
        
        Returns:
            True if configuration is valid, False otherwise
        """
        return len(self.validate()) == 0
