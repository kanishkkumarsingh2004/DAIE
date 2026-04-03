"""
Orchestrator architecture for multi-agent coordination.
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from daie.agents.agent import Agent

from daie.communication.manager import CommunicationManager

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    A generic multi-agent orchestration layer.

    It consists of one main agent and multiple sub-agents.
    The main agent acts as the coordinator/orchestrator, delegating tasks
    to sub-agents and aggregating their results.
    """

    def __init__(
        self,
        main_agent: "Agent",
        sub_agents: List["Agent"],
        context_name: str = "Team Collaboration",
        main_role: str = "Coordinator",
        sub_role: str = "Specialist",
        comm_manager: Optional[CommunicationManager] = None,
    ):
        self.main_agent = main_agent
        self.sub_agents = sub_agents
        self.context_name = context_name
        self.main_role = main_role
        self.sub_role = sub_role
        self.comm_manager = comm_manager or CommunicationManager()
        self._is_running = False
        self._parent_orchestrator_id: Optional[str] = None
        self._child_orchestrator_ids: List[str] = []
        self._child_node_ids: List[str] = []

    async def start(self):
        """Start the main agent and all sub-agents."""
        if self._is_running:
            return

        # Start communication manager if not already running
        if not self.comm_manager._is_running:
            await self.comm_manager.start()

        # Configure main agent
        sub_info = "\n".join(
            [
                f"- {s.name} (ID: {s.id}) - Goal: {s.config.goal if s.config.goal else 'Assist with various tasks'}"
                for s in self.sub_agents
            ]
        )
        main_sys_prompt = (
            f"{self.main_agent.config.system_prompt}\n\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            f"║  ORCHESTRATION CONTEXT: {self.context_name:<37}║\n"
            "╚══════════════════════════════════════════════════════════════╝\n\n"
            f"Your Role    : {self.main_role.upper()} — You are the lead coordinator responsible for\n"
            f"               understanding user requests, delegating work to your team,\n"
            f"               and synthesizing their outputs into a single coherent response.\n\n"
            f"Your Team ({self.sub_role.lower()}s):\n"
            f"{sub_info}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "RESPONSE PROTOCOL\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "You MUST respond with exactly ONE valid JSON object. No other text.\n\n"
            "SCENARIO A — Direct response (greetings, simple questions, status updates):\n"
            '  {"thought": "This is a simple question I can answer directly.", "answer": "Your complete plain-text response."}\n\n'
            f"SCENARIO B — Delegation required (tasks needing a {self.sub_role.lower()}'s expertise):\n"
            "  Step 1 — Delegate the task:\n"
            '  {"thought": "This requires Luna\'s expertise. I will delegate.", "tool": "a2a_delegate_task", "params": {"target_agent_id": "<exact_agent_id>", "task_payload": {"task": "<clear task description>"}}}\n\n'
            "  Step 2 — After receiving the tool result, synthesize and respond:\n"
            '  {"thought": "Luna has completed the task. I will now present her findings.", "answer": "Based on the work completed: <incorporate agent_response here as natural prose>"}\n\n'
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "STRICT RULES — VIOLATIONS WILL CAUSE ERRORS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            '1. The "answer" field MUST always be a plain text string.\n'
            '   ✗ WRONG : {"answer": {"data": "..."}}\n'
            '   ✗ WRONG : {"answer": [{"name": "Luna"}]}\n'
            '   ✓ CORRECT: {"answer": "The team consists of Luna and Alex."}\n\n'
            '2. After every tool call, you MUST follow up with an {"answer": "..."} in the next step.\n'
            '3. NEVER return null. NEVER leave "answer" empty or undefined.\n'
            "4. Use the EXACT agent IDs listed above when calling a2a_delegate_task.\n"
            "5. Do not address the user by a team member's name."
        )
        self.main_agent.config.system_prompt = main_sys_prompt

        # Configure sub-agents
        for sub_agent in self.sub_agents:
            other_subs = [s for s in self.sub_agents if s.id != sub_agent.id]
            others_info = "\n".join([f"- {s.name} (ID: {s.id})" for s in other_subs])
            sub_sys_prompt = (
                f"{sub_agent.config.system_prompt}\n\n"
                "╔══════════════════════════════════════════════════════════════╗\n"
                f"║  TEAM CONTEXT: {self.context_name:<47}║\n"
                "╚══════════════════════════════════════════════════════════════╝\n\n"
                f"Your Role      : {self.sub_role.upper()} — You are a specialist team member responsible\n"
                f"                 for executing tasks assigned to you by your {self.main_role.lower()}.\n\n"
                f"Your {self.main_role.capitalize()}: {self.main_agent.name} (ID: {self.main_agent.id})\n"
                f"Your Colleagues:\n"
                f"{others_info if others_info else '  (You are the only specialist on this team.)'}\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "EXECUTION GUIDELINES\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"- When you receive a task from {self.main_agent.name}, execute it thoroughly and professionally.\n"
                "- Provide complete, well-structured responses — your output will be presented to the end user.\n"
                "- Be specific, accurate, and detailed. Avoid vague or placeholder responses.\n"
                "- If you cannot complete a task, clearly explain why and what information you would need.\n"
                f"- Collaborate proactively with {self.main_agent.name} and your colleagues to achieve the best outcome."
            )
            sub_agent.config.system_prompt = sub_sys_prompt

        # Start main agent
        await self.main_agent.start(communication_manager=self.comm_manager)

        # Start sub-agents — agent.start() auto-creates memory manager when
        # persistent_memory=True is set in the agent's config
        start_tasks = [
            sub_agent.start(communication_manager=self.comm_manager)
            for sub_agent in self.sub_agents
        ]
        await asyncio.gather(*start_tasks)

        self._is_running = True
        logger.info(f"{self.context_name} with {self.main_role} '{self.main_agent.name}' started.")

    async def execute_task(self, task: str) -> Any:
        """
        Send a task to the orchestrator.
        The main agent will receive the task and orchestrate the sub-agents.
        """
        if not self._is_running:
            await self.start()

        logger.info(f"{self.context_name} received task: {task}")
        # The main agent's execute_task has the ReAct loop and A2A tools
        return await self.main_agent.execute_task(task)

    def set_parent(self, parent_orchestrator_id: str) -> "Orchestrator":
        """
        Set a parent orchestrator for this orchestrator.

        Args:
            parent_orchestrator_id: Unique identifier of the parent orchestrator

        Returns:
            Self for method chaining
        """
        self._parent_orchestrator_id = parent_orchestrator_id
        logger.debug(f"Orchestrator {self.context_name} set parent to {parent_orchestrator_id}")
        return self

    def add_child_orchestrator(self, child_orchestrator_id: str) -> "Orchestrator":
        """
        Add a child orchestrator to this orchestrator.

        Args:
            child_orchestrator_id: Unique identifier of the child orchestrator

        Returns:
            Self for method chaining
        """
        if child_orchestrator_id not in self._child_orchestrator_ids:
            self._child_orchestrator_ids.append(child_orchestrator_id)
            logger.debug(f"Orchestrator {self.context_name} added child orchestrator {child_orchestrator_id}")
        return self

    def remove_child_orchestrator(self, child_orchestrator_id: str) -> "Orchestrator":
        """
        Remove a child orchestrator from this orchestrator.

        Args:
            child_orchestrator_id: Unique identifier of the child orchestrator to remove

        Returns:
            Self for method chaining
        """
        if child_orchestrator_id in self._child_orchestrator_ids:
            self._child_orchestrator_ids.remove(child_orchestrator_id)
            logger.debug(f"Orchestrator {self.context_name} removed child orchestrator {child_orchestrator_id}")
        return self

    @property
    def parent_orchestrator_id(self) -> Optional[str]:
        """Get the parent orchestrator ID"""
        return self._parent_orchestrator_id

    @property
    def child_orchestrator_ids(self) -> List[str]:
        """Get list of child orchestrator IDs"""
        return self._child_orchestrator_ids.copy()

    @property
    def child_orchestrator_count(self) -> int:
        """Get number of child orchestrators"""
        return len(self._child_orchestrator_ids)

    def add_child_node(self, child_node_id: str) -> "Orchestrator":
        """
        Add a child node to this orchestrator.

        Args:
            child_node_id: Unique identifier of the child node

        Returns:
            Self for method chaining
        """
        if child_node_id not in self._child_node_ids:
            self._child_node_ids.append(child_node_id)
            logger.debug(f"Orchestrator {self.context_name} added child node {child_node_id}")
        return self

    def remove_child_node(self, child_node_id: str) -> "Orchestrator":
        """
        Remove a child node from this orchestrator.

        Args:
            child_node_id: Unique identifier of the child node to remove

        Returns:
            Self for method chaining
        """
        if child_node_id in self._child_node_ids:
            self._child_node_ids.remove(child_node_id)
            logger.debug(f"Orchestrator {self.context_name} removed child node {child_node_id}")
        return self

    @property
    def child_node_ids(self) -> List[str]:
        """Get list of child node IDs"""
        return self._child_node_ids.copy()

    @property
    def child_node_count(self) -> int:
        """Get number of child nodes"""
        return len(self._child_node_ids)

    async def stop(self):
        """Stop all agents in the orchestrator."""
        if not self._is_running:
            return

        await self.main_agent.stop()
        stop_tasks = [s.stop() for s in self.sub_agents]
        await asyncio.gather(*stop_tasks)

        if self.comm_manager._is_running:
            await self.comm_manager.stop()

        self._is_running = False
        logger.info(f"{self.context_name} stopped.")
