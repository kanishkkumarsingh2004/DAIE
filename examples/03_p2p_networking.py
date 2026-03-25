import asyncio
import os
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.communication import CommunicationManager
from daie.agents.message import AgentMessage

# Note: This example demonstrates the P2P Networking HTTP dispatch logic.
# You do not necessarily need an LLM running if you're just demonstrating the network transport layer.
set_llm(ollama_llm="llama3.2")

async def main():
    print("Starting P2P Network Simulation on localhost...")
    
    # 1. Create Communication Managers
    # In a real deployed environment, these would be running on separate machines.
    comm1 = CommunicationManager()
    comm2 = CommunicationManager()

    # 2. Configure Node 1
    config1 = AgentConfig(
        name="NodeAlfa",
        role=AgentRole.GENERAL_PURPOSE,
        network_url="http://localhost:8000"
    )
    agent1 = Agent(config=config1)

    # 3. Configure Node 2 (with strict Authentication and File Transfer booleans)
    config2 = AgentConfig(
        name="NodeBravo",
        role=AgentRole.GENERAL_PURPOSE,
        network_url="http://localhost:8001",
        auth_token="secure_token_123",
        allow_file_transfers=True
    )
    agent2 = Agent(config=config2)

    # Note: On a real network, nodes use decentralized tracking. 
    # For this local demo, we simulate registry presence:
    comm1.registry.register_node(agent2.id, {"role": "general"}, network_url="http://localhost:8001")
    comm2.registry.register_node(agent1.id, {"role": "general"}, network_url="http://localhost:8000")

    # 4. Start networks and agents (Spins up FastAPI on the given network_url ports)
    await comm1.start()
    await comm2.start()
    
    await agent1.start(communication_manager=comm1)
    await agent2.start(communication_manager=comm2)

    print(f"\nNodeAlfa ID: {agent1.id}")
    print(f"NodeBravo ID: {agent2.id}")
    
    # 5. Dispatch cross-network task
    print(f"\n[Network] Agent 1 sending a direct P2P HTTP ping to Agent 2...")
    
    msg = AgentMessage(
        sender_id=agent1.id,
        receiver_id=agent2.id,
        content="Hello from NodeAlfa!",
        message_type="text"
    )
    
    # Sending via the Manager transports it over HTTP since it sees the network_url!
    await comm1.send_message(msg)
    
    # 6. Cross-Network File Transfer Simulation
    print(f"\n[Network] Generating a local file to transport over Base64...")
    with open("demo_payload.txt", "w") as f:
        f.write("Highly classified network payload.")
        
    print(f"[Network] Agent 1 triggering A2A File Tool to drop file to Agent 2.")
    file_tool = agent1.get_tool("a2a_send_file")
    
    if file_tool:
        await file_tool._execute({
            "receiver_id": agent2.id, 
            "file_path": "demo_payload.txt", 
            "message": "Secure payload inbound!"
        })
        
    # Give the network a second to process the HTTP callbacks
    await asyncio.sleep(1)
    
    print("\nCheck your current directory for a new 'downloads' folder containing your safely decoded file!")
    
    # Cleanup
    if os.path.exists("demo_payload.txt"):
        os.remove("demo_payload.txt")
        
    await agent1.stop()
    await agent2.stop()
    comm1.stop()
    comm2.stop()

if __name__ == "__main__":
    asyncio.run(main())
