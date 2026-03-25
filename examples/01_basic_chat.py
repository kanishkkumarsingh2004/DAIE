import os
import asyncio
import logging
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.tools import FileManagerTool, APICallTool, tool

# Set up logging so we can see the Agent's "thoughts" and tool choices in real-time
logging.basicConfig(level=logging.INFO, format="%(message)s")

# 1. Configure the LLM globally (e.g., using a local Ollama model)
# You can also use LLMType.OPENAI, Anthropic, etc.
set_llm(ollama_llm="wizard-vicuna-uncensored:7b", stream=False)

async def main():
    # 2. Configure the agent
    config = AgentConfig(
        name="Alex",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a helpful and concise AI assistant.",
        gender="female",
        personality="sassy, witty, and very direct",
        behavior="always uses emojis and speaks enthusiastically",
        temperature=0.9,  # Dynamic override of the LLM temperature just for this agent
        max_tokens=500
    )
    
    # 3. Initialize the agent
    agent = Agent(config=config)
    
    # 4. Give the agent tools to interact with the environment
    agent.add_tool(FileManagerTool())
    agent.add_tool(APICallTool())
    
    # Let's add a custom precision tool specifically for their environment
    @tool(name="get_current_directory", description="Get the absolute path of the current working directory")
    def get_current_directory() -> str:
        return os.getcwd()
        
    @tool(name="get_current_time", description="Get the current local time")
    def get_current_time() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    agent.add_tool(get_current_directory)
    agent.add_tool(get_current_time)
    
    # 5. Start the agent (allocates memory and initializes tasks)
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
            
        # 6. Have the agent execute the task (ReAct Loop: Reason -> Tool -> Reason -> Answer)
        print("\n--- Agent is thinking ---")
        response = await agent.execute_task(user_input)
        
        # If execution failed or returned an error, print it explicitly
        if isinstance(response, str) and response.startswith("Error:"):
            print(f"{response}")
        else:
            print(f"\nAlex: {response}")
            
        print("\n" + "="*40 + "\n")
        
    # 7. Stop the agent cleanly
    await agent.stop()

if __name__ == "__main__":
    # Ensure you run this within the virtual environment where daie is installed.
    asyncio.run(main())
