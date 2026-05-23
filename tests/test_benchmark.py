"""
Tests for the swarm benchmarking module.
"""

import json

import pytest

from daie.cli.benchmark import (
    TASK_BATTERY,
    BenchmarkReport,
    TaskResult,
    _check_accuracy,
    _print_report,
)


# ── Task battery ──────────────────────────────────────────────────────────────


def test_task_battery_is_non_empty():
    """Task battery has at least 10 tasks."""
    assert len(TASK_BATTERY) >= 10


def test_task_battery_has_required_fields():
    """Every task in the battery has required fields."""
    required_keys = {"id", "prompt", "type", "ground_truth", "category"}
    for task in TASK_BATTERY:
        assert required_keys.issubset(task.keys()), f"Task {task.get('id', '?')} missing keys"


def test_task_battery_has_solo_and_consensus():
    """Task battery includes both solo and consensus tasks."""
    types = set(t["type"] for t in TASK_BATTERY)
    assert "solo" in types
    assert "consensus" in types


def test_task_battery_has_diverse_categories():
    """Task battery covers multiple categories."""
    categories = set(t["category"] for t in TASK_BATTERY)
    assert len(categories) >= 5  # arithmetic, reasoning, classification, etc.


def test_task_ids_are_unique():
    """All task IDs are unique."""
    ids = [t["id"] for t in TASK_BATTERY]
    assert len(ids) == len(set(ids))


# ── Accuracy checker ──────────────────────────────────────────────────────────


def test_check_accuracy_exact_match():
    """Exact match returns True."""
    assert _check_accuracy("42", "42") is True


def test_check_accuracy_case_insensitive():
    """Case-insensitive matching."""
    assert _check_accuracy("Paris", "paris") is True
    assert _check_accuracy("YES", "yes") is True


def test_check_accuracy_whitespace():
    """Handles extra whitespace."""
    assert _check_accuracy("42", "  42  ") is True


def test_check_accuracy_prefix_stripping():
    """Strips common answer prefixes."""
    assert _check_accuracy("42", "The answer is 42") is True
    assert _check_accuracy("42", "Answer: 42") is True


def test_check_accuracy_substring_match():
    """Substring matching works."""
    assert _check_accuracy("positive", "The sentiment is positive.") is True


def test_check_accuracy_mismatch():
    """Clear mismatches return False."""
    assert _check_accuracy("42", "43") is False
    assert _check_accuracy("yes", "no") is False


def test_check_accuracy_trailing_period():
    """Trailing periods are stripped."""
    assert _check_accuracy("Paris", "Paris.") is True


# ── TaskResult ────────────────────────────────────────────────────────────────


def test_task_result_creation():
    """TaskResult can be created with defaults."""
    r = TaskResult(task_id="t1", correct=True, latency_ms=150.5)
    assert r.task_id == "t1"
    assert r.correct is True
    assert r.latency_ms == 150.5


# ── BenchmarkReport ──────────────────────────────────────────────────────────


def test_benchmark_report_creation():
    """BenchmarkReport can be created with defaults."""
    report = BenchmarkReport(
        node_count=3,
        task_count=10,
        provider="ollama",
        model="llama3.2:latest",
    )
    assert report.node_count == 3
    assert report.accuracy == 0.0


def test_benchmark_report_to_dict():
    """BenchmarkReport serializes to dict."""
    report = BenchmarkReport(
        node_count=5,
        task_count=20,
        accuracy=0.85,
        total_tokens=5000,
    )
    d = report.to_dict()
    assert d["node_count"] == 5
    assert d["accuracy"] == 0.85
    assert d["total_tokens"] == 5000
    assert "results" in d


def test_benchmark_report_to_json():
    """BenchmarkReport serializes to valid JSON."""
    report = BenchmarkReport(
        node_count=3,
        task_count=10,
        accuracy=0.9,
        category_accuracy={"arithmetic": 1.0, "reasoning": 0.8},
    )
    json_str = json.dumps(report.to_dict())
    loaded = json.loads(json_str)
    assert loaded["category_accuracy"]["arithmetic"] == 1.0


# ── Report printing ──────────────────────────────────────────────────────────


def test_print_report_does_not_crash(capsys):
    """_print_report runs without errors."""
    report = BenchmarkReport(
        node_count=3,
        task_count=10,
        provider="ollama",
        model="llama3.2:latest",
        total_latency_ms=5000,
        avg_latency_ms=500,
        p50_latency_ms=450,
        p95_latency_ms=800,
        p99_latency_ms=950,
        min_latency_ms=200,
        max_latency_ms=1000,
        total_tokens=3000,
        tokens_per_second=600,
        accuracy=0.8,
        solo_accuracy=0.85,
        consensus_accuracy=0.75,
        category_accuracy={"arithmetic": 1.0, "reasoning": 0.67},
    )
    _print_report(report)
    captured = capsys.readouterr()
    assert "BENCHMARK REPORT" in captured.out
    assert "Latency" in captured.out
    assert "Throughput" in captured.out
    assert "Accuracy" in captured.out


# ── CLI registration ──────────────────────────────────────────────────────────


def test_benchmark_command_registered():
    """The benchmark command is registered in the CLI."""
    import argparse
    from daie.cli.benchmark import register_benchmark_commands

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    register_benchmark_commands(subparsers)

    # Parse benchmark args
    args = parser.parse_args(["benchmark", "--nodes", "5", "--tasks", "20"])
    assert args.nodes == 5
    assert args.tasks == 20
    assert args.provider == "ollama"
    assert args.model == "llama3.2:latest"
    assert hasattr(args, "func")


def test_benchmark_default_args():
    """Default benchmark args are sensible."""
    import argparse
    from daie.cli.benchmark import register_benchmark_commands

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    register_benchmark_commands(subparsers)

    args = parser.parse_args(["benchmark"])
    assert args.nodes == 3
    assert args.tasks == 10
    assert args.output is None
    assert args.verbose is False
