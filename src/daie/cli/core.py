"""
Central core system commands
Replaces typer and rich dependencies
"""

import argparse
import os
import signal
import time
from pathlib import Path

from daie.config import SystemConfig
from daie.core.server import start_server
from daie.core.system import DecentralizedAISystem
from daie.utils.console import print_error, print_info, print_success, print_header

# Optional daemon support
try:
    import daemon
    from daemon.pidfile import PIDLockFile

    DAEMON_AVAILABLE = True
except ImportError:
    DAEMON_AVAILABLE = False


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
            try:
                os.kill(pid, 0)
                return pid
            except (OSError, ProcessLookupError):
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


def start_core(args: argparse.Namespace):
    """Start the central core system"""
    # Check if system is already running
    pid = read_pid()
    if pid:
        print_error(f"Central core system is already running (PID: {pid})")
        exit(1)

    print_header("🚀 System Startup - Starting Central Core System")

    if args.background:
        print_info("Running in daemon mode (will persist after terminal closes)")

    if args.debug:
        print_info("Debug mode enabled")

    try:
        if args.background:
            if not DAEMON_AVAILABLE:
                print_error(
                    "Daemon mode requires 'python-daemon' package. Install it with: pip install python-daemon"
                )
                exit(1)

            pid_file = get_pid_file()
            print_info("Initializing system components...")

            with daemon.DaemonContext(
                working_directory=Path.cwd(),
                pidfile=PIDLockFile(str(pid_file)),
                stdout=open("/dev/null", "w"),
                stderr=open("/dev/null", "w"),
                detach_process=True,
            ):
                config = SystemConfig()
                DecentralizedAISystem(config=config)
                start_server("0.0.0.0", args.port, args.debug)

            # Wait for PID file verification
            max_wait = 5
            wait_time = 0.0
            while wait_time < max_wait:
                pid = read_pid()
                if pid:
                    break
                time.sleep(0.5)
                wait_time += 0.5

            if pid:
                print_success(f"Central core system started successfully! PID: {pid}")
                print_info(f"API server running at: http://localhost:{args.port}")
            else:
                print_info("Warning: Could not verify system startup")
        else:
            print_info("Initializing system components...")
            config = SystemConfig()
            DecentralizedAISystem(config=config)
            print_success(
                f"Central core system started successfully! API: http://localhost:{args.port}"
            )
            print_info("Press Ctrl+C to stop the server")
            start_server("0.0.0.0", args.port, args.debug)

    except KeyboardInterrupt:
        print_info("System startup interrupted")
        exit(0)
    except Exception as e:
        print_error(f"Failed to start central core system: {e}")
        exit(1)


def stop_core(args: argparse.Namespace):
    """Stop the central core system"""
    pid = read_pid()
    if not pid:
        print_info("Warning: Central core system is not running")
        exit(0)

    print_header("⏹️ System Shutdown - Stopping Central Core System")

    if args.force:
        print_info("Force stopping...")

    try:
        import platform
        import subprocess

        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/PID", str(pid)], capture_output=True, timeout=5)
        else:
            os.kill(pid, signal.SIGTERM)

        print_info("Initiating shutdown...")

        max_wait = 10
        wait_time = 0.0
        while wait_time < max_wait:
            try:
                os.kill(pid, 0)
            except (OSError, ProcessLookupError):
                break
            time.sleep(0.5)
            wait_time += 0.5

        try:
            os.kill(pid, 0)
            if args.force:
                print_info("Process did not terminate, force killing...")
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=5
                    )
                else:
                    os.kill(pid, signal.SIGKILL)
                time.sleep(1)
        except (OSError, ProcessLookupError):
            pass

        remove_pid_file()
        print_success("Central core system stopped successfully")

    except Exception as e:
        print_error(f"Error stopping system: {e}")
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError):
            remove_pid_file()
        exit(1)


def core_status(args: argparse.Namespace):
    """Check the status of the central core system"""
    pid = read_pid()
    if pid:
        print_header("🟢 Central Core System Status")
        print_success(f"System is running (PID: {pid})")
        print_info("API: http://localhost:3333")
    else:
        print_header("🔴 Central Core System Status")
        print_info("System is not running")


def restart_core(args: argparse.Namespace):
    """Restart the central core system"""
    print_header("🔄 System Restart - Restarting Central Core System")
    pid = read_pid()
    if pid:
        print_info("Stopping current instance...")
        stop_core(args)

    print_info("Starting new instance...")
    start_core(args)


def init_core(args: argparse.Namespace):
    """Initialize the system configuration"""
    print_header("⚙️ System Initialization - Initializing Decentralized AI Ecosystem")

    config_dir = Path.home() / ".daie"
    config_file = config_dir / "config.yaml"

    if config_dir.exists() and config_file.exists():
        choice = input(
            "Configuration already exists. Do you want to reinitialize? (y/n) [n]: "
        ).lower()
        if choice != "y":
            print_info("Initialization cancelled")
            return

    try:
        config_dir.mkdir(exist_ok=True)
        SystemConfig()
        print_success("System initialization completed successfully")
        print_info(f"Configuration directory: {config_dir}")
    except Exception as e:
        print_error(f"Failed to initialize system: {e}")
        exit(1)


def register_core_commands(subparsers):
    """Register core subcommands with the main parser"""
    core_parser = subparsers.add_parser("core", help="Central core system commands")
    core_subparsers = core_parser.add_subparsers(dest="core_command")

    # Start
    start_parser = core_subparsers.add_parser("start", help="Start the central core system")
    start_parser.add_argument("--background", "-b", action="store_true", help="Run in background")
    start_parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    start_parser.add_argument("--port", "-p", type=int, default=3333, help="Server port")
    start_parser.set_defaults(func=start_core)

    # Stop
    stop_parser = core_subparsers.add_parser("stop", help="Stop the central core system")
    stop_parser.add_argument("--force", "-f", action="store_true", help="Force stop")
    stop_parser.set_defaults(func=stop_core)

    # Status
    status_parser = core_subparsers.add_parser("status", help="Check status")
    status_parser.set_defaults(func=core_status)

    # Restart
    restart_parser = core_subparsers.add_parser("restart", help="Restart system")
    restart_parser.add_argument("--force", "-f", action="store_true", help="Force stop if needed")
    restart_parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    restart_parser.add_argument("--port", "-p", type=int, default=3333, help="Server port")
    restart_parser.set_defaults(func=restart_core, background=True)

    # Init
    init_parser = core_subparsers.add_parser("init", help="Initialize configuration")
    init_parser.set_defaults(func=init_core)
