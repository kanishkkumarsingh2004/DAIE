"""
Memory management module for agents

This module provides memory management capabilities for agents with support
for multiple storage backends:
- VectorDatabaseStorage: Uses ChromaDB for semantic search capabilities
- BinaryFileStorage: Uses pickle for fast binary serialization (default)
"""

from daie.memory.manager import MemoryManager
from daie.memory.storage import (
    BinaryFileStorage,
    MemoryItem,
    StorageBackend,
    VectorDatabaseStorage,
    create_storage_backend,
)

__all__ = [
    "MemoryManager",
    "StorageBackend",
    "MemoryItem",
    "VectorDatabaseStorage",
    "BinaryFileStorage",
    "create_storage_backend",
]
