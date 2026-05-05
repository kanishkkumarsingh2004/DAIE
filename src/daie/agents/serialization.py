"""
Agent state serialization and hot-reload.

Provides the ability to pause a running agent, serialize its state to a
JSON snapshot file, and resume it on the same or a different machine.

Usage::

    # Pause and save
    snapshot_dict = await agent.pause()
    agent.snapshot("./checkpoint.json")

    # Resume (possibly on another machine)
    agent = Agent.from_snapshot("./checkpoint.json", tools=[...])
    await agent.start()

The snapshot captures all *declarative* state (config, identity, tool names,
memory references) while deliberately excluding *runtime* state (event loops,
open sockets, asyncio tasks, LLM handles) which is reconstructed on resume.
"""

import datetime
import json
import logging
import platform
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Bump this when the snapshot format changes incompatibly
SNAPSHOT_VERSION = 1


@dataclass
class AgentSnapshot:
    """
    Serializable representation of an agent's state.

    This captures everything needed to reconstruct an agent on a
    different machine or after a restart:

    - **version**: Schema version for forward-compatibility checks.
    - **agent_id**: The agent's unique identifier (preserved across machines).
    - **created_at**: ISO-8601 timestamp of when the snapshot was taken.
    - **config**: Full ``AgentConfig.to_dict()`` output.
    - **tool_names**: Names of tools that were registered at snapshot time.
    - **task_metrics**: Cumulative token and tool-call counts.
    - **memory**: Persistent memory configuration (path, type, enabled).
    - **metadata**: Environment info (hostname, Python version, DAIE version).
    """

    version: int = SNAPSHOT_VERSION
    agent_id: str = ""
    created_at: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    tool_names: List[str] = field(default_factory=list)
    task_metrics: Dict[str, int] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    # ── serialization helpers ─────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSnapshot":
        """Create a snapshot from a dictionary, ignoring unknown keys."""
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentSnapshot":
        """Deserialize from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Union[str, Path]) -> Path:
        """Write the snapshot to a JSON file. Returns the resolved path."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        logger.info(f"Agent snapshot saved to {path}")
        return path

    @classmethod
    def load(cls, path: Union[str, Path]) -> "AgentSnapshot":
        """Load a snapshot from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))

        # Version check
        file_version = data.get("version", 0)
        if file_version > SNAPSHOT_VERSION:
            logger.warning(
                f"Snapshot version {file_version} is newer than supported "
                f"version {SNAPSHOT_VERSION}. Some fields may be ignored."
            )
        return cls.from_dict(data)


def _get_daie_version() -> str:
    """Best-effort retrieval of the installed daie version."""
    try:
        from importlib.metadata import version
        return version("daie")
    except Exception:
        return "unknown"


def serialize_agent(agent) -> AgentSnapshot:
    """
    Extract all serializable state from an ``Agent`` instance.

    Args:
        agent: A ``daie.agents.Agent`` instance (running or stopped).

    Returns:
        An ``AgentSnapshot`` containing the agent's portable state.
    """
    # Config
    config_dict = agent.config.to_dict()

    # Tool names (order-preserving)
    tool_names = list(agent.tools.keys())

    # Task metrics
    task_metrics = {
        "total_tokens_used": getattr(agent, "_current_task_tokens", 0),
        "total_tool_calls": getattr(agent, "_current_task_tool_calls", 0),
    }

    # Memory info
    memory_info: Dict[str, Any] = {"persistent": False}
    if getattr(agent.config, "persistent_memory", False):
        memory_info["persistent"] = True
        memory_info["root_path"] = "./agent_memory"
        memory_info["storage_type"] = "binary"
        # If a memory manager is attached, try to extract its actual path
        mm = getattr(agent, "memory_manager", None)
        if mm and hasattr(mm, "config"):
            memory_info["root_path"] = getattr(mm.config, "memory_root_path", "./agent_memory")
            memory_info["storage_type"] = getattr(mm.config, "memory_storage_type", "binary")

    # Environment metadata
    env_metadata = {
        "hostname": platform.node(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "daie_version": _get_daie_version(),
        "platform": platform.platform(),
    }

    return AgentSnapshot(
        version=SNAPSHOT_VERSION,
        agent_id=agent.id,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        config=config_dict,
        tool_names=tool_names,
        task_metrics=task_metrics,
        memory=memory_info,
        metadata=env_metadata,
    )


def deserialize_agent(
    snapshot: AgentSnapshot,
    tools: Optional[List[Any]] = None,
):
    """
    Reconstruct an ``Agent`` from a snapshot.

    The agent is created in a **stopped** state. Call ``await agent.start()``
    to resume execution.

    Args:
        snapshot: An ``AgentSnapshot`` (loaded from file or dict).
        tools: Optional list of tool instances to register. If not provided,
            the agent will start with no tools and a warning will be logged
            for each tool that was present in the snapshot.

    Returns:
        A new ``Agent`` instance with restored config and identity.
    """
    from daie.agents.config import AgentConfig, AgentRole
    from daie.agents.agent import Agent

    # Reconstruct config
    config = AgentConfig.from_dict(snapshot.config)

    # Force the original agent_id so identity is preserved
    config.agent_id = snapshot.agent_id

    # Create agent (this also preserves the E2EE keypair from config)
    agent = Agent(config=config)

    # The agent_id should match, but force it for safety
    agent.id = snapshot.agent_id

    # Register provided tools and warn about missing ones
    provided_tool_names = set()
    if tools:
        for tool in tools:
            agent.add_tool(tool)
            tool_name = getattr(tool, "name", None)
            if tool_name:
                provided_tool_names.add(tool_name)

    # Check for tools that were in the snapshot but not re-registered
    for name in snapshot.tool_names:
        if name not in provided_tool_names:
            logger.warning(
                f"Tool '{name}' was present in the snapshot but was not "
                f"provided during deserialization. The agent will not have "
                f"access to this tool until it is re-registered."
            )

    logger.info(
        f"Agent '{config.name}' (ID: {snapshot.agent_id}) deserialized from "
        f"snapshot v{snapshot.version} taken at {snapshot.created_at}"
    )

    return agent
