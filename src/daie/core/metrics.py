"""
Lightweight Prometheus-compatible metrics registry for DAIE.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional


class MetricsRegistry:
    """
    In-memory registry for system metrics.
    Exposes metrics in Prometheus text format.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._counters = defaultdict(float)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(list)
        self._initialized = True

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter."""
        key = self._get_key(name, labels)
        self._counters[key] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        key = self._get_key(name, labels)
        self._gauges[key] = value

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value (for histograms/summaries)."""
        key = self._get_key(name, labels)
        self._histograms[key].append(value)

    def _get_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        if not labels:
            return name
        label_str = ",".join([f'{k}="{v}"' for k, v in sorted(labels.items())])
        return f'{name}{{{label_str}}}'

    def export(self) -> str:
        """Export all metrics in Prometheus text format."""
        lines = []
        
        for key, value in self._counters.items():
            lines.append(f"{key} {value}")
            
        for key, value in self._gauges.items():
            lines.append(f"{key} {value}")
            
        # Very simple histogram representation (just exposing count and sum for now)
        for key, values in self._histograms.items():
            name_base = key.split('{')[0]
            labels = key[len(name_base):]
            lines.append(f"{name_base}_count{labels} {len(values)}")
            lines.append(f"{name_base}_sum{labels} {sum(values)}")
            
        return "\n".join(lines) + "\n"


class MetricsServer:
    """
    Lightweight HTTP server to expose metrics for Prometheus.
    """
    def __init__(self, registry: MetricsRegistry, port: int = 9090):
        self.registry = registry
        self.port = port
        self.server = None

    async def start(self):
        """Start the metrics HTTP server."""
        self.server = await asyncio.start_server(
            self._handle_request, "0.0.0.0", self.port
        )
        addr = self.server.sockets[0].getsockname()
        import logging
        logging.getLogger(__name__).info(f"Metrics server serving on {addr}")
        
    async def _handle_request(self, reader, writer):
        """Handle incoming HTTP GET /metrics requests."""
        data = await reader.read(1024)
        request = data.decode()
        
        if "GET /metrics" in request:
            body = self.registry.export()
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain; version=0.0.4\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{body}"
            )
        else:
            response = "HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n"
            
        writer.write(response.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def stop(self):
        """Stop the metrics server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None


# Global registry
metrics = MetricsRegistry()
