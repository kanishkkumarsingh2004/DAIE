FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Create agent_node_system directory
RUN mkdir -p /app/agent_node_system

# Install Python dependencies
COPY requirements.txt /app/agent_node_system/
RUN pip install --no-cache-dir -r /app/agent_node_system/requirements.txt

# Copy application code
COPY . /app/agent_node_system/

# Create local storage directory
RUN mkdir -p /app/agent_node_system/local_storage

# Health check (check if agent process is running)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD pgrep -f "python -m agent_node_system.agent_runtime.main_agent" > /dev/null || exit 1

# Command to run the application
CMD ["python", "-m", "agent_node_system.agent_runtime.main_agent"]
