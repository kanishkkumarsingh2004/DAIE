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

__version__ = "1.0.2"

from daie.agents import Agent, AgentConfig
from daie.tools import Tool, ToolRegistry
from daie.core import DecentralizedAISystem
from daie.core import (
    set_llm,
    get_llm,
    get_llm_config,
    reset_llm_config,
    LLMManager,
    LLMConfig,
    LLMType,
)
from daie.cli import cli

__all__ = [
    "__version__",
    "Agent",
    "AgentConfig",
    "Tool",
    "ToolRegistry",
    "DecentralizedAISystem",
    "cli",
    "set_llm",
    "get_llm",
    "get_llm_config",
    "reset_llm_config",
    "LLMManager",
    "LLMConfig",
    "LLMType",
]
