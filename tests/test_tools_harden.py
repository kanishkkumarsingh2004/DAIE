import asyncio
from daie.tools import CodeSandboxTool, WebSearchTool, DatabaseTool


async def test_code_sandbox():
    print("\n--- Testing CodeSandboxTool ---")
    tool = CodeSandboxTool()

    # Test valid computation
    res = await tool.execute({"code": "result = sum(range(100))"})
    print(f"RES: {res}")

    # Test blocked import
    res = await tool.execute({"code": "import os; print(os.name)"})
    print(f"RES BLOCKED: {res}")


async def test_web_search():
    print("\n--- Testing WebSearchTool ---")
    tool = WebSearchTool()

    # Test DuckDuckGo
    res = await tool.execute({"query": "Python asynchronous programming", "num_results": 2})
    print(f"Search Results Count: {len(res.get('results', []))}")
    if res.get("results"):
        print(f"Top Result: {res['results'][0]['title']}")


async def test_database_tool():
    print("\n--- Testing DatabaseTool ---")
    tool = DatabaseTool(connection_string="sqlite:///:memory:", allow_writes=True)

    # Create table
    await tool.execute(
        {"operation": "execute", "sql": "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"}
    )

    # Insert data
    await tool.execute(
        {"operation": "execute", "sql": "INSERT INTO test (name) VALUES ('DAIE Agent')"}
    )

    # Inspect schema
    res = await tool.execute({"operation": "inspect_schema"})
    print(f"Schema: {res.get('schema')}")

    # Query data
    res = await tool.execute({"operation": "query", "sql": "SELECT * FROM test"})
    print(f"Query Results: {res.get('rows')}")


async def main():
    try:
        await test_code_sandbox()
        await test_web_search()
        await test_database_tool()
        print("\n✅ All tool tests completed (Note: Playwright requires installation to test).")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
