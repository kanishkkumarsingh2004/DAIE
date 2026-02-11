"""
Common utility functions
"""

import uuid
import re
import time
from typing import Optional, Any


def generate_id() -> str:
    """
    Generate a unique ID using UUID v4

    Returns:
        Unique ID string
    """
    return str(uuid.uuid4())


def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise
    """
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email) is not None


def validate_url(url: str) -> bool:
    """
    Validate URL format

    Args:
        url: URL to validate

    Returns:
        True if URL is valid, False otherwise
    """
    url_regex = r"^(http|https)://[^\s]+$"
    return re.match(url_regex, url) is not None


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address format

    Args:
        ip: IP address to validate

    Returns:
        True if IP address is valid, False otherwise
    """
    import ipaddress

    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_port(port: int) -> bool:
    """
    Validate port number

    Args:
        port: Port number to validate

    Returns:
        True if port number is valid, False otherwise
    """
    return 1 <= port <= 65535


def retry(
    func,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Retry decorator for function execution with exponential backoff

    Args:
        func: Function to decorate
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier
        exceptions: Exception types to catch

    Returns:
        Decorated function
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        current_delay = delay

        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt == max_attempts:
                    break
                time.sleep(current_delay)
                current_delay *= backoff

        raise last_exception

    return wrapper


def memoize(func):
    """
    Memoization decorator for functions

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    import functools

    cache = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper


def measure_time(func):
    """
    Decorator to measure function execution time

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result

    return wrapper


def safe_execute(func, default: Any = None, exceptions: tuple = (Exception,)):
    """
    Safely execute a function with exception handling

    Args:
        func: Function to execute
        default: Default value to return on exception
        exceptions: Exception types to catch

    Returns:
        Function result or default value on exception
    """
    try:
        return func()
    except exceptions:
        return default


def parse_query_params(query_string: str) -> dict:
    """
    Parse query parameters from URL query string

    Args:
        query_string: Query string to parse

    Returns:
        Dictionary of query parameters
    """
    params = {}
    if not query_string:
        return params

    # Remove leading ? if present
    if query_string.startswith("?"):
        query_string = query_string[1:]

    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value

    return params


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if text is truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_bytes(size: int, decimal_places: int = 2) -> str:
    """
    Format bytes to human readable format

    Args:
        size: Size in bytes
        decimal_places: Number of decimal places to show

    Returns:
        Human readable format
    """
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0
    return f"{size:.{decimal_places}f} EB"


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def is_json(text: str) -> bool:
    """
    Check if text is valid JSON

    Args:
        text: Text to check

    Returns:
        True if text is valid JSON, False otherwise
    """
    try:
        import json

        json.loads(text)
        return True
    except Exception:
        return False


def safe_json_loads(text: str, default: Any = None):
    """
    Safely load JSON from string

    Args:
        text: JSON string
        default: Default value to return on error

    Returns:
        Parsed JSON or default value
    """
    try:
        import json

        return json.loads(text)
    except Exception:
        return default


def safe_json_dumps(obj: Any, default: Any = None):
    """
    Safely dump object to JSON string

    Args:
        obj: Object to dump
        default: Default value to return on error

    Returns:
        JSON string or default value
    """
    try:
        import json

        return json.dumps(obj)
    except Exception:
        return default
