"""
LLM (Large Language Model) management module
"""

import logging
from daie.core.tracing import trace_span
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMType(Enum):
    """LLM provider types"""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    OPENROUTER = "openrouter"


@dataclass
class LLMConfig:
    """LLM configuration"""

    llm_type: LLMType = LLMType.OLLAMA
    model_name: str = "llama3.2:latest"
    temperature: float = 0.7
    max_tokens: int = 1024
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    stream: bool = False
    """Whether to stream tokens as they are generated (default: False)"""
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

    async def initialize(self) -> "LLMManager":
        """
        Initialize the LLM manager - creates the LLM instance

        Returns:
            self for method chaining
        """
        # Pre-create the LLM instance to ensure it's available
        self.get_llm()
        logger.info(f"LLM initialized: {self.config.llm_type.value}:{self.config.model_name}")
        return self

    def set_llm(
        self,
        llm_type: Optional[LLMType] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        ollama_llm: Optional[str] = None,
        stream: Optional[bool] = None,
        **kwargs,
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
            stream: Whether to stream tokens as they are generated
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

        if stream is not None:
            self.config.stream = stream

        if kwargs:
            self.config.additional_params.update(kwargs)

        # Clear cached LLM instance
        self.llm = None
        logger.info(
            f"LLM configuration updated: {self.config.llm_type.value}:{self.config.model_name}"
        )

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
            elif self.config.llm_type == LLMType.OPENROUTER:
                llm = self._create_openrouter_llm()
            else:
                raise ValueError(f"Unsupported LLM type: {self.config.llm_type}")

            self._llm_cache[config_key] = llm
            return llm

        except Exception as e:
            logger.error(f"Failed to create LLM instance: {e}")
            raise

    def _create_ollama_llm(self):
        """Create an Ollama LLM instance using HTTP API"""

        class OllamaLLM:
            """Ollama LLM implementation with streaming support"""

            def __init__(self, config: LLMConfig):
                self.config = config
                self.base_url = config.base_url or "http://localhost:11434"
                # Reuse session for better performance
                self._session = None
                from daie.utils import http_client

                self._session = http_client.Session()
                self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            def _get_session(self):
                """Get the session for API calls"""
                return self._session

            @trace_span("llm_invoke")
            def invoke(
                self,
                prompt: str,
                stream: Optional[bool] = None,
                images: Optional[List[str]] = None,
                **kwargs,
            ) -> str:
                """
                Invoke the LLM with a prompt

                Args:
                    prompt: The prompt to send to the LLM
                    stream: Override streaming behaviour. If None, uses config.stream.
                    images: List of base64-encoded images (optional)
                    **kwargs: Additional parameters

                Returns:
                    Complete response as string
                """
                use_stream = self.config.stream if stream is None else stream
                if use_stream:
                    return self._invoke_stream(prompt, images=images, **kwargs)
                else:
                    return self._invoke_non_stream(prompt, images=images, **kwargs)

            def _invoke_non_stream(
                self, prompt: str, images: Optional[List[str]] = None, **kwargs
            ) -> str:
                """Non-streaming invocation"""
                try:
                    pass

                    session = self._get_session()

                    # Create message payload
                    messages = [{"role": "user", "content": prompt}]
                    if images:
                        messages[0]["images"] = images

                    payload = {
                        "model": self.config.model_name,
                        "messages": messages,
                        "temperature": self.config.temperature,
                        "stream": False,  # Disable streaming for simpler parsing
                    }

                    # Add max_tokens and Phase 3 acceleration options
                    options = {}
                    if self.config.max_tokens:
                        options["num_predict"] = self.config.max_tokens

                    from daie.config import SystemConfig

                    sys_cfg = SystemConfig()
                    if sys_cfg.gpu_layers > 0:
                        options["num_gpu"] = sys_cfg.gpu_layers
                    if sys_cfg.num_threads > 0:
                        options["num_thread"] = sys_cfg.num_threads

                    if options:
                        payload["options"] = options

                    # Call ollama API
                    response = session.post(
                        f"{self.base_url}/api/chat", json=payload, timeout=300.0
                    )

                    # Parse response
                    if response.status_code == 200:
                        data = response.json()

                        # Update usage stats
                        self.last_usage = {
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                            "total_tokens": data.get("prompt_eval_count", 0)
                            + data.get("eval_count", 0),
                        }

                        if "message" in data and "content" in data["message"]:
                            return data["message"]["content"]

                        logger.error(
                            f"Ollama API returned unexpected format: {response.text[:200]}"
                        )
                        return "Error: Failed to parse Ollama response format"

                    else:
                        logger.error(f"Ollama API error: Status code {response.status_code}")
                        logger.error(f"Error response: {response.text[:200]}")
                        return f"Error: Failed to communicate with Ollama (Status: {response.status_code})"

                except Exception as e:
                    from daie.utils import http_client as requests

                    if isinstance(e, requests.exceptions.ConnectionError):
                        logger.error("Ollama connection error: Could not connect to server")
                        return "Error: Could not connect to Ollama server. Is it running?"
                    elif isinstance(e, requests.exceptions.Timeout):
                        logger.error("Ollama timeout error: Request timed out")
                        return "Error: Request timed out. Ollama may be taking too long to respond."
                    else:
                        logger.error(f"Ollama LLM error: {e}")
                        return f"Error: {e}"

            def _invoke_stream(
                self, prompt: str, images: Optional[List[str]] = None, **kwargs
            ) -> str:
                """Streaming invocation with token-by-token display"""
                try:
                    import json
                    import sys

                    session = self._get_session()

                    # Create message payload
                    messages = [{"role": "user", "content": prompt}]
                    if images:
                        messages[0]["images"] = images

                    payload = {
                        "model": self.config.model_name,
                        "messages": messages,
                        "temperature": self.config.temperature,
                        "stream": True,
                    }

                    # Add max_tokens if supported
                    if self.config.max_tokens:
                        payload["options"] = {"num_predict": self.config.max_tokens}

                    # Call ollama API with streaming
                    response = session.post(
                        f"{self.base_url}/api/chat", json=payload, stream=True, timeout=300.0
                    )

                    if response.status_code != 200:
                        try:
                            err_msg = response.json().get("error", response.text)
                        except Exception:
                            err_msg = response.text
                        return (
                            f"Error: Ollama API returned status {response.status_code} - {err_msg}"
                        )

                    full_response = ""

                    # Process streaming responses
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8").strip()
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    token = data["message"]["content"]
                                    full_response += token
                                    sys.stdout.write(token)
                                    sys.stdout.flush()
                            except json.JSONDecodeError:
                                continue

                    print()  # New line after streaming completes
                    return full_response

                except Exception as e:
                    from daie.utils import http_client as requests

                    if isinstance(e, requests.exceptions.ConnectionError):
                        logger.error("Ollama connection error: Could not connect to server")
                        return "Error: Could not connect to Ollama server. Is it running?"
                    elif isinstance(e, requests.exceptions.Timeout):
                        logger.error("Ollama timeout error: Request timed out")
                        return "Error: Request timed out. Ollama may be taking too long to respond."
                    else:
                        logger.error(f"Ollama LLM error: {e}")
                        return f"Error: {e}"

            def __del__(self):
                """Cleanup session on deletion"""
                if self._session:
                    self._session.close()

        return OllamaLLM(self.config)

    def _create_openai_llm(self):
        """Create an OpenAI LLM instance using direct API calls"""

        class OpenAILLM:
            """OpenAI LLM implementation with streaming support"""

            def __init__(self, config: LLMConfig):
                self.config = config
                self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            @trace_span("llm_invoke")
            def invoke(self, prompt: str, stream: Optional[bool] = None, **kwargs) -> str:
                """
                Invoke the LLM with a prompt

                Args:
                    prompt: The prompt to send to the LLM
                    stream: Override streaming behaviour. If None, uses config.stream.
                    **kwargs: Additional parameters

                Returns:
                    Complete response as string
                """
                use_stream = self.config.stream if stream is None else stream
                if use_stream:
                    return self._invoke_stream(prompt, **kwargs)
                else:
                    return self._invoke_non_stream(prompt, **kwargs)

            def _invoke_non_stream(self, prompt: str, **kwargs) -> str:
                """Non-streaming invocation"""
                try:
                    from daie.utils import http_client as requests

                    url = f"{self.config.base_url or 'https://api.openai.com'}/v1/chat/completions"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config.api_key}",
                    }

                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                    }

                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()

                    data = response.json()

                    # Update usage stats
                    usage = data.get("usage", {})
                    self.last_usage = {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    }

                    return data["choices"][0]["message"]["content"]

                except Exception as e:
                    logger.error(f"OpenAI LLM error: {e}")
                    return f"Error: {e}"

            def _invoke_stream(self, prompt: str, **kwargs) -> str:
                """Streaming invocation with token-by-token display"""
                try:
                    import json
                    import sys

                    from daie.utils import http_client as requests

                    url = f"{self.config.base_url or 'https://api.openai.com'}/v1/chat/completions"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config.api_key}",
                    }

                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "stream": True,
                    }

                    response = requests.post(url, headers=headers, json=payload, stream=True)
                    response.raise_for_status()

                    full_response = ""

                    # Process streaming responses
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if "choices" in data and data["choices"]:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            token = delta["content"]
                                            full_response += token
                                            sys.stdout.write(token)
                                            sys.stdout.flush()
                                except json.JSONDecodeError:
                                    continue

                    return full_response

                except Exception as e:
                    logger.error(f"OpenAI LLM error: {e}")
                    return f"Error: {e}"

        return OpenAILLM(self.config)

    def _create_anthropic_llm(self):
        """Create an Anthropic LLM instance using direct API calls"""

        class AnthropicLLM:
            """Anthropic LLM implementation with streaming support"""

            def __init__(self, config: LLMConfig):
                self.config = config
                self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            def invoke(self, prompt: str, stream: Optional[bool] = None, **kwargs) -> str:
                """
                Invoke the LLM with a prompt

                Args:
                    prompt: The prompt to send to the LLM
                    stream: Override streaming behaviour. If None, uses config.stream.
                    **kwargs: Additional parameters

                Returns:
                    Complete response as string
                """
                use_stream = self.config.stream if stream is None else stream
                if use_stream:
                    return self._invoke_stream(prompt, **kwargs)
                else:
                    return self._invoke_non_stream(prompt, **kwargs)

            def _invoke_non_stream(self, prompt: str, **kwargs) -> str:
                """Non-streaming invocation"""
                try:
                    from daie.utils import http_client as requests

                    url = f"{self.config.base_url or 'https://api.anthropic.com'}/v1/messages"
                    headers = {
                        "Content-Type": "application/json",
                        "x-api-key": self.config.api_key,
                    }

                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                    }

                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()

                    data = response.json()

                    # Update usage stats
                    usage = data.get("usage", {})
                    self.last_usage = {
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0)
                        + usage.get("output_tokens", 0),
                    }

                    return data["content"][0]["text"]

                except Exception as e:
                    logger.error(f"Anthropic LLM error: {e}")
                    return f"Error: {e}"

            def _invoke_stream(self, prompt: str, **kwargs) -> str:
                """Streaming invocation with token-by-token display"""
                try:
                    import json
                    import sys

                    from daie.utils import http_client as requests

                    url = f"{self.config.base_url or 'https://api.anthropic.com'}/v1/messages"
                    headers = {
                        "Content-Type": "application/json",
                        "x-api-key": self.config.api_key,
                    }

                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "stream": True,
                    }

                    response = requests.post(url, headers=headers, json=payload, stream=True)
                    response.raise_for_status()

                    full_response = ""

                    # Process streaming responses
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if "delta" in data and "text" in data["delta"]:
                                        token = data["delta"]["text"]
                                        full_response += token
                                        sys.stdout.write(token)
                                        sys.stdout.flush()
                                except json.JSONDecodeError:
                                    continue

                    print()  # New line after streaming completes
                    return full_response

                except Exception as e:
                    logger.error(f"Anthropic LLM error: {e}")
                    return f"Error: {e}"

        return AnthropicLLM(self.config)

    def _create_google_llm(self):
        """Create a Google Cloud LLM instance using direct API calls"""

        class GoogleLLM:
            """Google Cloud LLM implementation with streaming support"""

            def __init__(self, config: LLMConfig):
                self.config = config

            def invoke(self, prompt: str, stream: Optional[bool] = None, **kwargs) -> str:
                """
                Invoke the LLM with a prompt

                Args:
                    prompt: The prompt to send to the LLM
                    stream: Override streaming behaviour. If None, uses config.stream.
                    **kwargs: Additional parameters

                Returns:
                    Complete response as string
                """
                use_stream = self.config.stream if stream is None else stream
                if use_stream:
                    return self._invoke_stream(prompt, **kwargs)
                else:
                    return self._invoke_non_stream(prompt, **kwargs)

            def _invoke_non_stream(self, prompt: str, **kwargs) -> str:
                """Non-streaming invocation using Google Gemini API"""
                try:
                    from daie.utils import http_client as requests

                    # Gemini API endpoint
                    api_key = self.config.api_key
                    model = self.config.model_name or "gemini-pro"
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": self.config.temperature,
                            "maxOutputTokens": self.config.max_tokens or 2048,
                        },
                    }

                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()

                    data = response.json()

                    # Extract text from Gemini response structure
                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            return candidate["content"]["parts"][0]["text"]

                    logger.error(f"Google API returned unexpected format: {data}")
                    return "Error: Failed to parse Google Gemini response"

                except Exception as e:
                    logger.error(f"Google LLM error: {e}")
                    return f"Error: {e}"

            def _invoke_stream(self, prompt: str, **kwargs) -> str:
                """Streaming invocation (simulated for now as Gemini stream is different)"""
                # For now, fallback to non-stream but log it
                logger.debug("Google Gemini streaming is handled as non-streaming in this version")
                return self._invoke_non_stream(prompt, **kwargs)

        return GoogleLLM(self.config)

    def _create_azure_llm(self):
        """Create an Azure OpenAI LLM instance using direct API calls"""

        class AzureLLM:
            """Azure OpenAI LLM implementation with streaming support"""

            def __init__(self, config: LLMConfig):
                self.config = config

            def invoke(self, prompt: str, stream: Optional[bool] = None, **kwargs) -> str:
                """
                Invoke the LLM with a prompt

                Args:
                    prompt: The prompt to send to the LLM
                    stream: Override streaming behaviour. If None, uses config.stream.
                    **kwargs: Additional parameters

                Returns:
                    Complete response as string
                """
                use_stream = self.config.stream if stream is None else stream
                if use_stream:
                    return self._invoke_stream(prompt, **kwargs)
                else:
                    return self._invoke_non_stream(prompt, **kwargs)

            def _invoke_non_stream(self, prompt: str, **kwargs) -> str:
                """Non-streaming invocation"""
                try:
                    from daie.utils import http_client as requests

                    # Azure OpenAI API endpoint format:
                    # https://{your-resource-name}.openai.azure.com/openai/deployments/{deployment-name}/chat/completions?api-version={api-version}
                    url = f"{self.config.base_url}/openai/deployments/{self.config.model_name}/chat/completions?api-version=2023-05-15"
                    headers = {
                        "Content-Type": "application/json",
                        "api-key": self.config.api_key,
                    }

                    payload = {
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                    }

                    response = requests.post(url, headers=headers, json=payload)
                    response.raise_for_status()

                    data = response.json()
                    return data["choices"][0]["message"]["content"]

                except Exception as e:
                    logger.error(f"Azure LLM error: {e}")
                    return f"Error: {e}"

            def _invoke_stream(self, prompt: str, **kwargs) -> str:
                """Streaming invocation with token-by-token display"""
                try:
                    import json
                    import sys

                    from daie.utils import http_client as requests

                    # Azure OpenAI API endpoint format:
                    # https://{your-resource-name}.openai.azure.com/openai/deployments/{deployment-name}/chat/completions?api-version={api-version}
                    url = f"{self.config.base_url}/openai/deployments/{self.config.model_name}/chat/completions?api-version=2023-05-15"
                    headers = {
                        "Content-Type": "application/json",
                        "api-key": self.config.api_key,
                    }

                    payload = {
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "stream": True,
                    }

                    response = requests.post(url, headers=headers, json=payload, stream=True)
                    response.raise_for_status()

                    full_response = ""

                    # Process streaming responses
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if "choices" in data and data["choices"]:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            token = delta["content"]
                                            full_response += token
                                            sys.stdout.write(token)
                                            sys.stdout.flush()
                                except json.JSONDecodeError:
                                    continue

                    print()  # New line after streaming completes
                    return full_response

                except Exception as e:
                    logger.error(f"Azure LLM error: {e}")
                    return f"Error: {e}"

        return AzureLLM(self.config)

    def _create_openrouter_llm(self):
        """Create an OpenRouter LLM instance using direct API calls"""

        class OpenRouterLLM:
            """OpenRouter LLM implementation with streaming support"""

            def __init__(self, config: LLMConfig):
                self.config = config

            def invoke(self, prompt: str, stream: Optional[bool] = None, **kwargs) -> str:
                """
                Invoke the LLM with a prompt

                Args:
                    prompt: The prompt to send to the LLM
                    stream: Override streaming behaviour. If None, uses config.stream.
                    **kwargs: Additional parameters

                Returns:
                    Complete response as string
                """
                use_stream = self.config.stream if stream is None else stream
                if use_stream:
                    return self._invoke_stream(prompt, **kwargs)
                else:
                    return self._invoke_non_stream(prompt, **kwargs)

            def _invoke_non_stream(self, prompt: str, **kwargs) -> str:
                """Non-streaming invocation"""
                try:
                    import json

                    from daie.utils import http_client as requests

                    url = (
                        f"{self.config.base_url or 'https://openrouter.ai'}/api/v1/chat/completions"
                    )
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config.api_key}",
                        "HTTP-Referer": self.config.additional_params.get("referer", ""),
                        "X-Title": self.config.additional_params.get("title", ""),
                    }

                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                    }

                    # Add additional parameters if present
                    if self.config.additional_params:
                        for key, value in self.config.additional_params.items():
                            if key not in ["referer", "title"] and key not in payload:
                                payload[key] = value

                    response = requests.post(url, headers=headers, data=json.dumps(payload))
                    response.raise_for_status()

                    data = response.json()
                    return data["choices"][0]["message"]["content"]

                except Exception as e:
                    logger.error(f"OpenRouter LLM error: {e}")
                    return f"Error: {e}"

            def _invoke_stream(self, prompt: str, **kwargs) -> str:
                """Streaming invocation with token-by-token display"""
                try:
                    import json
                    import sys

                    from daie.utils import http_client as requests

                    url = (
                        f"{self.config.base_url or 'https://openrouter.ai'}/api/v1/chat/completions"
                    )
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.config.api_key}",
                        "HTTP-Referer": self.config.additional_params.get("referer", ""),
                        "X-Title": self.config.additional_params.get("title", ""),
                    }

                    payload = {
                        "model": self.config.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "stream": True,
                    }

                    # Add additional parameters if present
                    if self.config.additional_params:
                        for key, value in self.config.additional_params.items():
                            if key not in ["referer", "title"] and key not in payload:
                                payload[key] = value

                    response = requests.post(
                        url, headers=headers, data=json.dumps(payload), stream=True
                    )
                    response.raise_for_status()

                    full_response = ""

                    # Process streaming responses
                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    if "choices" in data and data["choices"]:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            token = delta["content"]
                                            full_response += token
                                            sys.stdout.write(token)
                                            sys.stdout.flush()
                                except json.JSONDecodeError:
                                    continue

                    print()  # New line after streaming completes
                    return full_response

                except Exception as e:
                    logger.error(f"OpenRouter LLM error: {e}")
                    return f"Error: {e}"

        return OpenRouterLLM(self.config)

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
        import functools

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, functools.partial(self.get_llm().invoke, prompt, **kwargs)
        )


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
    stream: Optional[bool] = None,
    **kwargs,
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
        stream: Enable token streaming (default: False)
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
        stream=stream,
        **kwargs,
    )


def get_llm() -> Any:
    """
    Get the current LLM instance from the global manager

    Returns:
        LLM instance
    """
    return get_llm_manager().get_llm()


def get_llm_config() -> LLMConfig:
    """
    Get the current LLM configuration from the global manager

    Returns:
        LLMConfig instance
    """
    return get_llm_manager().config


def reset_llm_config() -> None:
    """
    Reset the LLM configuration to default values
    """
    get_llm_manager().config = LLMConfig()
    get_llm_manager().llm = None
