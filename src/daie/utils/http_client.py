"""
Lightweight HTTP client using urllib
Replaces requests dependency
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, Optional

try:
    import requests as _requests
except ImportError:
    _requests = None


# Exception classes for compatibility with requests library
class ConnectionError(Exception):
    """Connection error exception"""

    pass


class Timeout(Exception):
    """Timeout exception"""

    pass


class exceptions:
    """Namespace for exception classes (requests-compatible)"""

    ConnectionError = ConnectionError
    Timeout = Timeout


class Response:
    """Mock requests Response object"""

    def __init__(
        self, data: bytes, headers: Any, status_code: int, url: str = "", reason: str = ""
    ):
        self.content = data
        self.headers = headers
        self.status_code = status_code
        self.url = url
        self.reason = reason
        self.text = data.decode("utf-8") if data else ""
        self.encoding = "utf-8"

        # Simple elapsed time mock
        import collections

        Elapsed = collections.namedtuple("Elapsed", ["total_seconds"])
        self.elapsed = Elapsed(lambda: 0.1)

    def json(self) -> Any:
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}: {self.text}")

    def iter_lines(self):
        """Iterate over lines in the response content"""
        if not self.content:
            return
        for line in self.content.split(b"\n"):
            if line:
                yield line

    def iter_content(self, chunk_size: int = 8192):
        """Iterate over response content in chunks"""
        if not self.content:
            return
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i: i + chunk_size]


def request(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    json_data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    stream: bool = False,
) -> Response:
    """
    Make an HTTP request using urllib

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        params: Query parameters
        data: Raw data to send
        json_data: JSON data to send
        headers: Request headers
        timeout: Timeout in seconds
        stream: Whether to stream the response (for compatibility, not used with urllib)

    Returns:
        Response object
    """
    if headers is None:
        headers = {}

    if _requests is None and params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    body = None
    if json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
    elif data is not None:
        if isinstance(data, dict):
            body = urllib.parse.urlencode(data).encode("utf-8")
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif isinstance(data, str):
            body = data.encode("utf-8")
        else:
            body = data

    if _requests is not None:
        request_kwargs = {
            "headers": headers,
            "timeout": timeout,
            "stream": stream,
        }
        if params is not None:
            request_kwargs["params"] = params
        if json_data is not None:
            request_kwargs["json"] = json_data
        elif data is not None:
            request_kwargs["data"] = body
        return _requests.request(method, url, **request_kwargs)

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Read response content
            content = response.read()
            return Response(
                content, response.info(), response.getcode(), url=url, reason=response.reason
            )
    except urllib.error.HTTPError as e:
        # For HTTP errors, read the error content
        error_content = e.read()
        return Response(error_content, e.headers, e.code, url=url, reason=e.reason)
    except urllib.error.URLError as e:
        raise ConnectionError(f"Connection failed: {e}")
    except Exception as e:
        if "timed out" in str(e).lower():
            raise Timeout(f"Request timed out: {e}")
        raise Exception(f"Request failed: {e}")


def get(url: str, **kwargs) -> Response:
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> Response:
    return request("POST", url, **kwargs)


def put(url: str, **kwargs) -> Response:
    return request("PUT", url, **kwargs)


def delete(url: str, **kwargs) -> Response:
    return request("DELETE", url, **kwargs)


def patch(url: str, **kwargs) -> Response:
    return request("PATCH", url, **kwargs)


class Session:
    """Session class for making multiple requests with shared configuration"""

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = 30):
        """
        Initialize a session

        Args:
            headers: Default headers for all requests
            timeout: Default timeout in seconds
        """
        self.headers = headers or {}
        self.timeout = timeout

    def get(self, url: str, **kwargs) -> Response:
        """Make a GET request"""
        headers = {**self.headers, **kwargs.pop("headers", {})}
        timeout = kwargs.pop("timeout", self.timeout)
        return get(url, headers=headers, timeout=timeout, **kwargs)

    def post(self, url: str, **kwargs) -> Response:
        """Make a POST request"""
        headers = {**self.headers, **kwargs.pop("headers", {})}
        timeout = kwargs.pop("timeout", self.timeout)
        # Convert 'json' parameter to 'json_data' for compatibility
        if "json" in kwargs:
            kwargs["json_data"] = kwargs.pop("json")
        # Keep 'stream' parameter for compatibility with requests library
        # (urllib doesn't use it, but Ollama API expects it)
        return post(url, headers=headers, timeout=timeout, **kwargs)

    def put(self, url: str, **kwargs) -> Response:
        """Make a PUT request"""
        headers = {**self.headers, **kwargs.pop("headers", {})}
        timeout = kwargs.pop("timeout", self.timeout)
        # Convert 'json' parameter to 'json_data' for compatibility
        if "json" in kwargs:
            kwargs["json_data"] = kwargs.pop("json")
        # Keep 'stream' parameter for compatibility with requests library
        # (urllib doesn't use it, but Ollama API expects it)
        return put(url, headers=headers, timeout=timeout, **kwargs)

    def delete(self, url: str, **kwargs) -> Response:
        """Make a DELETE request"""
        headers = {**self.headers, **kwargs.pop("headers", {})}
        timeout = kwargs.pop("timeout", self.timeout)
        return delete(url, headers=headers, timeout=timeout, **kwargs)

    def patch(self, url: str, **kwargs) -> Response:
        """Make a PATCH request"""
        headers = {**self.headers, **kwargs.pop("headers", {})}
        timeout = kwargs.pop("timeout", self.timeout)
        # Convert 'json' parameter to 'json_data' for compatibility
        if "json" in kwargs:
            kwargs["json_data"] = kwargs.pop("json")
        # Keep 'stream' parameter for compatibility with requests library
        # (urllib doesn't use it, but Ollama API expects it)
        return patch(url, headers=headers, timeout=timeout, **kwargs)

    def close(self):
        """Close the session (no-op for urllib-based client)"""
        pass
