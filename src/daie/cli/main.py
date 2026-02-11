"""
Main CLI entry point for decentralized AI library
"""

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.columns import Columns
from rich.box import ROUNDED, SIMPLE

from daie.cli.agent import agent_app
from daie.cli.core import core_app

cli = typer.Typer(
    name="daie", help="Decentralized AI Ecosystem CLI", add_completion=True
)

cli.add_typer(agent_app, name="agent", help="Agent management commands")
cli.add_typer(core_app, name="core", help="Central core system commands")

console = Console()


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version information"
    ),
):
    """Decentralized AI Ecosystem CLI"""
    if ctx.invoked_subcommand is None:
        if version:
            from daie import __version__

            console.print(
                Panel(
                    f"[bold green]Decentralized AI Library[/bold green]\n"
                    f"[bold blue]Version:[/bold blue] {__version__}\n"
                    f"[bold blue]Repository:[/bold blue] https://github.com/decentralized-ai/daie_ecosystem",
                    title="[blue]📦 Library Information[/blue]",
                    border_style="blue",
                    box=ROUNDED,
                )
            )
        else:
            show_help(ctx)


def show_help(ctx: typer.Context):
    """Show help information with premium styling"""
    # ASCII Art Logo
    logo = """
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║    ██████╗ ███████╗███████╗████████╗██████╗  ██████╗  ██████╗              ║
║    ██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗██╔═══██╗             ║
║    ██████╔╝█████╗  ███████╗   ██║   ██████╔╝██║   ██║██║   ██║             ║
║    ██╔═══╝ ██╔══╝  ╚════██║   ██║   ██╔══██╗██║   ██║██║   ██║             ║
║    ██║     ███████╗███████║   ██║   ██║  ██║╚██████╔╝╚██████╔╝             ║
║    ╚═╝     ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝              ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """

    console.print(
        Panel(
            logo,
            title="[bold blue]DAIE[/bold blue]",
            border_style="blue",
            box=ROUNDED,
        )
    )

    console.print()

    # Description
    console.print(
        Panel(
            "A command-line interface for managing the Decentralized AI Ecosystem",
            border_style="cyan",
            box=SIMPLE,
        )
    )

    console.print()

    # Create commands table with premium styling
    table = Table(
        show_header=True, header_style="bold blue", border_style="cyan", box=ROUNDED
    )
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="magenta")

    # Core commands
    core_commands = [
        ("daie agent", "Manage AI agents"),
        ("daie core", "Manage central core system"),
    ]

    for cmd, desc in core_commands:
        table.add_row(cmd, desc)

    console.print(table)
    console.print()

    # Quick start examples with premium formatting
    console.print(
        Panel(
            "[bold]Quick Start Guide:[/bold]\n"
            "1. Initialize the system: [bold]daie core init[/bold]\n"
            "2. Create an agent: [bold]daie agent create[/bold]\n"
            "3. Start the system: [bold]daie core start --background[/bold]\n"
            "4. Check system status: [bold]daie core status[/bold]\n"
            "5. Start agents: [bold]daie agent start[/bold]",
            title="[blue]🚀 Getting Started[/blue]",
            border_style="blue",
            box=ROUNDED,
        )
    )

    console.print()

    # Example with tool
    console.print(
        Panel(
            "[bold]Example - Create and Run a Simple Agent:[/bold]\n"
            "Create a file named [bold]simple_agent.py[/bold]:\n\n"
            "[bold cyan]from daie import Agent, Tool\n"
            "from daie.tools import tool\n"
            "from daie.agents import AgentConfig, AgentRole\n\n"
            "@tool(\n"
            '    name="greeting",\n'
            '    description="Generate a greeting message",\n'
            '    category="general",\n'
            '    version="1.0.0"\n'
            ")\n"
            "async def greeting_tool(name: str) -> str:\n"
            '    return f"Hello, {name}! Welcome to the Decentralized AI Ecosystem!"\n\n'
            "# Create agent configuration\n"
            "config = AgentConfig(\n"
            '    name="GreetingAgent",\n'
            "    role=AgentRole.GENERAL_PURPOSE,\n"
            '    capabilities=["greeting"]\n'
            ")\n\n"
            "# Create and configure agent\n"
            "agent = Agent(config=config)\n"
            "agent.add_tool(greeting_tool)",
            title="[green]💡 Agent Example[/green]",
            border_style="green",
            box=ROUNDED,
        )
    )

    console.print()
    console.print(
        "Use [bold]daie [command] --help[/bold] for more information about a specific command"
    )
