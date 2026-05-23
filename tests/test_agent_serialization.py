"""
Tests for agent state serialization and hot-reload.
"""

import json
import os
import tempfile

import pytest

from daie.agents import Agent, AgentConfig, AgentRole, AgentSnapshot
from daie.agents.serialization import (
    SNAPSHOT_VERSION,
    deserialize_agent,
    serialize_agent,
)
from daie.tools import tool


# ── helpers ───────────────────────────────────────────────────────────────────


@tool(name="test_reverse", description="Reverse a string")
async def test_reverse(text: str) -> str:
    return text[::-1]


@tool(name="test_uppercase", description="Uppercase a string")
async def test_uppercase(text: str) -> str:
    return text.upper()


def _make_agent(**overrides) -> Agent:
    """Create a basic test agent."""
    defaults = dict(
        name="TestAgent",
        role=AgentRole.GENERAL_PURPOSE,
        goal="Unit testing",
        backstory="Created for tests",
        system_prompt="You are a test agent.",
    )
    defaults.update(overrides)
    config = AgentConfig(**defaults)
    agent = Agent(config=config)
    agent.add_tool(test_reverse)
    agent.add_tool(test_uppercase)
    return agent


# ── snapshot dataclass ────────────────────────────────────────────────────────


def test_snapshot_version():
    """Snapshot version is a positive integer."""
    assert SNAPSHOT_VERSION >= 1


def test_snapshot_roundtrip_dict():
    """AgentSnapshot survives dict serialization round-trip."""
    snap = AgentSnapshot(
        agent_id="abc-123",
        config={"name": "Test"},
        tool_names=["a", "b"],
    )
    d = snap.to_dict()
    restored = AgentSnapshot.from_dict(d)
    assert restored.agent_id == "abc-123"
    assert restored.config == {"name": "Test"}
    assert restored.tool_names == ["a", "b"]
    assert restored.version == SNAPSHOT_VERSION


def test_snapshot_roundtrip_json():
    """AgentSnapshot survives JSON string round-trip."""
    snap = AgentSnapshot(
        agent_id="xyz-789",
        config={"name": "JsonTest"},
        tool_names=["c"],
    )
    json_str = snap.to_json()
    restored = AgentSnapshot.from_json(json_str)
    assert restored.agent_id == "xyz-789"
    assert restored.tool_names == ["c"]


def test_snapshot_save_and_load(tmp_path):
    """AgentSnapshot can be saved to and loaded from a file."""
    snap = AgentSnapshot(
        agent_id="file-test",
        config={"name": "FileTest"},
        tool_names=["d", "e"],
    )
    path = tmp_path / "snapshot.json"
    snap.save(path)

    assert path.exists()

    loaded = AgentSnapshot.load(path)
    assert loaded.agent_id == "file-test"
    assert loaded.tool_names == ["d", "e"]

    # Verify the file is valid JSON
    with open(path) as f:
        data = json.load(f)
    assert data["version"] == SNAPSHOT_VERSION


def test_snapshot_load_missing_file():
    """Loading a non-existent snapshot file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        AgentSnapshot.load("/nonexistent/path/snapshot.json")


def test_snapshot_from_dict_ignores_unknown_keys():
    """Unknown keys in the dict are silently ignored."""
    snap = AgentSnapshot.from_dict({
        "agent_id": "test",
        "unknown_field": "should be ignored",
        "another_unknown": 42,
    })
    assert snap.agent_id == "test"
    assert not hasattr(snap, "unknown_field")


# ── serialize_agent / deserialize_agent ───────────────────────────────────────


def test_serialize_agent_captures_config():
    """serialize_agent captures the agent's config."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    assert snap.agent_id == agent.id
    assert snap.config["name"] == "TestAgent"
    assert snap.config["goal"] == "Unit testing"
    assert snap.version == SNAPSHOT_VERSION


def test_serialize_agent_captures_tool_names():
    """serialize_agent records the names of registered tools."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    assert "test_reverse" in snap.tool_names
    assert "test_uppercase" in snap.tool_names


def test_serialize_agent_captures_e2ee_keys():
    """serialize_agent preserves E2EE public and private keys."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    assert snap.config.get("public_key") is not None
    assert snap.config.get("private_key") is not None
    assert len(snap.config["public_key"]) > 0
    assert len(snap.config["private_key"]) > 0


def test_serialize_agent_captures_metadata():
    """serialize_agent includes environment metadata."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    assert "hostname" in snap.metadata
    assert "python_version" in snap.metadata
    assert "daie_version" in snap.metadata
    assert "platform" in snap.metadata


def test_serialize_agent_captures_created_at():
    """serialize_agent records a creation timestamp."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    assert snap.created_at != ""
    # Should be parseable as ISO-8601
    from datetime import datetime
    datetime.fromisoformat(snap.created_at)


def test_deserialize_agent_restores_identity():
    """deserialize_agent preserves agent ID and name."""
    agent = _make_agent()
    original_id = agent.id
    snap = serialize_agent(agent)

    restored = deserialize_agent(snap, tools=[test_reverse, test_uppercase])
    assert restored.id == original_id
    assert restored.name == "TestAgent"


def test_deserialize_agent_restores_config():
    """deserialize_agent restores full config."""
    agent = _make_agent(temperature=0.3, max_tokens=500)
    snap = serialize_agent(agent)

    restored = deserialize_agent(snap)
    assert restored.config.temperature == 0.3
    assert restored.config.max_tokens == 500


def test_deserialize_agent_restores_keys():
    """deserialize_agent preserves E2EE keypair identity."""
    agent = _make_agent()
    original_pub = agent.config.public_key
    original_priv = agent.config.private_key
    snap = serialize_agent(agent)

    restored = deserialize_agent(snap)
    assert restored.config.public_key == original_pub
    assert restored.config.private_key == original_priv


def test_deserialize_agent_registers_tools():
    """deserialize_agent registers provided tools."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    restored = deserialize_agent(snap, tools=[test_reverse])
    assert "test_reverse" in restored.tools
    assert "test_uppercase" not in restored.tools


def test_deserialize_agent_warns_missing_tools(caplog):
    """deserialize_agent warns about tools present in snapshot but not provided."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    import logging
    with caplog.at_level(logging.WARNING):
        restored = deserialize_agent(snap, tools=[test_reverse])

    assert any("test_uppercase" in record.message for record in caplog.records)


def test_deserialize_agent_is_stopped():
    """deserialize_agent creates agent in stopped state."""
    agent = _make_agent()
    snap = serialize_agent(agent)

    restored = deserialize_agent(snap)
    assert not restored.is_running


# ── Agent.snapshot / Agent.from_snapshot / Agent.pause ─────────────────────


def test_agent_snapshot_method():
    """Agent.snapshot() returns a dict with expected keys."""
    agent = _make_agent()
    d = agent.snapshot()

    assert isinstance(d, dict)
    assert d["agent_id"] == agent.id
    assert d["version"] == SNAPSHOT_VERSION
    assert "config" in d
    assert "tool_names" in d
    assert "metadata" in d


def test_agent_snapshot_to_file(tmp_path):
    """Agent.snapshot(path) writes JSON file."""
    agent = _make_agent()
    path = str(tmp_path / "agent.json")
    d = agent.snapshot(path)

    assert os.path.exists(path)
    with open(path) as f:
        loaded = json.load(f)
    assert loaded["agent_id"] == agent.id


def test_agent_from_snapshot_dict():
    """Agent.from_snapshot works with a dict."""
    agent = _make_agent()
    d = agent.snapshot()

    restored = Agent.from_snapshot(d, tools=[test_reverse, test_uppercase])
    assert restored.id == agent.id
    assert restored.name == "TestAgent"
    assert "test_reverse" in restored.tools


def test_agent_from_snapshot_file(tmp_path):
    """Agent.from_snapshot works with a file path."""
    agent = _make_agent()
    path = str(tmp_path / "agent.json")
    agent.snapshot(path)

    restored = Agent.from_snapshot(path, tools=[test_reverse])
    assert restored.id == agent.id
    assert "test_reverse" in restored.tools


def test_full_roundtrip(tmp_path):
    """Full round-trip: create → snapshot → file → from_snapshot → verify."""
    original = _make_agent(
        name="RoundTripper",
        goal="Survive serialization",
        temperature=0.42,
        persistent_memory=False,
    )
    original.add_tool(test_reverse)
    original.add_tool(test_uppercase)

    # Snapshot to file
    path = str(tmp_path / "roundtrip.json")
    snap_dict = original.snapshot(path)

    # Simulate loading on a different machine
    restored = Agent.from_snapshot(path, tools=[test_reverse, test_uppercase])

    # Verify identity
    assert restored.id == original.id
    assert restored.name == "RoundTripper"
    assert restored.config.goal == "Survive serialization"
    assert restored.config.temperature == 0.42

    # Verify tools
    assert set(restored.tools.keys()) == {"test_reverse", "test_uppercase"}

    # Verify E2EE keys preserved
    assert restored.config.public_key == original.config.public_key
    assert restored.config.private_key == original.config.private_key

    # Verify it's stopped
    assert not restored.is_running


@pytest.mark.asyncio
async def test_agent_pause():
    """Agent.pause() stops the agent and returns a snapshot."""
    agent = _make_agent()
    await agent.start()
    assert agent.is_running

    snap = await agent.pause()

    assert not agent.is_running
    assert isinstance(snap, dict)
    assert snap["agent_id"] == agent.id


@pytest.mark.asyncio
async def test_agent_pause_already_stopped():
    """Agent.pause() on a stopped agent just returns the snapshot."""
    agent = _make_agent()
    assert not agent.is_running

    snap = await agent.pause()
    assert isinstance(snap, dict)
    assert snap["agent_id"] == agent.id
