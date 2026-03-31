"""
In-house Tracing support for DAIE.
Provides lightweight tracing across agent nodes without external dependencies.
"""

import asyncio
import contextvars
import functools
import logging
import time
from daie.utils.encryption import uuid7
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Global context for tracing using contextvars for async safety
_current_span_var = contextvars.ContextVar("_current_span", default=None)


class Span:
    """
    Represents a single operation in a trace.
    """
    def __init__(self, name: str, trace_id: str, parent_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = str(uuid7())
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time = None
        self.status = "OK"
        self.attributes = {}
        self.exception = None
        self._token = None

    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the span."""
        self.attributes[key] = value

    def set_attributes(self, attributes: Dict[str, Any]):
        """Set multiple attributes on the span."""
        self.attributes.update(attributes)

    def set_status(self, status: str, message: Optional[str] = None):
        """Set the status of the span."""
        self.status = status
        if message:
            self.attributes["status_message"] = message

    def record_exception(self, exc: Exception):
        """Record an exception on the span."""
        self.exception = str(exc)
        self.status = "ERROR"

    def __enter__(self):
        self._token = _current_span_var.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if exc_type:
            self.record_exception(exc_val)
        
        # Log the span if tracing is enabled
        manager = TracerManager()
        if manager.is_enabled:
            duration = (self.end_time - self.start_time) * 1000
            parent_info = f" | parent:{self.parent_id}" if self.parent_id else ""
            logger.debug(
                f"[TRACE] {self.name} | trace:{self.trace_id} | span:{self.span_id}{parent_info} | "
                f"{duration:.2f}ms | {self.status}"
            )
        
        if self._token:
            _current_span_var.reset(self._token)


class TracerManager:
    """
    Manages tracing for the system.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TracerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._is_enabled = False
        self._service_name = "daie"

    def setup(self, service_name: str = "daie", enabled: bool = True, **kwargs):
        """Initialize tracing configuration."""
        self._service_name = service_name
        self._is_enabled = enabled
        if enabled:
            logger.info(f"In-house tracing initialized for service: {service_name}")

    @property
    def is_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._is_enabled

    def get_current_span(self) -> Optional[Span]:
        """Get the currently active span."""
        return _current_span_var.get()

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Span:
        """Start a new span, automatically nesting it if a parent exists."""
        current = self.get_current_span()
        
        if current:
            trace_id = current.trace_id
            parent_id = current.span_id
        else:
            trace_id = uuid7()
            parent_id = None
            
        span = Span(name, trace_id, parent_id)
        if attributes:
            span.set_attributes(attributes)
        return span


def trace_span(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to wrap a function call in a trace span.
    Supports both synchronous and asynchronous functions.
    """
    def decorator(func: Callable):
        span_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = TracerManager()
            if not manager.is_enabled:
                return await func(*args, **kwargs)

            with manager.start_span(span_name, attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Exception is recorded by Span.__exit__
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = TracerManager()
            if not manager.is_enabled:
                return func(*args, **kwargs)

            with manager.start_span(span_name, attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    # Exception is recorded by Span.__exit__
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def inject_trace_context(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject current trace context into metadata for propagation.
    """
    current = TracerManager().get_current_span()
    if current:
        metadata["trace_id"] = current.trace_id
        metadata["parent_span_id"] = current.span_id
    return metadata


def extract_trace_context(metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Extract trace context from metadata.
    """
    trace_id = metadata.get("trace_id")
    parent_id = metadata.get("parent_span_id")
    
    if trace_id:
        return {"trace_id": trace_id, "parent_id": parent_id}
    return None


class TraceContextManager:
    """
    Context manager for manual trace propagation (e.g. when receiving a message).
    """
    def __init__(self, metadata: Dict[str, Any]):
        self.metadata = metadata
        self.span = None

    def __enter__(self):
        ctx = extract_trace_context(self.metadata)
        if ctx:
            self.span = Span("received_message", ctx["trace_id"], ctx["parent_id"])
            self.span.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            self.span.__exit__(exc_type, exc_val, exc_tb)
