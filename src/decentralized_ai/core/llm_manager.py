"""
LLM (Large Language Model) management module
"""

import logging
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import subprocess

logger = logging.getLogger(__name__)


class LLMType(Enum):
    """LLM provider types"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"


@dataclass
class LLMConfig:
    """LLM configuration"""
    llm_type: LLMType = LLMType.OLLAMA
    model_name: str = "llama3"
    temperature: float = 0.7
    max_tokens: int = 1000
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


class LLMManager:
    """
    Manager class for LLM instances
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if self._initialized:
            if config is not None:
                self.config = config
                self.llm = None
            return
            
        self._initialized = True
        self.config = config or LLMConfig()
        self.llm: Optional[Any] = None
        self._llm_cache: Dict[str, Any] = {}
        
        logger.info("LLM Manager initialized")
        
    def set_llm(
        self,
        llm_type: Optional[LLMType] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        ollama_llm: Optional[str] = None,
        **kwargs
    ) -> "LLMManager":
        """
        Set the LLM configuration
        
        Args:
            llm_type: LLM provider type
            model_name: Model name
            temperature: Temperature setting
            max_tokens: Maximum tokens per response
            api_key: API key
            base_url: Base URL for API calls
            ollama_llm: Ollama model name (convenience parameter)
            **kwargs: Additional parameters
            
        Returns:
            self for method chaining
        """
        
        # If ollama_llm is specified, set llm_type to Ollama and model_name to the value
        if ollama_llm is not None:
            llm_type = LLMType.OLLAMA
            model_name = ollama_llm
            
        if llm_type is not None:
            if isinstance(llm_type, str):
                llm_type = LLMType(llm_type.lower())
            self.config.llm_type = llm_type
            
        if model_name is not None:
            self.config.model_name = model_name
            
        if temperature is not None:
            self.config.temperature = temperature
            
        if max_tokens is not None:
            self.config.max_tokens = max_tokens
            
        if api_key is not None:
            self.config.api_key = api_key
            
        if base_url is not None:
            self.config.base_url = base_url
            
        if kwargs:
            self.config.additional_params.update(kwargs)
            
        # Clear cached LLM instance
        self.llm = None
        logger.info(f"LLM configuration updated: {self.config.llm_type.value}:{self.config.model_name}")
        
        return self
    
    def get_llm(self) -> Any:
        """
        Get the current LLM instance
        
        Returns:
            LLM instance
        """
        if self.llm is None:
            self.llm = self._create_llm()
            
        return self.llm
    
    def _create_llm(self) -> Any:
        """
        Create a new LLM instance based on configuration
        
        Returns:
            LLM instance
        """
        config_key = f"{self.config.llm_type.value}:{self.config.model_name}"
        
        if config_key in self._llm_cache:
            return self._llm_cache[config_key]
            
        logger.info(f"Creating LLM instance: {config_key}")
        
        try:
            if self.config.llm_type == LLMType.OLLAMA:
                llm = self._create_ollama_llm()
            elif self.config.llm_type == LLMType.OPENAI:
                llm = self._create_openai_llm()
            elif self.config.llm_type == LLMType.ANTHROPIC:
                llm = self._create_anthropic_llm()
            elif self.config.llm_type == LLMType.GOOGLE:
                llm = self._create_google_llm()
            elif self.config.llm_type == LLMType.AZURE:
                llm = self._create_azure_llm()
            else:
                raise ValueError(f"Unsupported LLM type: {self.config.llm_type}")
                
            self._llm_cache[config_key] = llm
            return llm
            
        except Exception as e:
            logger.error(f"Failed to create LLM instance: {e}")
            raise
    
    def _create_ollama_llm(self):
        """Create an Ollama LLM instance using direct API calls"""
        class OllamaLLM:
            """Simple Ollama LLM implementation using subprocess calls"""
            
            def __init__(self, config: LLMConfig):
                self.config = config
                
            def invoke(self, prompt: str, **kwargs) -> str:
                """Invoke the LLM with a prompt"""
                try:
                    # Use ollama CLI directly for simplicity
                    import subprocess
                    import json
                    
                    # Create message payload
                    messages = [
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ]
                    
                    payload = {
                        "model": self.config.model_name,
                        "messages": messages,
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    }
                    
                    # Call ollama API
                    result = subprocess.run(
                        ["ollama", "chat", "--format", "json"],
                        input=json.dumps(payload),
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    # Parse response
                    response = json.loads(result.stdout)
                    return response.get("message", {}).get("content", "")
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"Ollama command failed: {e}")
                    logger.error(f"Error output: {e.stderr}")
                    return f"Error: Failed to communicate with Ollama - {e}"
                except Exception as e:
                    logger.error(f"Ollama LLM error: {e}")
                    return f"Error: {e}"
        
        return OllamaLLM(self.config)
    
    def _create_openai_llm(self):
        """Create an OpenAI LLM instance using direct API calls"""
        class OpenAILLM:
            """Simple OpenAI LLM implementation using requests"""
            
            def __init__(self, config: LLMConfig):
                self.config = config
                
            def invoke(self, prompt: str, **kwargs) -> str:
                """Invoke the LLM with a prompt"""
                try:
                    import requests
                    
                    url = f"{self.config.base_url or 'https://api.openai.com'}/v1/chat/completions"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config.api_key}"
                    }
                    
                    payload = {
                        "model": self.config.model_name,
                        "messages": [
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    }
                    
                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                    
                except Exception as e:
                    logger.error(f"OpenAI LLM error: {e}")
                    return f"Error: {e}"
        
        return OpenAILLM(self.config)
    
    def _create_anthropic_llm(self):
        """Create an Anthropic LLM instance using direct API calls"""
        class AnthropicLLM:
            """Simple Anthropic LLM implementation using requests"""
            
            def __init__(self, config: LLMConfig):
                self.config = config
                
            def invoke(self, prompt: str, **kwargs) -> str:
                """Invoke the LLM with a prompt"""
                try:
                    import requests
                    
                    url = f"{self.config.base_url or 'https://api.anthropic.com'}/v1/messages"
                    headers = {
                        "Content-Type": "application/json",
                        "x-api-key": self.config.api_key
                    }
                    
                    payload = {
                        "model": self.config.model_name,
                        "messages": [
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    }
                    
                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    return data["content"][0]["text"]
                    
                except Exception as e:
                    logger.error(f"Anthropic LLM error: {e}")
                    return f"Error: {e}"
        
        return AnthropicLLM(self.config)
    
    def _create_google_llm(self):
        """Create a Google Cloud LLM instance using direct API calls"""
        class GoogleLLM:
            """Simple Google Cloud LLM implementation using requests"""
            
            def __init__(self, config: LLMConfig):
                self.config = config
                
            def invoke(self, prompt: str, **kwargs) -> str:
                """Invoke the LLM with a prompt"""
                try:
                    import requests
                    
                    # This is a simplified version - Google's API is more complex
                    logger.warning("Google LLM support is experimental")
                    return f"Google LLM response to: {prompt[:50]}..."
                    
                except Exception as e:
                    logger.error(f"Google LLM error: {e}")
                    return f"Error: {e}"
        
        return GoogleLLM(self.config)
    
    def _create_azure_llm(self):
        """Create an Azure OpenAI LLM instance using direct API calls"""
        class AzureLLM:
            """Simple Azure OpenAI LLM implementation using requests"""
            
            def __init__(self, config: LLMConfig):
                self.config = config
                
            def invoke(self, prompt: str, **kwargs) -> str:
                """Invoke the LLM with a prompt"""
                try:
                    import requests
                    
                    # Azure OpenAI API endpoint format: 
                    # https://{your-resource-name}.openai.azure.com/openai/deployments/{deployment-name}/chat/completions?api-version={api-version}
                    url = f"{self.config.base_url}/openai/deployments/{self.config.model_name}/chat/completions?api-version=2023-05-15"
                    headers = {
                        "Content-Type": "application/json",
                        "api-key": self.config.api_key
                    }
                    
                    payload = {
                        "messages": [
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    }
                    
                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                    
                except Exception as e:
                    logger.error(f"Azure LLM error: {e}")
                    return f"Error: {e}"
        
        return AzureLLM(self.config)
    
    async def async_invoke(self, prompt: str, **kwargs) -> str:
        """
        Asynchronous invoke method
        
        Args:
            prompt: Prompt to send to LLM
            **kwargs: Additional parameters
            
        Returns:
            LLM response
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_llm().invoke, prompt, **kwargs)


# Singleton instance
_llm_manager = LLMManager()


def get_llm_manager() -> LLMManager:
    """
    Get the global LLM manager instance
    
    Returns:
        LLMManager instance
    """
    return _llm_manager


def set_llm(
    llm_type: Optional[LLMType] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    ollama_llm: Optional[str] = None,
    **kwargs
):
    """
    Set LLM configuration on the global manager
    
    Args:
        llm_type: LLM provider type
        model_name: Model name
        temperature: Temperature setting
        max_tokens: Maximum tokens per response
        api_key: API key
        base_url: Base URL for API calls
        ollama_llm: Ollama model name (convenience parameter)
        **kwargs: Additional parameters
    """
    get_llm_manager().set_llm(
        llm_type=llm_type,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
        base_url=base_url,
        ollama_llm=ollama_llm,
        **kwargs
    )


def get_llm() -> Any:
    """
    Get the current LLM instance from the global manager
    
    Returns:
        LLM instance
    """
    return get_llm_manager().get_llm()
