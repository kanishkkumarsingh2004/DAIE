"""
Agent-to-Agent communication tools.
"""

import asyncio
import json
from typing import Any, Dict

from daie.agents.message import AgentMessage
from daie.protocols.acp import AgentConnectProtocol, IOMapper
from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter


class A2ASendMessageTool(Tool):
    """
    Tool allowing an agent to send a message to another agent.
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="a2a_send_message",
            description="Send a text message to another agent identified by their agent ID and await a response.",
            category=ToolCategory.CUSTOM,
            parameters=[
                ToolParameter(
                    name="target_agent_id", type="string", description="ID of the receiving agent", required=True
                ),
                ToolParameter(name="message", type="string", description="The text message content", required=True),
            ],
        )
        super().__init__(metadata)
        self._agent_ref = None  # Reference to the calling agent

    def set_agent(self, agent):
        """Set the reference to the agent instance using this tool."""
        self._agent_ref = agent

    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target_agent_id = params.get("target_agent_id", "")
        message = params.get("message", "")

        if not target_agent_id or not message:
            return {"success": False, "error": "Both target_agent_id and message are required."}

        if not self._agent_ref:
            return {"success": False, "error": "Tool not bound to an agent context."}

        comm_mgr = getattr(self._agent_ref, "communication_manager", None)
        if not comm_mgr:
            return {"success": False, "error": "Communication Manager is not attached to this agent."}

        # Send the message
        agent_msg = AgentMessage(
            sender_id=self._agent_ref.id, receiver_id=target_agent_id, content=message, message_type="text"
        )

        success = await comm_mgr.send_message(agent_msg)
        return {
            "success": success,
            "info": f"Message dispatched to {target_agent_id}",
            "note": "A response should be awaited via the communication loop if synchronous wait is not enabled.",
        }


class A2ADelegateTaskTool(Tool):
    """
    Tool utilizing the Agent Connect Protocol to correctly delegate mapped tasks to other agents.
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="a2a_delegate_task",
            description="Delegate a specialized task to another agent. Optionally provide mapping rules for I/O mapper.",
            category=ToolCategory.CUSTOM,
            parameters=[
                ToolParameter(
                    name="target_agent_id", type="string", description="ID of the receiving agent", required=True
                ),
                ToolParameter(
                    name="task_payload", type="object", description="JSON payload of the task", required=True
                ),
                ToolParameter(
                    name="mapping_rules",
                    type="object",
                    description="Dictionary of ACP mapped fields",
                    required=False,
                    default={},
                ),
            ],
        )
        super().__init__(metadata)
        self._agent_ref = None

    def set_agent(self, agent):
        self._agent_ref = agent

    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target_agent_id = params.get("target_agent_id", "")
        task_payload = params.get("task_payload", {})
        mapping_rules = params.get("mapping_rules", {})

        if not target_agent_id:
            return {"success": False, "error": "target_agent_id is required."}

        if not self._agent_ref:
            return {"success": False, "error": "Tool not bound to an agent context."}

        # Format through ACP I/O Mapper
        acp = AgentConnectProtocol(mapper=IOMapper(mapping_rules))
        mapped_payload = acp.map_request(task_payload)

        comm_mgr = getattr(self._agent_ref, "communication_manager", None)
        if not comm_mgr:
            return {"success": False, "error": "Communication Manager is not attached to this agent."}

        from daie.utils import generate_id

        correlation_id = generate_id()

        # Pack task into message
        agent_msg = AgentMessage(
            sender_id=self._agent_ref.id,
            receiver_id=target_agent_id,
            content=json.dumps({"task": mapped_payload}),
            message_type="task",
            metadata={"correlation_id": correlation_id},
        )

        # Create a future to wait for the response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._agent_ref._pending_responses[correlation_id] = future

        try:
            success = await comm_mgr.send_message(agent_msg)
            if not success:
                self._agent_ref._pending_responses.pop(correlation_id, None)
                return {"success": False, "error": "Failed to send message."}

            # Wait for response with timeout
            response_content = await asyncio.wait_for(future, timeout=30.0)

            # Log the delegation and result in the calling agent's memory
            if hasattr(self._agent_ref, "memory_manager") and self._agent_ref.memory_manager:
                task_summary = str(task_payload)[:200]
                self._agent_ref.memory_manager.log_chat_history(
                    self._agent_ref.id,
                    f"[Delegated to {target_agent_id}]: {task_summary}"
                )
                self._agent_ref.memory_manager.log_chat_history(
                    self._agent_ref.id,
                    f"[Response from {target_agent_id}]: {str(response_content)[:500]}"
                )
                self._agent_ref.memory_manager.store_memory(
                    self._agent_ref.id,
                    f"Delegated task to {target_agent_id}: {task_summary}. Response: {str(response_content)[:300]}",
                    memory_type="episodic",
                    tags=["delegation", target_agent_id],
                )

            # Return just the sub-agent's response string so the orchestrator LLM
            # can directly use it without needing to parse a nested dict
            return {
                "success": True,
                "agent_response": str(response_content),
            }
        except asyncio.TimeoutError:
            self._agent_ref._pending_responses.pop(correlation_id, None)
            return {"success": False, "error": f"Task delegation to {target_agent_id} timed out after 30s."}
        except Exception as e:
            self._agent_ref._pending_responses.pop(correlation_id, None)
            return {"success": False, "error": f"Error during task delegation: {str(e)}"}
