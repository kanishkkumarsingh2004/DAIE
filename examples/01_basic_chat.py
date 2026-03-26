import asyncio
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole

# 1. Configure the LLM globally (e.g., using a local Ollama model)
# You can also use LLMType.OPENAI, Anthropic, etc.
set_llm(ollama_llm="llama3.2:1b", stream=True)

async def main():
    # 2. Configure the agent
    config = AgentConfig(
        name="LUNA",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a helpful and concise AI assistant.",
        gender="female",
        personality="sassy, witty, and very direct",
        behavior="always uses emojis and speaks enthusiastically",
        temperature=0.9,  # Dynamic override of the LLM temperature just for this agent
        max_tokens=1024,
        
    )
    
    # 3. Initialize the agent
    agent = Agent(config=config)
    
    # 4. Start the agent (allocates memory and initializes tasks)
    await agent.start()
    
    print("=== Basic Chat Loop ===")
    print("Type 'exit' or press Ctrl+C to quit.\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ('exit', 'quit'):
                break
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat loop...")
            break
            
        # 5. Send a conversational message
        response = await agent.send_message(user_input)
        
        # If streaming failed or returned an error, print it explicitly
        if response.startswith("Error:"):
            print(f"{response}")
            
        print("\n")
        
    # 6. Stop the agent cleanly
    await agent.stop()

if __name__ == "__main__":
    # Ensure you run this within the virtual environment where daie is installed.
    asyncio.run(main())
