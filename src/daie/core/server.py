"""
Central core web server
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging

from daie.core.system import DecentralizedAISystem
from daie.config import SystemConfig
from daie.agents import AgentConfig, AgentRole

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Decentralized AI Ecosystem API",
    description="API for managing the Decentralized AI Ecosystem",
    version="1.0.1"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize system
system: Optional[DecentralizedAISystem] = None


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global system
    config = SystemConfig()
    system = DecentralizedAISystem(config=config)
    logger.info("Central core server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown system on shutdown"""
    global system
    if system:
        system.stop()
    logger.info("Central core server stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    from daie import __version__
    return {"message": "Decentralized AI Ecosystem API", "version": __version__}


@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint"""
    raise HTTPException(status_code=204)  # No Content


@app.get("/status")
async def get_system_status():
    """Get system status"""
    if not system:
        raise HTTPException(status_code=500, detail="System not initialized")
    
    return system.get_status()


@app.get("/agents")
async def list_agents():
    """List all agents"""
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
                "status": "running" if agent.is_running else "stopped"
            }
            for agent in agents
        ]
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details"""
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
        "config": agent.config.to_dict()
    }


class AgentCreateRequest(BaseModel):
    """Request model for creating an agent"""
    name: str
    role: str = "general-purpose"
    goal: Optional[str] = None
    backstory: Optional[str] = None
    system_prompt: Optional[str] = None
    capabilities: List[str] = []


@app.post("/agents")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent"""
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
        capabilities=request.capabilities
    )
    
    from daie.agents import Agent
    agent = Agent(config=config)
    system.add_agent(agent)
    
    return {
        "message": "Agent created successfully",
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value
        }
    }


@app.post("/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start an agent"""
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
    """Stop an agent"""
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
    """Delete an agent"""
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


def start_server(host: str = "0.0.0.0", port: int = 3333, reload: bool = False):
    """Start the central core server"""
    uvicorn.run(
        "daie.core.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server(reload=True)
