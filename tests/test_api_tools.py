"""
Tests for API call tools
"""

import pytest
from unittest.mock import patch, MagicMock

from daie.tools import APICallTool, HTTPGetTool, HTTPPostTool


@pytest.mark.asyncio
@patch("daie.tools.api_tool.requests.request")
async def test_api_call_tool_get(mock_request):
    """Test APICallTool with GET method"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://api.example.com/data"
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.encoding = "utf-8"
    mock_response.reason = "OK"
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_response.json.return_value = {"data": "test"}
    mock_request.return_value = mock_response

    tool = APICallTool()
    result = await tool.execute(
        {"url": "https://api.example.com/data", "method": "GET"}
    )

    assert result["status_code"] == 200
    assert result["url"] == "https://api.example.com/data"
    assert "json" in result
    assert result["json"]["data"] == "test"
    assert "elapsed" in result


@pytest.mark.asyncio
@patch("daie.tools.api_tool.requests.get")
async def test_http_get_tool(mock_get):
    """Test HTTPGetTool"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://api.example.com/items"
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.encoding = "utf-8"
    mock_response.reason = "OK"
    mock_response.elapsed.total_seconds.return_value = 0.3
    mock_response.json.return_value = {"items": [1, 2, 3]}
    mock_get.return_value = mock_response

    tool = HTTPGetTool()
    result = await tool.execute(
        {"url": "https://api.example.com/items", "params": {"limit": 3}}
    )

    assert result["status_code"] == 200
    assert "json" in result
    assert len(result["json"]["items"]) == 3


@pytest.mark.asyncio
@patch("daie.tools.api_tool.requests.post")
async def test_http_post_tool(mock_post):
    """Test HTTPPostTool"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.url = "https://api.example.com/items"
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.encoding = "utf-8"
    mock_response.reason = "Created"
    mock_response.elapsed.total_seconds.return_value = 0.6
    mock_response.json.return_value = {"id": 1, "name": "Test Item"}
    mock_post.return_value = mock_response

    tool = HTTPPostTool()
    result = await tool.execute(
        {
            "url": "https://api.example.com/items",
            "json": {"name": "Test Item", "value": 42},
        }
    )

    assert result["status_code"] == 201
    assert "json" in result
    assert result["json"]["name"] == "Test Item"


@pytest.mark.asyncio
@patch("daie.tools.api_tool.requests.request")
async def test_api_call_tool_with_headers(mock_request):
    """Test APICallTool with custom headers"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://api.example.com/protected"
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.elapsed.total_seconds.return_value = 0.4
    mock_response.json.return_value = {"success": True}
    mock_request.return_value = mock_response

    tool = APICallTool()
    result = await tool.execute(
        {
            "url": "https://api.example.com/protected",
            "method": "GET",
            "headers": {"Authorization": "Bearer token123"},
        }
    )

    assert result["status_code"] == 200
    assert result["json"]["success"] is True


@pytest.mark.asyncio
async def test_api_call_tool_validation():
    """Test parameter validation for APICallTool"""
    tool = APICallTool()

    # Test missing required parameter (url)
    with pytest.raises(ValueError):
        await tool.execute({"method": "GET"})
