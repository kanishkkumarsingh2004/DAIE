"""Tests for tools module."""

import pytest
from unittest.mock import Mock, patch
from daie.tools.tool import Tool, ToolMetadata, ToolParameter, ToolCategory
from daie.tools.registry import ToolRegistry


class ConcreteTool(Tool):
    """Concrete implementation of Tool for testing purposes."""
    
    def __init__(self, metadata: ToolMetadata):
        super().__init__(metadata)
    
    async def _execute(self, params: dict) -> dict:
        return {"result": f"Processed: {params.get('text', '')}"}


class TestTool:
    """Tests for Tool class."""
    
    def test_tool_creation(self):
        """Test basic tool creation."""
        metadata = ToolMetadata(
            name="test-tool",
            description="Test tool description",
            category=ToolCategory.GENERAL,
            parameters=[
                ToolParameter(name="text", type="string", description="Input text")
            ]
        )
        
        tool = ConcreteTool(metadata)
        
        assert tool.name == "test-tool"
        assert tool.description == "Test tool description"
        assert tool.category == ToolCategory.GENERAL
        assert len(tool.parameters) == 1
        assert tool.parameters[0].name == "text"
    
    @pytest.mark.asyncio
    async def test_tool_validation(self):
        """Test tool parameter validation."""
        metadata = ToolMetadata(
            name="test-tool",
            description="Test tool description",
            category=ToolCategory.GENERAL,
            parameters=[
                ToolParameter(name="text", type="string", description="Input text", required=True)
            ]
        )
        
        tool = ConcreteTool(metadata)
        
        # Valid input
        errors = await tool.validate_params({"text": "test"})
        assert len(errors) == 0
        
        # Invalid input (missing required field)
        errors = await tool.validate_params({"missing": "field"})
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution."""
        metadata = ToolMetadata(
            name="test-tool",
            description="Test tool description",
            category=ToolCategory.GENERAL,
            parameters=[
                ToolParameter(name="text", type="string", description="Input text")
            ]
        )
        
        tool = ConcreteTool(metadata)
        result = await tool.execute({"text": "Hello World"})
        
        assert "result" in result
        assert "Hello World" in result["result"]


class TestToolRegistry:
    """Tests for ToolRegistry class."""
    
    def test_registry_creation(self):
        """Test tool registry creation."""
        registry = ToolRegistry()
        assert registry is not None
        assert len(registry._tools) == 0
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        
        metadata = ToolMetadata(
            name="test-tool",
            description="Test tool",
            category=ToolCategory.GENERAL
        )
        
        tool = ConcreteTool(metadata)
        registry.register(tool)
        
        assert len(registry._tools) == 1
        assert "test-tool" in registry._tools
    
    def test_register_duplicate_tool(self):
        """Test registering duplicate tool."""
        registry = ToolRegistry()
        
        metadata1 = ToolMetadata(
            name="test-tool",
            description="Test tool 1",
            category=ToolCategory.GENERAL
        )
        
        metadata2 = ToolMetadata(
            name="test-tool",
            description="Test tool 2",
            category=ToolCategory.GENERAL
        )
        
        tool1 = ConcreteTool(metadata1)
        tool2 = ConcreteTool(metadata2)
        
        registry.register(tool1)
        with pytest.raises(ValueError):
            registry.register(tool2)
    
    def test_get_tool(self):
        """Test tool retrieval."""
        registry = ToolRegistry()
        
        metadata = ToolMetadata(
            name="test-tool",
            description="Test tool",
            category=ToolCategory.GENERAL
        )
        
        tool = ConcreteTool(metadata)
        registry.register(tool)
        
        retrieved_tool = registry.get_tool("test-tool")
        assert retrieved_tool is not None
        assert retrieved_tool.name == "test-tool"
    
    def test_get_nonexistent_tool(self):
        """Test retrieving nonexistent tool."""
        registry = ToolRegistry()
        assert registry.get_tool("nonexistent") is None
    
    def test_unregister_tool(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        
        metadata = ToolMetadata(
            name="test-tool",
            description="Test tool",
            category=ToolCategory.GENERAL
        )
        
        tool = ConcreteTool(metadata)
        registry.register(tool)
        assert len(registry._tools) == 1
        
        registry.unregister("test-tool")
        assert len(registry._tools) == 0
        assert registry.get_tool("test-tool") is None
    
    def test_list_tools(self):
        """Test listing available tools."""
        registry = ToolRegistry()
        
        metadata1 = ToolMetadata(
            name="tool1",
            description="Tool 1",
            category=ToolCategory.GENERAL
        )
        
        metadata2 = ToolMetadata(
            name="tool2",
            description="Tool 2",
            category=ToolCategory.GENERAL
        )
        
        tool1 = ConcreteTool(metadata1)
        tool2 = ConcreteTool(metadata2)
        
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list_tools()
        assert len(tools) == 2
        
        # Check that both tools are in the list
        tool_names = [tool.name for tool in tools]
        assert "tool1" in tool_names
        assert "tool2" in tool_names


class TestToolIntegration:
    """Integration tests for tools module."""
    
    def test_tool_chain_creation(self):
        """Test creating and using tool chains."""
        registry = ToolRegistry()
        
        # Register test tools
        metadata1 = ToolMetadata(
            name="tool1",
            description="First tool",
            category=ToolCategory.GENERAL,
            parameters=[
                ToolParameter(name="text", type="string", description="Input text", required=True)
            ]
        )
        
        metadata2 = ToolMetadata(
            name="tool2",
            description="Second tool",
            category=ToolCategory.GENERAL,
            parameters=[
                ToolParameter(name="processed", type="string", description="Processed text", required=True)
            ]
        )
        
        tool1 = ConcreteTool(metadata1)
        tool2 = ConcreteTool(metadata2)
        
        registry.register(tool1)
        registry.register(tool2)
        
        # Test tool chain can be created
        assert len(registry.list_tools()) == 2
    
    def test_tool_registry_instance(self):
        """Test tool registry separate instances."""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        
        metadata = ToolMetadata(
            name="test-tool",
            description="Test tool",
            category=ToolCategory.GENERAL
        )
        
        tool = ConcreteTool(metadata)
        registry1.register(tool)
        
        # Each registry should have separate tools
        assert registry1.get_tool("test-tool") is not None
        assert registry2.get_tool("test-tool") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
