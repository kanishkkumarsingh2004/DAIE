# Decentralized AI Ecosystem

A lightweight Python library for creating and managing AI agents with tools, featuring decentralized communication and memory management.

## Features

### 🚀 **Core Features**
- **Lightweight Design**: Minimal dependencies, optimized for speed and resource efficiency
- **Agent Management**: Create, configure, and manage AI agents with unique identities
- **Tool System**: Define and register reusable tools for agents to execute
- **Decentralized Communication**: Agents communicate via NATS JetStream
- **Memory Management**: Agent-specific memories with persistence support
- **LLM Integration**: Centralized LLM management with Ollama integration (default: llama3)
- **CLI Interface**: Command-line tools for system management

### 🤖 **Agent Features**
Each agent has:
- **Unique Identity**: ID, name, role, goal, backstory, and system prompt
- **Local Tool Execution**: Agents execute tools locally within their own context
- **Chat History**: Individual memory stores with working, semantic, and episodic memory
- **Vector Database**: Each agent has its own vector database for semantic search (in development)
- **LangGraph Workflow**: Each agent has its own LangGraph workflow (in development)
- **LLM from Core**: Agents fetch LLM instances from the centralized LLM manager

## Installation

### Prerequisites
- Python 3.10+
- Ollama (for LLM functionality)
- NATS JetStream (for communication)

### Install the Library
```bash
pip install -e .
```

### Install Ollama
1. Download and install Ollama from [ollama.com](https://ollama.com/download)
2. Pull the default model:
   ```bash
   ollama pull llama3
   ```

## Quick Start

### Example: Creating a Simple Agent
```python
#!/usr/bin/env python3
import asyncio
import logging
from decentralized_ai import Agent, AgentConfig, Tool, ToolRegistry
from decentralized_ai.agents import AgentRole
from decentralized_ai.tools import tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("=== Decentralized AI Ecosystem Example ===")
    
    # Create a tool
    @tool(
        name="greeting",
        description="Generate a greeting message",
        category="general",
        version="1.0.0"
    )
    async def greeting_tool(name: str, language: str = "en") -> str:
        greetings = {
            "en": f"Hello, {name}! Welcome to the Decentralized AI Ecosystem!",
            "es": f"Hola, {name}! ¡Bienvenido al Ecosistema AI Descentralizado!",
            "fr": f"Bonjour, {name}! Bienvenue dans l'écosystème AI décentralisé!",
            "de": f"Hallo, {name}! Willkommen im dezentralen KI-Ökosystem!"
        }
        return greetings.get(language.lower(), greetings["en"])
    
    # Create agent configuration with new features
    config = AgentConfig(
        name="ResearchAgent",
        role=AgentRole.SPECIALIZED,
        goal="Research information on given topics",
        backstory="Created to assist with research and information gathering",
        system_prompt="You are a research assistant that helps users find and analyze information.",
        capabilities=["greeting"]
    )
    
    # Create agent
    agent = Agent(config=config)
    agent.add_tool(greeting_tool)
    
    # Test tool execution
    result = await greeting_tool.execute({"name": "Alice", "language": "es"})
    logger.info(f"✅ Tool executed successfully: {result}")
    
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
dai agent list

# Create a new agent
dai agent create --name "MyAgent" --role "general-purpose" --goal "Help users with questions"

# Start an agent
dai agent start <agent-id>

# Stop an agent
dai agent stop <agent-id>

# Get agent status
dai agent status <agent-id>

# Delete an agent
dai agent delete <agent-id>
```

### Core System Management
```bash
# Initialize the system
dai core init

# Start the central core system
dai core start

# Stop the central core system
dai core stop

# Restart the central core system
dai core restart

# Get system status
dai core status

# View system logs
dai core logs

# Check system health
dai core health
```

## LLM Configuration

### Setting LLM Parameters
```python
from decentralized_ai import set_llm, get_llm_config, LLMType

# Using Ollama (default)
set_llm(ollama_llm="llama3")
set_llm(ollama_llm="mistral", temperature=0.3, max_tokens=1500)

# Using OpenAI
set_llm(
    llm_type=LLMType.OPENAI,
    model_name="gpt-3.5-turbo",
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

#### Ollama Models:
- llama3 (default)
- llama3.2:latest
- mistral
- llama2
- gemma

#### OpenAI Models:
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-3.5-turbo

## Configuration

### Environment Variables
```bash
# System configuration
DAI_LOG_LEVEL=INFO
DAI_NATS_URL=nats://localhost:4222
DAI_CENTRAL_CORE_URL=http://localhost:8000

# LLM configuration
DAI_DEFAULT_LLM_MODEL=llama3
DAI_LLM_TEMPERATURE=0.7
DAI_LLM_MAX_TOKENS=1000

# Database configuration
DAI_DATABASE_URL=sqlite:///:memory:
DAI_REDIS_URL=redis://localhost:6379/0
```

## Architecture

### System Components
1. **Agent**: Individual AI entity with specific capabilities
2. **Tool**: Reusable functionality that agents can execute
3. **LLM Manager**: Handles LLM integration with various providers
4. **Communication Manager**: Facilitates agent communication via NATS
5. **Memory Manager**: Manages agent memory storage and retrieval
6. **Tool Registry**: Central repository for available tools
7. **Central Core System**: Orchestrator for the entire ecosystem

### Communication Protocol
Agents communicate using NATS JetStream with the following message types:
- **Text Messages**: Direct communication between agents
- **Tasks**: Requests for tool execution
- **Responses**: Results from task execution
- **Events**: System and agent events

## Development

### Prerequisites
- Python 3.10+
- Docker (for running dependencies)
- Poetry (for package management)

### Setup
```bash
# Clone the repository
git clone https://github.com/decentralized-ai/decentralized-ai-ecosystem.git
cd decentralized-ai-ecosystem

# Install dependencies
poetry install

# Run tests
poetry run pytest tests/

# Run the CLI
poetry run dai --help
```

### Project Structure
```
src/decentralized_ai/
├── __init__.py          # Package initialization
├── core/                # Core system components
│   ├── __init__.py
│   ├── system.py       # DecentralizedAISystem class
│   ├── node.py         # Node class for system components
│   └── llm_manager.py  # LLM management
├── agents/             # Agent implementation
│   ├── __init__.py
│   ├── agent.py        # Agent class
│   ├── config.py       # Agent configuration
│   └── message.py      # AgentMessage class
├── tools/              # Tool system
│   ├── __init__.py
│   ├── tool.py         # Tool class
│   └── registry.py     # ToolRegistry class
├── communication/      # Communication system
│   ├── __init__.py
│   └── manager.py      # CommunicationManager class
├── memory/             # Memory management
│   ├── __init__.py
│   └── manager.py      # MemoryManager class
├── config/             # Configuration system
│   ├── __init__.py
│   └── system.py       # SystemConfig class
├── utils/              # Utility functions
│   ├── __init__.py
│   └── logger.py       # Logger configuration
└── cli/                # CLI interface
    ├── __init__.py
    ├── main.py         # Main CLI entry point
    ├── agent.py        # Agent management commands
    └── core.py         # Core system commands
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the tests
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions or support, please contact **KANISHK KUMAR SINGH** at kanishkkumar2004@gmail.com.
