"""
Decentralized AI Ecosystem Library
A professional, optimized Python library for creating and managing AI agents with tools

This library provides a high-level API for:
- Creating and configuring AI agents with intelligent tool selection
- Defining and registering tools with automatic parameter fixing
- Setting up communication between agents
- Managing agent memory with efficient persistence
- Deploying agents with optimized performance

Example usage:
>>> from daie import Agent, AgentConfig, set_llm
>>> from daie.agents import AgentRole

# Configure LLM (default: llama3.2:latest from Ollama with session pooling)
>>> set_llm(ollama_llm="llama3.2:latest")

# Create an agent with configuration
>>> config = AgentConfig(
...     name="MyAgent",
...     role=AgentRole.GENERAL_PURPOSE,
...     task_timeout=30,
...     max_concurrent_tasks=10
... )
>>> agent = Agent(config=config)

# Start the agent (initializes task queue)
>>> await agent.start()

# Execute tasks with natural language
>>> result = await agent.execute_task("Say hello to Alice")
"""

__version__ = "1.0.4"

from daie.agents import (Agent, AgentConfig, AgentMessage, AgentRole)
from daie.cli import cli
from daie.core import (DecentralizedAISystem, HybridOrchestratorNode,
                       LLMConfig, LLMManager, LLMType, MultiNodeHybridSystem,
                       Node, Orchestrator, get_llm, get_llm_config, reset_llm_config,
                       set_llm)
from daie.tools import Tool, ToolRegistry

__all__ = [
    "__version__",
    "Agent",
    "AgentConfig",
    "AgentRole",
    "AgentMessage",
    "Orchestrator",
    "Tool",
    "ToolRegistry",
    "DecentralizedAISystem",
    "Node",
    "HybridOrchestratorNode",
    "MultiNodeHybridSystem",
    "cli",
    "set_llm",
    "get_llm",
    "get_llm_config",
    "reset_llm_config",
    "LLMManager",
    "LLMConfig",
    "LLMType",
]
