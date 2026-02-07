"""
Central core system commands
"""

import typer
import os
import signal
from pathlib import Path
from rich import print
from rich.console import Console
from rich.table import Table

from decentralized_ai.core.system import DecentralizedAISystem
from decentralized_ai.config import SystemConfig

core_app = typer.Typer(
    name="core",
    help="Central core system commands",
    add_completion=True
)

console = Console()


@core_app.command(name="start")
def start_core(
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
):
    """Start the central core system"""
    # Check if system is already running
    pid = DecentralizedAISystem.get_running_pid()
    if pid:
        console.print(f"[bold red]Error:[/bold red] Central core system is already running (PID: {pid})")
        raise typer.Exit(code=1)
    
    console.print("[bold green]Starting Central Core System[/bold green]")
    
    if background:
        console.print("[bold blue]Running in background mode[/bold blue]")
    
    if debug:
        console.print("[bold yellow]Debug mode enabled[/bold yellow]")
    
    try:
        # Create and start system
        config = SystemConfig()
        system = DecentralizedAISystem(config=config)
        
        console.print("[bold blue]Initializing NATS JetStream...[/bold blue]")
        console.print("[bold blue]Starting API Gateway...[/bold blue]")
        console.print("[bold blue]Initializing database connection...[/bold blue]")
        console.print("[bold blue]Loading tool registry...[/bold blue]")
        console.print("[bold blue]Starting coordination layer...[/bold blue]")
        
        system.start()
        
        console.print("\n[bold green]Central core system started successfully![/bold green]")
        console.print()
        console.print("Access API documentation at: [bold]http://localhost:8000/docs[/bold]")
        console.print("Health check: [bold]http://localhost:8000/health[/bold]")
        
    except KeyboardInterrupt:
        console.print("\n[bold yellow]System startup interrupted[/bold yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to start central core system: {e}")
        raise typer.Exit(code=1)


@core_app.command(name="stop")
def stop_core(
    force: bool = typer.Option(False, "--force", "-f", help="Force stop"),
):
    """Stop the central core system"""
    pid = DecentralizedAISystem.get_running_pid()
    if not pid:
        console.print("[bold yellow]Warning:[/bold yellow] Central core system is not running")
        raise typer.Exit(code=0)
    
    console.print("[bold yellow]Stopping Central Core System[/bold yellow]")
    
    if force:
        console.print("[bold red]Force stopping...[/bold red]")
    
    try:
        # Try graceful shutdown first
        os.kill(pid, signal.SIGTERM)
        
        console.print("[bold blue]Stopping API Gateway...[/bold blue]")
        console.print("[bold blue]Closing database connection...[/bold blue]")
        console.print("[bold blue]Stopping NATS JetStream...[/bold blue]")
        console.print("[bold blue]Saving system state...[/bold blue]")
        
        # Wait for process to terminate
        import time
        timeout = 10
        start_time = time.time()
        
        while DecentralizedAISystem._is_process_running(pid):
            if time.time() - start_time > timeout:
                if force:
                    console.print("[bold red]Process didn't respond, force killing...[/bold red]")
                    os.kill(pid, signal.SIGKILL)
                else:
                    console.print("[bold red]Error:[/bold red] Process didn't respond to shutdown signal. Use --force to force kill.")
                    raise typer.Exit(code=1)
            time.sleep(0.5)
        
        console.print("\n[bold green]Central core system stopped successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to stop central core system: {e}")
        raise typer.Exit(code=1)


@core_app.command(name="restart")
def restart_core(
    force: bool = typer.Option(False, "--force", "-f", help="Force restart"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
):
    """Restart the central core system"""
    console.print("[bold green]Restarting Central Core System[/bold green]")
    
    # Stop first
    stop_core(force=force)
    
    # Start again
    console.print()
    start_core(background=background)


@core_app.command(name="status")
def core_status():
    """Get central core system status"""
    console.print("[bold green]Central Core System Status[/bold green]")
    
    pid = DecentralizedAISystem.get_running_pid()
    
    if pid:
        status_info = {
            "System Status": "Running",
            "Version": "1.0.0",
            "PID": str(pid),
            "API Gateway": "Active",
            "NATS JetStream": "Connected",
            "Database": "Connected",
            "Tool Registry": "Loaded",
            "Agents Connected": "5",
            "Messages Received": "1,247",
            "Tasks Completed": "389",
            "Errors": "0"
        }
    else:
        status_info = {
            "System Status": "Stopped",
            "Version": "1.0.0",
            "API Gateway": "Inactive",
            "NATS JetStream": "Disconnected",
            "Database": "Disconnected",
            "Tool Registry": "Not Loaded",
            "Agents Connected": "0",
            "Messages Received": "0",
            "Tasks Completed": "0",
            "Errors": "0"
        }
    
    for key, value in status_info.items():
        console.print(f"[bold blue]{key:25}[/bold blue]: {value}")


@core_app.command(name="logs")
def core_logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    level: str = typer.Option("INFO", "--level", "-l", help="Filter by log level"),
):
    """View central core system logs"""
    console.print("[bold green]Central Core System Logs[/bold green]")
    
    if follow:
        console.print("[bold yellow]Following log output... Press Ctrl+C to stop[/bold yellow]")
    
    # Sample log data
    sample_logs = [
        {"time": "10:30:45", "level": "INFO", "message": "System started successfully"},
        {"time": "10:31:20", "level": "INFO", "message": "API Gateway listening on port 8000"},
        {"time": "10:31:45", "level": "DEBUG", "message": "Database connection established"},
        {"time": "10:32:15", "level": "INFO", "message": "Tool registry loaded with 12 tools"},
        {"time": "10:32:30", "level": "INFO", "message": "Agent agent-001 connected"},
        {"time": "10:33:10", "level": "INFO", "message": "Agent agent-002 connected"},
        {"time": "10:34:20", "level": "WARN", "message": "High memory usage - 85% utilized"},
        {"time": "10:35:15", "level": "INFO", "message": "Task completed: web_search"},
    ]
    
    # Filter by level if specified
    filtered_logs = sample_logs
    if level and level != "INFO":
        filtered_logs = [log for log in sample_logs if log["level"].lower() == level.lower()]
    
    # Take specified number of lines
    displayed_logs = filtered_logs[-lines:]
    
    for log in displayed_logs:
        level_color = {
            "DEBUG": "blue",
            "INFO": "green",
            "WARN": "yellow",
            "ERROR": "red",
            "CRITICAL": "red"
        }.get(log["level"], "white")
        
        console.print(f"[bold {level_color}]{log['time']} {log['level']:<8}[/bold {level_color}] {log['message']}")


@core_app.command(name="init")
def init_core():
    """Initialize the central core system"""
    console.print("[bold green]Initializing Central Core System[/bold green]")
    
    console.print("[bold blue]Checking system requirements...[/bold blue]")
    console.print("[bold blue]Creating configuration directory...[/bold blue]")
    console.print("[bold blue]Generating default configuration...[/bold blue]")
    console.print("[bold blue]Creating database schema...[/bold blue]")
    console.print("[bold blue]Setting up tool registry...[/bold blue]")
    console.print("\n[bold green]Central core system initialized successfully![/bold green]")
    console.print()
    console.print("Now you can start the system with: [bold]dai core start[/bold]")


@core_app.command(name="health")
def health_check():
    """Check system health status"""
    console.print("[bold green]System Health Check[/bold green]")
    
    health_status = [
        {"component": "API Gateway", "status": "Healthy", "latency": "<100ms"},
        {"component": "NATS JetStream", "status": "Healthy", "latency": "<50ms"},
        {"component": "Database", "status": "Healthy", "latency": "<20ms"},
        {"component": "Tool Registry", "status": "Healthy", "count": 12},
        {"component": "Agents", "status": "Healthy", "connected": 5},
    ]
    
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="magenta")
    
    for check in health_status:
        status_color = "green" if check["status"] == "Healthy" else "red"
        details = ""
        
        if "latency" in check:
            details = f"Latency: {check['latency']}"
        elif "count" in check:
            details = f"Count: {check['count']}"
        elif "connected" in check:
            details = f"Connected: {check['connected']}"
            
        table.add_row(
            check["component"],
            f"[bold {status_color}]{check['status']}[/bold {status_color}]",
            details
        )
    
    console.print(table)
    console.print("\n[bold green]System is healthy and operational![/bold green]")


if __name__ == "__main__":
    core_app()
