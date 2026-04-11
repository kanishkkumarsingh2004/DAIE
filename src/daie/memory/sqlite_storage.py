"""
SQLite-based storage backend for agent memory management.
Provides relational persistence with support for shared memory namespaces.
"""

import json
import logging
import os
import sqlite3
import time
from typing import Dict, List, Optional

from daie.memory.storage import StorageBackend, MemoryItem

logger = logging.getLogger(__name__)


class SQLiteStorage(StorageBackend):
    """
    SQLite storage backend for agent memory.

    This backend provides relational storage for memories, allowing for
    exact retrieval and easier shared memory implementation.
    """

    def __init__(self):
        self._root_path = None
        self._db_path = None
        self._conn = None

    def initialize(self, root_path: str) -> None:
        """Initialize SQLite database and ensure tables exist"""
        self._root_path = root_path
        self._db_path = os.path.join(root_path, "daie_memory.db")
        os.makedirs(root_path, exist_ok=True)

        try:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

            # Enable WAL mode for better concurrency
            self._conn.execute("PRAGMA journal_mode=WAL")

            # Create memories table
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    content TEXT,
                    memory_type TEXT,
                    timestamp REAL,
                    metadata_json TEXT,
                    tags_json TEXT,
                    namespace TEXT
                )
            """)

            # Create indexes for performance
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_type ON memories(agent_id, memory_type)"
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_namespace ON memories(namespace)")

            self._conn.commit()
            logger.info(f"SQLite storage initialized at: {self._db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            raise

    def save_agent_memory(self, agent_id: str, memories: Dict[str, List[MemoryItem]]) -> None:
        """Save agent memory to SQLite"""
        try:
            for memory_type, items in memories.items():
                for item in items:
                    self._conn.execute(
                        """
                        INSERT OR REPLACE INTO memories
                        (id, agent_id, content, memory_type, timestamp, metadata_json, tags_json, namespace)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            item.id,
                            agent_id,
                            item.content,
                            item.memory_type,
                            item.timestamp,
                            json.dumps(item.metadata),
                            json.dumps(item.tags),
                            item.metadata.get("namespace"),
                        ),
                    )
            self._conn.commit()
        except Exception as e:
            logger.error(f"Failed to save agent memory to SQLite: {e}")
            self._conn.rollback()
            raise

    def load_agent_memory(self, agent_id: str) -> Dict[str, List[MemoryItem]]:
        """Load agent memory from SQLite"""
        memories = {"working": [], "semantic": [], "episodic": [], "long_term": []}

        try:
            cursor = self._conn.execute(
                "SELECT * FROM memories WHERE agent_id = ? AND (namespace IS NULL OR namespace = '')",
                (agent_id,),
            )
            rows = cursor.fetchall()

            for row in rows:
                m_type = row["memory_type"]
                item = MemoryItem(
                    id=row["id"],
                    content=row["content"],
                    memory_type=m_type,
                    timestamp=row["timestamp"],
                    metadata=json.loads(row["metadata_json"]),
                    tags=json.loads(row["tags_json"]),
                )
                if m_type in memories:
                    memories[m_type].append(item)
                else:
                    memories[m_type] = [item]

            return memories
        except Exception as e:
            logger.error(f"Failed to load agent memory from SQLite: {e}")
            return memories

    def delete_agent_memory(self, agent_id: str) -> None:
        """Delete all memories for a specific agent"""
        try:
            self._conn.execute("DELETE FROM memories WHERE agent_id = ?", (agent_id,))
            self._conn.commit()
            logger.debug(f"Deleted memories for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to delete agent memory: {e}")
            self._conn.rollback()
            raise

    def list_agents(self) -> List[str]:
        """List all agent IDs with stored memories"""
        try:
            cursor = self._conn.execute(
                "SELECT DISTINCT agent_id FROM memories WHERE agent_id IS NOT NULL"
            )
            return [row["agent_id"] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to list agents from SQLite: {e}")
            return []

    def log_history(self, agent_id: str, content: str) -> None:
        """Log history - implementation for persistent store could be adding to a history table"""
        # For now, we align with the file-based history logging if root_path exists
        if self._root_path:
            agent_dir = os.path.join(self._root_path, agent_id)
            os.makedirs(agent_dir, exist_ok=True)
            history_file = os.path.join(agent_dir, "history.txt")
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open(history_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] {content}\n")
            except Exception as e:
                logger.error(f"Failed to log history for agent {agent_id}: {e}")

    # Extension methods for shared memory
    def store_shared_memory(self, namespace: str, item: MemoryItem) -> None:
        """Store a memory item in a shared namespace"""
        try:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO memories
                (id, agent_id, content, memory_type, timestamp, metadata_json, tags_json, namespace)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    item.id,
                    None,  # Shared memories might not have a specific owner
                    item.content,
                    item.memory_type,
                    item.timestamp,
                    json.dumps(item.metadata),
                    json.dumps(item.tags),
                    namespace,
                ),
            )
            self._conn.commit()
        except Exception as e:
            logger.error(f"Failed to store shared memory in SQLite: {e}")
            self._conn.rollback()
            raise

    def retrieve_shared_memory(
        self, namespace: str, memory_type: Optional[str] = None
    ) -> List[MemoryItem]:
        """Retrieve memories from a shared namespace"""
        try:
            query = "SELECT * FROM memories WHERE namespace = ?"
            params = [namespace]

            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type)

            cursor = self._conn.execute(query, tuple(params))
            rows = cursor.fetchall()

            return [
                MemoryItem(
                    id=row["id"],
                    content=row["content"],
                    memory_type=row["memory_type"],
                    timestamp=row["timestamp"],
                    metadata=json.loads(row["metadata_json"]),
                    tags=json.loads(row["tags_json"]),
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve shared memory from SQLite: {e}")
            return []
