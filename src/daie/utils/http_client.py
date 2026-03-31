"""
Lightweight HTTP client using urllib
Replaces requests dependency
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, Optional, Union


class Response:
    """Mock requests Response object"""

    def __init__(self, data: bytes, headers: Any, status_code: int, url: str = "", reason: str = ""):
        self.content = data
        self.headers = headers
        self.status_code = status_code
        self.url = url
        self.reason = reason
        self.text = data.decode("utf-8") if data else ""
        self.encoding = "utf-8"
        
        # Simple elapsed time mock
        import collections
        self.elapsed = collections.namedtuple("Elapsed", ["total_seconds"])(lambda: 0.1)
        self.elapsed.total_seconds = lambda: 0.1

    def json(self) -> Any:
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}: {self.text}")


def request(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    json_data: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
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

    Returns:
        Response object
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    if headers is None:
        headers = {}

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

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return Response(response.read(), response.info(), response.getcode(), url=url, reason=response.reason)
    except urllib.error.HTTPError as e:
        return Response(e.read(), e.headers, e.code, url=url, reason=e.reason)
    except Exception as e:
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
