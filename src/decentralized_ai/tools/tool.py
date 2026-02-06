"""
Base tool class and tool creation API
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Tool categories for classification"""
    GENERAL = "general"
    SEARCH = "search"
    FILE = "file"
    SYSTEM = "system"
    WEB = "web"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"


@dataclass
class ToolParameter:
    """Parameter definition for tools"""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None


@dataclass
class ToolMetadata:
    """Tool metadata"""
    name: str
    description: str
    category: ToolCategory = ToolCategory.GENERAL
    version: str = "1.0.0"
    author: str = "Unknown"
    capabilities: List[str] = field(default_factory=list)
    parameters: List[ToolParameter] = field(default_factory=list)


class Tool(ABC):
    """
    Base class for all tools in the Decentralized AI Ecosystem

    This abstract base class defines the interface that all tools must implement.
    Tools are reusable components that agents can use to perform specific tasks.

    Example:
    >>> from decentralized_ai.tools import Tool, ToolCategory, ToolParameter
    >>> from decentralized_ai.tools import ToolMetadata

    >>> class WebSearchTool(Tool):
    ...     def __init__(self):
    ...         metadata = ToolMetadata(
    ...             name="web_search",
    ...             description="Search the web for information",
    ...             category=ToolCategory.SEARCH,
    ...             parameters=[
    ...                 ToolParameter(
    ...                     name="query",
    ...                     type="string",
    ...                     description="Search query text",
    ...                     required=True
    ...                 ),
    ...                 ToolParameter(
    ...                     name="num_results",
    ...                     type="integer",
    ...                     description="Number of results to return",
    ...                     required=False,
    ...                     default=5
    ...                 )
    ...             ]
    ...         )
    ...         super().__init__(metadata)
    ...
    ...     async def execute(self, params: Dict[str, Any]) -> Any:
    ...         query = params.get("query")
    ...         num_results = params.get("num_results", 5)
    ...         # Implement search functionality
    ...         return {"results": [f"Result {i} for {query}" for i in range(num_results)]}

    >>> # Create and use the tool
    >>> search_tool = WebSearchTool()
    >>> result = await search_tool.execute({"query": "Python programming", "num_results": 3})
    """

    def __init__(self, metadata: ToolMetadata):
        """
        Initialize a tool instance

        Args:
            metadata: Tool metadata
        """
        self.metadata = metadata
        self._is_initialized = False
        self._validation_errors: List[str] = []

        # Validate the tool metadata
        self._validate_metadata()
        if self._validation_errors:
            logger.warning(f"Tool {metadata.name} has validation errors: {self._validation_errors}")

    @property
    def name(self) -> str:
        """Get tool name"""
        return self.metadata.name

    @property
    def description(self) -> str:
        """Get tool description"""
        return self.metadata.description

    @property
    def category(self) -> ToolCategory:
        """Get tool category"""
        return self.metadata.category

    @property
    def version(self) -> str:
        """Get tool version"""
        return self.metadata.version

    @property
    def parameters(self) -> List[ToolParameter]:
        """Get tool parameters"""
        return self.metadata.parameters

    @property
    def is_initialized(self) -> bool:
        """Check if tool is initialized"""
        return self._is_initialized

    @property
    def validation_errors(self) -> List[str]:
        """Get validation errors"""
        return self._validation_errors

    def _validate_metadata(self) -> None:
        """Validate tool metadata"""
        self._validation_errors = []

        if not self.metadata.name or len(self.metadata.name.strip()) == 0:
            self._validation_errors.append("Tool name cannot be empty")

        if not self.metadata.description or len(self.metadata.description.strip()) == 0:
            self._validation_errors.append("Tool description cannot be empty")

        # Validate parameters
        param_names = []
        for param in self.metadata.parameters:
            if not param.name:
                self._validation_errors.append("Parameter name cannot be empty")
                continue
            
            if param.name in param_names:
                self._validation_errors.append(f"Duplicate parameter: {param.name}")
            param_names.append(param.name)

            if param.required and param.default is not None:
                logger.warning(f"Parameter {param.name} is required but has a default value")

    async def initialize(self) -> bool:
        """
        Initialize the tool

        This method should be called before using the tool. It allows the tool
        to set up any necessary resources or connections.

        Returns:
            True if initialization succeeded, False otherwise
        """
        if self._is_initialized:
            return True

        try:
            logger.info(f"Initializing tool: {self.metadata.name}")
            await self._initialize()
            self._is_initialized = True
            logger.info(f"Tool {self.metadata.name} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize tool {self.metadata.name}: {e}")
            return False

    async def _initialize(self) -> None:
        """
        Internal initialization method (can be overridden by subclasses)

        Subclasses should implement this method to handle tool-specific initialization.
        """
        pass

    async def shutdown(self) -> bool:
        """
        Shutdown the tool

        This method should be called when the tool is no longer needed. It allows
        the tool to clean up any resources or connections.

        Returns:
            True if shutdown succeeded, False otherwise
        """
        if not self._is_initialized:
            return True

        try:
            logger.info(f"Shutting down tool: {self.metadata.name}")
            await self._shutdown()
            self._is_initialized = False
            logger.info(f"Tool {self.metadata.name} shut down successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to shut down tool {self.metadata.name}: {e}")
            return False

    async def _shutdown(self) -> None:
        """
        Internal shutdown method (can be overridden by subclasses)

        Subclasses should implement this method to handle tool-specific shutdown.
        """
        pass

    async def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate parameters for the tool

        Args:
            params: Parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for param in self.metadata.parameters:
            if param.required and param.name not in params:
                errors.append(f"Required parameter '{param.name}' is missing")
                continue

            if param.name in params:
                value = params[param.name]
                
                # Type validation
                if param.type == "integer" and not isinstance(value, int):
                    errors.append(f"Parameter '{param.name}' must be an integer")
                elif param.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Parameter '{param.name}' must be a number")
                elif param.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Parameter '{param.name}' must be a boolean")
                elif param.type == "array" and not isinstance(value, list):
                    errors.append(f"Parameter '{param.name}' must be an array")
                elif param.type == "object" and not isinstance(value, dict):
                    errors.append(f"Parameter '{param.name}' must be an object")

                # Choice validation
                if param.choices and value not in param.choices:
                    errors.append(f"Parameter '{param.name}' must be one of the allowed choices: {', '.join(param.choices)}")

        # Check for extra parameters
        allowed_params = {param.name for param in self.metadata.parameters}
        for param_name in params:
            if param_name not in allowed_params:
                logger.warning(f"Unknown parameter '{param_name}' for tool '{self.metadata.name}'")

        return errors

    async def execute(self, params: Dict[str, Any]) -> Any:
        """
        Execute the tool with the given parameters

        Args:
            params: Parameters for the tool

        Returns:
            Result of tool execution

        Raises:
            Exception: If tool execution fails
        """
        if not self._is_initialized:
            await self.initialize()

        # Validate parameters
        errors = await self.validate_params(params)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

        # Prepare parameters with defaults
        prepared_params = {}
        for param in self.metadata.parameters:
            if param.name in params:
                prepared_params[param.name] = params[param.name]
            elif param.default is not None:
                prepared_params[param.name] = param.default

        try:
            logger.debug(f"Executing tool '{self.metadata.name}' with params: {prepared_params}")
            result = await self._execute(prepared_params)
            logger.debug(f"Tool '{self.metadata.name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool '{self.metadata.name}': {e}")
            raise

    @abstractmethod
    async def _execute(self, params: Dict[str, Any]) -> Any:
        """
        Internal execution method (must be implemented by subclasses)

        Args:
            params: Prepared parameters for the tool

        Returns:
            Result of tool execution

        Raises:
            Exception: If tool execution fails
        """
        pass

    def get_metadata_dict(self) -> Dict[str, Any]:
        """
        Get tool metadata as dictionary

        Returns:
            Dictionary representation of tool metadata
        """
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "category": self.metadata.category.value,
            "version": self.metadata.version,
            "author": self.metadata.author,
            "capabilities": self.metadata.capabilities,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default": param.default,
                    "choices": param.choices
                }
                for param in self.metadata.parameters
            ]
        }


def tool(
    name: str,
    description: str,
    category: str = "general",
    version: str = "1.0.0",
    author: str = "Unknown",
    capabilities: Optional[List[str]] = None
):
    """
    Decorator to create a tool from a function

    Args:
        name: Tool name
        description: Tool description
        category: Tool category (default: "general")
        version: Tool version (default: "1.0.0")
        author: Tool author (default: "Unknown")
        capabilities: List of capabilities (default: None)

    Returns:
        Decorator function
    """
    capabilities = capabilities or []
    
    def decorator(func: Callable):
        class FunctionTool(Tool):
            def __init__(self):
                # Extract function parameters from signature
                import inspect
                signature = inspect.signature(func)
                parameters = []
                
                for param_name, param in signature.parameters.items():
                    if param_name == "self":
                        continue
                        
                    param_info = ToolParameter(
                        name=param_name,
                        type="string",  # Default type
                        required=param.default == param.empty
                    )
                    
                    if param.default != param.empty:
                        param_info.default = param.default
                        
                    parameters.append(param_info)
                
                metadata = ToolMetadata(
                    name=name,
                    description=description,
                    category=ToolCategory(category),
                    version=version,
                    author=author,
                    capabilities=capabilities,
                    parameters=parameters
                )
                
                super().__init__(metadata)
                
            async def _execute(self, params: Dict[str, Any]) -> Any:
                try:
                    return await func(**params)
                except TypeError:
                    return func(**params)
        
        return FunctionTool()
        
    return decorator
