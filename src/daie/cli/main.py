"""
Main CLI entry point for decentralized AI library
Replaces typer and rich dependencies
"""

import argparse
from daie.cli.agent import register_agent_commands
from daie.cli.benchmark import register_benchmark_commands
from daie.cli.core import register_core_commands
from daie.utils.console import print_header, print_info


def show_help():
    """Show help information with premium styling"""
    logo = r"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        WELCOME TO DAIE                                     ║
╚════════════════════════════════════════════════════════════════════════════╝
    """
    print_header("DAIE - Decentralized AI Ecosystem CLI")
    print(logo)
    print_info("A command-line interface for managing the Decentralized AI Ecosystem")
    print("\nAvailable Commands:")
    print("  daie agent      - Manage AI agents")
    print("  daie core       - Manage central core system")
    print("  daie benchmark  - Run swarm performance benchmarks")
    print("\nQuick Start Guide:")
    print("  1. Initialize the system: daie core init")
    print("  2. Create an agent:       daie agent create")
    print("  3. Start the system:      daie core start --background")
    print("  4. Check status:          daie core status")
    print("\nUse 'daie [command] --help' for more information about a specific command")


def cli():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="daie", description="Decentralized AI Ecosystem CLI", add_help=False
    )
    parser.add_argument("--version", "-v", action="store_true", help="Show version information")
    parser.add_argument("--help", "-h", action="store_true", help="Show help information")

    subparsers = parser.add_subparsers(dest="command")

    # Register subcommands
    register_agent_commands(subparsers)
    register_core_commands(subparsers)
    register_benchmark_commands(subparsers)

    args = parser.parse_args()

    if args.version:
        from daie import __version__

        print_header(f"Decentralized AI Library - Version: {__version__}")
        print("Repository: https://github.com/decentralized-ai/daie_ecosystem")
        return

    if args.help or not args.command:
        show_help()
        return

    # Execute the command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
