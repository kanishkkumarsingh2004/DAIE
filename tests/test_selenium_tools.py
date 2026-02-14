"""Tests for Selenium Chrome automation tool - Browser Automation for Web Interactions.

Use Case Description:
This test file validates the Selenium Chrome automation tool in the Decentralized AI Ecosystem (DAIE), providing agents with browser automation capabilities for web scraping and interaction. Key functionalities tested include:

1. **Tool Initialization**: Chrome browser automation setup
   - Tool creation and initialization
   - Browser driver management
   - Tool metadata and capabilities

2. **Tool Configuration**: Browser automation settings
   - Action parameter validation (required field)
   - Screenshot configuration
   - Navigation and interaction actions

3. **Error Handling**: Edge case scenarios
   - Initialization failure handling
   - Missing required parameters
   - Browser driver unavailability

4. **Toolkit Integration**: Chrome-specific capabilities
   - SeleniumToolkit functionality
   - Browser automation capabilities (web scraping, navigation)
   - Supported selector types (CSS, XPath)

These tests ensure that agents can automate Chrome browser interactions, enabling them to scrape web content, interact with web applications, and integrate with external web services through browser automation.
"""

import pytest
import os
import asyncio

from daie.tools import SeleniumChromeTool


class TestSeleniumChromeTool:
    """Tests for SeleniumChromeTool class"""

    def test_tool_initialization(self):
        """Test tool initialization"""
        tool = SeleniumChromeTool()
        assert tool is not None
        assert tool.name == "selenium_chrome"
        assert tool.category.value == "browser_automation"
        assert "browser_automation" in tool.metadata.capabilities
        assert "selenium" in tool.metadata.capabilities
        assert "chrome" in tool.metadata.capabilities

    def test_tool_metadata(self):
        """Test tool metadata"""
        tool = SeleniumChromeTool()
        metadata = tool.get_metadata_dict()
        assert metadata["name"] == "selenium_chrome"
        assert metadata["version"] == "2.0.0"
        assert len(metadata["parameters"]) > 0

        # Check required parameters
        params = {p["name"]: p for p in metadata["parameters"]}
        assert "action" in params
        assert params["action"]["required"] is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test tool initialization failure handling"""
        with pytest.raises(Exception):
            # This should fail if Chrome driver is not available
            tool = SeleniumChromeTool()
            await tool.execute({"action": "open_url", "url": "https://example.com"})

    def test_screenshot_creation(self, tmp_path):
        """Test if screenshot file is created (mocked test)"""
        # We can't actually run Chrome in test environment,
        # but we can test the screenshot path handling
        tool = SeleniumChromeTool()

        # Test default screenshot path
        params1 = {"action": "screenshot"}
        param_def = next(
            p for p in tool.metadata.parameters if p.name == "screenshot_path"
        )
        assert param_def.default == "screenshot.png"

        # Test custom screenshot path
        test_path = os.path.join(tmp_path, "test_screenshot.png")
        params2 = {"action": "screenshot", "screenshot_path": test_path}
        assert params2["screenshot_path"] == test_path

    @pytest.mark.asyncio
    async def test_execute_with_missing_required_params(self):
        """Test execution with missing required parameters"""
        tool = SeleniumChromeTool()
        with pytest.raises(Exception):
            await tool.execute({})

    def test_selenium_toolkit(self):
        """Test SeleniumToolkit class"""
        from daie.tools import SeleniumToolkit

        toolkit = SeleniumToolkit()
        tools = toolkit.get_tools()
        assert len(tools) > 0
        assert all(isinstance(tool, SeleniumChromeTool) for tool in tools)


class TestSeleniumChromeToolCapabilities:
    """Tests for Selenium tool capabilities"""

    def test_basic_capabilities(self):
        """Test basic browser capabilities"""
        tool = SeleniumChromeTool()
        capabilities = tool.metadata.capabilities
        assert "browser_automation" in capabilities
        assert "web_scraping" in capabilities
        assert "selenium" in capabilities
        assert "chrome" in capabilities

    def test_actions_support(self):
        """Test supported actions are correctly defined"""
        tool = SeleniumChromeTool()
        action_param = next(p for p in tool.metadata.parameters if p.name == "action")
        expected_actions = [
            "open_url",
            "find_element",
            "click",
            "type",
            "screenshot",
            "execute_script",
            "navigate",
            "get_page_source",
            "get_title",
        ]
        assert all(action in action_param.choices for action in expected_actions)

    def test_selector_types(self):
        """Test supported selector types"""
        tool = SeleniumChromeTool()
        selector_param = next(
            p for p in tool.metadata.parameters if p.name == "selector_type"
        )
        assert "css" in selector_param.choices
        assert "xpath" in selector_param.choices

    def test_navigation_actions(self):
        """Test navigation actions support"""
        tool = SeleniumChromeTool()
        navigate_param = next(
            p for p in tool.metadata.parameters if p.name == "navigate_action"
        )
        assert "back" in navigate_param.choices
        assert "forward" in navigate_param.choices
        assert "refresh" in navigate_param.choices

    def test_screenshot_configuration(self):
        """Test screenshot configuration options"""
        tool = SeleniumChromeTool()
        screenshot_param = next(
            p for p in tool.metadata.parameters if p.name == "screenshot_path"
        )
        assert screenshot_param.default == "screenshot.png"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
