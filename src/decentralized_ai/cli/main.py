"""
Main CLI entry point for decentralized AI library
"""

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from decentralized_ai.cli.agent import agent_app
from decentralized_ai.cli.core import core_app

cli = typer.Typer(
    name="dai",
    help="Decentralized AI Ecosystem CLI",
    add_completion=True
)

cli.add_typer(agent_app, name="agent", help="Agent management commands")
cli.add_typer(core_app, name="core", help="Central core system commands")

console = Console()


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version information")
):
    """Decentralized AI Ecosystem CLI"""
    if ctx.invoked_subcommand is None:
        if version:
            from decentralized_ai import __version__
            console.print(f"Decentralized AI Library version: {__version__}")
            console.print("\nLearn more at: https://github.com/decentralized-ai/decentralized_ai_ecosystem")
        else:
            show_help(ctx)


def show_help(ctx: typer.Context):
    """Show help information"""
    console.print("[bold green]Decentralized AI Ecosystem CLI[/bold green]")
    console.print()
    console.print("A command-line interface for managing the Decentralized AI Ecosystem")
    console.print()
    
    # Create commands table
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="magenta")
    
    # Core commands
    core_commands = [
        ("dai agent", "Manage AI agents"),
        ("dai core", "Manage central core system"),
    ]
    
    for cmd, desc in core_commands:
        table.add_row(cmd, desc)
    
    console.print(table)
    console.print()
    console.print("Use [bold]dai [command] --help[/bold] for more information about a specific command")
    console.print()
    
    # Quick start examples
    console.print("[bold]Quick Start:[/bold]")
    console.print("1. Initialize the system: [bold]dai core init[/bold]")
    console.print("2. Create an agent: [bold]dai agent create[/bold]")
    console.print("3. Start the system: [bold]dai core start[/bold]")
    console.print("4. Start agents: [bold]dai agent start[/bold]")
    console.print()
    
    # Example with tool
    console.print("[bold]Example - Create and Run a Simple Agent:[/bold]")
    console.print("Create a file named [bold]simple_agent.py[/bold]:")
    console.print("""
from decentralized_ai import Agent, Tool
from decentralized_ai.tools import tool
from decentralized_ai.agents import AgentConfig, AgentRole

@tool(
    name="greeting",
    description="Generate a greeting message",
    category="general",
    version="1.0.0"
)
async def greeting_tool(name: str) -> str:
    return f"Hello, {name}! Welcome to the Decentralized AI Ecosystem!"

# Create agent configuration
config = AgentConfig(
    name="GreetingAgent",
    role=AgentRole.GENERAL_PURPOSE,
    capabilities=["greeting"]
)

# Create and configure agent
agent = Agent(config=config)
agent.add_tool(greeting_tool)

# Start the agent
agent.start()
""")
    console.print()
    console.print("Run with: [bold]python simple_agent.py[/bold]")


if __name__ == "__main__":
    cli()
