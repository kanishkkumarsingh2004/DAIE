"""
Agent Node System - Central Client
Decentralized AI Ecosystem

This module handles communication with the Central Core System.
It provides methods for connecting, registering, sending/receiving messages,
and managing the connection lifecycle.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import asyncio
import websockets
import json
import logging
import time
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

class CentralClient:
    """Client for communicating with the Central Core System"""
    
    def __init__(self, central_core_url: str, agent_id: str):
        """
        Initialize the central client
        
        Args:
            central_core_url: URL of the central core system
            agent_id: Unique identifier for this agent
        """
        self.central_core_url = central_core_url.rstrip('/')
        self.agent_id = agent_id
        self.websocket_url = f"{self.central_core_url.replace('http', 'ws', 1)}/ws/{agent_id}"
        self.session_token = None
        self.websocket = None
        self.connected = False
        self.last_message_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        logger.info(f"Central client initialized for agent {agent_id}")
        logger.info(f"Central core URL: {self.central_core_url}")
        logger.info(f"WebSocket URL: {self.websocket_url}")
    
    async def connect(self) -> bool:
        """
        Establish a connection to the Central Core System
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Connecting to central core system...")
            
            # Test if central core is reachable
            health_url = f"{self.central_core_url}/health"
            response = await asyncio.to_thread(requests.get, health_url, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Central core health check failed: {response.status_code}")
                return False
            
            # Establish WebSocket connection
            self.websocket = await websockets.connect(self.websocket_url)
            self.connected = True
            self.reconnect_attempts = 0
            self.last_message_time = time.time()
            
            logger.info("Connected to central core system successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to central core: {e}")
            self.connected = False
            self.websocket = None
            
            self.reconnect_attempts += 1
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.critical("Maximum reconnection attempts reached")
                raise
            
            return False
    
    async def disconnect(self):
        """Disconnect from the Central Core System"""
        if self.connected and self.websocket:
            try:
                await self.websocket.close()
                logger.info("Disconnected from central core system")
            except Exception as e:
                logger.error(f"Error during disconnection: {e}")
            finally:
                self.connected = False
                self.websocket = None
                self.session_token = None
    
    async def register_agent(self, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register the agent with the Central Core System
        
        Args:
            agent_info: Dictionary containing agent information
            
        Returns:
            Registration response from central core
        """
        try:
            register_url = f"{self.central_core_url}/agents/register"
            response = await asyncio.to_thread(
                requests.post, 
                register_url, 
                json=agent_info, 
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                self.session_token = result.get("session_token")
                logger.info("Agent registered successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_heartbeat(self, heartbeat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send heartbeat to Central Core System
        
        Args:
            heartbeat_data: Dictionary containing heartbeat information
            
        Returns:
            Heartbeat response from central core
        """
        try:
            heartbeat_url = f"{self.central_core_url}/agents/{self.agent_id}/heartbeat"
            response = await asyncio.to_thread(
                requests.post,
                heartbeat_url,
                json=heartbeat_data,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                self.last_message_time = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_messages(self) -> list:
        """
        Get pending messages from Central Core System
        
        Returns:
            List of messages for this agent
        """
        try:
            messages_url = f"{self.central_core_url}/agents/{self.agent_id}/messages"
            response = await asyncio.to_thread(
                requests.get,
                messages_url,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("messages", [])
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to Central Core System
        
        Args:
            message: Dictionary containing message data
            
        Returns:
            Response from central core
        """
        try:
            send_url = f"{self.central_core_url}/messages/send"
            response = await asyncio.to_thread(
                requests.post,
                send_url,
                json=message,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                self.last_message_time = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request tool execution from Central Core System
        
        Args:
            tool_data: Dictionary containing tool execution request
            
        Returns:
            Response from central core
        """
        try:
            tool_url = f"{self.central_core_url}/tools/execute"
            response = await asyncio.to_thread(
                requests.post,
                tool_url,
                json=tool_data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute tool: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_status(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send agent status to Central Core System
        
        Args:
            status_data: Dictionary containing status information
            
        Returns:
            Response from central core
        """
        try:
            status_url = f"{self.central_core_url}/agents/{self.agent_id}/status"
            response = await asyncio.to_thread(
                requests.post,
                status_url,
                json=status_data,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                self.last_message_time = time.time()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send status: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_config(self) -> Dict[str, Any]:
        """
        Get configuration from Central Core System
        
        Returns:
            Configuration data from central core
        """
        try:
            config_url = f"{self.central_core_url}/agents/{self.agent_id}/config"
            response = await asyncio.to_thread(
                requests.get,
                config_url,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("config", {})
            
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            return {}
    
    async def get_tools(self) -> list:
        """
        Get available tools from Central Core System
        
        Returns:
            List of available tools
        """
        try:
            tools_url = f"{self.central_core_url}/tools"
            response = await asyncio.to_thread(
                requests.get,
                tools_url,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("tools", [])
            
        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            return []
    
    async def check_connection(self) -> bool:
        """
        Check if connection is still active
        
        Returns:
            True if connection is active, False otherwise
        """
        if not self.connected:
            return False
        
        # Check if we've received any messages recently
        if time.time() - self.last_message_time > 300:  # 5 minutes
            logger.warning("Connection timeout: No messages received in 5 minutes")
            return False
        
        return True
    
    async def request_reconnect(self) -> bool:
        """
        Request a reconnection to the Central Core System
        
        Returns:
            True if reconnection successful, False otherwise
        """
        logger.info("Attempting reconnection to central core system...")
        
        try:
            # Disconnect first if still connected
            if self.connected:
                await self.disconnect()
            
            # Wait a short delay before reconnecting
            await asyncio.sleep(5)
            
            # Attempt to reconnect
            return await self.connect()
            
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {e}")
            return False
    
    async def send_error_report(self, error_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an error report to Central Core System
        
        Args:
            error_data: Dictionary containing error information
            
        Returns:
            Response from central core
        """
        try:
            error_url = f"{self.central_core_url}/agents/{self.agent_id}/errors"
            response = await asyncio.to_thread(
                requests.post,
                error_url,
                json=error_data,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send error report: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update agent profile with Central Core System
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Response from central core
        """
        try:
            profile_url = f"{self.central_core_url}/agents/{self.agent_id}/profile"
            response = await asyncio.to_thread(
                requests.put,
                profile_url,
                json=profile_data,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics from Central Core System
        
        Returns:
            System statistics data
        """
        try:
            stats_url = f"{self.central_core_url}/stats"
            response = await asyncio.to_thread(
                requests.get,
                stats_url,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
