FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Create central_core_system directory
RUN mkdir -p /app/central_core_system

# Install Python dependencies
COPY requirements.txt /app/central_core_system/
RUN pip install --no-cache-dir -r /app/central_core_system/requirements.txt

# Copy application code
COPY . /app/central_core_system/

# Create data directory
RUN mkdir -p /app/central_core_system/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "central_core_system.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
