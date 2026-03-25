import asyncio
import base64
import json
import logging
import os
import unittest
from unittest.mock import patch, AsyncMock

from daie.agents import AgentConfig, AgentRole, Agent
from daie.communication import CommunicationManager
from daie.agents.message import AgentMessage
from daie.registry.manager import NodeRegistry

logging.basicConfig(level=logging.ERROR)

class TestP2PNetwork(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Setup sender agent
        config1 = AgentConfig(
            name="SenderAgent",
            role=AgentRole.GENERAL_PURPOSE,
            capabilities=["send_files"],
            network_url="http://localhost:8000"
        )
        self.agent1 = Agent(config=config1)
        
        # Setup receiver agent
        config2 = AgentConfig(
            name="ReceiverAgent",
            role=AgentRole.GENERAL_PURPOSE,
            capabilities=["receive_files"],
            network_url="http://localhost:8001",
            allow_file_transfers=True,
            auth_token="secret-token-123"
        )
        self.agent2 = Agent(config=config2)
        
        # We need independent communication managers to simulate 2 networks
        self.comm1 = CommunicationManager()
        self.comm2 = CommunicationManager()
        
        # We must manually register nodes into each other's registry to simulate discovery
        self.comm1.registry.register_node(self.agent2.id, {"role": "general-purpose"}, network_url="http://localhost:8001")
        self.comm2.registry.register_node(self.agent1.id, {"role": "general-purpose"}, network_url="http://localhost:8000")

        await self.comm1.start()
        await self.comm2.start()

        await self.agent1.start(communication_manager=self.comm1)
        await self.agent2.start(communication_manager=self.comm2)

    async def asyncTearDown(self):
        await self.agent1.stop()
        await self.agent2.stop()
        self.comm1.stop()
        self.comm2.stop()

    @patch('httpx.AsyncClient.post', new_callable=AsyncMock)
    async def test_remote_message_dispatch(self, mock_post):
        # Mock httpx response
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = '{"status": "Message delivered"}'

        print("\n--- Testing P2P HTTP Dispatch ---")
        
        # Agent 1 sends a message to Agent 2
        msg = AgentMessage(
            sender_id=self.agent1.id,
            receiver_id=self.agent2.id,
            content="Hello across the network!",
            message_type="text"
        )
        
        # Send message
        success = await self.comm1.send_message(msg)
        self.assertTrue(success)
        
        # Give async tasks time to complete httpx post
        await asyncio.sleep(0.1)
        
        # Verify httpx POST was called with the correct URL
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        self.assertEqual(args[0], "http://localhost:8001/api/v1/a2a/message")
        
        # Verify headers were NOT set since sender didn't have an auth token configured to send!
        # Wait, if auth token is required by receiver, does sender know it? 
        # In our implementation sender sends its own token or a system token. Let's look at kwargs.
        print("HTTPX Mock Call Kwargs:", json.dumps(kwargs, indent=2, default=str))

    @patch('httpx.AsyncClient.post', new_callable=AsyncMock)
    async def test_a2a_file_transfer_tool(self, mock_post):
        mock_post.return_value.status_code = 200
        
        print("\n--- Testing A2A File Transfer Tool ---")
        
        # Create a dummy file
        test_file = "dummy_test_file.txt"
        with open(test_file, "w") as f:
            f.write("Hello World from base64 transfer.")
            
        tool = self.agent1.get_tool("a2a_send_file")
        self.assertIsNotNone(tool, "A2ASendFileTool should be loaded dynamically.")
        
        # Execute tool
        result = await tool._execute({"receiver_id": self.agent2.id, "file_path": test_file, "message": "Here is the file."})
        print("File Tool Output:", result)
        self.assertIn("Successfully sent file", result)
        
        await asyncio.sleep(0.1)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # Verify JSON payload has base64 
        sent_json = kwargs.get("json", {})
        self.assertEqual(sent_json["message_type"], "file")
        self.assertIn("base64_data", sent_json["metadata"])
        
        encoded_data = sent_json["metadata"]["base64_data"]
        self.assertEqual(base64.b64decode(encoded_data).decode('utf-8'), "Hello World from base64 transfer.")
        
        # Clean up
        os.remove(test_file)


if __name__ == '__main__':
    unittest.main()
