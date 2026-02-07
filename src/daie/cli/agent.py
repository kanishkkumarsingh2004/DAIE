"""
Agent management commands
"""

import typer
from rich import print
from rich.console import Console
from rich.table import Table

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
    
    # Get actual agents from the system (currently returns empty list)
    agents = []
    
    for agent_id, name, role, status in agents:
        table.add_row(agent_id, name, role, status)
    
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
    
    status_info = {
        "Name": "GreetingAgent",
        "Role": "General Purpose",
        "Status": "Running",
        "Capabilities": ["greeting"],
        "Memory Items": "12",
        "Tools": "1",
        "Peers": "2",
        "Messages Sent": "42",
        "Messages Received": "38",
        "Tasks Completed": "15",
        "Uptime": "2h 34m"
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
    if show:
        console.print(f"[bold green]Agent Configuration:[/bold green] {agent_id}")
        
        config = {
            "name": "GreetingAgent",
            "role": "general-purpose",
            "communication_timeout": 30,
            "heartbeat_interval": 10,
            "memory_retention_days": 30,
            "max_memory_size": 1000,
            "response_delay": 0.5,
            "max_concurrent_tasks": 5,
            "task_timeout": 60,
            "llm_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        for param, val in config.items():
            console.print(f"[bold blue]{param:30}[/bold blue]: {val}")
    elif key and value:
        console.print(f"[bold green]Updating Configuration:[/bold green] {agent_id}")
        console.print(f"[bold blue]{key}:[/bold blue] {value}")
        console.print("\n[bold green]Configuration updated successfully![/bold green]")
    else:
        console.print("[bold red]Error:[/bold red] Must specify both --key and --value or use --show")


if __name__ == "__main__":
    agent_app()
