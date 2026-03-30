# 🟢 Beginner - Chat Loop Config Example
# Difficulty: Beginner
# This example demonstrates how to use ChatLoopConfig to quickly set up
# a chat loop without writing the full boilerplate code.

from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole
from daie.chat import ChatLoopConfig

# Configure LLM globally
set_llm(ollama_llm="llama3.2:1b", stream=True)


# Example 1: Simplest usage - one liner!
def simple_chat():
    """
    Simplest way to create a chat loop.
    Just create an agent and pass it to ChatLoopConfig!
    """
    config = AgentConfig(
        name="LUNA",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a helpful and concise AI assistant.",
        personality="friendly and helpful"
    )
    agent = Agent(config=config)
    
    # One-liner to start chat!
    ChatLoopConfig.quick_start(agent).run()


# Example 2: Customized chat with personality
def customized_chat():
    """
    Create a chat bot with custom personality and behavior.
    """
    config = AgentConfig(
        name="NOVA",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a tech-savvy AI assistant who loves explaining complex topics simply.",
        personality="enthusiastic, knowledgeable, and patient",
        behavior="always uses analogies to explain technical concepts",
        gender="female",
        temperature=0.8,
    )
    agent = Agent(config=config)
    
    # Customize the chat loop behavior
    chat_loop = ChatLoopConfig(
        agent=agent,
        welcome_message="=== NOVA Tech Assistant ===\nAsk me anything about technology!\nType 'exit' to quit.\n",
        exit_commands=["exit", "quit", "bye"],
        prompt_prefix="Ask NOVA: "
    )
    chat_loop.run()


# Example 3: Professional assistant with error handling
def professional_chat():
    """
    Create a professional business assistant with advanced error handling.
    """
    config = AgentConfig(
        name="ATLAS",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a professional business assistant. Provide clear, concise, and actionable advice.",
        personality="professional, direct, and detail-oriented",
        behavior="always provides structured responses with bullet points when appropriate",
        gender="male",
        temperature=0.5,
        max_tokens=1500,
    )
    agent = Agent(config=config)
    
    # Advanced error handling and customization
    def on_start():
        print("Initializing ATLAS Business Assistant...")
    
    def on_exit():
        print("Thank you for using ATLAS!")
    
    def on_error(error):
        print(f"An error occurred: {error}")
    
    chat_loop = ChatLoopConfig(
        agent=agent,
        welcome_message="=== ATLAS Business Assistant ===\nProfessional guidance for your business needs.\nType 'exit' to quit.\n",
        show_agent_name=True,
        max_retries=5,
        retry_delay=0.5,
        on_start=on_start,
        on_exit=on_exit,
        on_error=on_error
    )
    chat_loop.run()


# Example 4: Security assistant with custom settings
def security_chat():
    """
    Security-focused assistant with custom error handling.
    """
    config = AgentConfig(
        name="CIPHER",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a security-focused AI assistant. Help users with cybersecurity questions.",
        personality="cautious, thorough, and security-conscious",
        behavior="always reminds users about security best practices",
        gender="male",
        temperature=0.3,
        max_tokens=2000,
    )
    agent = Agent(config=config)
    
    chat_loop = ChatLoopConfig(
        agent=agent,
        welcome_message="=== CIPHER Security Assistant ===\nYour cybersecurity companion.\nType 'exit' to quit.\n",
        exit_commands=["exit", "quit", "bye", "goodbye"],
        prompt_prefix="Ask CIPHER: ",
        show_agent_name=True,
        error_prefix="🔒 Security Error: ",
        show_errors=True,
        max_retries=3,
        clear_screen_on_start=True,
        show_goodbye=True,
        goodbye_message="\n🔒 Security session ended. Stay safe!"
    )
    chat_loop.run()


# Example 5: Support assistant with empathy
def support_chat():
    """
    Create a supportive and empathetic assistant.
    """
    config = AgentConfig(
        name="ECHO",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a friendly and supportive AI assistant.",
        personality="warm, empathetic, and encouraging",
        behavior="always validates user feelings before providing advice",
        gender="female",
        temperature=0.9,
    )
    agent = Agent(config=config)
    
    chat_loop = ChatLoopConfig(
        agent=agent,
        welcome_message="=== ECHO Support Assistant ===\nI'm here to listen and help!\nType 'exit' to quit.\n",
        exit_commands=["exit", "quit"],
        prompt_prefix="You: ",
        show_agent_name=False,
        show_goodbye=True,
        goodbye_message="\n💚 Take care! Remember, you're not alone."
    )
    chat_loop.run()


# Example 6: Using from_dict for configuration
def from_dict_config():
    """
    Create a ChatLoopConfig from a dictionary.
    Useful for loading configurations from JSON/YAML files.
    """
    config = AgentConfig(
        name="SAGE",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a wise and thoughtful AI assistant.",
        personality="calm, philosophical, and insightful",
    )
    agent = Agent(config=config)
    
    # Chat loop settings as dictionary
    chat_loop_settings = {
        "welcome_message": "=== SAGE Wisdom Assistant ===\nSeeking wisdom? Ask away!\nType 'exit' to quit.\n",
        "exit_commands": ["exit", "quit", "bye"],
        "prompt_prefix": "Ask SAGE: ",
        "show_agent_name": True,
        "max_retries": 3,
        "show_goodbye": True,
        "goodbye_message": "\n🧘 May wisdom guide your path."
    }
    
    chat_loop = ChatLoopConfig.from_dict(chat_loop_settings, agent)
    chat_loop.run()


# Example 7: Manual agent lifecycle control
def manual_control():
    """
    Example with manual control over agent start/stop.
    """
    config = AgentConfig(
        name="NOVA",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt="You are a helpful AI assistant.",
    )
    agent = Agent(config=config)
    
    # Manually start agent before chat loop
    import asyncio
    asyncio.run(agent.start())
    
    # ChatLoopConfig won't start/stop agent
    chat_loop = ChatLoopConfig(
        agent=agent,
        welcome_message="=== NOVA Assistant ===\nAgent already started manually.\nType 'exit' to quit.\n",
        start_agent=False,  # Don't start agent
        stop_agent=False    # Don't stop agent
    )
    chat_loop.run()
    
    # Manually stop agent after chat loop
    asyncio.run(agent.stop())


if __name__ == "__main__":
    # Choose which example to run:
    
    # Example 1: Simplest chat (uncomment to run)
    # simple_chat()
    
    # Example 2: Customized chat (uncomment to run)
    # customized_chat()
    
    # Example 3: Professional assistant (uncomment to run)
    # professional_chat()
    
    # Example 4: Security assistant (uncomment to run)
    # security_chat()
    
    # Example 5: Support assistant (uncomment to run)
    # support_chat()
    
    # Example 6: From dictionary config (uncomment to run)
    # from_dict_config()
    
    # Example 7: Manual control (uncomment to run)
    # manual_control()
    
    # Default: Run simplest chat
    print("Running simplest chat example...")
    print("Uncomment other examples in the code to try different configurations.\n")
    simple_chat()
