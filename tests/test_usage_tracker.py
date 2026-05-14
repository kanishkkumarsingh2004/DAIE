"""
Tests for agent usage tracking and cost estimation.
"""

import csv

import pytest

from daie.core.usage_tracker import (
    PRICING_TABLE,
    UsageRecord,
    UsageTracker,
    _lookup_pricing,
)


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_tracker():
    """Reset the singleton tracker before each test."""
    UsageTracker._reset_singleton()
    yield
    UsageTracker._reset_singleton()


# ── UsageRecord ───────────────────────────────────────────────────────────────


def test_usage_record_creation():
    """UsageRecord can be created with defaults."""
    rec = UsageRecord(agent_id="a1", prompt_tokens=100, completion_tokens=50)
    assert rec.total_tokens == 0  # Not auto-computed in __init__
    assert rec.agent_id == "a1"


def test_usage_record_to_dict():
    """UsageRecord serializes to dict."""
    rec = UsageRecord(
        task_id="t1",
        agent_id="a1",
        agent_name="Test",
        provider="openai",
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        estimated_cost_usd=0.001,
    )
    d = rec.to_dict()
    assert d["task_id"] == "t1"
    assert d["total_tokens"] == 150
    assert "timestamp" in d


# ── pricing lookup ────────────────────────────────────────────────────────────


def test_lookup_pricing_ollama():
    """Ollama models are free."""
    inp, out = _lookup_pricing("ollama", "llama3.2:latest")
    assert inp == 0.0
    assert out == 0.0


def test_lookup_pricing_openai_exact():
    """Exact model match for OpenAI."""
    inp, out = _lookup_pricing("openai", "gpt-4o")
    assert inp == 0.0025
    assert out == 0.01


def test_lookup_pricing_openai_prefix():
    """Prefix match for versioned OpenAI models."""
    inp, out = _lookup_pricing("openai", "gpt-4o-2024-05-13")
    assert inp == 0.0025
    assert out == 0.01


def test_lookup_pricing_anthropic():
    """Anthropic pricing lookup."""
    inp, out = _lookup_pricing("anthropic", "claude-3-opus")
    assert inp == 0.015
    assert out == 0.075


def test_lookup_pricing_unknown_provider():
    """Unknown provider returns zero cost."""
    inp, out = _lookup_pricing("unknown_provider", "some-model")
    assert inp == 0.0
    assert out == 0.0


def test_lookup_pricing_fallback():
    """Unknown model falls back to wildcard."""
    inp, out = _lookup_pricing("openai", "future-model-2025")
    # Should hit the "*" wildcard for openai
    assert inp > 0.0


# ── UsageTracker.record ───────────────────────────────────────────────────────


def test_tracker_record_basic():
    """Tracker records a usage entry."""
    tracker = UsageTracker()
    rec = tracker.record(
        task_id="task-1",
        agent_id="agent-1",
        agent_name="TestAgent",
        provider="openai",
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50,
    )
    assert rec.total_tokens == 150
    assert rec.estimated_cost_usd > 0.0
    assert len(tracker.records) == 1


def test_tracker_record_ollama_zero_cost():
    """Ollama records have $0.00 cost."""
    tracker = UsageTracker()
    rec = tracker.record(
        task_id="task-1",
        agent_id="agent-1",
        agent_name="TestAgent",
        provider="ollama",
        model="llama3.2:latest",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    assert rec.estimated_cost_usd == 0.0


def test_tracker_record_cost_calculation():
    """Cost is calculated correctly from token counts and pricing."""
    tracker = UsageTracker()
    rec = tracker.record(
        task_id="task-1",
        agent_id="agent-1",
        agent_name="TestAgent",
        provider="openai",
        model="gpt-4o",
        prompt_tokens=1000,
        completion_tokens=1000,
    )
    # gpt-4o: input=$0.0025/1K, output=$0.01/1K
    expected = (1000 / 1000 * 0.0025) + (1000 / 1000 * 0.01)
    assert abs(rec.estimated_cost_usd - expected) < 1e-10


# ── Aggregation ───────────────────────────────────────────────────────────────


def _populate_tracker():
    """Helper: populate tracker with sample data."""
    tracker = UsageTracker()
    tracker.record("t1", "a1", "Agent1", "openai", "gpt-4o", 100, 50)
    tracker.record("t1", "a1", "Agent1", "openai", "gpt-4o", 200, 100)
    tracker.record("t2", "a1", "Agent1", "openai", "gpt-4o", 150, 75)
    tracker.record("t3", "a2", "Agent2", "ollama", "llama3", 500, 300)
    return tracker


def test_get_task_summary():
    """Task summary aggregates records for a specific task."""
    tracker = _populate_tracker()
    summary = tracker.get_task_summary("t1")
    assert summary["invocation_count"] == 2
    assert summary["task_count"] == 1
    assert summary["prompt_tokens"] == 300
    assert summary["completion_tokens"] == 150
    assert summary["total_tokens"] == 450


def test_get_task_summary_empty():
    """Task summary returns zero for non-existent task."""
    tracker = _populate_tracker()
    summary = tracker.get_task_summary("nonexistent")
    assert summary["invocation_count"] == 0
    assert summary["total_tokens"] == 0


def test_get_agent_summary():
    """Agent summary aggregates across all tasks for one agent."""
    tracker = _populate_tracker()
    summary = tracker.get_agent_summary("a1")
    assert summary["invocation_count"] == 3
    assert summary["task_count"] == 2  # t1 and t2
    assert summary["prompt_tokens"] == 450
    assert summary["estimated_cost_usd"] > 0.0


def test_get_agent_summary_ollama():
    """Agent summary for Ollama agent shows zero cost."""
    tracker = _populate_tracker()
    summary = tracker.get_agent_summary("a2")
    assert summary["invocation_count"] == 1
    assert summary["total_tokens"] == 800
    assert summary["estimated_cost_usd"] == 0.0


def test_get_session_summary():
    """Session summary aggregates across all agents."""
    tracker = _populate_tracker()
    summary = tracker.get_session_summary()
    assert summary["invocation_count"] == 4
    assert summary["task_count"] == 3  # t1, t2, t3
    assert "agents" in summary
    assert "a1" in summary["agents"]
    assert "a2" in summary["agents"]


def test_get_report():
    """Full report includes session, agents, and models."""
    tracker = _populate_tracker()
    report = tracker.get_report()
    assert "models" in report
    assert "openai/gpt-4o" in report["models"]
    assert "ollama/llama3" in report["models"]


# ── set_pricing ───────────────────────────────────────────────────────────────


def test_set_pricing_new_provider():
    """set_pricing adds new provider/model pricing."""
    UsageTracker.set_pricing("custom_provider", "custom-model", 0.01, 0.02)
    inp, out = _lookup_pricing("custom_provider", "custom-model")
    assert inp == 0.01
    assert out == 0.02
    # Cleanup
    del PRICING_TABLE["custom_provider"]


def test_set_pricing_override():
    """set_pricing overrides existing pricing."""
    original = _lookup_pricing("openai", "gpt-4o")
    UsageTracker.set_pricing("openai", "gpt-4o", 0.999, 0.888)
    assert _lookup_pricing("openai", "gpt-4o") == (0.999, 0.888)
    # Restore
    PRICING_TABLE["openai"]["gpt-4o"] = original


# ── export_csv ────────────────────────────────────────────────────────────────


def test_export_csv(tmp_path):
    """export_csv writes valid CSV with correct headers and data."""
    tracker = _populate_tracker()
    path = tmp_path / "usage.csv"
    result = tracker.export_csv(path)

    assert result == path
    assert path.exists()

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 4
    assert "task_id" in rows[0]
    assert "estimated_cost_usd" in rows[0]
    assert rows[0]["agent_name"] == "Agent1"


def test_export_csv_empty(tmp_path):
    """export_csv works with no records."""
    tracker = UsageTracker()
    path = tmp_path / "empty.csv"
    tracker.export_csv(path)

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 0


# ── lifecycle ─────────────────────────────────────────────────────────────────


def test_reset():
    """reset clears all records."""
    tracker =  ()
    assert len(tracker.records) == 4
    tracker.reset()
    assert len(tracker.records) == 0


def test_singleton():
    """UsageTracker is a singleton."""
    t1 = UsageTracker()
    t2 = UsageTracker()
    assert t1 is t2


def test_records_is_copy():
    """tracker.records returns a copy, not the internal list."""
    tracker = _populate_tracker()
    records = tracker.records
    records.clear()
    assert len(tracker.records) == 4  # Original unaffected
