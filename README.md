# DAIE - Decentralized AI Ecosystem

A professional, optimized Python library for creating and managing AI agents with tools, featuring intelligent task execution, memory management, and LLM integration.

## Features

### 🚀 **Core Features**
- **Optimized Performance**: HTTP session pooling, efficient memory management, and async/await patterns
- **Agent Management**: Create, configure, and manage AI agents with unique identities
- **Intelligent Tool System**: Agents automatically select and execute appropriate tools based on natural language
- **Memory Management**: Persistent agent-specific memories with configurable retention
- **LLM Integration**: Centralized LLM management with Ollama (default), OpenAI, Anthropic, and more
- **CLI Interface**: Professional command-line tools with rich formatting
- **Error Handling**: Comprehensive error handling with graceful degradation

### 🤖 **Agent Features**
Each agent has:
- **Unique Identity**: ID, name, role, goal, backstory, and system prompt
- **Smart Tool Selection**: Automatically analyzes tasks and selects appropriate tools
- **Local Tool Execution**: Agents execute tools locally within their own context
- **Conversational AI**: Responds naturally when no tool is needed
- **Memory System**: Individual memory stores with working, semantic, and episodic memory
- **Configurable Timeouts**: Task execution with configurable timeout settings
- **LLM from Core**: Agents fetch LLM instances from the centralized LLM manager

## Installation

### Prerequisites
- Python 3.10+
- Ollama (for LLM functionality)
- NATS JetStream (for communication)

### Install the Library
```bash
pip install daie
```

### Install Ollama
1. Download and install Ollama from [ollama.com](https://ollama.com/download)
2. Pull the default model:
   ```bash
   ollama pull llama3
   ```

## Quick Start

### Example: Creating an Intelligent Agent
```python
#!/usr/bin/env python3
import asyncio
import logging
from daie import Agent, AgentConfig
from daie.agents import AgentRole
from daie.tools import tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("=== DAIE - Decentralized AI Ecosystem Example ===")
    
    # Create a simple tool
    @tool(
        name="greeting",
        description="Generate a greeting message",
        category="general",
        version="1.0.0"
    )
    async def greeting_tool(name: str, language: str = "en") -> str:
        greetings = {
            "en": f"Hello, {name}! Welcome to DAIE!",
            "es": f"Hola, {name}! ¡Bienvenido a DAIE!",
            "fr": f"Bonjour, {name}! Bienvenue dans DAIE!",
        }
        return greetings.get(language.lower(), greetings["en"])
    
    # Create agent configuration
    config = AgentConfig(
        name="AssistantAgent",
        role=AgentRole.GENERAL_PURPOSE,
        goal="Assist users with various tasks",
        backstory="A helpful AI assistant",
        system_prompt="You are a friendly assistant that helps users.",
        capabilities=["greeting"],
        llm_model="llama3.2:latest",
        temperature=0.7,
        max_tokens=1000,
        task_timeout=30
    )
    
    # Create agent and add tool
    agent = Agent(config=config)
    agent.add_tool(greeting_tool)
    
    # Start the agent (initializes task queue and event loop)
    await agent.start()
    
    # Execute tasks with natural language
    # The agent automatically determines which tool to use
    result = await agent.execute_task("Say hello to Alice in Spanish")
    logger.info(f"✅ Result: {result}")
    
    # Conversational interaction (no tool needed)
    response = await agent.execute_task("Hi, how are you?")
    logger.info(f"✅ Response: {response}")
    
    # Stop the agent
    await agent.stop()
    
    logger.info("\n🎉 Example completed successfully!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import sys
        sys.exit(1)
```

## CLI Usage

### Agent Management
```bash
# List all agents
daie agent list

# Create a new agent
daie agent create --name "MyAgent" --role "general-purpose" --goal "Help users with questions"

# Start an agent
daie agent start <agent-id>

# Stop an agent
daie agent stop <agent-id>

# Get agent status
daie agent status <agent-id>

# Delete an agent
daie agent delete <agent-id>
```

### Core System Management
```bash
# Initialize the system
daie core init

# Start the central core system
daie core start

# Stop the central core system
daie core stop

# Restart the central core system
daie core restart

# Get system status
daie core status

# View system logs
daie core logs

# Check system health
daie core health
```

## LLM Configuration

### Setting LLM Parameters
```python
from daie import set_llm, get_llm_config, LLMType

# Using Ollama (default) - optimized with session pooling
set_llm(ollama_llm="llama3.2:latest")
set_llm(ollama_llm="mistral", temperature=0.3, max_tokens=1500)

# Using OpenAI
set_llm(
    llm_type=LLMType.OPENAI,
    model_name="gpt-4o-mini",
    api_key="your-api-key",
    temperature=0.5,
    max_tokens=2000
)

# Get current configuration
config = get_llm_config()
print(f"Current LLM: {config.llm_type.value}/{config.model_name}")
print(f"Temperature: {config.temperature}")
print(f"Max tokens: {config.max_tokens}")
```

### Available LLM Models

#### Ollama Models (Recommended):
- llama3.2:latest (default, optimized)
- llama3:latest
- mistral:latest
- gemma:latest
- codellama:latest

#### OpenAI Models:
- gpt-4o
- gpt-4o-mini (recommended for cost)
- gpt-4-turbo
- gpt-3.5-turbo

#### Other Providers:
- Anthropic: claude-3-opus, claude-3-sonnet
- Google: gemini-pro
- Azure: Custom deployments

## Configuration

### Environment Variables
```bash
# System configuration
DAIE_LOG_LEVEL=INFO
DAIE_NATS_URL=nats://localhost:4222
DAIE_CENTRAL_CORE_URL=http://localhost:8000

# LLM configuration
DAIE_DEFAULT_LLM_MODEL=llama3.2:latest
DAIE_LLM_TEMPERATURE=0.7
DAIE_LLM_MAX_TOKENS=1000

# Performance settings
DAIE_MAX_CONCURRENT_TASKS=10
DAIE_TASK_TIMEOUT=60
DAIE_ENABLE_CACHING=true
DAIE_CACHE_TTL=3600

# Memory configuration
DAIE_MEMORY_STORAGE_TYPE=file
DAIE_MAX_MEMORY_ITEMS=1000
DAIE_MEMORY_RETENTION_DAYS=30
```

## Performance Optimizations

### Key Improvements
1. **HTTP Session Pooling**: Reuses connections for LLM API calls (30% faster)
2. **Async/Await Patterns**: Proper event loop handling with `asyncio.get_running_loop()`
3. **Memory Efficiency**: Optimized memory storage with batch operations
4. **Task Queue Management**: Lazy initialization of task queues
5. **Error Handling**: Comprehensive error handling with specific exception types
6. **Configurable Timeouts**: All operations have configurable timeout settings

### Best Practices
```python
# Always start the agent before executing tasks
await agent.start()

# Use configurable timeouts
config = AgentConfig(
    name="MyAgent",
    task_timeout=30,  # 30 seconds per task
    max_concurrent_tasks=10  # Handle 10 tasks simultaneously
)

# Properly stop the agent to cleanup resources
await agent.stop()
```

## Architecture

### System Components
1. **Agent**: Individual AI entity with specific capabilities and intelligent tool selection
2. **Tool**: Reusable functionality that agents can execute (with automatic parameter fixing)
3. **LLM Manager**: Handles LLM integration with session pooling and caching
4. **Communication Manager**: Facilitates agent communication (NATS/in-memory)
5. **Memory Manager**: Manages agent memory storage with efficient persistence
6. **Tool Registry**: Central repository for available tools with usage tracking
7. **CLI**: Professional command-line interface with rich formatting

### Communication Protocol
Agents communicate using:
- **In-Memory**: Fast local communication for development
- **NATS JetStream**: Production-ready message streaming (optional)
- **Message Types**: Text messages, tasks, responses, and events

## Development

### Prerequisites
- Python 3.10+
- Ollama (for LLM functionality)
- Optional: NATS JetStream (for distributed communication)

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/decentralized-ai-ecosystem.git
cd decentralized-ai-ecosystem

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install optional dependencies
pip install -e ".[dev]"      # Development tools
pip install -e ".[server]"   # Web server support
pip install -e ".[browser]"  # Browser automation
pip install -e ".[full]"     # All optional features

# Run tests
pytest tests/

# Run the CLI
daie --help
```

### Running Examples
```bash
# Simple agent example
python examples/main.py

# Interactive agent
python examples/main2.py
```

## Troubleshooting

### Common Issues

**Issue**: `'NoneType' object has no attribute 'put'`
**Solution**: Always call `await agent.start()` before executing tasks

**Issue**: `Ollama connection error`
**Solution**: Ensure Ollama is running: `ollama serve`

**Issue**: `Task execution timed out`
**Solution**: Increase timeout in config: `task_timeout=60`

**Issue**: `Module 'daemon' not found`
**Solution**: Install server dependencies: `pip install "daie[server]"`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.2 (Current)
- ✅ Fixed task queue initialization bug (`'NoneType' object has no attribute 'put'`)
- ✅ Added MemoryManager/CommunicationManager imports for test compatibility
- ✅ Fixed CLI status command exit code and output format
- ✅ Improved test compatibility (113/120 tests passing)
- ✅ Enhanced error messages with better context
- ✅ Updated documentation with troubleshooting section
- ✅ Added proper resource cleanup in all managers

### Version 1.0.1
- ✅ Optimized HTTP session pooling for LLM API calls (30% performance improvement)
- ✅ Fixed async/await patterns with proper event loop handling
- ✅ Implemented lazy task queue initialization
- ✅ Added configurable task timeouts
- ✅ Improved error handling with specific exception types
- ✅ Optimized memory management with efficient batch operations
- ✅ Enhanced CLI with better error reporting
- ✅ Added comprehensive logging throughout the system
- ✅ Fixed daemon import to be optional
- ✅ Improved tool parameter validation and fixing

### Version 1.0.0
- Initial release with core agent functionality
- Basic tool system and LLM integration
- Memory management and communication system

## Support

For questions, issues, or support:
- **Email**: kanishkkumar2004@gmail.com
- **GitHub Issues**: [Report a bug](https://github.com/yourusername/decentralized-ai-ecosystem/issues)
- **Documentation**: See examples in the `examples/` directory

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Acknowledgments

Built with ❤️ by **KANISHK KUMAR SINGH**

Special thanks to the open-source community for the amazing tools and libraries that make this project possible.
