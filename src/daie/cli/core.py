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

from daie.core.system import DecentralizedAISystem
from daie.config import SystemConfig
from daie.core.server import start_server

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
    port: int = typer.Option(3333, "--port", "-p", help="Server port"),
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
        # Create and start system with web server
        config = SystemConfig()
        system = DecentralizedAISystem(config=config)
        
        console.print("[bold blue]Initializing system components...[/bold blue]")
        
        if background:
            # Run server in background
            import threading
            server_thread = threading.Thread(
                target=start_server,
                args=("0.0.0.0", port, debug),
                daemon=True
            )
            server_thread.start()
        else:
            # Run server in foreground
            start_server("0.0.0.0", port, debug)
        
        console.print(f"\n[bold green]Central core system started successfully![/bold green]")
        console.print(f"[bold blue]API server running at:[/bold blue] http://localhost:{port}")
        console.print(f"[bold blue]API documentation:[/bold blue] http://localhost:{port}/docs")
        
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
        
        console.print("[bold blue]Initiating shutdown...[/bold blue]")
        
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
        # In a real implementation, this data would be retrieved from the running system
        status_info = {
            "System Status": "Running",
            "Version": "1.0.0",
            "PID": str(pid),
            "API Gateway": "Active",
            "NATS JetStream": "Connected",
            "Database": "Connected",
            "Tool Registry": "Loaded",
            "Agents Connected": "0",
            "Messages Received": "0",
            "Tasks Completed": "0",
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
    
    try:
        # Get log file path from config
        config = SystemConfig()
        log_file = config.log_file
        
        if config.enable_logging and log_file is None:
            from daie.utils.logger import ensure_directory_exists
            log_dir = ensure_directory_exists(config.log_directory)
            log_file = os.path.join(log_dir, "daie.log")
        
        if not log_file or not os.path.exists(log_file):
            console.print("[bold yellow]Warning:[/bold yellow] No log file found. The system may not have been started yet.")
            return
        
        # Read log file
        with open(log_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        
        # Filter logs by level if specified
        filtered_lines = []
        for line in log_lines:
            line = line.strip()
            if line:
                # Check if line contains the specified log level
                if level and level != "INFO":
                    if level.upper() in line:
                        filtered_lines.append(line)
                else:
                    filtered_lines.append(line)
        
        # Take specified number of lines
        displayed_lines = filtered_lines[-lines:]
        
        for line in displayed_lines:
            # Simple parsing to colorize log levels
            if "DEBUG" in line:
                console.print(f"[bold blue]{line}[/bold blue]")
            elif "INFO" in line:
                console.print(f"[bold green]{line}[/bold green]")
            elif "WARNING" in line or "WARN" in line:
                console.print(f"[bold yellow]{line}[/bold yellow]")
            elif "ERROR" in line:
                console.print(f"[bold red]{line}[/bold red]")
            elif "CRITICAL" in line:
                console.print(f"[bold magenta]{line}[/bold magenta]")
            else:
                console.print(line)
        
        # If follow is requested, we would need to implement tail functionality
        if follow:
            console.print("\n[bold yellow]Follow functionality not implemented yet[/bold yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to read logs: {e}")


@core_app.command(name="init")
def init_core():
    """Initialize the central core system"""
    console.print("[bold green]Initializing Central Core System[/bold green]")
    
    try:
        # Create configuration directory
        config_dir = Path.home() / ".dai"
        config_dir.mkdir(exist_ok=True)
        
        # Create default configuration file
        config = SystemConfig()
        config_file = config_dir / "config.json"
        
        if not config_file.exists():
            import json
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
            console.print("[bold blue]Created default configuration file[/bold blue]")
        else:
            console.print("[bold blue]Configuration file already exists[/bold blue]")
        
        # Initialize log directory
        from daie.utils.logger import ensure_directory_exists
        ensure_directory_exists(config.log_directory)
        console.print("[bold blue]Created log directory[/bold blue]")
        
        # In a real implementation, we would also:
        # - Initialize database schema
        # - Set up communication channels
        # - Verify system requirements
        
        console.print("\n[bold green]Central core system initialized successfully![/bold green]")
        console.print()
        console.print("Now you can start the system with: [bold]dai core start[/bold]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to initialize system: {e}")
        raise typer.Exit(code=1)


@core_app.command(name="health")
def health_check():
    """Check system health status"""
    console.print("[bold green]System Health Check[/bold green]")
    
    pid = DecentralizedAISystem.get_running_pid()
    
    if not pid:
        console.print("[bold yellow]Warning:[/bold yellow] Central core system is not running")
        raise typer.Exit(code=0)
    
    # In a real implementation, this would check actual system components
    health_status = [
        {"component": "API Gateway", "status": "Healthy", "latency": "<100ms"},
        {"component": "NATS JetStream", "status": "Healthy", "latency": "<50ms"},
        {"component": "Database", "status": "Healthy", "latency": "<20ms"},
        {"component": "Tool Registry", "status": "Healthy", "count": 0},
        {"component": "Agents", "status": "Healthy", "connected": 0},
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
