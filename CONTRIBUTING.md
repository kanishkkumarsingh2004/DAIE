# Contributing to DAIE

Thank you for your interest in contributing to the Decentralized AI Ecosystem (DAIE)! This guide covers development setup, testing requirements, and contribution workflow.

---

## 🚀 Quick Start for Contributors

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | ≥ 3.10 | Core runtime |
| **NATS JetStream** | ≥ 2.10 | Message broker for P2P communication |
| **Ollama** | Latest | Local LLM inference (default) |
| **Chrome/Chromium** | Latest | Playwright browser automation |
| **Git** | ≥ 2.30 | Version control |

### Optional (for full feature tests)

| Tool | Install Command | Tests Affected |
|------|----------------|----------------|
| `chromadb` | `pip install chromadb sentence-transformers` | Vector RAG backend |
| `faiss-cpu` | `pip install faiss-cpu sentence-transformers` | FAISS RAG backend |
| `playwright` | `pip install playwright && playwright install chromium` | Browser automation |
| `aiosqlite` + `asyncpg` | `pip install aiosqlite asyncpg` | DatabaseTool |
| `tavily-python` | `pip install tavily-python` | WebSearchTool fallback |
| `opencv-python` | `pip install opencv-python` | Vision/Camera |
| `pyaudio` | `pip install pyaudio` (needs `portaudio19-dev`) | Audio I/O |

---

## 🧪 Testing Requirements

### 1. Local Test Environment

```bash
# Clone and setup
git clone https://github.com/kanishkkumarsingh2004/decentralized-ai-ecosystem.git
cd decentralized-ai-ecosystem
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,vector,faiss,playwright,database,email,search,server]"
playwright install chromium

# Start NATS JetStream (required for P2P/communication tests)
docker run -d --name nats -p 4222:4222 -p 8222:8222 nats:latest -js

# Start Ollama (required for LLM-dependent tests)
ollama serve &
ollama pull llama3.2:1b
```

### 2. Run Test Suite

```bash
# Full test suite (344 tests)
pytest tests/ -v

# Quick unit tests only (no external dependencies)
pytest tests/ -v -k "not selenium and not p2p and not network"

# Specific component tests
pytest tests/test_agents.py tests/test_orchestrator.py tests/test_parliament.py -v
pytest tests/test_communication.py tests/test_core.py -v
pytest tests/test_tools_harden.py tests/test_rag_engine.py -v
```

### 3. Test Categories

| Category | Command | External Deps |
|----------|---------|---------------|
| **Core Units** | `pytest tests/test_agents.py tests/test_*config*.py tests/test_serialization.py` | None |
| **Orchestration** | `pytest tests/test_orchestrator.py tests/test_parliament.py tests/test_hybrid_parliament.py` | NATS, Ollama |
| **Tools** | `pytest tests/test_file_manager.py tests/test_tools.py tests/test_tools_harden.py` | NATS, Ollama, Tavily (optional) |
| **RAG/Memory** | `pytest tests/test_rag_engine.py tests/test_memory.py` | ChromaDB/FAISS (optional) |
| **Communication** | `pytest tests/test_communication.py tests/test_registry_auth.py tests/test_p2p_network.py` | NATS |
| **Browser** | `pytest tests/test_selenium_tools.py` | Playwright + Chromium |
| **Integration** | `pytest tests/test_integration.py` | All above |
| **Full Suite** | `pytest tests/` | All above |

### 4. Expected Test Times

| Suite | Time (approx) |
|-------|---------------|
| Core units | ~5s |
| Orchestration | ~30s |
| Tools | ~10s |
| RAG/Memory | ~20s |
| Communication | ~60s (NATS startup) |
| Browser | ~5s |
| **Full** | **~2-3 min** |

---

## 📋 Example Verification Checklist

Before submitting PRs, verify these examples work:

```bash
# 1. Basic chat (requires Ollama)
python examples/01_basic_chat.py
# Type "exit" to quit

# 2. Custom tools
python examples/02_custom_tools.py

# 3. P2P networking (requires 2 terminals + NATS)
python examples/03_p2p_networking.py

# 4. RAG chat
python examples/04_vector_rag_chat.py

# 5. Vision chat (requires Ollama vision model + camera)
# ollama pull qwen3-vl:2b
python examples/05_vision_chat.py

# 6. Node agents demo
python examples/08_node_agents_demo.py

# 7. Node agents interactive
python examples/07_node_agents_interactive.py

# 8. Bidirectional P2P routing
python examples/09_bidirectional_p2p_routing.py

# 9. Hybrid orchestrator + node
python examples/10_hybrid_orchestrator_node.py

# 10. Chat loop configs
python examples/12_chat_loop_config.py

# 11. Parliament demo
python examples/parliament_demo.py

# 12. Hybrid parliament demo
python examples/hybrid_parliament_demo.py

# 13. Grand parliament + persistent memory
python examples/13_grand_parliament_persistent_memory.py

# 14. A2A block communication
python examples/15_a2a_block_communication.py
```

### Quick Automated Check

```bash
# Run all examples that don't need interactive input
cd examples
for f in *.py; do
    echo "=== Testing $f ==="
    timeout 30 python "$f" 2>&1 | head -20 || echo "⚠️ $f timed out or failed"
done
```

---

## 🔧 Development Workflow

### Code Style

```bash
# Format
black src/ tests/ examples/

# Lint
flake8 src/ tests/ examples/

# Type check
mypy src/

# All checks
pytest tests/ && black --check src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Pre-commit Hooks (Recommended)

```bash
pip install pre-commit
pre-commit install
```

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(orchestrator): add parallel task delegation

Add ParallelExecutor support to Orchestrator for concurrent
sub-agent execution with configurable concurrency limits.

Closes #123
```

---

## 🐛 Debugging Common Test Issues

### NATS Connection Failed
```bash
# Check NATS is running
docker ps | grep nats
# Or start it
docker run -d --name nats -p 4222:4222 nats:latest -js
```

### Ollama Model Not Found
```bash
ollama pull llama3.2:1b
# Or set custom model
export DAIE_OLLAMA_MODEL=llama3.1:8b
```

### Playwright Browser Missing
```bash
playwright install chromium
# On Linux may need:
sudo playwright install-deps chromium
```

### Import Errors (ModuleNotFoundError)
```bash
# Reinstall in editable mode
pip install -e ".[dev,vector,faiss,playwright,database,email,search,server]"
```

### Port Conflicts
- NATS: 4222, 8222
- Default agent WebSocket: 8000+
- Prometheus metrics: 9090

---

## 📝 Pull Request Checklist

- [ ] All tests pass: `pytest tests/`
- [ ] Code formatted: `black src/ tests/ examples/`
- [ ] Linting clean: `flake8 src/ tests/ examples/`
- [ ] Types valid: `mypy src/`
- [ ] New tests added for new features
- [ ] Documentation updated (README, docstrings, docs/)
- [ ] Examples verified (see Example Verification Checklist)
- [ ] Commit messages follow convention
- [ ] No secrets/tokens in code

---

## 📚 Documentation

- **Architecture**: `docs/orchestrator.md`, `docs/parliament.md`, `docs/node.md`
- **Networking**: `docs/p2p.md`, `docs/communication.md`, `docs/network_configuration.md`
- **RAG**: `docs/rag.md`
- **Tools**: `docs/tools.md`
- **Memory**: `docs/memory.md`
- **CLI**: `docs/cli.md`

---

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/kanishkkumarsingh2004/decentralized-ai-ecosystem/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kanishkkumarsingh2004/decentralized-ai-ecosystem/discussions)
- **Discord**: [DAIE Community](https://discord.gg/daie) (if available)

---

**Thank you for contributing to DAIE!** 🚀