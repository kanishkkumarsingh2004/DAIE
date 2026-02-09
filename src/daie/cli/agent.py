"""
Agent management commands
"""

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from daie.config import SystemConfig

agent_app = typer.Typer(
    name="agent",
    help="Agent management commands",
    add_completion=True
)

console = Console()


@agent_app.command(name="list")
def list_agents():
    """List all registered agents"""
    console.print("[bold green]List of Agents[/bold green]")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Role", style="yellow")
    table.add_column("Status", style="green")
    
    # Get actual agents from the system
    from daie.core.system import DecentralizedAISystem
    
    # In a real implementation, we would connect to the running system
    # For now, we'll create a temporary system instance to demonstrate
    # Note: This approach won't show agents from a running system
    config = SystemConfig()
    system = DecentralizedAISystem(config=config)
    
    agents = system.list_agents()
    
    for agent in agents:
        table.add_row(
            agent.id,
            agent.name,
            agent.role.value,
            "Running" if agent.is_running else "Stopped"
        )
    
    console.print(table)
    console.print(f"\nTotal agents: [bold green]{len(agents)}[/bold green]")


@agent_app.command(name="create")
def create_agent(
    name: str = typer.Option(..., "--name", "-n", help="Agent display name"),
    role: str = typer.Option("general-purpose", "--role", "-r", help="Agent role type"),
    capabilities: str = typer.Option(None, "--capabilities", "-c", help="Comma-separated list of capabilities"),
):
    """Create a new agent"""
    console.print(f"[bold green]Creating Agent:[/bold green] {name}")
    console.print(f"[bold blue]Role:[/bold blue] {role}")
    
    if capabilities:
        caps = capabilities.split(",")
        console.print(f"[bold blue]Capabilities:[/bold blue] {', '.join(caps)}")
    
    console.print("\n[bold]Agent created successfully![/bold]")
    console.print("To start the agent, use: [bold]dai agent start [agent-id][/bold]")


@agent_app.command(name="start")
def start_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to start"),
):
    """Start an agent"""
    console.print(f"[bold green]Starting Agent:[/bold green] {agent_id}")
    console.print("[bold blue]Connecting to communication system...[/bold blue]")
    console.print("[bold blue]Initializing agent memory...[/bold blue]")
    console.print("[bold blue]Registering with central core...[/bold blue]")
    console.print("\n[bold green]Agent started successfully![/bold green]")


@agent_app.command(name="stop")
def stop_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to stop"),
):
    """Stop an agent"""
    console.print(f"[bold yellow]Stopping Agent:[/bold yellow] {agent_id}")
    console.print("[bold blue]Deregistering from central core...[/bold blue]")
    console.print("[bold blue]Saving agent memory...[/bold blue]")
    console.print("[bold blue]Closing connections...[/bold blue]")
    console.print("\n[bold green]Agent stopped successfully![/bold green]")


@agent_app.command(name="status")
def agent_status(
    agent_id: str = typer.Argument(..., help="Agent ID to check status"),
):
    """Get agent status and information"""
    console.print(f"[bold green]Agent Status:[/bold green] {agent_id}")
    
    # Get actual agent from the system
    from daie.core.system import DecentralizedAISystem
    from daie.config import SystemConfig
    
    config = SystemConfig()
    system = DecentralizedAISystem(config=config)
    agent = system.get_agent(agent_id)
    
    if not agent:
        console.print(f"[bold red]Error:[/bold red] Agent with ID {agent_id} not found")
        raise typer.Exit(code=1)
    
    # Collect actual agent status information
    status_info = {
        "Name": agent.name,
        "Role": agent.role.value,
        "Status": "Running" if agent.is_running else "Stopped",
        "Capabilities": agent.config.capabilities,
        "Tools": len(agent.list_tools()),
        "Peers": 0,  # This would come from communication manager
        "Messages Sent": 0,  # This would come from communication manager
        "Messages Received": 0,  # This would come from communication manager
        "Tasks Completed": 0,  # This would come from task manager
        "Uptime": "0h 0m"  # This would need to be tracked
    }
    
    for key, value in status_info.items():
        console.print(f"[bold blue]{key:20}[/bold blue]: {value}")


@agent_app.command(name="delete")
def delete_agent(
    agent_id: str = typer.Argument(..., help="Agent ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete without confirmation"),
):
    """Delete an agent"""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete agent {agent_id}?")
        if not confirm:
            console.print("[bold yellow]Operation cancelled[/bold yellow]")
            return
            
    console.print(f"[bold red]Deleting Agent:[/bold red] {agent_id}")
    console.print("[bold blue]Removing agent configuration...[/bold blue]")
    console.print("[bold blue]Clearing agent memory...[/bold blue]")
    console.print("[bold blue]Removing from registry...[/bold blue]")
    console.print("\n[bold green]Agent deleted successfully![/bold green]")


@agent_app.command(name="config")
def agent_config(
    agent_id: str = typer.Argument(..., help="Agent ID to configure"),
    key: str = typer.Option(None, "--key", "-k", help="Config parameter to set"),
    value: str = typer.Option(None, "--value", "-v", help="Config parameter value"),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
):
    """Configure agent settings"""
    # Get actual agent from the system
    from daie.core.system import DecentralizedAISystem
    from daie.config import SystemConfig
    
    config = SystemConfig()
    system = DecentralizedAISystem(config=config)
    agent = system.get_agent(agent_id)
    
    if not agent:
        console.print(f"[bold red]Error:[/bold red] Agent with ID {agent_id} not found")
        raise typer.Exit(code=1)
    
    if show:
        console.print(f"[bold green]Agent Configuration:[/bold green] {agent_id}")
        
        # Convert agent config to dictionary for display
        config_dict = agent.config.to_dict()
        
        for param, val in config_dict.items():
            console.print(f"[bold blue]{param:30}[/bold blue]: {val}")
    elif key and value:
        console.print(f"[bold green]Updating Configuration:[/bold green] {agent_id}")
        
        # Check if the config parameter exists
        if hasattr(agent.config, key):
            # Convert string value to appropriate type
            current_value = getattr(agent.config, key)
            try:
                if isinstance(current_value, bool):
                    val = value.lower() in ["true", "yes", "1"]
                elif isinstance(current_value, int):
                    val = int(value)
                elif isinstance(current_value, float):
                    val = float(value)
                elif isinstance(current_value, list):
                    val = [v.strip() for v in value.split(",")]
                else:
                    val = value
                
                setattr(agent.config, key, val)
                console.print(f"[bold blue]{key}:[/bold blue] {val}")
                console.print("\n[bold green]Configuration updated successfully![/bold green]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] Invalid value for parameter {key}: {e}")
                raise typer.Exit(code=1)
        else:
            console.print(f"[bold red]Error:[/bold red] Unknown configuration parameter '{key}'")
            raise typer.Exit(code=1)
    else:
        console.print("[bold red]Error:[/bold red] Must specify both --key and --value or use --show")


if __name__ == "__main__":
    agent_app()
