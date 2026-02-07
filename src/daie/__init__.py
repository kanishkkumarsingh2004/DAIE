"""
Decentralized AI Ecosystem Library
A simplified Python library for creating and deploying AI agents with tools

This library provides a high-level API for:
- Creating and configuring AI agents
- Defining and registering tools
- Setting up communication between agents
- Managing agent memory and state
- Deploying agents to various environments

Example usage:
>>> from daie import Agent, Tool, set_llm
>>> from daie.tools import WebSearchTool

# Configure LLM (default: llama3 from Ollama)
>>> set_llm(ollama_llm="llama3.2:latest")

# Create a tool
>>> search_tool = WebSearchTool(name="web_search", description="Search the web for information")

# Create an agent with tools
>>> agent = Agent(
...     name="MyAgent",
...     role="general-purpose",
...     tools=[search_tool]
... )

# Start the agent
>>> agent.start()
"""

__version__ = "1.0.0"

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
    LLMType
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
    "LLMType"
]
