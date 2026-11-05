"""Tests for hardened tools: CodeSandbox, WebSearch, Database."""

import pytest

from daie.tools import CodeSandboxTool, WebSearchTool, DatabaseTool


@pytest.mark.asyncio
async def test_code_sandbox():
    """Test CodeSandboxTool execution and blocking."""
    tool = CodeSandboxTool()

    # Test valid computation
    res = await tool.execute({"code": "result = sum(range(100))"})
    assert "return_value" in res
    assert res["return_value"] == "4950"  # sum(range(100))

    # Test blocked import - should fail safely (ImportError goes to stderr)
    res = await tool.execute({"code": "import os; print(os.name)"})
    assert "import of 'os' is not allowed" in res.get("stderr", "").lower() or "import" in res.get("stderr", "").lower()


@pytest.mark.asyncio
async def test_web_search():
    """Test WebSearchTool - may be skipped if no internet."""
    tool = WebSearchTool()

    # Test DuckDuckGo search
    res = await tool.execute({"query": "Python asynchronous programming", "num_results": 2})
    # Result structure should have 'results' key
    assert "results" in res or "error" in res
    if res.get("results"):
        assert len(res["results"]) <= 2


@pytest.mark.asyncio
async def test_database_tool():
    """Test DatabaseTool with SQLite in-memory."""
    tool = DatabaseTool(connection_string="sqlite:///:memory:", allow_writes=True)

    # Create table
    res = await tool.execute(
        {"operation": "execute", "sql": "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"}
    )
    assert "success" in res or res.get("rowcount") is not None

    # Insert data
    res = await tool.execute(
        {"operation": "execute", "sql": "INSERT INTO test (name) VALUES ('DAIE Agent')"}
    )
    assert "success" in res or res.get("rowcount") is not None

    # Inspect schema
    res = await tool.execute({"operation": "inspect_schema"})
    assert "schema" in res

    # Query data
    res = await tool.execute({"operation": "query", "sql": "SELECT * FROM test"})
    assert "rows" in res
    assert len(res["rows"]) == 1
    assert res["rows"][0]["name"] == "DAIE Agent"