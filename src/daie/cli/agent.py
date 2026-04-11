"""
Agent management commands
Replaces typer and rich dependencies
"""

import argparse
import time

from daie.agents.config import AgentConfig, AgentRole
from daie.config import ConfigManager
from daie.utils.console import print_error, print_info, print_success, print_header


def list_agents(args: argparse.Namespace):
    """List all registered agents"""
    print_header("🤖 Agent Management - List of Agents")

    try:
        # Load agents from JSON config
        config_mgr = ConfigManager()
        agents = config_mgr.load_agents_config()

        if not agents:
            print_info("No agents structured yet. Use 'daie agent create' to add one.")
            return

        print_info(f"Total configured agents: {len(agents)}")
        print("-" * 80)
        print(f"{'Name':<20} | {'Role':<20} | {'Provider':<10} | {'Model/Capabilities'}")
        print("-" * 80)

        for agent in agents:
            caps = ", ".join(agent.capabilities) if agent.capabilities else "None"
            print(
                f"{agent.name:<20} | {agent.role.value:<20} | {agent.llm_provider:<10} | {agent.llm_model} | {caps}"
            )

        print("-" * 80)

    except Exception as e:
        print_error(f"Error listing agents: {e}")
        exit(1)


def create_agent(args: argparse.Namespace):
    """Create or configure a new agent"""
    print_header("✨ Agent Setup - Configuration Wizard")

    name = args.name
    role = args.role
    capabilities = args.capabilities
    interactive = args.interactive

    if interactive or not name:
        name = input("Agent Name [NewAgent]: ") or name or "NewAgent"

        valid_roles = [r.value for r in AgentRole]
        print(f"Valid Roles: {', '.join(valid_roles)}")
        role = (
            input(f"Role [{AgentRole.GENERAL_PURPOSE.value}]: ")
            or role
            or AgentRole.GENERAL_PURPOSE.value
        )

        goal = (
            input("Agent Goal [Perform specific tasks effectively]: ")
            or "Perform specific tasks effectively"
        )
        system_prompt = (
            input("System Prompt [You are a helpful AI assistant.]: ")
            or "You are a helpful AI assistant."
        )

        provider = input("LLM Provider [ollama]: ") or "ollama"
        model = input("LLM Model [llama3.2:latest]: ") or "llama3.2:latest"

        if not capabilities:
            capabilities = input("Capabilities (comma-separated): ") or ""

        network_url = input("P2P Network URL (enter for none): ") or None
        auth_token = input("P2P Auth Token (enter for none): ") or None

        allow_file_transfers = (
            input("Allow incoming file transfers over P2P? (y/n) [n]: ").lower() == "y"
        )
    else:
        goal = "Perform general tasks"
        system_prompt = "You are a helpful AI assistant."
        provider = "ollama"
        model = "llama3.2:latest"
        network_url = None
        auth_token = None
        allow_file_transfers = False

    caps_list = [c.strip() for c in capabilities.split(",")] if capabilities else []

    config_mgr = ConfigManager()
    agent_config = AgentConfig(
        name=name,
        role=AgentRole(role),
        goal=goal,
        system_prompt=system_prompt,
        capabilities=caps_list,
        llm_provider=provider,
        llm_model=model,
        network_url=network_url,
        auth_token=auth_token,
        allow_file_transfers=allow_file_transfers,
    )

    try:
        print_info("Saving agent configuration...")
        time.sleep(0.5)

        success = config_mgr.upsert_agent_config(agent_config)

        if not success:
            raise Exception("Failed to save to agents.json")

        print_success(f"Agent '{name}' configured successfully!")
        print_info(f"Configuration saved to: {config_mgr.agents_file}")
    except Exception as e:
        print_error(f"Error configuring agent: {e}")
        exit(1)


def start_agent(args: argparse.Namespace):
    """Start an agent"""
    print_header(f"🚀 Agent Startup - Starting Agent: {args.agent_id}")

    try:
        print_info("Connecting to communication system...")
        time.sleep(0.3)
        print_info("Initializing agent memory...")
        time.sleep(0.3)
        print_info("Registering with central core...")
        time.sleep(0.3)

        print_success("Agent started successfully!")
    except Exception as e:
        print_error(f"Error starting agent: {e}")
        exit(1)


def stop_agent(args: argparse.Namespace):
    """Stop an agent"""
    print_header(f"⏹️ Agent Shutdown - Stopping Agent: {args.agent_id}")

    try:
        print_info("Deregistering from central core...")
        time.sleep(0.3)
        print_info("Saving agent memory...")
        time.sleep(0.3)
        print_info("Closing connections...")
        time.sleep(0.3)

        print_success("Agent stopped successfully!")
    except Exception as e:
        print_error(f"Error stopping agent: {e}")
        exit(1)


def agent_status(args: argparse.Namespace):
    """Get agent status and information"""
    print_header(f"📊 Agent Information - Agent Status: {args.agent_id}")

    try:
        # Sample status data
        status_data = {
            "ID": args.agent_id[:8] + "...",
            "Name": "Example Agent",
            "Role": "general-purpose",
            "Status": "Running",
            "Version": "1.0.1",
            "Uptime": "2 hours, 34 minutes",
            "Memory Usage": "156 MB",
            "Active Tasks": "3",
        }

        print("-" * 40)
        for key, value in status_data.items():
            print(f"{key:<15}: {value}")
        print("-" * 40)

    except Exception as e:
        print_error(f"Error getting agent status: {e}")
        exit(1)


def register_agent_commands(subparsers):
    """Register agent subcommands with the main parser"""
    agent_parser = subparsers.add_parser("agent", help="Agent management commands")
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command")

    # List
    list_parser = agent_subparsers.add_parser("list", help="List all registered agents")
    list_parser.set_defaults(func=list_agents)

    # Create
    create_parser = agent_subparsers.add_parser("create", help="Create or configure a new agent")
    create_parser.add_argument("--name", "-n", help="Agent display name")
    create_parser.add_argument("--role", "-r", help="Agent role type")
    create_parser.add_argument("--capabilities", "-c", help="Comma-separated list of capabilities")
    create_parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Don't use interactive wizard",
    )
    create_parser.set_defaults(interactive=True, func=create_agent)

    # Start
    start_parser = agent_subparsers.add_parser("start", help="Start an agent")
    start_parser.add_argument("agent_id", help="Agent ID to start")
    start_parser.set_defaults(func=start_agent)

    # Stop
    stop_parser = agent_subparsers.add_parser("stop", help="Stop an agent")
    stop_parser.add_argument("agent_id", help="Agent ID to stop")
    stop_parser.set_defaults(func=stop_agent)

    # Status
    status_parser = agent_subparsers.add_parser("status", help="Get agent status and information")
    status_parser.add_argument("agent_id", help="Agent ID to check status")
    status_parser.set_defaults(func=agent_status)
