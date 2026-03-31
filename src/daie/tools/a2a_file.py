import base64
import mimetypes
import os
from typing import Any, Dict

from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter


class A2ASendFileTool(Tool):
    """
    Tool for transferring files over the P2P A2A Network securely by converting them to base64.
    The receiver must have allow_file_transfers = True in their configuration.
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="a2a_send_file",
            description="Transfer a file to another agent by its ID over the P2P network.",
            category=ToolCategory.CUSTOM,
            parameters=[
                ToolParameter(
                    name="receiver_id",
                    type="string",
                    description="The target Agent ID to receive the file.",
                    required=True,
                ),
                ToolParameter(
                    name="file_path", type="string", description="The local path of the file to send.", required=True
                ),
                ToolParameter(
                    name="message",
                    type="string",
                    description="Optional message context regarding the file.",
                    required=False,
                ),
            ],
        )
        super().__init__(metadata)
        self._agent_ref = None

    def set_agent(self, agent):
        self._agent_ref = agent

    async def _execute(self, arguments: Dict[str, Any]) -> str:
        receiver_id = arguments.get("receiver_id")
        file_path = arguments.get("file_path")
        message_text = arguments.get("message", "")

        if not receiver_id or not file_path:
            return "Error: receiver_id and file_path must be provided."

        if not self._agent_ref:
            return "Error: Tool not bound to an agent context."

        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."

        if not hasattr(self._agent_ref, "communication_manager") or self._agent_ref.communication_manager is None:
            return "Error: Agent is not connected to any network. CommunicationManager is required."

        # Read file and encode it as base64
        try:
            with open(file_path, "rb") as f:
                file_data_bytes = f.read()
            base64_encoded = base64.b64encode(file_data_bytes).decode("utf-8")
        except Exception as e:
            return f"Error reading file: {e}"

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        file_name = os.path.basename(file_path)

        from daie.agents.message import AgentMessage

        # We send it as a "file" type message
        msg = AgentMessage(
            sender_id=self._agent_ref.id,
            receiver_id=receiver_id,
            content=message_text,
            message_type="file",
            metadata={"file_name": file_name, "mime_type": mime_type, "base64_data": base64_encoded},
        )

        success = await self._agent_ref.communication_manager.send_message(msg)
        if success:
            return f"Successfully sent file {file_name} over P2P network to {receiver_id}."
        else:
            return f"Failed to send file. Check if {receiver_id} exists on the network and is reachable."
