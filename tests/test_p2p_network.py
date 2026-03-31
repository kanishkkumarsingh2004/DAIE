import asyncio
import base64
import json
import logging
import os
import unittest
from unittest.mock import AsyncMock, patch

from daie.agents import Agent, AgentConfig, AgentRole
from daie.agents.message import AgentMessage
from daie.communication import CommunicationManager

logging.basicConfig(level=logging.ERROR)


class TestP2PNetwork(unittest.IsolatedAsyncioTestCase):
    """
    Test P2P networking functionality.

    Network Configuration:
    - network_url: The URL where THIS agent is hosted (others use this to reach it)
    - network_connections: Dict of peer_id -> URL for agents THIS agent can directly reach
    """

    async def asyncSetUp(self):
        # Setup sender agent
        # network_url: The URL where THIS agent is hosted (others use this to reach it)
        config1 = AgentConfig(
            name="SenderAgent",
            role=AgentRole.GENERAL_PURPOSE,
            capabilities=["send_files"],
            network_url="http://localhost:8000",  # This agent is hosted on localhost:8000
        )
        self.agent1 = Agent(config=config1)

        # Setup receiver agent
        # network_url: The URL where THIS agent is hosted (others use this to reach it)
        config2 = AgentConfig(
            name="ReceiverAgent",
            role=AgentRole.GENERAL_PURPOSE,
            capabilities=["receive_files"],
            network_url="http://localhost:8001",  # This agent is hosted on localhost:8001
            allow_file_transfers=True,
            auth_token="secret-token-123",
        )
        self.agent2 = Agent(config=config2)

        # We need independent communication managers to simulate 2 networks
        self.comm1 = CommunicationManager()
        self.comm2 = CommunicationManager()

        # We must manually register nodes into each other's registry to simulate discovery
        # network_url: The URL where the agent is hosted (others use this to reach it)
        self.comm1.registry.register_node(
            self.agent2.id, {"role": "general-purpose"}, network_url="http://localhost:8001"
        )
        self.comm2.registry.register_node(
            self.agent1.id, {"role": "general-purpose"}, network_url="http://localhost:8000"
        )

        await self.comm1.start()
        await self.comm2.start()

        await self.agent1.start(communication_manager=self.comm1)
        await self.agent2.start(communication_manager=self.comm2)

    async def asyncTearDown(self):
        await self.agent1.stop()
        await self.agent2.stop()
        await self.comm1.stop()
        await self.comm2.stop()

    @patch("websockets.connect")
    async def test_remote_message_dispatch(self, mock_connect):
        # Mock websockets response
        mock_websocket = AsyncMock()
        mock_websocket.recv.return_value = '{"status": "Message delivered"}'
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        print("\n--- Testing P2P HTTP Dispatch ---")

        # Agent 1 sends a message to Agent 2
        msg = AgentMessage(
            sender_id=self.agent1.id,
            receiver_id=self.agent2.id,
            content="Hello across the network!",
            message_type="text",
        )

        # Send message
        success = await self.comm1.send_message(msg)
        self.assertTrue(success)

        # Give async tasks time to complete websocket task
        await asyncio.sleep(0.1)

        # Verify websocket context was called with the correct URL
        mock_connect.assert_called_once()
        args, kwargs = mock_connect.call_args

        self.assertEqual(args[0], "ws://localhost:8001/ws/a2a/message")

        # Verify send was called
        mock_websocket.send.assert_called_once()
        print("Websocket Send Call Args:", json.dumps(mock_websocket.send.call_args[0], indent=2, default=str))

    @patch("websockets.connect")
    async def test_a2a_file_transfer_tool(self, mock_connect):
        mock_websocket = AsyncMock()
        mock_websocket.recv.return_value = '{"status": "Message delivered"}'
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        print("\n--- Testing A2A File Transfer Tool ---")

        # Create a dummy file
        test_file = "dummy_test_file.txt"
        with open(test_file, "w") as f:
            f.write("Hello World from base64 transfer.")

        tool = self.agent1.get_tool("a2a_send_file")
        self.assertIsNotNone(tool, "A2ASendFileTool should be loaded dynamically.")

        # Execute tool
        result = await tool._execute(
            {"receiver_id": self.agent2.id, "file_path": test_file, "message": "Here is the file."}
        )
        print("File Tool Output:", result)
        self.assertIn("Successfully sent file", result)

        await asyncio.sleep(0.1)
        mock_connect.assert_called_once()
        mock_websocket.send.assert_called_once()

        # Verify JSON payload has base64
        sent_json_str = mock_websocket.send.call_args[0][0]
        sent_json = json.loads(sent_json_str)
        self.assertEqual(sent_json["message_type"], "file")
        self.assertIn("base64_data", sent_json["metadata"])

        encoded_data = sent_json["metadata"]["base64_data"]
        self.assertEqual(base64.b64decode(encoded_data).decode("utf-8"), "Hello World from base64 transfer.")

        # Clean up
        os.remove(test_file)


if __name__ == "__main__":
    unittest.main()
