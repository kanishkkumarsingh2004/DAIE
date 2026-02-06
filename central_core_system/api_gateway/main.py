#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Central Core System
Main API Gateway Entry Point

This is the main entry point for the Central Core System. It provides:
- API endpoints for agent registration and communication
- WebSocket server for real-time communication
- Health check endpoints
- System status monitoring

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("central_core.log")
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Decentralized AI Ecosystem - Central Core API",
    description="API for the Decentralized AI Ecosystem's Central Core System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the system is running
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "central-core",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )

# System status endpoint
@app.get("/status")
async def system_status():
    """
    System status endpoint with detailed information
    """
    try:
        # This would typically query various system components
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "central-core",
                "version": "1.0.0",
                "agents": 0,
                "messages": 0,
                "tasks": 0,
                "uptime": "0 days, 0 hours, 0 minutes",
                "components": {
                    "database": "connected",
                    "redis": "connected",
                    "llm_cluster": "available",
                    "message_router": "running",
                    "agent_registry": "active"
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, agent_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        logger.info(f"Agent {agent_id} connected")
    
    def disconnect(self, agent_id: str):
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            logger.info(f"Agent {agent_id} disconnected")
    
    async def send_personal_message(self, message: str, agent_id: str):
        if agent_id in self.active_connections:
            await self.active_connections[agent_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

# WebSocket endpoint for agent communication
@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for real-time communication with agents
    """
    try:
        await manager.connect(agent_id, websocket)
        logger.info(f"Agent {agent_id} connected via WebSocket")
        
        while True:
            # Receive message from agent
            data = await websocket.receive_text()
            logger.info(f"Received message from {agent_id}: {data}")
            
            # For now, just echo back
            await manager.send_personal_message(f"Received: {data}", agent_id)
    except WebSocketDisconnect:
        manager.disconnect(agent_id)
        logger.info(f"Agent {agent_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        manager.disconnect(agent_id)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with system information
    """
    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcome to the Decentralized AI Ecosystem Central Core System",
            "service": "central-core",
            "version": "1.0.0",
            "documentation": "/docs",
            "health": "/health",
            "status": "/status"
        }
    )

# API endpoints for agent management (placeholder)
@app.post("/agents/register")
async def register_agent(agent_data: dict):
    """
    Register a new agent with the system
    """
    try:
        logger.info(f"Registering agent: {agent_data.get('agent_id', 'unknown')}")
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Agent registered successfully",
                "agent_id": agent_data.get('agent_id'),
                "session_token": "mock-session-token"
            }
        )
    except Exception as e:
        logger.error(f"Failed to register agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to register agent")

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get information about a specific agent
    """
    try:
        logger.info(f"Fetching agent information for: {agent_id}")
        return JSONResponse(
            status_code=200,
            content={
                "agent_id": agent_id,
                "status": "connected",
                "role": "general-purpose",
                "capabilities": ["web_search", "file_access"],
                "last_activity": "2024-01-01T00:00:00Z"
            }
        )
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent")

@app.get("/agents")
async def list_agents():
    """
    List all active agents in the system
    """
    try:
        logger.info("Fetching list of active agents")
        return JSONResponse(
            status_code=200,
            content={
                "count": 0,
                "agents": []
            }
        )
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")

# API endpoints for message routing (placeholder)
@app.post("/messages/send")
async def send_message(message_data: dict):
    """
    Send a message from one agent to another
    """
    try:
        logger.info(f"Processing message: {message_data}")
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Message sent successfully",
                "message_id": "mock-message-id"
            }
        )
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

# API endpoints for tool execution (placeholder)
@app.post("/tools/execute")
async def execute_tool(tool_data: dict):
    """
    Execute a tool on behalf of an agent
    """
    try:
        logger.info(f"Executing tool: {tool_data}")
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Tool executed successfully",
                "result": "mock-result"
            }
        )
    except Exception as e:
        logger.error(f"Failed to execute tool: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute tool")

if __name__ == "__main__":
    logger.info("Starting Decentralized AI Ecosystem Central Core System...")
    
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
