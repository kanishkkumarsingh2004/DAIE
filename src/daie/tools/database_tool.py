import logging
import asyncio
from typing import Any, Dict, List

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter

logger = logging.getLogger(__name__)


class DatabaseTool(Tool):
    """
    Professional Database Interaction Tool.

    Supports SQLite and PostgreSQL with native async execution.
    - 'query': Run SELECT/READ operations.
    - 'execute': Run INSERT/UPDATE/DELETE (if allow_writes=True).
    - 'inspect_schema': One-shot retrieval of all table schemas.
    - 'list_tables': Retrieve table names.
    - 'describe_table': Get detailed column info for a specific table.

    Example:
        >>> tool = DatabaseTool(connection_string="sqlite:///data.db")
        >>> result = await tool.execute({"operation": "inspect_schema"})
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
            description="Interact with SQLite or PostgreSQL databases. Query data, inspect schemas, and manage records.",
            category=ToolCategory.DATABASE,
            version="1.1.0",
            author="DAIE",
            capabilities=["sql_query", "schema_inspection", "data_management"],
            parameters=[
                ToolParameter(
                    name="operation",
                    type="string",
                    description="Database operation to perform",
                    required=True,
                    choices=["query", "execute", "list_tables", "describe_table", "inspect_schema"],
                ),
                ToolParameter(
                    name="sql",
                    type="string",
                    description="SQL statement for 'query' or 'execute'",
                    required=False,
                ),
                ToolParameter(
                    name="table_name",
                    type="string",
                    description="Table name for 'describe_table'",
                    required=False,
                ),
            ],
        )
        super().__init__(metadata)

    async def _execute(self, params: Dict[str, Any]) -> Any:
        operation = params["operation"]

        try:
            if self._db_type == "sqlite":
                return await self._execute_sqlite(operation, params)
            else:
                return await self._execute_postgresql(operation, params)
        except Exception as e:
            logger.error(f"Database error during {operation}: {e}")
            return {"success": False, "error": str(e)}

    async def _get_sqlite_conn(self):
        """Get or initialize async SQLite connection."""
        if self._conn:
            return self._conn

        db_path = self._connection_string.replace("sqlite:///", "").replace("sqlite://", "")
        if not db_path:
            db_path = ":memory:"

        try:
            import aiosqlite

            self._conn = await aiosqlite.connect(db_path)
            self._conn.row_factory = aiosqlite.Row
            return self._conn
        except ImportError:
            # Sync fallback
            import sqlite3

            def _sync_conn():
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            self._conn = await asyncio.to_thread(_sync_conn)
            return self._conn

    async def _execute_sqlite(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        conn = await self._get_sqlite_conn()

        if operation == "list_tables":
            sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            rows = await self._run_sqlite_query(conn, sql)
            return {"success": True, "tables": [r[0] for r in rows]}

        elif operation == "inspect_schema":
            tables_sql = (
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [r[0] for r in await self._run_sqlite_query(conn, tables_sql)]

            schema = {}
            for table in tables:
                info_sql = f"PRAGMA table_info('{table}')"
                columns = await self._run_sqlite_query(conn, info_sql)
                schema[table] = [{"name": c[1], "type": c[2], "pk": bool(c[5])} for c in columns]
            return {"success": True, "schema": schema}

        elif operation == "describe_table":
            table = params.get("table_name")
            if not table:
                return {"success": False, "error": "table_name required"}
            rows = await self._run_sqlite_query(conn, f"PRAGMA table_info('{table}')")
            return {"success": True, "table": table, "columns": [dict(r) for r in rows]}

        elif operation == "query":
            sql = params.get("sql")
            if not sql:
                return {"success": False, "error": "sql required"}
            if not sql.strip().upper().startswith(("SELECT", "WITH", "PRAGMA")):
                return {"success": False, "error": "Only read operations allowed for 'query'"}
            rows = await self._run_sqlite_query(conn, sql)
            return {"success": True, "rows": [dict(r) for r in rows[:1000]], "count": len(rows)}

        elif operation == "execute":
            if not self._allow_writes:
                return {"success": False, "error": "Writes disabled"}
            sql = params.get("sql")
            if not sql:
                return {"success": False, "error": "sql required"}

            if hasattr(conn, "execute"):  # aiosqlite
                await conn.execute(sql)
                await conn.commit()
            else:  # sqlite3 object

                def _do():
                    conn.execute(sql)
                    conn.commit()

                await asyncio.to_thread(_do)
            return {"success": True, "message": "Execution successful"}

        return {"success": False, "error": f"Unknown operation: {operation}"}

    async def _run_sqlite_query(self, conn, sql: str) -> List[Any]:
        """Helper to run query on either aiosqlite or sqlite3 backend."""
        if hasattr(conn, "execute_fetchall"):  # aiosqlite
            return await conn.execute_fetchall(sql)
        elif hasattr(conn, "execute"):  # aiosqlite alternative or fallback
            if asyncio.iscoroutinefunction(conn.execute):
                cursor = await conn.execute(sql)
                return await cursor.fetchall()
            else:
                return await asyncio.to_thread(lambda: conn.execute(sql).fetchall())
        return []

    async def _execute_postgresql(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import asyncpg
        except ImportError:
            return {"success": False, "error": "asyncpg not installed"}

        conn = await asyncpg.connect(self._connection_string)
        try:
            if operation == "list_tables":
                rows = await conn.fetch(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
                return {"success": True, "tables": [r["table_name"] for r in rows]}

            elif operation == "inspect_schema":
                rows = await conn.fetch(
                    "SELECT table_name, column_name, data_type "
                    "FROM information_schema.columns WHERE table_schema = 'public' "
                    "ORDER BY table_name, ordinal_position"
                )
                schema = {}
                for r in rows:
                    t = r["table_name"]
                    if t not in schema:
                        schema[t] = []
                    schema[t].append({"name": r["column_name"], "type": r["data_type"]})
                return {"success": True, "schema": schema}

            elif operation == "query":
                sql = params.get("sql")
                rows = await conn.fetch(sql)
                return {"success": True, "rows": [dict(r) for r in rows[:1000]], "count": len(rows)}

            elif operation == "execute":
                if not self._allow_writes:
                    return {"success": False, "error": "Writes disabled"}
                await conn.execute(params.get("sql"))
                return {"success": True, "message": "Execution successful"}

        finally:
            await conn.close()

    async def _shutdown(self):
        if self._conn:
            try:
                if hasattr(self._conn, "close"):
                    if asyncio.iscoroutinefunction(self._conn.close):
                        await self._conn.close()
                    else:
                        self._conn.close()
            except Exception:
                pass
            self._conn = None
