"""
Database Tool — SQLite and PostgreSQL support.

Provides database interaction capabilities for agents with
query, execute, list_tables, and describe_table operations.
"""

import logging
from typing import Any, Dict

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)


class DatabaseTool(Tool):
    """
    Database interaction tool supporting SQLite and PostgreSQL.

    - SQLite: Uses ``aiosqlite`` for async operations (or stdlib ``sqlite3``)
    - PostgreSQL: Uses ``asyncpg`` for async operations

    Read-only mode by default. Set ``allow_writes=True`` for INSERT/UPDATE/DELETE.

    Example:
        >>> tool = DatabaseTool(connection_string="sqlite:///mydb.db")
        >>> result = await tool.execute({"operation": "list_tables"})
        >>> result = await tool.execute({"operation": "query", "sql": "SELECT * FROM users LIMIT 10"})
    """

    def __init__(
        self,
        connection_string: str = "sqlite:///:memory:",
        allow_writes: bool = False,
    ):
        self._connection_string = connection_string
        self._allow_writes = allow_writes
        self._db_type = "sqlite" if "sqlite" in connection_string else "postgresql"
        self._conn = None

        metadata = ToolMetadata(
            name="database",
            description="Query and interact with SQLite or PostgreSQL databases. List tables, describe schemas, run SQL queries.",
            category=ToolCategory.DATABASE,
            version="1.0.0",
            author="DAIE",
            capabilities=["sql_query", "database_management", "data_retrieval"],
            parameters=[
                ToolParameter(
                    name="operation",
                    type="string",
                    description="Database operation to perform",
                    required=True,
                    choices=["query", "execute", "list_tables", "describe_table"],
                ),
                ToolParameter(
                    name="sql",
                    type="string",
                    description="SQL statement to execute (for 'query' and 'execute' operations)",
                    required=False,
                ),
                ToolParameter(
                    name="table_name",
                    type="string",
                    description="Table name (for 'describe_table' operation)",
                    required=False,
                ),
                ToolParameter(
                    name="params",
                    type="object",
                    description="SQL parameters for parameterized queries",
                    required=False,
                    default=None,
                ),
            ],
        )
        super().__init__(metadata)

    async def _get_sqlite_conn(self):
        """Get or create SQLite connection."""
        if self._conn is not None:
            return self._conn

        db_path = self._connection_string.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path == ":memory:":
            db_path = ":memory:"

        try:
            import aiosqlite

            self._conn = await aiosqlite.connect(db_path)
            self._conn.row_factory = aiosqlite.Row
        except ImportError:
            # Fallback to sync sqlite3 with asyncio.to_thread
            import asyncio
            import sqlite3

            def _connect():
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            self._conn = await asyncio.to_thread(_connect)

        return self._conn

    async def _execute(self, params: Dict[str, Any]) -> Any:
        operation = params["operation"]

        if self._db_type == "sqlite":
            return await self._execute_sqlite(operation, params)
        else:
            return await self._execute_postgresql(operation, params)

    async def _execute_sqlite(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQLite operation."""
        import asyncio

        conn = await self._get_sqlite_conn()

        if operation == "list_tables":
            try:
                import aiosqlite

                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                rows = await cursor.fetchall()
                tables = [row[0] for row in rows]
            except ImportError:
                def _list():
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    )
                    return [row[0] for row in cursor.fetchall()]
                tables = await asyncio.to_thread(_list)

            return {"success": True, "tables": tables}

        elif operation == "describe_table":
            table_name = params.get("table_name")
            if not table_name:
                return {"success": False, "error": "table_name is required"}

            try:
                import aiosqlite

                cursor = await conn.execute(f"PRAGMA table_info('{table_name}')")
                rows = await cursor.fetchall()
                columns = [
                    {"name": row[1], "type": row[2], "nullable": not row[3], "primary_key": bool(row[5])}
                    for row in rows
                ]
            except ImportError:
                def _describe():
                    cursor = conn.execute(f"PRAGMA table_info('{table_name}')")
                    return [
                        {"name": row[1], "type": row[2], "nullable": not row[3], "primary_key": bool(row[5])}
                        for row in cursor.fetchall()
                    ]
                columns = await asyncio.to_thread(_describe)

            return {"success": True, "table": table_name, "columns": columns}

        elif operation == "query":
            sql = params.get("sql")
            if not sql:
                return {"success": False, "error": "SQL is required for query operation"}

            sql_upper = sql.strip().upper()
            if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
                return {"success": False, "error": "Only SELECT/WITH queries are allowed. Use 'execute' for writes."}

            try:
                import aiosqlite

                cursor = await conn.execute(sql)
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                data = [dict(zip(columns, row)) for row in rows]
            except ImportError:
                def _query():
                    cursor = conn.execute(sql)
                    cols = [desc[0] for desc in cursor.description] if cursor.description else []
                    return cols, cursor.fetchall()
                columns, rows = await asyncio.to_thread(_query)
                data = [dict(zip(columns, row)) for row in rows]

            return {"success": True, "columns": columns, "rows": data[:1000], "row_count": len(data)}

        elif operation == "execute":
            if not self._allow_writes:
                return {"success": False, "error": "Write operations are disabled. Set allow_writes=True."}

            sql = params.get("sql")
            if not sql:
                return {"success": False, "error": "SQL is required for execute operation"}

            try:
                import aiosqlite

                await conn.execute(sql)
                await conn.commit()
            except ImportError:
                def _execute():
                    conn.execute(sql)
                    conn.commit()
                await asyncio.to_thread(_execute)

            return {"success": True, "message": "Statement executed successfully"}

        return {"success": False, "error": f"Unknown operation: {operation}"}

    async def _execute_postgresql(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PostgreSQL operation."""
        try:
            import asyncpg
        except ImportError:
            return {
                "success": False,
                "error": "asyncpg not installed. Install with: pip install asyncpg",
            }

        conn_str = self._connection_string.replace("postgresql://", "")

        try:
            conn = await asyncpg.connect(self._connection_string)
        except Exception as e:
            return {"success": False, "error": f"Connection failed: {e}"}

        try:
            if operation == "list_tables":
                rows = await conn.fetch(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )
                return {"success": True, "tables": [row["table_name"] for row in rows]}

            elif operation == "describe_table":
                table_name = params.get("table_name")
                if not table_name:
                    return {"success": False, "error": "table_name is required"}
                rows = await conn.fetch(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_name = $1 ORDER BY ordinal_position",
                    table_name,
                )
                columns = [
                    {"name": row["column_name"], "type": row["data_type"], "nullable": row["is_nullable"] == "YES"}
                    for row in rows
                ]
                return {"success": True, "table": table_name, "columns": columns}

            elif operation == "query":
                sql = params.get("sql")
                if not sql:
                    return {"success": False, "error": "SQL is required"}
                rows = await conn.fetch(sql)
                data = [dict(row) for row in rows[:1000]]
                return {"success": True, "rows": data, "row_count": len(rows)}

            elif operation == "execute":
                if not self._allow_writes:
                    return {"success": False, "error": "Write operations disabled"}
                sql = params.get("sql")
                if not sql:
                    return {"success": False, "error": "SQL is required"}
                await conn.execute(sql)
                return {"success": True, "message": "Executed successfully"}

        finally:
            await conn.close()

        return {"success": False, "error": f"Unknown operation: {operation}"}

    async def _shutdown(self):
        if self._conn:
            try:
                if hasattr(self._conn, "close"):
                    import asyncio
                    if asyncio.iscoroutinefunction(self._conn.close):
                        await self._conn.close()
                    else:
                        self._conn.close()
            except Exception:
                pass
            self._conn = None
