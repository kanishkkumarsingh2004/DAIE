"""
API call tool using requests library
"""

import logging
from typing import Dict, Any, Optional
import requests
from daie.tools.tool import Tool, ToolMetadata, ToolParameter, ToolCategory
logger = logging.getLogger(__name__)

class APICallTool(Tool):
    """
    A tool for making HTTP API calls using the requests library.

    This tool supports various HTTP methods (GET, POST, PUT, DELETE, etc.) and
    allows sending headers, query parameters, and request bodies.
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="api_call",
            description="Tool for making HTTP API calls to external services - use this for operations like fetching data from APIs, sending data to APIs, or interacting with web services using HTTP methods (GET, POST, PUT, DELETE, etc.)",
            category=ToolCategory.API,
            version="1.0.0",
            author="Decentralized AI Ecosystem",
            capabilities=[
                "http_get",
                "http_post",
                "http_put",
                "http_delete",
                "http_patch",
                "api_requests",
            ],
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="API endpoint URL to call",
                    required=True,
                ),
                ToolParameter(
                    name="method",
                    type="string",
                    description="HTTP method to use (GET, POST, PUT, DELETE, PATCH)",
                    required=True,
                    default="GET",
                    choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
                ),
                ToolParameter(
                    name="headers",
                    type="object",
                    description="HTTP headers to send with the request",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="params",
                    type="object",
                    description="Query parameters to include in the URL",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="data",
                    type="object",
                    description="Form data to send with the request (for POST/PUT)",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="json",
                    type="object",
                    description="JSON data to send with the request (for POST/PUT)",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="timeout",
                    type="number",
                    description="Request timeout in seconds",
                    required=False,
                    default=30,
                ),
                ToolParameter(
                    name="verify_ssl",
                    type="boolean",
                    description="Whether to verify SSL certificates",
                    required=False,
                    default=True,
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the API call

        Args:
            params: Parameters for the API call

        Returns:
            Dictionary containing the response details

        Raises:
            Exception: If the API call fails
        """
        url = params.get("url")
        method = params.get("method", "GET").upper()
        headers = params.get("headers") or {}
        params_dict = params.get("params") or {}
        data = params.get("data")
        json_data = params.get("json")
        timeout = params.get("timeout", 30)
        verify_ssl = params.get("verify_ssl", True)

        logger.debug(f"Making API call: {method} {url}")

        try:
            # Prepare request kwargs efficiently
            request_kwargs = {
                "headers": headers,
                "params": params_dict,
                "timeout": timeout,
                "verify": verify_ssl,
            }

            if data:
                request_kwargs["data"] = data
            if json_data:
                request_kwargs["json"] = json_data

            # Make the API call
            response = requests.request(method, url, **request_kwargs)

            # Prepare response efficiently
            result = {
                "status_code": response.status_code,
                "url": response.url,
                "headers": dict(response.headers),
                "reason": response.reason,
                "elapsed": response.elapsed.total_seconds(),
            }

            # Try to parse JSON response
            try:
                result["json"] = response.json()
            except Exception:
                result["text"] = response.text[:1000]  # Limit text size

            logger.debug(
                f"API call completed: {response.status_code} {response.reason}"
            )

            return result

        except requests.exceptions.Timeout:
            logger.error(f"API call timed out: {url}")
            raise Exception(f"Request timed out after {timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f"Failed to connect to {url}")
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise


class HTTPGetTool(Tool):
    """
    Simplified tool for making HTTP GET requests.
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="http_get",
            description="Make HTTP GET requests to retrieve data from APIs",
            category=ToolCategory.API,
            version="1.0.0",
            author="Decentralized AI Ecosystem",
            capabilities=["http_get", "api_requests"],
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="API endpoint URL to call",
                    required=True,
                ),
                ToolParameter(
                    name="headers",
                    type="object",
                    description="HTTP headers to send with the request",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="params",
                    type="object",
                    description="Query parameters to include in the URL",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="timeout",
                    type="number",
                    description="Request timeout in seconds",
                    required=False,
                    default=30,
                ),
                ToolParameter(
                    name="verify_ssl",
                    type="boolean",
                    description="Whether to verify SSL certificates",
                    required=False,
                    default=True,
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute HTTP GET request

        Args:
            params: Parameters for the GET request

        Returns:
            Dictionary containing the response details
        """
        url = params.get("url")
        headers = params.get("headers") or {}
        params_dict = params.get("params") or {}
        timeout = params.get("timeout", 30)
        verify_ssl = params.get("verify_ssl", True)

        logger.debug(f"Making GET request: {url}")

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params_dict,
                timeout=timeout,
                verify=verify_ssl,
            )

            result = {
                "status_code": response.status_code,
                "url": response.url,
                "headers": dict(response.headers),
                "encoding": response.encoding,
                "reason": response.reason,
                "elapsed": response.elapsed.total_seconds(),
            }

            try:
                result["json"] = response.json()
            except Exception:
                result["text"] = response.text

            logger.debug(
                f"GET request completed: {response.status_code} {response.reason}"
            )

            return result

        except Exception as e:
            logger.error(f"GET request failed: {e}")
            raise


class HTTPPostTool(Tool):
    """
    Simplified tool for making HTTP POST requests.
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="http_post",
            description="Make HTTP POST requests to send data to APIs",
            category=ToolCategory.API,
            version="1.0.0",
            author="Decentralized AI Ecosystem",
            capabilities=["http_post", "api_requests"],
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="API endpoint URL to call",
                    required=True,
                ),
                ToolParameter(
                    name="headers",
                    type="object",
                    description="HTTP headers to send with the request",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="params",
                    type="object",
                    description="Query parameters to include in the URL",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="data",
                    type="object",
                    description="Form data to send with the request",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="json",
                    type="object",
                    description="JSON data to send with the request",
                    required=False,
                    default=None,
                ),
                ToolParameter(
                    name="timeout",
                    type="number",
                    description="Request timeout in seconds",
                    required=False,
                    default=30,
                ),
                ToolParameter(
                    name="verify_ssl",
                    type="boolean",
                    description="Whether to verify SSL certificates",
                    required=False,
                    default=True,
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute HTTP POST request

        Args:
            params: Parameters for the POST request

        Returns:
            Dictionary containing the response details
        """
        url = params.get("url")
        headers = params.get("headers") or {}
        params_dict = params.get("params") or {}
        data = params.get("data")
        json_data = params.get("json")
        timeout = params.get("timeout", 30)
        verify_ssl = params.get("verify_ssl", True)

        logger.debug(f"Making POST request: {url}")

        try:
            request_kwargs = {
                "headers": headers,
                "params": params_dict,
                "timeout": timeout,
                "verify": verify_ssl,
            }

            if data:
                request_kwargs["data"] = data
            if json_data:
                request_kwargs["json"] = json_data

            response = requests.post(url, **request_kwargs)

            result = {
                "status_code": response.status_code,
                "url": response.url,
                "headers": dict(response.headers),
                "encoding": response.encoding,
                "reason": response.reason,
                "elapsed": response.elapsed.total_seconds(),
            }

            try:
                result["json"] = response.json()
            except Exception:
                result["text"] = response.text

            logger.debug(
                f"POST request completed: {response.status_code} {response.reason}"
            )

            return result

        except Exception as e:
            logger.error(f"POST request failed: {e}")
            raise


class APIToolkit:
    """
    Collection of API tools for easy access
    """

    @staticmethod
    def get_tools() -> list:
        """
        Get all API tools

        Returns:
            List of API tool instances
        """
        return [APICallTool(), HTTPGetTool(), HTTPPostTool()]
