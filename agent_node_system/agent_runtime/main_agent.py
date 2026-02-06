#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
Main Agent Runtime Entry Point

This is the main entry point for the Agent Node System. It provides:
- Agent initialization and lifecycle management
- Communication with Central Core System
- Message handling and processing
- Tool execution management
- Identity and security management

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import os
import sys
import logging
import asyncio
import argparse
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent_node.log")
    ]
)

logger = logging.getLogger(__name__)

class AgentNode:
    """Main Agent Node class responsible for all agent operations"""
    
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config = None
        self.is_running = False
        self.connected = False
        self.agent_id = None
        self.agent_name = None
        self.agent_role = None
        self.central_core_url = None
        self.websocket_url = None
        self.last_heartbeat = None
        self.connection_retry_count = 0
        self.max_retry_count = 5
        
        # Initialize system components
        self._initialize_config()
        self._initialize_identity()
        self._initialize_communication()
        self._initialize_memory()
        self._initialize_tool_executor()
    
    def _initialize_config(self):
        """Initialize configuration from file or environment variables"""
        logger.info("Initializing agent configuration...")
        try:
            # Load configuration
            from agent_node_system.config.environment import EnvironmentConfig
            self.config = EnvironmentConfig()
            
            # Set properties from config
            self.agent_id = self.config.AGENT_ID
            self.agent_name = self.config.AGENT_NAME
            self.agent_role = self.config.AGENT_ROLE
            self.central_core_url = self.config.CENTRAL_CORE_URL
            self.websocket_url = self.config.WEBSOCKET_URL
            
            logger.info(f"Agent ID: {self.agent_id}")
            logger.info(f"Agent Name: {self.agent_name}")
            logger.info(f"Agent Role: {self.agent_role}")
            logger.info(f"Central Core URL: {self.central_core_url}")
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {e}")
            sys.exit(1)
    
    def _initialize_identity(self):
        """Initialize agent identity and security"""
        logger.info("Initializing agent identity...")
        try:
            from agent_node_system.identity.keypair_manager import KeypairManager
            self.keypair_manager = KeypairManager()
            
            # Check if identity exists, if not generate new one
            if not self.keypair_manager.has_keys():
                logger.warning("Agent identity not found. Generating new identity...")
                self.keypair_manager.generate_keys()
            
            logger.info("Agent identity initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize identity: {e}")
            sys.exit(1)
    
    def _initialize_communication(self):
        """Initialize communication with Central Core System"""
        logger.info("Initializing communication system...")
        try:
            from agent_node_system.communication.central_client import CentralClient
            from agent_node_system.communication.p2p_client import P2PClient
            
            self.central_client = CentralClient(self.central_core_url, self.agent_id)
            self.p2p_client = P2PClient(self.agent_id)
            
            logger.info("Communication system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize communication: {e}")
            sys.exit(1)
    
    def _initialize_memory(self):
        """Initialize memory system"""
        logger.info("Initializing memory system...")
        try:
            from agent_node_system.memory_system.short_term.working_memory import WorkingMemory
            from agent_node_system.memory_system.episodic.chat_history import ChatHistory
            from agent_node_system.memory_system.semantic.vector_store import VectorStore
            
            self.working_memory = WorkingMemory()
            self.chat_history = ChatHistory()
            self.vector_store = VectorStore()
            
            logger.info("Memory system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            sys.exit(1)
    
    def _initialize_tool_executor(self):
        """Initialize tool executor"""
        logger.info("Initializing tool executor...")
        try:
            from agent_node_system.tool_executor.tool_loader import ToolLoader
            from agent_node_system.tool_executor.permission_manager import PermissionManager
            
            self.tool_loader = ToolLoader()
            self.permission_manager = PermissionManager()
            
            # Load available tools
            self.tools = self.tool_loader.load_tools()
            logger.info(f"Loaded {len(self.tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize tool executor: {e}")
            sys.exit(1)
    
    async def connect_to_central_core(self):
        """Connect to Central Core System"""
        logger.info("Connecting to Central Core System...")
        try:
            # Attempt to connect
            success = await self.central_client.connect()
            
            if success:
                self.connected = True
                self.connection_retry_count = 0
                self.last_heartbeat = datetime.now()
                logger.info("Connected to Central Core System successfully")
                
                # Register agent
                await self.register_with_central_core()
            else:
                self.connected = False
                self.connection_retry_count += 1
                logger.warning(f"Failed to connect to Central Core System (attempt {self.connection_retry_count}/{self.max_retry_count})")
                
                if self.connection_retry_count >= self.max_retry_count:
                    logger.error("Maximum connection retries reached. Exiting...")
                    self.is_running = False
        
        except Exception as e:
            self.connected = False
            self.connection_retry_count += 1
            logger.error(f"Connection error: {e}")
    
    async def register_with_central_core(self):
        """Register agent with Central Core System"""
        logger.info("Registering agent with Central Core System...")
        try:
            # Send registration request
            response = await self.central_client.register_agent({
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "agent_role": self.agent_role,
                "capabilities": list(self.tools.keys())  # List available tools
            })
            
            if response.get("success"):
                logger.info("Agent registered successfully")
                self.session_token = response.get("session_token")
            else:
                logger.warning(f"Failed to register agent: {response.get('message', 'Unknown error')}")
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
    
    async def send_heartbeat(self):
        """Send heartbeat to Central Core System"""
        if not self.connected:
            return
        
        try:
            response = await self.central_client.send_heartbeat({
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "status": "alive",
                "cpu_usage": 0,  # Placeholder
                "memory_usage": 0,  # Placeholder
                "active_tasks": len(self.working_memory.get_active_tasks())
            })
            
            if response.get("success"):
                self.last_heartbeat = datetime.now()
            else:
                logger.warning("Heartbeat failed")
        
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            self.connected = False
    
    async def process_messages(self):
        """Process incoming messages"""
        if not self.connected:
            return
        
        try:
            # Check for new messages
            messages = await self.central_client.get_messages()
            
            for message in messages:
                logger.info(f"Processing message: {message}")
                await self.handle_message(message)
        
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    async def handle_message(self, message):
        """Handle incoming messages from Central Core System or other agents"""
        try:
            message_type = message.get("type")
            
            if message_type == "chat/message":
                await self.handle_chat_message(message)
            elif message_type == "task/assign":
                await self.handle_task_assignment(message)
            elif message_type == "tool/request":
                await self.handle_tool_request(message)
            elif message_type == "system/command":
                await self.handle_system_command(message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def handle_chat_message(self, message):
        """Handle chat messages from other agents"""
        logger.info(f"Received chat message from {message.get('sender')}: {message.get('content')}")
        
        # Simple echo response for testing
        response = {
            "type": "chat/message",
            "sender": self.agent_id,
            "recipient": message.get("sender"),
            "content": f"I received your message: {message.get('content')}",
            "timestamp": datetime.now().isoformat()
        }
        
        await self.central_client.send_message(response)
    
    async def handle_task_assignment(self, message):
        """Handle task assignment from Central Core System"""
        logger.info(f"Received task assignment: {message.get('task_id')}")
        
        # Process task and send status update
        status = {
            "type": "task/status",
            "task_id": message.get("task_id"),
            "status": "accepted",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.central_client.send_message(status)
    
    async def handle_tool_request(self, message):
        """Handle tool execution requests"""
        logger.info(f"Received tool request: {message.get('tool_name')}")
        
        # Execute tool if permissions are granted
        tool_name = message.get("tool_name")
        parameters = message.get("parameters")
        
        if tool_name in self.tools:
            if self.permission_manager.check_permission(tool_name):
                result = await self.tools[tool_name].execute(parameters)
                response = {
                    "type": "tool/response",
                    "tool_name": tool_name,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                response = {
                    "type": "tool/response",
                    "tool_name": tool_name,
                    "error": "Permission denied",
                    "timestamp": datetime.now().isoformat()
                }
        else:
            response = {
                "type": "tool/response",
                "tool_name": tool_name,
                "error": "Tool not found",
                "timestamp": datetime.now().isoformat()
            }
        
        await self.central_client.send_message(response)
    
    async def handle_system_command(self, message):
        """Handle system commands from Central Core System"""
        logger.info(f"Received system command: {message.get('command')}")
        
        command = message.get("command")
        
        if command == "shutdown":
            logger.info("Shutdown command received. Exiting...")
            self.is_running = False
        elif command == "restart":
            logger.info("Restart command received. Restarting...")
            await self.restart()
        elif command == "status":
            await self.send_status_update()
        else:
            logger.warning(f"Unknown system command: {command}")
    
    async def send_status_update(self):
        """Send status update to Central Core System"""
        status = {
            "type": "agent/status",
            "agent_id": self.agent_id,
            "status": "running" if self.is_running else "stopped",
            "connected": self.connected,
            "cpu_usage": 0,  # Placeholder
            "memory_usage": 0,  # Placeholder
            "active_tasks": len(self.working_memory.get_active_tasks()),
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.central_client.send_message(status)
    
    async def restart(self):
        """Restart the agent"""
        logger.info("Restarting agent...")
        self.is_running = False
    
    async def main_loop(self):
        """Main agent loop that runs continuously"""
        logger.info("Starting agent main loop...")
        
        # Connection attempt
        if not self.connected:
            await self.connect_to_central_core()
            
            if not self.connected:
                logger.warning("Waiting before reconnection attempt...")
                await asyncio.sleep(self.config.RECONNECT_INTERVAL)
                return
        
        # Main operations
        try:
            # Send heartbeat
            await self.send_heartbeat()
            
            # Process messages
            await self.process_messages()
            
            # Perform local operations
            await self.perform_local_operations()
            
            # Wait for next iteration
            await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Main loop error: {e}")
    
    async def perform_local_operations(self):
        """Perform local operations (background tasks)"""
        try:
            # Update local memory
            await self.working_memory.cleanup()
            
            # Sync memory with Central Core System
            await self.sync_memory()
            
        except Exception as e:
            logger.error(f"Local operations error: {e}")
    
    async def sync_memory(self):
        """Sync local memory with Central Core System"""
        try:
            # This would typically sync recent interactions and knowledge
            pass
        except Exception as e:
            logger.error(f"Memory sync error: {e}")
    
    async def start(self):
        """Start the agent node"""
        logger.info("Starting Agent Node System...")
        self.is_running = True
        
        try:
            while self.is_running:
                await self.main_loop()
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt. Stopping agent...")
            self.is_running = False
        except Exception as e:
            logger.error(f"Agent error: {e}")
            self.is_running = False
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the agent node"""
        logger.info("Stopping Agent Node System...")
        self.is_running = False
        
        try:
            # Disconnect from Central Core System
            if self.connected:
                logger.info("Disconnecting from Central Core System...")
                await self.central_client.disconnect()
            
            # Cleanup resources
            logger.info("Cleaning up resources...")
            
            # Save state
            await self.save_state()
        
        except Exception as e:
            logger.error(f"Error during stop: {e}")
    
    async def save_state(self):
        """Save agent state to disk"""
        try:
            logger.info("Saving agent state...")
            # Save memory, active tasks, etc.
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

def main():
    """Main function to start the agent node"""
    parser = argparse.ArgumentParser(
        description="Decentralized AI Ecosystem - Agent Node System"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    logger.setLevel(args.log_level)
    
    logger.info("=" * 60)
    logger.info("Decentralized AI Ecosystem - Agent Node System")
    logger.info(f"Version: 1.0.0")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Create and start agent
        agent = AgentNode(args.config)
        asyncio.run(agent.start())
        
    except Exception as e:
        logger.critical(f"Failed to start agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
