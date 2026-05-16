"""
Agent usage tracking and cost estimation.

Tracks token usage per task, per agent, and per session. Provides
estimated cost for each LLM provider based on a built-in pricing table.

Usage::

    # Automatic — tracking is built into every agent
    result = await agent.execute_task("Summarize this data")
    print(agent.usage_report)

    # Session-wide report across all agents
    from daie.core.usage_tracker import UsageTracker
    tracker = UsageTracker()
    print(tracker.get_session_summary())
    tracker.export_csv("./usage_log.csv")
"""

import csv
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ── Pricing table (USD per 1K tokens) ────────────────────────────────────────
# Format: (provider, model_prefix) → (input_cost_per_1k, output_cost_per_1k)
# Users can override via UsageTracker.set_pricing()

PRICING_TABLE: Dict[str, Dict[str, tuple]] = {
    "ollama": {
        "*": (0.0, 0.0),  # Local models — free
    },
    "openai": {
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-4o": (0.0025, 0.01),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0005, 0.0015),
        "o1": (0.015, 0.06),
        "o1-mini": (0.003, 0.012),
        "*": (0.005, 0.015),  # Fallback for unknown OpenAI models
    },
    "anthropic": {
        "claude-sonnet-4-20250514": (0.003, 0.015),
        "claude-3-5-sonnet": (0.003, 0.015),
        "claude-3-haiku": (0.00025, 0.00125),
        "claude-3-opus": (0.015, 0.075),
        "*": (0.003, 0.015),  # Fallback
    },
    "google": {
        "gemini-pro": (0.000125, 0.000375),
        "gemini-1.5-pro": (0.00125, 0.005),
        "gemini-1.5-flash": (0.000075, 0.0003),
        "*": (0.00025, 0.001),  # Fallback
    },
    "azure": {
        "*": (0.005, 0.015),  # Same as OpenAI equivalents on average
    },
    "openrouter": {
        "*": (0.005, 0.015),  # Varies by model — user should override
    },
}


def _lookup_pricing(provider: str, model: str) -> tuple:
    """
    Look up the (input_cost_per_1k, output_cost_per_1k) for a provider/model.

    Tries exact match first, then prefix match, then wildcard.
    Returns (0.0, 0.0) if provider is unknown.
    """
    provider = provider.lower()
    model = model.lower()

    provider_prices = PRICING_TABLE.get(provider, {})
    if not provider_prices:
        return (0.0, 0.0)

    # Exact match
    if model in provider_prices:
        return provider_prices[model]

    # Prefix match (e.g. "gpt-4o-2024-05-13" matches "gpt-4o")
    for prefix, pricing in provider_prices.items():
        if prefix != "*" and model.startswith(prefix):
            return pricing

    # Wildcard fallback
    return provider_prices.get("*", (0.0, 0.0))


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class UsageRecord:
    """
    One LLM invocation record.

    Tracks token counts, cost, and metadata for a single LLM call
    within a task.
    """

    task_id: str = ""
    agent_id: str = ""
    agent_name: str = ""
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Tracker ───────────────────────────────────────────────────────────────────


class UsageTracker:
    """
    Singleton tracker for LLM token usage and cost estimation.

    Automatically records every LLM invocation across all agents in the
    process. Provides per-task, per-agent, and per-session aggregation.

    This class is a singleton — all agents share the same tracker instance.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._records: List[UsageRecord] = []
        self._initialized = True

    def record(
        self,
        task_id: str,
        agent_id: str,
        agent_name: str,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> UsageRecord:
        """
        Record a single LLM invocation.

        Args:
            task_id: Unique ID for the current task.
            agent_id: The agent's ID.
            agent_name: The agent's display name.
            provider: LLM provider (e.g. "openai", "ollama").
            model: Model name (e.g. "gpt-4o", "llama3.2:latest").
            prompt_tokens: Number of input tokens.
            completion_tokens: Number of output tokens.

        Returns:
            The created ``UsageRecord``.
        """
        total = prompt_tokens + completion_tokens
        input_cost, output_cost = _lookup_pricing(provider, model)
        estimated_cost = (prompt_tokens / 1000.0 * input_cost) + (
            completion_tokens / 1000.0 * output_cost
        )

        rec = UsageRecord(
            task_id=task_id,
            agent_id=agent_id,
            agent_name=agent_name,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            estimated_cost_usd=estimated_cost,
        )
        self._records.append(rec)

        logger.debug(
            f"Usage: {agent_name} [{provider}/{model}] "
            f"prompt={prompt_tokens} completion={completion_tokens} "
            f"cost=${estimated_cost:.6f}"
        )
        return rec

    # ── Aggregation ───────────────────────────────────────────────────────

    def get_task_summary(self, task_id: str) -> Dict[str, Any]:
        """Get aggregated usage for a specific task."""
        records = [r for r in self._records if r.task_id == task_id]
        return self._aggregate(records, label=f"task:{task_id}")

    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get aggregated usage for a specific agent across all tasks."""
        records = [r for r in self._records if r.agent_id == agent_id]
        return self._aggregate(records, label=f"agent:{agent_id}")

    def get_session_summary(self) -> Dict[str, Any]:
        """Get aggregated usage across all agents and tasks in this session."""
        summary = self._aggregate(self._records, label="session")

        # Add per-agent breakdown
        agent_ids = set(r.agent_id for r in self._records)
        summary["agents"] = {
            aid: self._aggregate(
                [r for r in self._records if r.agent_id == aid],
                label=f"agent:{aid}",
            )
            for aid in agent_ids
        }
        return summary

    def get_report(self) -> Dict[str, Any]:
        """
        Full report with session summary, per-agent breakdown,
        and per-model breakdown.
        """
        session = self.get_session_summary()

        # Per-model breakdown
        models = set((r.provider, r.model) for r in self._records)
        session["models"] = {}
        for provider, model in models:
            key = f"{provider}/{model}"
            model_records = [
                r for r in self._records if r.provider == provider and r.model == model
            ]
            session["models"][key] = self._aggregate(model_records, label=key)

        return session

    def _aggregate(self, records: List[UsageRecord], label: str = "") -> Dict[str, Any]:
        """Aggregate a list of usage records into a summary."""
        if not records:
            return {
                "label": label,
                "invocation_count": 0,
                "task_count": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
            }

        return {
            "label": label,
            "invocation_count": len(records),
            "task_count": len(set(r.task_id for r in records)),
            "prompt_tokens": sum(r.prompt_tokens for r in records),
            "completion_tokens": sum(r.completion_tokens for r in records),
            "total_tokens": sum(r.total_tokens for r in records),
            "estimated_cost_usd": sum(r.estimated_cost_usd for r in records),
        }

    # ── Pricing ───────────────────────────────────────────────────────────

    @staticmethod
    def set_pricing(
        provider: str, model: str, input_cost_per_1k: float, output_cost_per_1k: float
    ):
        """
        Override or add pricing for a specific provider/model.

        Args:
            provider: Provider name (e.g. "openai", "anthropic").
            model: Model name or "*" for wildcard.
            input_cost_per_1k: Cost per 1K input tokens in USD.
            output_cost_per_1k: Cost per 1K output tokens in USD.
        """
        provider = provider.lower()
        if provider not in PRICING_TABLE:
            PRICING_TABLE[provider] = {}
        PRICING_TABLE[provider][model.lower()] = (input_cost_per_1k, output_cost_per_1k)
        logger.info(f"Pricing updated: {provider}/{model} = ${input_cost_per_1k}/${output_cost_per_1k} per 1K tokens")

    # ── Export ────────────────────────────────────────────────────────────

    def export_csv(self, path: Union[str, Path]) -> Path:
        """
        Export all usage records to a CSV file.

        Args:
            path: File path for the CSV output.

        Returns:
            The resolved path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "task_id", "agent_id", "agent_name", "provider", "model",
            "prompt_tokens", "completion_tokens", "total_tokens",
            "estimated_cost_usd", "timestamp",
        ]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for rec in self._records:
                writer.writerow(rec.to_dict())

        logger.info(f"Usage records exported to {path} ({len(self._records)} records)")
        return path

    # ── Lifecycle ─────────────────────────────────────────────────────────

    @property
    def records(self) -> List[UsageRecord]:
        """All recorded usage entries (read-only copy)."""
        return list(self._records)

    def reset(self):
        """Clear all recorded usage data."""
        count = len(self._records)
        self._records.clear()
        logger.info(f"Usage tracker reset ({count} records cleared)")

    @classmethod
    def _reset_singleton(cls):
        """Reset the singleton instance (for testing only)."""
        cls._instance = None
