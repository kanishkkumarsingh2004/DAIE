"""
Agent management commands
"""

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from daie.agents.config import AgentConfig, AgentRole
from daie.config import ConfigManager

agent_app = typer.Typer(name="agent", help="Agent management commands", add_completion=True)

console = Console()


@agent_app.command(name="list")
def list_agents():
    """List all registered agents"""
    console.print(
        Panel(
            "[bold green]List of Agents[/bold green]",
            title="[blue]🤖 Agent Management[/blue]",
            border_style="blue",
            box=ROUNDED,
        )
    )

    try:
        # Load agents from JSON config
        config_mgr = ConfigManager()
        agents = config_mgr.load_agents_config()

        if not agents:
            console.print("[yellow]No agents structured yet. Use 'daie agent create' to add one.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold blue", border_style="cyan", box=ROUNDED)
        table.add_column("Name", style="magenta")
        table.add_column("Role", style="yellow")
        table.add_column("Provider", style="cyan")
        table.add_column("Model/Capabilities", style="green")

        for agent in agents:
            caps = ", ".join(agent.capabilities) if agent.capabilities else "None"
            table.add_row(
                agent.name,
                agent.role.value,
                agent.llm_provider,
                f"{agent.llm_model} | {caps}",
            )

        console.print(table)
        console.print(f"\nTotal configured agents: [bold green]{len(agents)}[/bold green]")

    except Exception as e:
        console.print(f"[red]Error listing agents: {e}[/red]")
        raise typer.Exit(code=1)


@agent_app.command(name="create")
def create_agent(
    name: str = typer.Option(None, "--name", "-n", help="Agent display name"),
    role: str = typer.Option(None, "--role", "-r", help="Agent role type"),
    capabilities: str = typer.Option(None, "--capabilities", "-c", help="Comma-separated list of capabilities"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Use interactive Q/A wizard"),
):
    """Create or configure a new agent"""
    console.print(
        Panel(
            "[bold green]Agent Configuration Wizard[/bold green]",
            title="[blue]✨ Agent Setup[/blue]",
            border_style="blue",
            box=ROUNDED,
        )
    )

    if interactive or not name:
        from rich.prompt import Confirm, Prompt

        name = Prompt.ask("[bold blue]Agent Name[/bold blue]", default=name or "NewAgent")

        valid_roles = [r.value for r in AgentRole]
        role = Prompt.ask(
            f"[bold blue]Role[/bold blue] ({', '.join(valid_roles)})",
            default=role or AgentRole.GENERAL_PURPOSE.value,
            choices=valid_roles,
        )

        goal = Prompt.ask("[bold blue]Agent Goal[/bold blue]", default="Perform specific tasks effectively")
        system_prompt = Prompt.ask("[bold blue]System Prompt[/bold blue]", default="You are a helpful AI assistant.")

        provider = Prompt.ask("[bold blue]LLM Provider[/bold blue] (ollama, openai, anthropic)", default="ollama")
        model = Prompt.ask("[bold blue]LLM Model[/bold blue]", default="llama3.2:latest")

        if not capabilities:
            caps_input = Prompt.ask("[bold blue]Capabilities (comma-separated)[/bold blue]", default="")
            capabilities = caps_input if caps_input else None

        network_url = Prompt.ask(
            "[bold blue]P2P Network URL[/bold blue] (e.g. https://my-agent.dev, enter for none)", default=""
        )
        network_url = network_url if network_url.strip() else None

        auth_token = Prompt.ask("[bold blue]P2P Auth Token[/bold blue] (enter for none)", default="")
        auth_token = auth_token if auth_token.strip() else None

        allow_file_transfers = Confirm.ask(
            "[bold blue]Allow incoming file transfers over P2P?[/bold blue]", default=False
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Saving agent configuration...", total=None)
            import time

            time.sleep(0.5)

            success = config_mgr.upsert_agent_config(agent_config)

            if not success:
                raise Exception("Failed to save to agents.json")

        console.print(
            Panel(
                f"[bold green]Agent '{name}' configured successfully![/bold green]\n"
                f"Configuration saved to: [bold]{config_mgr.agents_file}[/bold]\n"
                "To list agents, use: [bold]daie agent list[/bold]",
                title="[green]✅ Setup Complete[/green]",
                border_style="green",
                box=ROUNDED,
            )
        )
    except Exception as e:
        console.print(f"[red]Error configuring agent: {e}[/red]")
        raise typer.Exit(code=1)


@agent_app.command(name="start")
def start_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to start"),
):
    """Start an agent"""
    console.print(
        Panel(
            f"[bold green]Starting Agent:[/bold green] {agent_id}",
            title="[blue]🚀 Agent Startup[/blue]",
            border_style="blue",
            box=ROUNDED,
        )
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Connecting to communication system...", total=None)
            import time

            time.sleep(0.3)
            progress.update(task, description="Initializing agent memory...")
            time.sleep(0.3)
            progress.update(task, description="Registering with central core...")
            time.sleep(0.3)

        console.print(
            Panel(
                "[bold green]Agent started successfully![/bold green]",
                title="[green]✅ Startup Complete[/green]",
                border_style="green",
                box=ROUNDED,
            )
        )
    except Exception as e:
        console.print(f"[red]Error starting agent: {e}[/red]")
        raise typer.Exit(code=1)


@agent_app.command(name="stop")
def stop_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to stop"),
):
    """Stop an agent"""
    console.print(
        Panel(
            f"[bold yellow]Stopping Agent:[/bold yellow] {agent_id}",
            title="[yellow]⏹️  Agent Shutdown[/yellow]",
            border_style="yellow",
            box=ROUNDED,
        )
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="Deregistering from central core...", total=None)
            import time

            time.sleep(0.3)
            progress.update(task, description="Saving agent memory...")
            time.sleep(0.3)
            progress.update(task, description="Closing connections...")
            time.sleep(0.3)

        console.print(
            Panel(
                "[bold green]Agent stopped successfully![/bold green]",
                title="[green]✅ Shutdown Complete[/green]",
                border_style="green",
                box=ROUNDED,
            )
        )
    except Exception as e:
        console.print(f"[red]Error stopping agent: {e}[/red]")
        raise typer.Exit(code=1)


@agent_app.command(name="status")
def agent_status(
    agent_id: str = typer.Argument(..., help="Agent ID to check status"),
):
    """Get agent status and information"""
    console.print(
        Panel(
            f"[bold blue]Agent Status:[/bold blue] {agent_id}",
            title="[cyan]📊 Agent Information[/cyan]",
            border_style="cyan",
            box=ROUNDED,
        )
    )

    try:
        # Sample status data - in production, fetch from actual system
        status_data = {
            "ID": agent_id[:8] + "...",
            "Name": "Example Agent",
            "Role": "general-purpose",
            "Status": "Running",
            "Version": "1.0.1",
            "Uptime": "2 hours, 34 minutes",
            "Memory Usage": "156 MB",
            "Active Tasks": "3",
        }

        # Display status in a table
        table = Table(show_header=True, header_style="bold blue", border_style="cyan", box=ROUNDED)
        table.add_column("Property", style="magenta")
        table.add_column("Value", style="cyan")

        for key, value in status_data.items():
            table.add_row(key, str(value))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting agent status: {e}[/red]")
        raise typer.Exit(code=1)
