# Decentralized AI Ecosystem

A fully decentralized AI agentic system where agents communicate like humans through a decentralized brain network.

## 📚 Overview

This project creates a revolutionary decentralized AI ecosystem with:

- **Central Core System**: LLM cluster, tools storage, and coordination layer
- **Agent Node System**: Unlimited agents running on external computers worldwide
- **Decentralized Communication**: Secure, encrypted peer-to-peer messaging
- **Persistent Memory**: Each agent has unique knowledge storage and identity
- **Rich Toolset**: Web search, file access, system operations, and custom tools
- **High Performance**: Low latency communication and distributed task processing

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- NATS JetStream (included in Docker Compose)
- pip package manager

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd decentralized_ai_ecosystem
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r central_core_system/requirements.txt
   pip install -r agent_node_system/requirements.txt
   ```

4. **Copy and configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**:
   ```bash
   # Create PostgreSQL database
   createdb decentralized_ai
   ```

### Starting the System

#### Option 1: Using Shell Scripts (Recommended)

**Terminal 1 - Start Central Core System**:
```bash
./start_central_core.sh start
```

**Terminal 2 - Start Agent Node System**:
```bash
./start_agent_node.sh start
```

#### Option 2: Using Docker Compose

```bash
docker-compose up -d
```

#### Option 3: Manual Start

**Terminal 1 - Start Central Core System**:
```bash
cd central_core_system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn central_core_system.api_gateway.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Terminal 2 - Start Agent Node System**:
```bash
cd agent_node_system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m agent_node_system.agent_runtime.main_agent
```

### Accessing the System

- **Central Core API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **System Status**: http://localhost:8000/status

## 📖 Usage Guide

### Shell Script Commands

**Central Core System**:
```bash
./start_central_core.sh [command]
# Commands: start, stop, restart, status, logs, tail, check
```

**Agent Node System**:
```bash
./start_agent_node.sh [command]
# Commands: start, stop, restart, status, logs, tail, check, reset
```

### Configuration

Main configuration files:
- `central_core_system/config/settings.py` - Central core configuration
- `agent_node_system/config/environment.py` - Agent node configuration
- `.env` - Environment variables (copy from .env.example)

## 📊 System Architecture

### Central Core Components

- **LLM Cluster**: Model routing, embeddings, planning, reasoning
- **Tools MCP Server**: Tool registry, execution, protocol
- **Coordination Layer**: NATS JetStream based communication, event streaming, task routing
- **Global Memory Federation**: Knowledge graph, episodic archive, semantic memory
- **Identity Authority**: DID registry, key management, verification
- **API Gateway**: Authentication, rate limiting, CORS

### Agent Node Components

- **Agent Runtime**: Main agent, state management, lifecycle
- **Communication**: NATS JetStream client, libp2p P2P, X25519/AES encryption
- **Identity**: Keypair manager, Ed25519 signatures, verification
- **Memory System**: Working memory, chat history, vector storage
- **Local Tools**: Web search, file system, system operations
- **Tool Executor**: Tool loader, sandbox, permission manager

## 🔧 Development

### Adding New Tools

1. Create tool implementation in `agent_node_system/local_tools/`
2. Register tool in `central_core_system/tool_mcp_server/tool_registry/`
3. Define tool protocol in `central_core_system/tool_mcp_server/tool_protocol/`
4. Update agent configuration in `agent_node_system/config/role_config.py`

### Creating Custom Agent Roles

1. Define role configuration in `agent_node_system/config/role_config.py`
2. Implement role-specific behavior in `agent_node_system/agent_runtime/`
3. Register role capabilities in `central_core_system/coordination_layer/agent_registry/`

## 🔒 Security

The system implements comprehensive security features:
- End-to-end AES-256 encryption
- Ed25519 digital signatures
- DID-based decentralized identity
- Trust score system
- Sandboxed tool execution
- JWT authentication
- Rate limiting and CORS

## 📈 Performance

- **Response Time**: < 200ms for API calls, < 500ms for LLM calls
- **Message Throughput**: 100+ messages/second
- **Agent Capacity**: 1000+ concurrent agents
- **Scalability**: Horizontal scaling across multiple servers

## 🔧 Troubleshooting

### Common Issues

1. **Connection failures**: Check firewall settings and network connectivity
2. **Performance issues**: Monitor CPU/RAM usage, optimize tool execution
3. **Authentication errors**: Verify DID and key management
4. **Message delivery failures**: Check message router and retry mechanisms

### Log Files

- Central core: `central_core.log`
- Agent node: `agent_node.log`

### Health Check

```bash
curl http://localhost:8000/health
```

## 🚀 Deployment

### Production Deployment

1. **System Requirements**:
   - CPU: 8+ cores (x86_64)
   - RAM: 32GB+
   - Storage: 500GB SSD+
   - Network: 100Mbps+

2. **Docker Deployment**:
   ```bash
   docker-compose up -d --build
   ```

3. **Kubernetes Deployment**:
   See `central_core_system/infrastructure/kubernetes/` for Kubernetes configurations.

## 📚 Documentation

- **Architecture Overview**: [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
- **API Documentation**: http://localhost:8000/docs
- **Configuration Reference**: See configuration files

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes
6. Push to your branch
7. Create a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

If you encounter any issues or have questions:

1. Check the [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
2. Review the [FAQ](#faq)
3. Create a GitHub issue
4. Join our Discord community

## 📊 Performance Monitoring

### Prometheus Metrics
```
http://localhost:9090
```

### Grafana Dashboard
```
http://localhost:3000 (admin/admin)
```

## 🎯 Roadmap

- [ ] Federated Learning across agents
- [ ] Blockchain integration for immutable history
- [ ] Edge computing for low-latency tasks
- [ ] Multi-modal communication (images, video, audio)
- [ ] Autonomous learning capabilities
- [ ] Energy efficiency optimizations

## 🔄 Version History

- **1.0.0**: Initial release with basic agent communication and tool execution

## 📞 Contact

For more information, please contact:
- Email: support@decentralizedai.tech
- Website: https://www.decentralizedai.tech
- Discord: https://discord.gg/decentralizedai

---

**Note**: This system is designed for educational and research purposes. Always follow best practices for security and comply with all applicable laws and regulations.
