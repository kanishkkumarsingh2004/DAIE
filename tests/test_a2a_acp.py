"""
Test script for verifying ConfigManager, A2A, and ACP.
"""

import asyncio
import os
import shutil
from pathlib import Path
from daie.config import SystemConfig, ConfigManager
from daie.agents.config import AgentConfig, AgentRole
from daie.agents import Agent
from daie.core.system import DecentralizedAISystem
from daie.tools.a2a import A2ASendMessageTool, A2ADelegateTaskTool
from daie.protocols.acp import AgentConnectProtocol, IOMapper
from daie.agents.message import AgentMessage

async def main():
    print("--- Testing ConfigManager ---")
    local_config_dir = Path("config")
    
    # Cleanup previous run
    if local_config_dir.exists():
        shutil.rmtree(local_config_dir)
        
    config_mgr = ConfigManager(override_dir="config")
    agents = config_mgr.load_agents_config()
    print("Loaded default agents:", [a.name for a in agents])
    
    a1 = AgentConfig(name="WorkerA", role=AgentRole.WORKER, llm_model="dummy")
    a2 = AgentConfig(name="WorkerB", role=AgentRole.WORKER, llm_model="dummy")
    config_mgr.save_agents_config([a1, a2])
    print("Saved WorkerA and WorkerB configs.")

    print("\n--- Testing ACP I/O Mapper ---")
    acp_mapper = IOMapper(mapping_rules={"input_text": "extracted_result"})
    acp = AgentConnectProtocol(mapper=acp_mapper)
    
    agent_1_out = {"extracted_result": "Hello World", "other_meta": True}
    mapped_input = acp.map_request(agent_1_out)
    
    print("Agent 1 Output:", agent_1_out)
    print("ACP Mapped Request (Agent 2 Input):", mapped_input)
    assert mapped_input == {"input_text": "Hello World"}
    
    print("\n--- Testing A2A Tools Attachment ---")
    sys_config = SystemConfig()
    system = DecentralizedAISystem(config=sys_config)
    
    # Simulate loading from config
    agent1 = Agent(config=a1)
    agent2 = Agent(config=a2)
    
    # Manually configure the IDs so we can send predictable messages
    agent1.id = "agentA"
    agent2.id = "agentB"
    
    system.add_agent(agent1)
    system.add_agent(agent2)
    
    # Start communication system
    await system.communication_manager.start()
    
    # Start agents (This mounts the A2A tools automatically)
    await agent1.start(communication_manager=system.communication_manager)
    await agent2.start(communication_manager=system.communication_manager)
    
    print("Agent 1 tool names:", list(agent1.tools.keys()))
    assert "a2a_send_message" in agent1.tools
    assert "a2a_delegate_task" in agent1.tools
    
    print("\n--- Testing A2A SendMessageTool ---")
    send_tool = agent1.get_tool("a2a_send_message")
    res = await send_tool.execute({
        "target_agent_id": "agentB",
        "message": "Hello from Agent A!"
    })
    print("sendMessage execute result:", res)
    
    # Let the loop process the message
    await asyncio.sleep(0.5)
    
    # Check if Agent 2 received the message
    msgs = system.communication_manager.receive_messages("agentB")
    print("Agent B inbox size:", len(msgs))
    last_msg = msgs[-1] if msgs else None
    if last_msg:
        print("Agent B received:", last_msg.content)
    
    print("\n--- Testing A2A DelegateTaskTool with ACP Mapping ---")
    delegate_tool = agent1.get_tool("a2a_delegate_task")
    res = await delegate_tool.execute({
        "target_agent_id": "agentB",
        "task_payload": {"extracted_data": "123"},
        "mapping_rules": {"calc_input": "extracted_data"}
    })
    print("delegateTask execute result:", res)
    print("mapped_payload inside detail:", res["mapped_payload"])
    
    # Clean up
    await agent1.stop()
    await agent2.stop()
    system.communication_manager.stop()
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
