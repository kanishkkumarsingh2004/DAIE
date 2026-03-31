"""
Orchestrator architecture for multi-agent coordination.
"""

import asyncio
import logging
from typing import Any, List, Optional

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
        main_agent: Agent,
        sub_agents: List[Agent],
        context_name: str = "Classroom",
        main_role: str = "Teacher",
        sub_role: str = "Student",
        comm_manager: Optional[CommunicationManager] = None,
    ):
        self.main_agent = main_agent
        self.sub_agents = sub_agents
        self.context_name = context_name
        self.main_role = main_role
        self.sub_role = sub_role
        self.comm_manager = comm_manager or CommunicationManager()
        self._is_running = False

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
            f"You are the {self.main_role.upper()} in a {self.context_name}. Your {self.sub_role.lower()}s are:\n{sub_info}\n\n"
            "ORCHESTRATION RULES:\n"
            '1. If the user input is a greeting (like \'hi\', \'hello\', \'how are you\'), DO NOT delegate to others. Respond directly with a friendly greeting using {"thought":"reason", "answer":"..."}.\n'
            f"2. For tasks required specialized work, break them down and delegate sub-tasks to {self.sub_role.lower()}s individually.\n"
            "3. To delegate to a sub-agent, you MUST use the tool 'a2a_delegate_task' with parameters 'target_agent_id' and 'task_payload'.\n"
            '4. Example tool call: {"thought":"Delegating work", "tool":"a2a_delegate_task", "params":{"target_agent_id":"agent_id", "task_payload":{"task":"Specific task description"}}}\n'
            "5. After receiving answers, combine them into a final response.\n"
            "6. FINAL ANSWER FORMAT: Your final response MUST be a clear, professional, and well-structured string in the 'answer' field. DO NOT use sub-agent names to refer to the user (the user is your supervisor/client). DO NOT output raw JSON in the answer field itself."
        )
        self.main_agent.config.system_prompt = main_sys_prompt

        # Configure sub-agents
        for sub_agent in self.sub_agents:
            other_subs = [s for s in self.sub_agents if s.id != sub_agent.id]
            others_info = "\n".join([f"- {s.name} (ID: {s.id})" for s in other_subs])
            sub_sys_prompt = (
                f"{sub_agent.config.system_prompt}\n\n"
                f"You are a {self.sub_role.upper()} in a {self.context_name}. Your {self.main_role.lower()} is {self.main_agent.name} (ID: {self.main_agent.id}).\n"
                f"Other {self.sub_role.lower()}s in the {self.context_name} are:\n{others_info if others_info else '(None)'}\n\n"
                f"You should follow instructions from the {self.main_role.lower()}. "
                "You can discuss with others using 'a2a_send_message' if it helps solve the task."
            )
            sub_agent.config.system_prompt = sub_sys_prompt

        # Start main agent
        await self.main_agent.start(communication_manager=self.comm_manager)

        # Start sub-agents
        start_tasks = [sub_agent.start(communication_manager=self.comm_manager) for sub_agent in self.sub_agents]
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
