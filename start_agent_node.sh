#!/bin/bash

# Agent Node System Startup Script
# This script launches an Agent Node for the Decentralized AI Ecosystem

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_NODE_DIR="$PROJECT_DIR/agent_node_system"
VENV_DIR="$AGENT_NODE_DIR/venv"
LOG_FILE="$PROJECT_DIR/agent_node.log"
PID_FILE="$PROJECT_DIR/agent_node.pid"
IDENTITY_FILE="$AGENT_NODE_DIR/identity/identity.json"

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

# Function to generate agent identity
generate_identity() {
    print_message "$BLUE" "Generating agent identity..."

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    if [ -f "$AGENT_NODE_DIR/identity/keypair_manager.py" ]; then
        python -c "from agent_node_system.identity.keypair_manager import KeypairManager; KeypairManager().generate_keys()"
        if [ $? -eq 0 ]; then
            print_message "$GREEN" "Agent identity created successfully"
        else
            print_message "$RED" "Failed to generate agent identity"
            deactivate
            return 1
        fi
    else
        print_message "$RED" "Keypair manager not found: $AGENT_NODE_DIR/identity/keypair_manager.py"
        deactivate
        return 1
    fi

    deactivate
    return 0
}

# Function to start agent node
start_agent_node() {
    print_message "$BLUE" "Starting Decentralized AI Agent Node..."

    # Check if already running
    if is_running; then
        print_message "$YELLOW" "Agent node is already running (PID: $(cat "$PID_FILE"))"
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
    if ! pip install -q -r "$AGENT_NODE_DIR/requirements.txt"; then
        print_message "$RED" "Failed to install dependencies"
        deactivate
        return 1
    fi

    # Check and generate identity if needed
    if [ ! -f "$IDENTITY_FILE" ]; then
        print_message "$YELLOW" "Agent identity not found. Generating..."
        if ! generate_identity; then
            deactivate
            return 1
        fi
    fi

    # Check and create log directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Check central core connectivity
    print_message "$BLUE" "Checking central core connectivity..."
    if ! python -c "
import requests
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        print('Success')
    else:
        print('Failed')
except Exception as e:
    print('Error:', str(e))
" > /dev/null; then
        print_message "$YELLOW" "Warning: Cannot connect to central core at http://localhost:8000"
        print_message "$YELLOW" "Make sure central core is running before starting agents"
        read -p "Continue with startup anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            deactivate
            return 1
        fi
    else
        print_message "$GREEN" "Connected to central core successfully"
    fi

    # Start agent node
    print_message "$BLUE" "Launching agent node..."
    if [ -f "$AGENT_NODE_DIR/agent_runtime/main_agent.py" ]; then
        python -m agent_node_system.agent_runtime.main_agent \
            --config "$AGENT_NODE_DIR/config/environment.py" \
            > "$LOG_FILE" 2>&1 &
        
        local PID=$!
        if [ $? -eq 0 ]; then
            echo "$PID" > "$PID_FILE"
            print_message "$GREEN" "Agent node started successfully!"
            print_message "$GREEN" "PID: $PID"
            print_message "$GREEN" "Log file: $LOG_FILE"
            print_message "$GREEN" "Identity: $IDENTITY_FILE"
        else
            print_message "$RED" "Failed to start agent node"
            deactivate
            return 1
        fi
    else
        print_message "$RED" "Main application file not found: $AGENT_NODE_DIR/agent_runtime/main_agent.py"
        deactivate
        return 1
    fi

    # Deactivate virtual environment
    deactivate
    return 0
}

# Function to stop agent node
stop_agent_node() {
    print_message "$BLUE" "Stopping Decentralized AI Agent Node..."

    if ! is_running; then
        print_message "$YELLOW" "Agent node is not running"
        return 1
    fi

    local PID=$(cat "$PID_FILE")
    print_message "$BLUE" "Terminating process $PID..."
    
    # First try graceful shutdown
    kill -TERM "$PID"
    sleep 3
    
    # If still running, force kill
    if ps -p "$PID" > /dev/null 2>&1; then
        print_message "$YELLOW" "Process still running, forcing termination..."
        kill -KILL "$PID"
        sleep 2
    fi
    
    # Cleanup
    rm -f "$PID_FILE"
    print_message "$GREEN" "Agent node stopped successfully"
    return 0
}

# Function to restart agent node
restart_agent_node() {
    stop_agent_node
    sleep 2
    start_agent_node
    return $?
}

# Function to view status
view_status() {
    if is_running; then
        print_message "$GREEN" "Agent node is RUNNING"
        print_message "$BLUE" "PID: $(cat "$PID_FILE")"
        print_message "$BLUE" "Log file: $LOG_FILE"
        print_message "$BLUE" "Identity file: $IDENTITY_FILE"
        
        # Check if agent is connected to central core
        if grep -q "Connected to central core" "$LOG_FILE" 2>/dev/null; then
            print_message "$GREEN" "Connected to central core"
        else
            print_message "$YELLOW" "Not connected to central core"
        fi
    else
        print_message "$RED" "Agent node is NOT running"
    fi
}

# Function to view logs
view_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        print_message "$YELLOW" "Log file not found: $LOG_FILE"
        return 1
    fi
    
    if [ "$1" == "tail" ]; then
        print_message "$BLUE" "Tailing agent node logs (press Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        print_message "$BLUE" "Displaying agent node logs:"
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
    
    # Check required directories
    if [ ! -d "$AGENT_NODE_DIR" ]; then
        print_message "$RED" "Agent node directory not found: $AGENT_NODE_DIR"
        return 1
    fi
    
    if [ ! -f "$AGENT_NODE_DIR/requirements.txt" ]; then
        print_message "$RED" "Requirements file not found: $AGENT_NODE_DIR/requirements.txt"
        return 1
    fi
    
    if [ ! -f "$AGENT_NODE_DIR/agent_runtime/main_agent.py" ]; then
        print_message "$RED" "Main application file not found: $AGENT_NODE_DIR/agent_runtime/main_agent.py"
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

# Function to reset agent identity
reset_identity() {
    print_message "$BLUE" "Resetting agent identity..."
    
    if is_running; then
        print_message "$YELLOW" "Agent node must be stopped first"
        return 1
    fi
    
    if [ -f "$IDENTITY_FILE" ]; then
        read -p "Are you sure you want to delete existing identity? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f "$IDENTITY_FILE"
            print_message "$GREEN" "Identity file removed"
        else
            print_message "$YELLOW" "Operation cancelled"
            return 1
        fi
    fi
    
    # Regenerate identity
    if [ -d "$VENV_DIR" ]; then
        generate_identity
    else
        print_message "$YELLOW" "Virtual environment not found. Identity will be generated on next startup"
    fi
    
    return 0
}

# Function to display help
display_help() {
    echo "Usage: $0 {start|stop|restart|status|logs|tail|check|reset}"
    echo ""
    echo "Commands:"
    echo "  start    Start agent node"
    echo "  stop     Stop agent node"
    echo "  restart  Restart agent node"
    echo "  status   Show current status"
    echo "  logs     Display log file"
    echo "  tail     Tail log file (follow)"
    echo "  check    Check system dependencies"
    echo "  reset    Reset agent identity"
    echo ""
    echo "Example:"
    echo "  $0 start"
}

# Main script logic
case "${1:-}" in
    start)
        start_agent_node
        ;;
    stop)
        stop_agent_node
        ;;
    restart)
        restart_agent_node
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
    reset)
        reset_identity
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
