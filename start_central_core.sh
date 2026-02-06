#!/bin/bash

# Central Core System Startup Script
# This script launches the Decentralized AI Ecosystem's central core server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CENTRAL_CORE_DIR="$PROJECT_DIR/central_core_system"
VENV_DIR="$CENTRAL_CORE_DIR/venv"
LOG_FILE="$PROJECT_DIR/central_core.log"
PID_FILE="$PROJECT_DIR/central_core.pid"

# Function to print messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# Function to check if process is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0 # Running
        else
            rm -f "$PID_FILE"
            return 1 # Not running
        fi
    fi
    return 1 # No PID file
}

# Function to start central core
start_central_core() {
    print_message "$BLUE" "Starting Decentralized AI Central Core System..."

    # Check if already running
    if is_running; then
        print_message "$YELLOW" "Central core is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_message "$YELLOW" "Virtual environment not found. Creating..."
        if ! python3 -m venv "$VENV_DIR"; then
            print_message "$RED" "Failed to create virtual environment"
            return 1
        fi
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Install/update dependencies
    print_message "$BLUE" "Checking dependencies..."
    if ! pip install -q -r "$CENTRAL_CORE_DIR/requirements.txt"; then
        print_message "$RED" "Failed to install dependencies"
        deactivate
        return 1
    fi

    # Check and create log directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Start central core server
    print_message "$BLUE" "Launching central core server..."
    if [ -f "$CENTRAL_CORE_DIR/api_gateway/main.py" ]; then
        # Use Uvicorn ASGI server
        uvicorn central_core_system.api_gateway.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 4 \
            --log-level info \
            --access-log \
            > "$LOG_FILE" 2>&1 &
        
        local PID=$!
        if [ $? -eq 0 ]; then
            echo "$PID" > "$PID_FILE"
            print_message "$GREEN" "Central core server started successfully!"
            print_message "$GREEN" "PID: $PID"
            print_message "$GREEN" "Log file: $LOG_FILE"
            print_message "$GREEN" "API: http://localhost:8000"
            print_message "$GREEN" "Documentation: http://localhost:8000/docs"
        else
            print_message "$RED" "Failed to start central core server"
            deactivate
            return 1
        fi
    else
        print_message "$RED" "Main application file not found: $CENTRAL_CORE_DIR/api_gateway/main.py"
        deactivate
        return 1
    fi

    # Deactivate virtual environment
    deactivate
    return 0
}

# Function to stop central core
stop_central_core() {
    print_message "$BLUE" "Stopping Decentralized AI Central Core System..."

    if ! is_running; then
        print_message "$YELLOW" "Central core is not running"
        return 1
    fi

    local PID=$(cat "$PID_FILE")
    print_message "$BLUE" "Terminating process $PID..."
    
    # First try graceful shutdown
    kill -TERM "$PID"
    sleep 5
    
    # If still running, force kill
    if ps -p "$PID" > /dev/null 2>&1; then
        print_message "$YELLOW" "Process still running, forcing termination..."
        kill -KILL "$PID"
        sleep 2
    fi
    
    # Cleanup
    rm -f "$PID_FILE"
    print_message "$GREEN" "Central core server stopped successfully"
    return 0
}

# Function to restart central core
restart_central_core() {
    stop_central_core
    sleep 2
    start_central_core
    return $?
}

# Function to view status
view_status() {
    if is_running; then
        print_message "$GREEN" "Central core server is RUNNING"
        print_message "$BLUE" "PID: $(cat "$PID_FILE")"
        print_message "$BLUE" "Log file: $LOG_FILE"
        print_message "$BLUE" "API: http://localhost:8000"
        
        # Check if port is accessible
        if nc -z localhost 8000 > /dev/null 2>&1; then
            print_message "$GREEN" "Port 8000 is listening"
        else
            print_message "$YELLOW" "Port 8000 is not accessible"
        fi
    else
        print_message "$RED" "Central core server is NOT running"
    fi
}

# Function to view logs
view_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_message "$YELLOW" "Log file not found: $LOG_FILE"
        return 1
    fi
    
    if [ "$1" == "tail" ]; then
        print_message "$BLUE" "Tailing central core logs (press Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        print_message "$BLUE" "Displaying central core logs:"
        cat "$LOG_FILE"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_message "$BLUE" "Checking system dependencies..."
    
    local missing_deps=()
    
    # Check Python
    if ! command -v python3 > /dev/null 2>&1; then
        missing_deps+=("python3")
    elif [ "$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1)" -lt 3 ] || [ "$(python3 --version | cut -d' ' -f2 | cut -d'.' -f2)" -lt 11 ]; then
        print_message "$YELLOW" "Warning: Python version should be 3.11+ (found $(python3 --version))"
    fi
    
    # Check pip
    if ! command -v pip3 > /dev/null 2>&1; then
        missing_deps+=("pip3")
    fi
    
    # Check nc (netcat) for port testing
    if ! command -v nc > /dev/null 2>&1; then
        missing_deps+=("nc")
    fi
    
    # Check required directories
    if [ ! -d "$CENTRAL_CORE_DIR" ]; then
        print_message "$RED" "Central core directory not found: $CENTRAL_CORE_DIR"
        return 1
    fi
    
    if [ ! -f "$CENTRAL_CORE_DIR/requirements.txt" ]; then
        print_message "$RED" "Requirements file not found: $CENTRAL_CORE_DIR/requirements.txt"
        return 1
    fi
    
    if [ ! -f "$CENTRAL_CORE_DIR/api_gateway/main.py" ]; then
        print_message "$RED" "Main application file not found: $CENTRAL_CORE_DIR/api_gateway/main.py"
        return 1
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_message "$RED" "Missing dependencies: ${missing_deps[*]}"
        print_message "$YELLOW" "Please install them using your system package manager"
        return 1
    fi
    
    print_message "$GREEN" "All dependencies check passed"
    return 0
}

# Function to display help
display_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|tail|check}"
    echo ""
    echo "Commands:"
    echo "  start    Start central core server"
    echo "  stop     Stop central core server"
    echo "  restart  Restart central core server"
    echo "  status   Show current status"
    echo "  logs     Display log file"
    echo "  tail     Tail log file (follow)"
    echo "  check    Check system dependencies"
    echo ""
    echo "Example:"
    echo "  $0 start"
}

# Main script logic
case "${1:-}" in
    start)
        start_central_core
        ;;
    stop)
        stop_central_core
        ;;
    restart)
        restart_central_core
        ;;
    status)
        view_status
        ;;
    logs)
        view_logs
        ;;
    tail)
        view_logs tail
        ;;
    check)
        check_dependencies
        ;;
    help|--help|-h)
        display_help
        ;;
    *)
        echo "Error: Invalid command"
        echo ""
        display_help
        exit 1
        ;;
esac

exit $?
