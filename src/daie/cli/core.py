"""
Central core system commands
"""

import typer
import os
import signal
import time
import daemon
from daemon.pidfile import PIDLockFile
            
from pathlib import Path
from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from daie.core.system import DecentralizedAISystem
from daie.config import SystemConfig
from daie.core.server import start_server

core_app = typer.Typer(
    name="core",
    help="Central core system commands",
    add_completion=True
)

console = Console()


def get_pid_file():
    """Get the path to the PID file"""
    config_dir = Path.home() / ".daie"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "core.pid"


def read_pid():
    """Read PID from file"""
    pid_file = get_pid_file()
    if pid_file.exists():
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            # Check if process is actually running
            if os.path.exists(f"/proc/{pid}"):
                return pid
            else:
                # PID file exists but process doesn't, clean it up
                pid_file.unlink()
        except Exception:
            pass
    return None


def write_pid(pid):
    """Write PID to file"""
    pid_file = get_pid_file()
    with open(pid_file, "w") as f:
        f.write(str(pid))


def remove_pid_file():
    """Remove PID file"""
    pid_file = get_pid_file()
    if pid_file.exists():
        pid_file.unlink()


@core_app.command(name="start")
def start_core(
    background: bool = typer.Option(False, "--background", "-b", help="Run in background (daemon mode)"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
    port: int = typer.Option(3333, "--port", "-p", help="Server port"),
):
    """Start the central core system"""
    # Check if system is already running
    pid = read_pid()
    if pid:
        console.print(
            Panel(
                f"[bold red]Error:[/bold red] Central core system is already running (PID: {pid})",
                title="[red]❌ System Error[/red]",
                border_style="red"
            )
        )
        raise typer.Exit(code=1)
    
    console.print(
        Panel(
            "[bold green]Starting Central Core System[/bold green]",
            title="[green]🚀 System Startup[/green]",
            border_style="green"
        )
    )
    
    if background:
        console.print("[bold blue]Running in daemon mode (will persist after terminal closes)[/bold blue]")
    
    if debug:
        console.print("[bold yellow]Debug mode enabled[/bold yellow]")
    
    try:
        if background:
            # Run as daemon using python-daemon
            
            pid_file = get_pid_file()
            
            # Show progress while initializing
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Initializing system components...", total=None)
                with daemon.DaemonContext(
                    working_directory=Path.cwd(),
                    pidfile=PIDLockFile(str(pid_file)),
                    stdout=open("/dev/null", "w"),
                    stderr=open("/dev/null", "w"),
                    detach_process=True
                ):
                    # Create and start system with web server
                    config = SystemConfig()
                    system = DecentralizedAISystem(config=config)
                    start_server("0.0.0.0", port, debug)
            
            # Wait for PID file to be created
            max_wait = 5
            wait_time = 0
            while wait_time < max_wait:
                pid = read_pid()
                if pid:
                    break
                time.sleep(0.5)
                wait_time += 0.5
            
            if pid:
                console.print(
                    Panel(
                        f"[bold green]Central core system started successfully![/bold green]\n"
                        f"[bold blue]PID:[/bold blue] {pid}\n"
                        f"[bold blue]API server running at:[/bold blue] http://localhost:{port}\n"
                        f"[bold blue]API documentation:[/bold blue] http://localhost:{port}/docs",
                        title="[green]✅ Startup Complete[/green]",
                        border_style="green"
                    )
                )
            else:
                console.print(
                    Panel(
                        "[bold yellow]Warning:[/yellow] Could not verify system startup",
                        title="[yellow]⚠️  Warning[/yellow]",
                        border_style="yellow"
                    )
                )
        else:
            # Run in foreground
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Initializing system components...", total=None)
                config = SystemConfig()
                system = DecentralizedAISystem(config=config)
            
            console.print(
                Panel(
                    f"[bold green]Central core system started successfully![/green]\n"
                    f"[bold blue]API server running at:[/blue] http://localhost:{port}\n"
                    f"[bold blue]API documentation:[/blue] http://localhost:{port}/docs\n"
                    f"[bold yellow]Press Ctrl+C to stop the server[/yellow]",
                    title="[green]✅ Startup Complete[/green]",
                    border_style="green"
                )
            )
            start_server("0.0.0.0", port, debug)
            
    except KeyboardInterrupt:
        console.print(
            Panel(
                "[bold yellow]System startup interrupted[/yellow]",
                title="[yellow]⚠️  Interrupted[/yellow]",
                border_style="yellow"
            )
        )
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(
            Panel(
                f"[bold red]Error:[/red] Failed to start central core system: {e}",
                title="[red]❌ Startup Failed[/red]",
                border_style="red"
            )
        )
        raise typer.Exit(code=1)


@core_app.command(name="stop")
def stop_core(
    force: bool = typer.Option(False, "--force", "-f", help="Force stop"),
):
    """Stop the central core system"""
    pid = read_pid()
    if not pid:
        console.print(
            Panel(
                "[bold yellow]Warning:[/yellow] Central core system is not running",
                title="[yellow]⚠️  Warning[/yellow]",
                border_style="yellow"
            )
        )
        raise typer.Exit(code=0)
    
    console.print(
        Panel(
            "[bold yellow]Stopping Central Core System[/yellow]",
            title="[yellow]⏹️  System Shutdown[/yellow]",
            border_style="yellow"
        )
    )
    
    if force:
        console.print("[bold red]Force stopping...[/red]")
    
    try:
        # Try graceful shutdown first
        os.kill(pid, signal.SIGTERM)
        
        console.print("[bold blue]Initiating shutdown...[/blue]")
        
        # Wait for process to terminate
        import time
        max_wait = 10
        wait_time = 0
        while wait_time < max_wait:
            if not os.path.exists(f"/proc/{pid}"):
                break
            time.sleep(0.5)
            wait_time += 0.5
        
        if os.path.exists(f"/proc/{pid}") and force:
            console.print("[bold red]Process did not terminate, force killing...[/red]")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        
        if not os.path.exists(f"/proc/{pid}"):
            remove_pid_file()
            console.print(
                Panel(
                    "[bold green]Central core system stopped successfully[/green]",
                    title="[green]✅ Shutdown Complete[/green]",
                    border_style="green"
                )
            )
        else:
            console.print(
                Panel(
                    "[bold red]Error:[/red] Failed to stop central core system",
                    title="[red]❌ Shutdown Failed[/red]",
                    border_style="red"
                )
            )
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(
            Panel(
                f"[bold red]Error:[/red] {e}",
                title="[red]❌ Shutdown Error[/red]",
                border_style="red"
            )
        )
        # Clean up PID file if process doesn't exist
        if not os.path.exists(f"/proc/{pid}"):
            remove_pid_file()
        raise typer.Exit(code=1)


@core_app.command(name="status")
def core_status():
    """Check the status of the central core system"""
    pid = read_pid()
    
    if pid:
        console.print(
            Panel(
                f"[bold green]Central core system is running[/green]\n"
                f"[bold blue]PID:[/blue] {pid}\n"
                f"[bold blue]Port:[/blue] 3333\n"
                f"[bold blue]API:[/blue] http://localhost:3333\n"
                f"[bold blue]Docs:[/blue] http://localhost:3333/docs",
                title="[green]🟢 System Status[/green]",
                border_style="green"
            )
        )
    else:
        console.print(
            Panel(
                "[bold yellow]Central core system is not running[/bold yellow]",
                title="[yellow]🔴 System Status[/yellow]",
                border_style="yellow"
            )
        )
    raise typer.Exit(code=0 if pid else 1)


@core_app.command(name="restart")
def restart_core(
    force: bool = typer.Option(False, "--force", "-f", help="Force stop if needed"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
    port: int = typer.Option(3333, "--port", "-p", help="Server port"),
):
    """Restart the central core system"""
    console.print(
        Panel(
            "[bold blue]Restarting Central Core System[/blue]",
            title="[blue]🔄 System Restart[/blue]",
            border_style="blue"
        )
    )
    
    # Stop if running
    pid = read_pid()
    if pid:
        console.print("[bold yellow]Stopping current instance...[/yellow]")
        try:
            stop_core(force)
        except Exception as e:
            console.print(
                Panel(
                    f"[bold red]Error stopping system:[/red] {e}",
                    title="[red]❌ Stop Error[/red]",
                    border_style="red"
                )
            )
            raise typer.Exit(code=1)
    
    # Start again
    console.print("[bold green]Starting new instance...[/green]")
    start_core(background=True, debug=debug, port=port)


@core_app.command(name="init")
def init_core():
    """Initialize the system configuration"""
    console.print(
        Panel(
            "[bold blue]Initializing Decentralized AI Ecosystem[/blue]",
            title="[blue]⚙️  System Initialization[/blue]",
            border_style="blue"
        )
    )
    
    config_dir = Path.home() / ".daie"
    config_file = config_dir / "config.yaml"
    
    if config_dir.exists() and config_file.exists():
        if not Confirm.ask("Configuration already exists. Do you want to reinitialize?"):
            console.print("[bold yellow]Initialization cancelled[/yellow]")
            raise typer.Exit(code=0)
    
    try:
        config_dir.mkdir(exist_ok=True)
        
        # Create default configuration
        config = SystemConfig()
        
        console.print(
            Panel(
                "[bold green]System initialization completed successfully[/green]\n"
                f"[bold blue]Configuration directory:[/blue] {config_dir}",
                title="[green]✅ Initialization Complete[/green]",
                border_style="green"
            )
        )
    except Exception as e:
        console.print(
            Panel(
                f"[bold red]Error:[/red] Failed to initialize system: {e}",
                title="[red]❌ Initialization Failed[/red]",
                border_style="red"
            )
        )
        raise typer.Exit(code=1)
