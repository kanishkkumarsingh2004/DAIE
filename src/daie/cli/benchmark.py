"""
Swarm benchmarking CLI command.

Spins up a local multi-agent swarm, runs a preset task battery, and
reports latency, token throughput, and consensus accuracy.

Usage::

    daie benchmark --nodes 5 --tasks 20
    daie benchmark --nodes 3 --tasks 10 --provider ollama --model llama3.2:latest
    daie benchmark --output results.json
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from daie.utils.console import Console, print_error, print_header, print_info, print_success

logger = logging.getLogger(__name__)


# ── Task battery ──────────────────────────────────────────────────────────────
# Each task has a prompt, a type (solo/consensus), and an optional ground-truth
# answer for accuracy measurement.

TASK_BATTERY = [
    {
        "id": "math-001",
        "prompt": "What is 17 * 23? Return ONLY the number.",
        "type": "solo",
        "ground_truth": "391",
        "category": "arithmetic",
    },
    {
        "id": "math-002",
        "prompt": "What is 144 / 12? Return ONLY the number.",
        "type": "solo",
        "ground_truth": "12",
        "category": "arithmetic",
    },
    {
        "id": "math-003",
        "prompt": "What is the square root of 256? Return ONLY the number.",
        "type": "solo",
        "ground_truth": "16",
        "category": "arithmetic",
    },
    {
        "id": "reason-001",
        "prompt": "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost? Return ONLY the dollar amount.",
        "type": "solo",
        "ground_truth": "$0.05",
        "category": "reasoning",
    },
    {
        "id": "reason-002",
        "prompt": "If it takes 5 machines 5 minutes to make 5 widgets, how many minutes would it take 100 machines to make 100 widgets? Return ONLY the number of minutes.",
        "type": "solo",
        "ground_truth": "5",
        "category": "reasoning",
    },
    {
        "id": "classify-001",
        "prompt": "Classify the sentiment of this text as exactly one of: positive, negative, neutral. Text: 'I absolutely love this product, it changed my life!' Return ONLY the classification word.",
        "type": "solo",
        "ground_truth": "positive",
        "category": "classification",
    },
    {
        "id": "classify-002",
        "prompt": "Classify the sentiment of this text as exactly one of: positive, negative, neutral. Text: 'The service was okay, nothing special.' Return ONLY the classification word.",
        "type": "solo",
        "ground_truth": "neutral",
        "category": "classification",
    },
    {
        "id": "extract-001",
        "prompt": "Extract the email address from this text: 'Contact John at john.doe@example.com for details.' Return ONLY the email address.",
        "type": "solo",
        "ground_truth": "john.doe@example.com",
        "category": "extraction",
    },
    {
        "id": "consensus-001",
        "prompt": "What is the capital of France? Return ONLY the city name.",
        "type": "consensus",
        "ground_truth": "Paris",
        "category": "knowledge",
    },
    {
        "id": "consensus-002",
        "prompt": "Is water wet? Answer with ONLY 'yes' or 'no'.",
        "type": "consensus",
        "ground_truth": "yes",
        "category": "knowledge",
    },
    {
        "id": "format-001",
        "prompt": "List the first 5 prime numbers separated by commas. Return ONLY the numbers.",
        "type": "solo",
        "ground_truth": "2, 3, 5, 7, 11",
        "category": "formatting",
    },
    {
        "id": "format-002",
        "prompt": "Convert the number 255 to hexadecimal. Return ONLY the hex value with 0x prefix.",
        "type": "solo",
        "ground_truth": "0xFF",
        "category": "formatting",
    },
    {
        "id": "logic-001",
        "prompt": "All roses are flowers. Some flowers fade quickly. Can we conclude that some roses fade quickly? Answer ONLY 'yes' or 'no'.",
        "type": "solo",
        "ground_truth": "no",
        "category": "logic",
    },
    {
        "id": "logic-002",
        "prompt": "If A > B and B > C, is A > C? Answer ONLY 'yes' or 'no'.",
        "type": "solo",
        "ground_truth": "yes",
        "category": "logic",
    },
    {
        "id": "code-001",
        "prompt": "What does `len('hello')` return in Python? Return ONLY the number.",
        "type": "solo",
        "ground_truth": "5",
        "category": "code",
    },
    {
        "id": "consensus-003",
        "prompt": "What is 2 + 2? Return ONLY the number.",
        "type": "consensus",
        "ground_truth": "4",
        "category": "arithmetic",
    },
    {
        "id": "translate-001",
        "prompt": "Translate 'hello' to Spanish. Return ONLY the Spanish word.",
        "type": "solo",
        "ground_truth": "hola",
        "category": "translation",
    },
    {
        "id": "reason-003",
        "prompt": "A farmer has 17 sheep. All but 9 die. How many sheep are left? Return ONLY the number.",
        "type": "solo",
        "ground_truth": "9",
        "category": "reasoning",
    },
    {
        "id": "classify-003",
        "prompt": "Is the number 37 prime? Answer ONLY 'yes' or 'no'.",
        "type": "solo",
        "ground_truth": "yes",
        "category": "classification",
    },
    {
        "id": "consensus-004",
        "prompt": "How many continents are there on Earth? Return ONLY the number.",
        "type": "consensus",
        "ground_truth": "7",
        "category": "knowledge",
    },
]


# ── Result data model ─────────────────────────────────────────────────────────


@dataclass
class TaskResult:
    """Result of a single benchmark task."""

    task_id: str = ""
    category: str = ""
    task_type: str = ""  # "solo" or "consensus"
    agent_id: str = ""
    prompt: str = ""
    expected: str = ""
    actual: str = ""
    correct: bool = False
    latency_ms: float = 0.0
    tokens_used: int = 0


@dataclass
class BenchmarkReport:
    """Aggregated benchmark report."""

    node_count: int = 0
    task_count: int = 0
    provider: str = ""
    model: str = ""
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    total_tokens: int = 0
    tokens_per_second: float = 0.0
    accuracy: float = 0.0
    consensus_accuracy: float = 0.0
    solo_accuracy: float = 0.0
    category_accuracy: Dict[str, float] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Accuracy checker ──────────────────────────────────────────────────────────


def _check_accuracy(expected: str, actual: str) -> bool:
    """
    Fuzzy accuracy check — normalizes whitespace, case, and common
    formatting differences before comparing.
    """
    def normalize(s: str) -> str:
        s = s.strip().lower()
        # Remove common wrappers
        for prefix in ["the answer is ", "answer: ", "result: "]:
            if s.startswith(prefix):
                s = s[len(prefix):]
        # Remove trailing punctuation
        s = s.rstrip(".")
        # Normalize whitespace
        s = " ".join(s.split())
        return s

    return normalize(expected) in normalize(actual) or normalize(actual) in normalize(expected)


# ── Core benchmark runner ─────────────────────────────────────────────────────


async def _run_benchmark(
    node_count: int,
    task_count: int,
    provider: str,
    model: str,
    verbose: bool = False,
) -> BenchmarkReport:
    """
    Spin up agents, run the task battery, and collect results.
    """
    from daie.agents import Agent, AgentConfig, AgentRole

    # Select tasks (cycle through the battery if task_count > len)
    tasks = []
    for i in range(task_count):
        tasks.append(TASK_BATTERY[i % len(TASK_BATTERY)])

    # Create agents
    print_info(f"Spinning up {node_count} agent(s)...")
    agents = []
    for i in range(node_count):
        config = AgentConfig(
            name=f"BenchAgent-{i}",
            role=AgentRole.GENERAL_PURPOSE,
            goal="Execute benchmark tasks accurately and concisely",
            system_prompt=(
                "You are a benchmark agent. Answer questions as concisely as possible. "
                "Return ONLY the requested answer with no explanation or extra text."
            ),
            llm_provider=provider,
            llm_model=model,
        )
        agent = Agent(config=config)
        agents.append(agent)

    # Start all agents
    for agent in agents:
        await agent.start()

    print_success(f"{node_count} agent(s) ready")
    print_info(f"Running {task_count} task(s)...")
    print()

    results: List[TaskResult] = []
    task_idx = 0

    for task in tasks:
        task_idx += 1
        task_id = task["id"]
        task_type = task["type"]
        prompt = task["prompt"]
        expected = task["ground_truth"]
        category = task["category"]

        # Round-robin agent assignment for solo tasks
        agent = agents[task_idx % node_count]

        start_time = time.perf_counter()

        try:
            if task_type == "consensus" and node_count >= 2:
                # Use Parliament for consensus tasks
                from daie.agents import Parliament

                parliament = Parliament(sub_agents=agents[:min(node_count, 4)], max_review_rounds=1)
                raw_result = await parliament.deliberate(prompt)
                if isinstance(raw_result, dict):
                    actual = str(raw_result.get("final_answer", raw_result))
                else:
                    actual = str(raw_result)
            else:
                actual = await agent.execute_task(prompt)
        except Exception as exc:
            actual = f"[ERROR: {exc}]"
            logger.warning(f"Task {task_id} failed: {exc}")

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        correct = _check_accuracy(expected, actual)

        # Token tracking
        tokens = agent._current_task_tokens

        result = TaskResult(
            task_id=task_id,
            category=category,
            task_type=task_type,
            agent_id=agent.id,
            prompt=prompt,
            expected=expected,
            actual=actual.strip()[:200],
            correct=correct,
            latency_ms=round(elapsed_ms, 2),
            tokens_used=tokens,
        )
        results.append(result)

        # Live progress
        status = f"{Console.OKGREEN}✓{Console.ENDC}" if correct else f"{Console.FAIL}✗{Console.ENDC}"
        print(
            f"  [{task_idx:3d}/{task_count}] {status} {task_id:<16s} "
            f"{elapsed_ms:8.0f}ms  {tokens:5d} tok  "
            f"{'(' + category + ')':>16s}"
        )

        if verbose and not correct:
            print(f"           Expected: {expected}")
            print(f"           Got:      {actual.strip()[:100]}")

    # Stop agents
    for agent in agents:
        await agent.stop()

    # ── Compile report ────────────────────────────────────────────────────
    latencies = [r.latency_ms for r in results]
    total_tokens = sum(r.tokens_used for r in results)
    total_latency = sum(latencies)

    solo_results = [r for r in results if r.task_type == "solo"]
    consensus_results = [r for r in results if r.task_type == "consensus"]

    # Category breakdown
    categories = set(r.category for r in results)
    category_accuracy = {}
    for cat in categories:
        cat_results = [r for r in results if r.category == cat]
        if cat_results:
            category_accuracy[cat] = sum(1 for r in cat_results if r.correct) / len(cat_results)

    report = BenchmarkReport(
        node_count=node_count,
        task_count=task_count,
        provider=provider,
        model=model,
        total_latency_ms=round(total_latency, 2),
        avg_latency_ms=round(statistics.mean(latencies), 2) if latencies else 0,
        p50_latency_ms=round(statistics.median(latencies), 2) if latencies else 0,
        p95_latency_ms=round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 2),
        p99_latency_ms=round(sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0, 2),
        min_latency_ms=round(min(latencies), 2) if latencies else 0,
        max_latency_ms=round(max(latencies), 2) if latencies else 0,
        total_tokens=total_tokens,
        tokens_per_second=round(total_tokens / (total_latency / 1000), 2) if total_latency > 0 else 0,
        accuracy=sum(1 for r in results if r.correct) / len(results) if results else 0,
        solo_accuracy=(
            sum(1 for r in solo_results if r.correct) / len(solo_results)
            if solo_results else 0
        ),
        consensus_accuracy=(
            sum(1 for r in consensus_results if r.correct) / len(consensus_results)
            if consensus_results else 0
        ),
        category_accuracy=category_accuracy,
        results=[asdict(r) for r in results],
    )

    return report


# ── Pretty printing ───────────────────────────────────────────────────────────


def _print_report(report: BenchmarkReport):
    """Print the benchmark report with premium formatting."""
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║              DAIE SWARM BENCHMARK REPORT                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # Configuration
    print(f"  {'Provider':<20s}  {report.provider}")
    print(f"  {'Model':<20s}  {report.model}")
    print(f"  {'Agents':<20s}  {report.node_count}")
    print(f"  {'Tasks executed':<20s}  {report.task_count}")
    print()

    # Latency
    print("  ┌─── Latency ───────────────────────────────────────────────┐")
    print(f"  │  {'Total':<14s}  {report.total_latency_ms:>10.0f} ms                       │")
    print(f"  │  {'Average':<14s}  {report.avg_latency_ms:>10.0f} ms                       │")
    print(f"  │  {'P50 (median)':<14s}  {report.p50_latency_ms:>10.0f} ms                       │")
    print(f"  │  {'P95':<14s}  {report.p95_latency_ms:>10.0f} ms                       │")
    print(f"  │  {'P99':<14s}  {report.p99_latency_ms:>10.0f} ms                       │")
    print(f"  │  {'Min':<14s}  {report.min_latency_ms:>10.0f} ms                       │")
    print(f"  │  {'Max':<14s}  {report.max_latency_ms:>10.0f} ms                       │")
    print("  └──────────────────────────────────────────────────────────┘")
    print()

    # Throughput
    print("  ┌─── Throughput ─────────────────────────────────────────────┐")
    print(f"  │  {'Total tokens':<14s}  {report.total_tokens:>10d}                            │")
    print(f"  │  {'Tokens/sec':<14s}  {report.tokens_per_second:>10.1f}                            │")
    print("  └──────────────────────────────────────────────────────────┘")
    print()

    # Accuracy
    accuracy_color = Console.OKGREEN if report.accuracy >= 0.8 else (
        Console.WARNING if report.accuracy >= 0.5 else Console.FAIL
    )
    print("  ┌─── Accuracy ──────────────────────────────────────────────┐")
    print(f"  │  {'Overall':<14s}  {accuracy_color}{report.accuracy:>9.1%}{Console.ENDC}                             │")
    print(f"  │  {'Solo tasks':<14s}  {report.solo_accuracy:>9.1%}                             │")
    print(f"  │  {'Consensus':<14s}  {report.consensus_accuracy:>9.1%}                             │")
    print("  │                                                          │")

    for cat, acc in sorted(report.category_accuracy.items()):
        cat_color = Console.OKGREEN if acc >= 0.8 else (Console.WARNING if acc >= 0.5 else Console.FAIL)
        print(f"  │    {cat:<12s}  {cat_color}{acc:>9.1%}{Console.ENDC}                             │")

    print("  └──────────────────────────────────────────────────────────┘")
    print()


# ── CLI integration ───────────────────────────────────────────────────────────


def run_benchmark_command(args: argparse.Namespace):
    """Entry point for `daie benchmark` CLI command."""
    print_header("⚡ DAIE Swarm Benchmark")
    print()

    node_count = args.nodes
    task_count = args.tasks
    provider = args.provider
    model = args.model
    output_file = args.output
    verbose = args.verbose

    print_info(f"Configuration: {node_count} nodes × {task_count} tasks")
    print_info(f"LLM: {provider}/{model}")
    print()

    # Set up the LLM
    from daie.core.llm_manager import LLMType, set_llm
    set_llm(llm_type=LLMType(provider), model_name=model)

    # Run the benchmark
    try:
        report = asyncio.run(
            _run_benchmark(
                node_count=node_count,
                task_count=task_count,
                provider=provider,
                model=model,
                verbose=verbose,
            )
        )
    except KeyboardInterrupt:
        print_error("\nBenchmark interrupted by user")
        return
    except Exception as exc:
        print_error(f"Benchmark failed: {exc}")
        logger.error(f"Benchmark failed: {exc}", exc_info=True)
        return

    _print_report(report)

    # Save JSON output if requested
    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        print_success(f"Report saved to {path}")


def register_benchmark_commands(subparsers):
    """Register the benchmark subcommand with the main CLI parser."""
    bench_parser = subparsers.add_parser(
        "benchmark",
        help="Run swarm benchmark to measure latency, throughput, and accuracy",
    )
    bench_parser.add_argument(
        "--nodes", "-n",
        type=int,
        default=3,
        help="Number of agents to spin up (default: 3)",
    )
    bench_parser.add_argument(
        "--tasks", "-t",
        type=int,
        default=10,
        help="Number of tasks to run (default: 10)",
    )
    bench_parser.add_argument(
        "--provider", "-p",
        type=str,
        default="ollama",
        help="LLM provider (default: ollama)",
    )
    bench_parser.add_argument(
        "--model", "-m",
        type=str,
        default="llama3.2:latest",
        help="LLM model name (default: llama3.2:latest)",
    )
    bench_parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Save JSON report to this file path",
    )
    bench_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show expected vs actual for failed tasks",
    )
    bench_parser.set_defaults(func=run_benchmark_command)
