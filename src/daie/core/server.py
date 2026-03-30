"""
Central core web server (optional - requires fastapi and uvicorn)
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List
    import json

    from daie.core.system import DecentralizedAISystem
    from daie.config import SystemConfig
    from daie.agents import AgentConfig, AgentRole

    system: Optional[DecentralizedAISystem] = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        global system
        config = SystemConfig()
        system = DecentralizedAISystem(config=config)
        system.load_configured_agents()
        logger.info("Central core server started with configured agents.")
        yield
        # Shutdown
        if system:
            system.stop()
        logger.info("Central core server stopped")

    app = FastAPI(
        title="Decentralized AI Ecosystem API",
        description="API for managing the Decentralized AI Ecosystem",
        version="1.0.4",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        from daie import __version__
        return {"message": "Decentralized AI Ecosystem API", "version": __version__}

    @app.get("/favicon.ico")
    async def favicon():
        raise HTTPException(status_code=204)

    @app.get("/status")
    async def get_system_status():
        if not system:
            raise HTTPException(status_code=500, detail="System not initialized")
        return system.get_status()

    @app.get("/agents")
    async def list_agents():
        if not system:
            raise HTTPException(status_code=500, detail="System not initialized")
        agents = system.list_agents()
        return {
            "count": len(agents),
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "status": "running" if agent.is_running else "stopped",
                }
                for agent in agents
            ],
        }

    @app.get("/agents/{agent_id}")
    async def get_agent(agent_id: str):
        if not system:
            raise HTTPException(status_code=500, detail="System not initialized")
        agent = system.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value,
            "status": "running" if agent.is_running else "stopped",
            "config": agent.config.to_dict(),
        }

    class AgentCreateRequest(BaseModel):
        name: str
        role: str = "general-purpose"
        goal: Optional[str] = None
        backstory: Optional[str] = None
        system_prompt: Optional[str] = None
        capabilities: List[str] = []

    @app.post("/agents")
    async def create_agent(request: AgentCreateRequest):
        if not system:
            raise HTTPException(status_code=500, detail="System not initialized")
        try:
            role = AgentRole(request.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
        config = AgentConfig(
            name=request.name,
            role=role,
            goal=request.goal,
            backstory=request.backstory,
            system_prompt=request.system_prompt,
            capabilities=request.capabilities,
        )
        from daie.agents import Agent
        agent = Agent(config=config)
        system.add_agent(agent)
        return {
            "message": "Agent created successfully",
            "agent": {"id": agent.id, "name": agent.name, "role": agent.role.value},
        }

    @app.post("/agents/{agent_id}/start")
    async def start_agent(agent_id: str):
        if not system:
            raise HTTPException(status_code=500, detail="System not initialized")
        agent = system.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            agent.start()
            return {"message": "Agent started successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/agents/{agent_id}/stop")
    async def stop_agent(agent_id: str):
        if not system:
            raise HTTPException(status_code=500, detail="System not initialized")
        agent = system.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            agent.stop()
            return {"message": "Agent stopped successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/agents/{agent_id}")
    async def delete_agent(agent_id: str):
        if not system:
            raise HTTPException(status_code=500, detail="System not initialized")
        agent = system.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        try:
            del system.agents[agent_id]
            return {"message": "Agent deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    from daie.agents.message import AgentMessage
    
    @app.websocket("/ws/a2a/message")
    async def websocket_a2a_message(websocket: WebSocket):
        await websocket.accept()
        logger.info("WebSocket connection established for A2A messaging")
        
        try:
            while True:
                try:
                    # Receive message from WebSocket
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    receiver_id = message_data.get("receiver_id")
                    
                    if not system:
                        await websocket.send_text(json.dumps({"error": "System not initialized"}))
                        continue
                    
                    agent = system.get_agent(receiver_id)
                    if not agent:
                        await websocket.send_text(json.dumps({"error": "Receiver agent not found"}))
                        continue
                        
                    # Auth check via message metadata
                    expected_token = getattr(agent.config, 'auth_token', None)
                    if expected_token:
                        auth_token = message_data.get("auth_token", "")
                        if auth_token != expected_token:
                            await websocket.send_text(json.dumps({"error": "Unauthorized: Invalid token"}))
                            continue
                        
                    if not hasattr(agent, 'communication_manager') or not agent.communication_manager:
                        await websocket.send_text(json.dumps({"error": "Agent CommunicationManager not active"}))
                        continue
                        
                    message = AgentMessage(
                        sender_id=message_data.get("sender_id", ""),
                        receiver_id=message_data.get("receiver_id", ""),
                        content=message_data.get("content", ""),
                        message_type=message_data.get("message_type", "text"),
                        metadata=message_data.get("metadata", {})
                    )
                    
                    # Inject the message into the agent's queue directly (or via communication manager)
                    import asyncio
                    task = asyncio.create_task(agent._handle_message(message))
                    # Add error handling for the background task
                    task.add_done_callback(lambda t: t.exception() if t.done() and not t.cancelled() else None)
                    
                    # Send acknowledgment
                    await websocket.send_text(json.dumps({"status": "Message delivered"}))
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_text(json.dumps({"error": f"Internal server error: {str(e)}"}))
                    
        except WebSocketDisconnect:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            try:
                await websocket.close()
            except Exception as close_error:
                logger.debug(f"Error closing WebSocket: {close_error}")

    def start_server(host: str = "0.0.0.0", port: int = 3333, reload: bool = False):
        """Start the central core server"""
        uvicorn.run(
            "daie.core.server:app", host=host, port=port, reload=reload, log_level="info"
        )

    SERVER_AVAILABLE = True

except ImportError:
    SERVER_AVAILABLE = False
    app = None

    def start_server(host: str = "0.0.0.0", port: int = 3333, reload: bool = False):
        raise ImportError(
            "Server support requires fastapi and uvicorn. "
            "Install with: pip install 'daie[server]'"
        )
