# CLI (Command Line Interface)

DAIE provides a powerful command-line interface for managing agents, the core system, and performing common tasks.

## Installation

The CLI is automatically installed when you install DAIE:

```bash
pip install daie
```

---

## Quick Start

```bash
# Show help
daie --help

# Show version
daie --version

# Initialize the system
daie core init

# Create an agent
daie agent create --name "MyAgent" --role "general-purpose"

# Start the core system
daie core start --background

# Check system status
daie core status

# Start an agent
daie agent start <agent-id>
```

---

## Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `daie core init` | Initialize the core system |
| `daie core start` | Start the core system |
| `daie core start --background` | Start the core system in background |
| `daie core stop` | Stop the core system |
| `daie core status` | Show core system status |
| `daie core health` | Check system health |

### Agent Commands

| Command | Description |
|---------|-------------|
| `daie agent create` | Create a new agent |
| `daie agent list` | List all agents |
| `daie agent start <agent-id>` | Start an agent |
| `daie agent stop <agent-id>` | Stop an agent |
| `daie agent status <agent-id>` | Show agent status |
| `daie agent delete <agent-id>` | Delete an agent |

---

## Core Commands

### daie core init

Initialize the core system:

```bash
daie core init
```

This creates necessary configuration files and directories.

### daie core start

Start the core system:

```bash
# Start in foreground
daie core start

# Start in background
daie core start --background
```

### daie core stop

Stop the core system:

```bash
daie core stop
```

### daie core status

Show core system status:

```bash
daie core status
```

### daie core health

Check system health:

```bash
daie core health
```

---

## Agent Commands

### daie agent create

Create a new agent:

```bash
# Create with default settings
daie agent create --name "MyAgent"

# Create with specific role
daie agent create --name "Researcher" --role "specialized"

# Create with capabilities
daie agent create --name "Analyst" --role "analyzer" --capabilities "data_analysis,reporting"
```

Available roles:
- `general-purpose` — General purpose agent
- `specialized` — Specialized agent
- `coordinator` — Coordinator agent
- `worker` — Worker agent
- `analyzer` — Analyzer agent
- `executor` — Executor agent

### daie agent list

List all agents:

```bash
daie agent list
```

### daie agent start

Start an agent:

```bash
daie agent start <agent-id>
```

### daie agent stop

Stop an agent:

```bash
daie agent stop <agent-id>
```

### daie agent status

Show agent status:

```bash
daie agent status <agent-id>
```

### daie agent delete

Delete an agent:

```bash
daie agent delete <agent-id>
```

---

## Global Options

| Option | Description |
|--------|-------------|
| `--help`, `-h` | Show help information |
| `--version`, `-v` | Show version information |

---

## Examples

### Complete Workflow

```bash
# 1. Initialize the system
daie core init

# 2. Start the core system in background
daie core start --background

# 3. Create agents
daie agent create --name "Professor" --role "coordinator"
daie agent create --name "Researcher" --role "specialized"
daie agent create --name "Analyst" --role "analyzer"

# 4. List agents
daie agent list

# 5. Start agents
daie agent start <professor-id>
daie agent start <researcher-id>
daie agent start <analyst-id>

# 6. Check status
daie core status
daie agent status <professor-id>

# 7. Stop agents
daie agent stop <professor-id>
daie agent stop <researcher-id>
daie agent stop <analyst-id>

# 8. Stop core system
daie core stop
```

### Quick Agent Creation

```bash
# Create and start an agent in one go
daie agent create --name "QuickAgent" --role "general-purpose"
daie agent start <quick-agent-id>
```

---

## Configuration

The CLI uses the same configuration as the Python API. Configuration is stored in:

- **Linux/Mac**: `~/.daie/config.yaml`
- **Windows**: `%USERPROFILE%\.daie\config.yaml`

---

## Troubleshooting

### Common Issues

1. **Command not found**: Ensure DAIE is installed: `pip install daie`
2. **Permission denied**: Check file permissions for configuration directory
3. **Port already in use**: Stop existing core system: `daie core stop`
4. **Agent not found**: List agents: `daie agent list`

### Getting Help

```bash
# Show general help
daie --help

# Show help for specific command
daie core --help
daie agent --help
daie agent create --help
```

---

## Next Steps

- [Getting Started](getting-started.md) — Installation and basic concepts
- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [Communication](communication.md) — P2P networking and file transfers
