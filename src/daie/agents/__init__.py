"""
Agent creation and management module
"""

from daie.agents.agent import Agent
from daie.agents.config import AgentConfig, AgentRole
from daie.agents.message import AgentMessage
from daie.agents.parliament import Parliament, ReviewOutput, ConsensusOutput
from daie.agents.router import AgentRouter, create_router
from daie.agents.orchestrator import OrchestratorAgent
from daie.agents.hybrid_parliament import HybridParliamentOrchestrator
from daie.agents.serialization import AgentSnapshot
from daie.agents.structured_output import OutputValidationError

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentRole",
    "AgentMessage",
    "AgentSnapshot",
    "AgentRouter",
    "OutputValidationError",
    "Parliament",
    "ReviewOutput",
    "ConsensusOutput",
    "OrchestratorAgent",
    "HybridParliamentOrchestrator",
    "create_router",
]

