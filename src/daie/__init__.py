"""
Decentralized AI Ecosystem Library
A professional, production-ready Python library for building autonomous AI agents
with tool use, multi-agent orchestration, P2P networking, and persistent memory.

Example usage:
>>> from daie import Agent, AgentConfig, set_llm
>>> from daie.agents import AgentRole

>>> set_llm(ollama_llm="llama3.2:latest")
>>> agent = Agent(config=AgentConfig(name="MyAgent", role=AgentRole.GENERAL_PURPOSE))
>>> await agent.start()
>>> result = await agent.execute_task("Say hello")
>>> await agent.stop()
"""

__version__ = "1.1.0"
__author__ = "Kanishk Kumar Singh"
__email__ = "kanishkkumar2004@gmail.com"
__license__ = "MIT"

from daie.agents import Agent, AgentConfig, AgentMessage, AgentRole
from daie.cli import cli
from daie.core import (
    DecentralizedAISystem,
    HybridOrchestratorNode,
    LLMConfig,
    LLMManager,
    LLMType,
    MultiNodeHybridSystem,
    Node,
    Orchestrator,
    get_llm,
    get_llm_config,
    reset_llm_config,
    set_llm,
)
from daie.tools import Tool, ToolRegistry

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    # Agents
    "Agent",
    "AgentConfig",
    "AgentRole",
    "AgentMessage",
    # Orchestration
    "Orchestrator",
    "HybridOrchestratorNode",
    "MultiNodeHybridSystem",
    # Tools
    "Tool",
    "ToolRegistry",
    # System
    "DecentralizedAISystem",
    "Node",
    # LLM
    "set_llm",
    "get_llm",
    "get_llm_config",
    "reset_llm_config",
    "LLMManager",
    "LLMConfig",
    "LLMType",
    # CLI
    "cli",
]
