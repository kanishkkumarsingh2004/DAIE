"""
Chat Module

Provides functionality for running interactive chat loops with agents.
Includes pre-configured chat loop setup so users don't need to write
the full chat loop code. Simply configure and run!

Also includes configurations for:
- NodeChatConfig: Single node with orchestrator and sub-agents
- OrchestratorChatConfig: Multiple hybrid nodes working together
- HybridChatConfig: Simple chat loop for hybrid systems
"""

from .chat_loop_config import ChatLoopConfig
from .hybrid_chat_config import HybridChatConfig
from .node_chat_config import NodeChatConfig
from .orchestrator_chat_config import OrchestratorChatConfig

__all__ = ["ChatLoopConfig", "NodeChatConfig", "OrchestratorChatConfig", "HybridChatConfig"]
