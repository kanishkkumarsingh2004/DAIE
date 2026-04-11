import asyncio
import os
import shutil
from daie.memory.sqlite_storage import SQLiteStorage
from daie.memory.storage import MemoryItem


async def test_sqlite_persistence():
    print("\n--- Testing SQLite Persistence ---")
    root_path = "./test_memory_db"
    if os.path.exists(root_path):
        shutil.rmtree(root_path)

    storage = SQLiteStorage()
    storage.initialize(root_path)

    agent_id = "agent_test_1"
    items = {
        "working": [
            MemoryItem(id="1", content="Thought 1", memory_type="working", timestamp=100.0),
            MemoryItem(id="2", content="Thought 2", memory_type="working", timestamp=200.0),
        ],
        "episodic": [
            MemoryItem(id="3", content="Event 1", memory_type="episodic", timestamp=150.0),
        ],
    }

    print(f"Saving memory for {agent_id}...")
    storage.save_agent_memory(agent_id, items)

    # Simulate restart
    print("Re-initializing storage...")
    storage2 = SQLiteStorage()
    storage2.initialize(root_path)

    loaded = storage2.load_agent_memory(agent_id)
    print(
        f"Loaded {len(loaded.get('working', []))} working items and {len(loaded.get('episodic', []))} episodic items."
    )

    assert len(loaded["working"]) == 2
    assert loaded["working"][0].content == "Thought 1"
    assert len(loaded["episodic"]) == 1

    print("✅ Persistence Test Passed!")


async def test_shared_memory():
    print("\n--- Testing Shared Memory Namespacing ---")
    root_path = "./test_shared_memory_db"
    if os.path.exists(root_path):
        shutil.rmtree(root_path)

    storage = SQLiteStorage()
    storage.initialize(root_path)

    namespace = "orchestrator_alpha"
    item = MemoryItem(
        id="shared_1", content="Shared knowledge", memory_type="semantic", timestamp=300.0
    )

    print(f"Storing shared memory in namespace '{namespace}'...")
    storage.store_shared_memory(namespace, item)

    print("Retrieving shared memory...")
    retrieved = storage.retrieve_shared_memory(namespace)
    print(f"Retrieved {len(retrieved)} items.")

    assert len(retrieved) == 1
    assert retrieved[0].content == "Shared knowledge"

    print("✅ Shared Memory Test Passed!")


async def run_tests():
    try:
        await test_sqlite_persistence()
        await test_shared_memory()
    finally:
        # Cleanup
        for path in ["./test_memory_db", "./test_shared_memory_db"]:
            if os.path.exists(path):
                shutil.rmtree(path)


if __name__ == "__main__":
    asyncio.run(run_tests())
