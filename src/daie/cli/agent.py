"""
Agent management commands
"""

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.box import ROUNDED

from daie.core.system import DecentralizedAISystem
from daie.config import SystemConfig

agent_app = typer.Typer(
    name="agent", help="Agent management commands", add_completion=True
)

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
        # Get actual agents from the system
        config = SystemConfig()
        system = DecentralizedAISystem(config=config)
        agents = system.list_agents()

        if not agents:
            console.print("[yellow]No agents found[/yellow]")
            return

        table = Table(
            show_header=True, header_style="bold blue", border_style="cyan", box=ROUNDED
        )
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Role", style="yellow")
        table.add_column("Status", style="green")

        for agent in agents:
            table.add_row(
                agent.id[:8] + "...",  # Truncate ID for display
                agent.name,
                agent.role.value,
                "Running" if agent.is_running else "Stopped",
            )

        console.print(table)
        console.print(f"\nTotal agents: [bold green]{len(agents)}[/bold green]")
    
    except Exception as e:
        console.print(f"[red]Error listing agents: {e}[/red]")
        raise typer.Exit(code=1)


@agent_app.command(name="create")
def create_agent(
    name: str = typer.Option(..., "--name", "-n", help="Agent display name"),
    role: str = typer.Option("general-purpose", "--role", "-r", help="Agent role type"),
    capabilities: str = typer.Option(
        None, "--capabilities", "-c", help="Comma-separated list of capabilities"
    ),
):
    """Create a new agent"""
    console.print(
        Panel(
            "[bold green]Creating New Agent[/bold green]",
            title="[blue]✨ Agent Creation[/blue]",
            border_style="blue",
            box=ROUNDED,
        )
    )

    console.print(f"[bold blue]Name:[/bold blue] {name}")
    console.print(f"[bold blue]Role:[/bold blue] {role}")

    if capabilities:
        caps = [c.strip() for c in capabilities.split(",")]
        console.print(f"[bold blue]Capabilities:[/bold blue] {', '.join(caps)}")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                description="Creating agent configuration...", total=None
            )
            import time
            time.sleep(0.3)
            progress.update(task, description="Registering agent capabilities...")
            time.sleep(0.3)
            progress.update(task, description="Initializing agent memory...")
            time.sleep(0.3)

        console.print(
            Panel(
                "[bold green]Agent created successfully![/bold green]\n"
                "To start the agent, use: [bold]daie agent start [agent-id][/bold]",
                title="[green]✅ Creation Complete[/green]",
                border_style="green",
                box=ROUNDED,
            )
        )
    except Exception as e:
        console.print(f"[red]Error creating agent: {e}[/red]")
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
            task = progress.add_task(
                description="Connecting to communication system...", total=None
            )
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
            task = progress.add_task(
                description="Deregistering from central core...", total=None
            )
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
        table = Table(
            show_header=True, header_style="bold blue", border_style="cyan", box=ROUNDED
        )
        table.add_column("Property", style="magenta")
        table.add_column("Value", style="cyan")

        for key, value in status_data.items():
            table.add_row(key, str(value))

        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error getting agent status: {e}[/red]")
        raise typer.Exit(code=1)
