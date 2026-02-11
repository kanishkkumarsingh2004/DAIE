"""
Tool registry module for managing tools
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

from daie.tools.tool import Tool, ToolMetadata, ToolCategory

logger = logging.getLogger(__name__)


@dataclass
class ToolRegistration:
    """Tool registration information"""

    tool: Tool
    metadata: ToolMetadata
    registered_at: float
    usage_count: int = 0


class ToolRegistry:
    """
    Tool registry for managing available tools in the system

    This class provides a central repository for registering, retrieving, and
    managing tools available to agents in the decentralized AI ecosystem.

    Example:
    >>> from daie.tools import ToolRegistry
    >>> from daie.tools import Tool

    >>> # Create tool registry
    >>> registry = ToolRegistry()

    >>> # Register a tool
    >>> tool = MyTool()
    >>> registry.register(tool)

    >>> # Get a tool
    >>> retrieved_tool = registry.get_tool("my_tool")

    >>> # List all tools
    >>> all_tools = registry.list_tools()

    >>> # Search tools
    >>> search_results = registry.search_tools("search")
    """

    def __init__(self):
        """Initialize tool registry"""
        self._tools: Dict[str, ToolRegistration] = {}
        self._categories: Dict[str, List[Tool]] = {}
        self._tool_events = {"register": [], "unregister": [], "update": []}
        self._usage_counts: Dict[str, int] = {}
        logger.info("Tool registry initialized")

    def register_tool(self, name: str):
        """
        Decorator for registering a tool with the registry

        Args:
            name: Tool name

        Returns:
            Decorator function
        """

        def decorator(cls):
            # Check if this is already an instance or a class
            if isinstance(cls, Tool):
                tool_instance = cls
            else:
                # If it's a class, instantiate it
                tool_instance = cls()

            tool_instance.name = name
            self.register(tool_instance)
            return cls

        return decorator

    def unregister_tool(self, tool_name: str) -> "ToolRegistry":
        """
        Unregister a tool from the registry (alias for unregister)

        Args:
            tool_name: Name of tool to unregister

        Returns:
            self for method chaining
        """
        return self.unregister(tool_name)

    def invoke_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Invoke a tool with the given parameters

        Args:
            tool_name: Name of tool to invoke
            **kwargs: Parameters to pass to the tool

        Returns:
            Result of tool invocation

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        return tool.execute(**kwargs)

    def register(self, tool: Tool) -> "ToolRegistry":
        """
        Register a tool with the registry

        Args:
            tool: Tool instance to register

        Returns:
            self for method chaining

        Raises:
            ValueError: If tool with same name already exists
        """
        tool_name = tool.name

        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' already registered")

        import time

        registration = ToolRegistration(
            tool=tool, metadata=tool.metadata, registered_at=time.time(), usage_count=0
        )

        self._tools[tool_name] = registration

        # Add to category index
        category = tool.category.value
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool)

        # Track usage count
        self._usage_counts[tool_name] = 0

        logger.info(f"Tool '{tool_name}' registered successfully")
        self._notify_event("register", tool)

        return self

    def unregister(self, tool_name: str) -> "ToolRegistry":
        """
        Unregister a tool from the registry

        Args:
            tool_name: Name of tool to unregister

        Returns:
            self for method chaining
        """
        if tool_name not in self._tools:
            logger.warning(f"Tool '{tool_name}' not found for unregistration")
            return self

        tool = self._tools[tool_name].tool

        # Remove from category index
        category = tool.category.value
        if category in self._categories and tool in self._categories[category]:
            self._categories[category].remove(tool)
            if not self._categories[category]:
                del self._categories[category]

        # Remove from tools dictionary
        del self._tools[tool_name]

        # Remove usage count
        if tool_name in self._usage_counts:
            del self._usage_counts[tool_name]

        logger.info(f"Tool '{tool_name}' unregistered successfully")
        self._notify_event("unregister", tool)

        return self

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name

        Args:
            tool_name: Name of tool to get

        Returns:
            Tool instance or None if not found
        """
        if tool_name not in self._tools:
            logger.debug(f"Tool '{tool_name}' not found")
            return None

        # Increment usage count
        self._usage_counts[tool_name] = self._usage_counts.get(tool_name, 0) + 1
        self._tools[tool_name].usage_count += 1

        return self._tools[tool_name].tool

    def list_tools(self) -> List[Tool]:
        """
        List all registered tools

        Returns:
            List of tool instances
        """
        return [registration.tool for registration in self._tools.values()]

    def list_categories(self) -> List[str]:
        """
        List all tool categories

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """
        Get all tools in a specific category

        Args:
            category: Category name to filter by

        Returns:
            List of tool instances in the category
        """
        return self._categories.get(category.lower(), [])

    def search_tools(self, keyword: str) -> List[Tool]:
        """
        Search tools by keyword

        Args:
            keyword: Keyword to search for in name or description

        Returns:
            List of matching tool instances
        """
        keyword = keyword.lower()
        matching_tools = []

        for registration in self._tools.values():
            if (
                keyword in registration.metadata.name.lower()
                or keyword in registration.metadata.description.lower()
                or any(
                    keyword in cap.lower() for cap in registration.metadata.capabilities
                )
            ):
                matching_tools.append(registration.tool)

        return matching_tools

    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get tool metadata

        Args:
            tool_name: Name of tool to get metadata for

        Returns:
            Tool metadata or None if not found
        """
        if tool_name not in self._tools:
            return None

        return self._tools[tool_name].metadata

    def get_usage_count(self, tool_name: str) -> int:
        """
        Get usage count for a tool

        Args:
            tool_name: Name of tool to get usage count for

        Returns:
            Number of times the tool has been used
        """
        return self._usage_counts.get(tool_name, 0)

    def get_top_used_tools(self, count: int = 10) -> List[Tool]:
        """
        Get most used tools

        Args:
            count: Number of top tools to return (default: 10)

        Returns:
            List of tool instances sorted by usage count
        """
        sorted_tools = sorted(
            self._tools.values(), key=lambda x: x.usage_count, reverse=True
        )

        return [registration.tool for registration in sorted_tools[:count]]

    def get_tool_count(self) -> int:
        """
        Get total number of registered tools

        Returns:
            Number of registered tools
        """
        return len(self._tools)

    def is_tool_registered(self, tool_name: str) -> bool:
        """
        Check if a tool is registered

        Args:
            tool_name: Name of tool to check

        Returns:
            True if tool is registered, False otherwise
        """
        return tool_name in self._tools

    def clear_all(self) -> "ToolRegistry":
        """
        Clear all registered tools

        Returns:
            self for method chaining
        """
        tools_to_remove = list(self._tools.keys())
        for tool_name in tools_to_remove:
            self.unregister(tool_name)

        logger.info("All tools unregistered")
        return self

    def on_event(
        self, event_type: str, handler: Callable[[Tool], None]
    ) -> "ToolRegistry":
        """
        Register an event handler for tool events

        Args:
            event_type: Event type (register, unregister, update)
            handler: Handler function to call

        Returns:
            self for method chaining
        """
        if event_type in self._tool_events:
            self._tool_events[event_type].append(handler)

        return self

    def _notify_event(self, event_type: str, tool: Tool):
        """Notify event handlers"""
        for handler in self._tool_events.get(event_type, []):
            try:
                handler(tool)
            except Exception as e:
                logger.error(f"Error in event handler for tool '{tool.name}': {e}")

    def update_tool(self, old_tool_name: str, new_tool: Tool) -> "ToolRegistry":
        """
        Update an existing tool registration

        Args:
            old_tool_name: Name of tool to update
            new_tool: New tool instance

        Returns:
            self for method chaining
        """
        if old_tool_name not in self._tools:
            raise ValueError(f"Tool '{old_tool_name}' not found")

        self.unregister(old_tool_name)
        self.register(new_tool)

        self._notify_event("update", new_tool)

        return self

    def get_tool_registration_info(self, tool_name: str) -> Optional[ToolRegistration]:
        """
        Get detailed tool registration information

        Args:
            tool_name: Name of tool to get info for

        Returns:
            Tool registration information or None if not found
        """
        return self._tools.get(tool_name)

    def get_registry_info(self) -> Dict[str, any]:
        """
        Get registry information and statistics

        Returns:
            Dictionary with registry statistics
        """
        from collections import defaultdict

        category_counts = defaultdict(int)
        for registration in self._tools.values():
            category_counts[registration.metadata.category.value] += 1

        return {
            "total_tools": self.get_tool_count(),
            "categories": list(category_counts.keys()),
            "category_counts": dict(category_counts),
            "total_usage": sum(self._usage_counts.values()),
            "top_used": [
                {"name": tool.name, "usage": self._usage_counts[tool.name]}
                for tool in self.get_top_used_tools(10)
            ],
        }
