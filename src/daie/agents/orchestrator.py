"""
Specialized Orchestrator Agent for complex task decomposition and delegation.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from daie.agents.agent import Agent
from daie.agents.config import AgentConfig
from daie.agents.message import AgentMessage

logger = logging.getLogger(__name__)


# Specialized prompt for decomposition
ORCHESTRATOR_SYSTEM_PROMPT = """You are a High-Level Orchestrator in a Decentralized AI Swarm.
Your primary goal is to take complex user requests and decompose them into smaller, manageable sub-tasks.

GUIDELINES:
1. DECOMPOSE: Break the task into discrete steps or specialized roles.
2. DISCOVER: Look for tools that allow you to delegate or communicate with other agents.
3. DELEGATE: Use tools like 'a2a_delegate_task' or 'a2a_send_message' to hand off work to specialists.
4. SYNTHESIZE: Once sub-tasks are complete, gather the results and provide a final cohesive answer.

Be strategic. Do not do everything yourself if there's a specialized tool or agent available.
If you need a tool you don't have, try calling it anyway; the swarm might discover a specialist for you.
"""


class OrchestratorAgent(Agent):
    """
    An agent specifically tuned for task decomposition and multi-agent coordination.
    It automatically adds delegation tools and uses a coordinator-focused system prompt.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="Orchestrator",
                role="coordinator",
                system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
                temperature=0.2  # Lower temperature for stable planning
            )
        else:
            # Append orchestrator rules to existing prompt
            config.system_prompt += f"\n\n{ORCHESTRATOR_SYSTEM_PROMPT}"
            
        super().__init__(config=config)
        logger.info(f"OrchestratorAgent '{self.name}' initialized.")

    async def decompose_and_execute(self, complex_task: str) -> str:
        """
        Explicitly run a decomposition phase before execution.
        """
        logger.info(f"Orchestrator '{self.name}' decomposing task: {complex_task[:50]}...")
        
        # We can add a "Plan" phase here if desired,
        # but the default ReAct loop already handles multi-step reasoning.
        # Here we just ensure we have the right tools.
        
        return await self.arun(complex_task)

    async def _handle_message(self, message: AgentMessage):
        """
        Enhanced message handling for coordination.
        """
        # If we receive a 'status_update' or 'progress' report, we might want to log it specifically
        if message.metadata.get("type") == "progress":
            logger.info(f"Orchestrator received progress update from {message.sender_id}: {message.content}")
            
        await super()._handle_message(message)
