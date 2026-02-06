# Troubleshooting Guide

## Common Issues and Solutions

### 1. Central Core System

#### Issue 1: Port 8000 already in use
**Error message**: "Address already in use" or "Port 8000 is already bound"

**Solution**:
```bash
# Find and kill process using port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Or use a different port
# In central_core_system/config/settings.py:
API_PORT = 8001
```

#### Issue 2: PostgreSQL connection error
**Error message**: "Could not connect to server" or "Connection refused"

**Solution**:
```bash
# Check if PostgreSQL is running
pg_lsclusters  # Ubuntu/Debian
brew services list  # macOS (Homebrew)
systemctl status postgresql  # CentOS/RHEL

# Start PostgreSQL service
sudo service postgresql start  # Ubuntu/Debian
brew services start postgresql  # macOS (Homebrew)
systemctl start postgresql  # CentOS/RHEL

# Verify database connection
psql -h localhost -U postgres -d decentralized_ai
```

#### Issue 3: Redis connection error
**Error message**: "Connection refused" or "Redis server not responding"

**Solution**:
```bash
# Check if Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis service
sudo service redis-server start  # Ubuntu/Debian
brew services start redis  # macOS (Homebrew)
systemctl start redis  # CentOS/RHEL

# Verify Redis connection
redis-cli info server
```

#### Issue 4: Missing dependencies
**Error message**: "ModuleNotFoundError" or "ImportError"

**Solution**:
```bash
# Reinstall dependencies
cd central_core_system
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Issue 5: Database initialization error
**Error message**: "relation does not exist" or "table not found"

**Solution**:
```bash
# Recreate the database
dropdb decentralized_ai
createdb decentralized_ai

# Run database migrations
python -m central_core_system.database.initialize
```

### 2. Agent Node System

#### Issue 1: Cannot connect to central core
**Error message**: "Connection refused" or "Timeout"

**Solution**:
```bash
# Verify central core is running
curl http://localhost:8000/health  # Should return {"status":"healthy"}

# Check firewall settings
sudo ufw allow 8000/tcp  # Ubuntu/Debian
sudo firewall-cmd --add-port=8000/tcp --permanent  # CentOS/RHEL

# Check network connectivity
ping localhost
nc -zv localhost 8000
```

#### Issue 2: Agent identity not found
**Error message**: "Key pair not found" or "Identity file not found"

**Solution**:
```bash
# Generate new identity
cd agent_node_system
python3 -m venv venv
source venv/bin/activate
python -m agent_node_system.identity.keypair_manager --generate
```

#### Issue 3: Local storage access error
**Error message**: "Permission denied" or "No such file or directory"

**Solution**:
```bash
# Check permissions
ls -la agent_node_system/local_storage/
chmod -R 755 agent_node_system/local_storage/
mkdir -p agent_node_system/local_storage

# Verify path accessibility
test -d agent_node_system/local_storage && echo "Storage directory accessible"
```

#### Issue 4: Tool execution failures
**Error message**: "Permission denied" or "Tool not found"

**Solution**:
```bash
# Verify tool permissions
ls -la agent_node_system/local_tools/
chmod +x agent_node_system/local_tools/*.py

# Check tool definitions
ls -la central_core_system/tool_mcp_server/tool_registry/
grep -r "class" central_core_system/tool_mcp_server/tool_registry/
```

### 3. Docker Deployment

#### Issue 1: Container startup failures
**Error message**: "Container exited with code 1" or "Health check failed"

**Solution**:
```bash
# Check container logs
docker-compose logs central-core
docker-compose logs agent-node

# Check Docker service status
systemctl status docker  # Linux
brew services list  # macOS (Homebrew)

# Recreate containers
docker-compose down
docker-compose up -d --build
```

#### Issue 2: Network connectivity between containers
**Error message**: "Could not connect to host" or "Timeout"

**Solution**:
```bash
# Check Docker network
docker network ls
docker network inspect decentralized_ai_network

# Check container IP addresses
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' decentralized_ai_ecosystem_central-core_1

# Verify DNS resolution
docker exec -it decentralized_ai_ecosystem_central-core_1 nslookup agent-node
```

### 4. Performance Issues

#### Issue 1: High CPU usage
**Solution**:
```bash
# Check system resources
top  # Press 'q' to quit

# Limit API workers
# In central_core_system/config/settings.py:
API_WORKERS = 2  # Reduce from 4 to 2

# Adjust task parallelism
# In central_core_system/config/settings.py:
MAX_CONCURRENT_TASKS = 25
```

#### Issue 2: High memory usage
**Solution**:
```bash
# Monitor memory usage
ps aux | grep python | sort -rk 4,4

# Adjust vector DB settings
# In central_core_system/config/settings.py:
MAX_KNOWLEDGE_SIZE = 50000  # Reduce from 100000

# Enable memory cleanup
# In agent_node_system/config/environment.py:
MEMORY_CLEANUP_INTERVAL = 1800  # Reduce from 3600
```

### 5. Security Issues

#### Issue 1: Authentication failures
**Error message**: "Invalid token" or "Permission denied"

**Solution**:
```bash
# Check secret key consistency
# In .env file:
SECRET_KEY=your-unique-secret-key-here

# Regenerate agent identity
./start_agent_node.sh reset
./start_agent_node.sh start

# Verify agent registration
curl -X GET "http://localhost:8000/agents"
```

#### Issue 2: Encryption errors
**Error message**: "Decryption failed" or "Invalid signature"

**Solution**:
```bash
# Check if keys are compatible
ls -la agent_node_system/identity/
stat agent_node_system/identity/*.pem

# Regenerate agent identity
python -m agent_node_system.identity.keypair_manager --regenerate

# Verify signature functionality
python -m agent_node_system.identity.keypair_manager --test
```

### 6. Debugging Tips

#### Enable debug logging
```bash
# In central_core_system/config/settings.py:
LOG_LEVEL = "DEBUG"

# In agent_node_system/config/environment.py:
LOG_LEVEL = "DEBUG"
```

#### Check application logs
```bash
# View central core logs
tail -f central_core.log

# View agent node logs
tail -f agent_node.log

# Filter error messages
grep "ERROR" central_core.log
grep "ERROR" agent_node.log
```

#### Use Python debug mode
```bash
# Run central core with debug
cd central_core_system
uvicorn central_core_system.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Run agent node with debug
cd agent_node_system
python -m agent_node_system.agent_runtime.main_agent --debug --log-level DEBUG
```

#### Database debugging
```bash
# Check PostgreSQL connections
psql -h localhost -U postgres -c "SELECT * FROM pg_stat_activity;"

# Check Redis info
redis-cli info stats
redis-cli info memory
```

### 7. System Check Script

Create a system check script:
```bash
#!/bin/bash
echo "=== Decentralized AI Ecosystem System Check ==="
echo ""

echo "=== Python ==="
python3 --version

echo ""
echo "=== Network ==="
nc -zv localhost 8000
nc -zv localhost 5432
nc -zv localhost 6379

echo ""
echo "=== Services ==="
curl -f http://localhost:8000/health && echo " - Central Core" || echo " - Central Core [DOWN]"

echo ""
echo "=== Files ==="
test -f central_core.log && echo "Central core log exists"
test -f agent_node.log && echo "Agent node log exists"
test -d agent_node_system/identity && echo "Agent identity directory exists"
test -f agent_node_system/identity/private_key.pem && echo "Private key exists"
test -f agent_node_system/identity/public_key.pem && echo "Public key exists"
```

### 8. Common Commands

#### System management
```bash
# Stop all services
./start_central_core.sh stop
./start_agent_node.sh stop
docker-compose down

# Restart services
./start_central_core.sh restart
./start_agent_node.sh restart
docker-compose restart

# Check status
./start_central_core.sh status
./start_agent_node.sh status
docker-compose ps

# View logs
./start_central_core.sh logs
./start_agent_node.sh logs
docker-compose logs -f
```

#### Performance monitoring
```bash
# System resources
top -d 5

# Process monitoring
ps aux | grep python

# Network monitoring
iftop

# Disk usage
df -h
du -sh .
```

### 9. Emergency Recovery

#### Restore from backup
```bash
# Restore PostgreSQL database
pg_restore -h localhost -U postgres -d decentralized_ai backup.sql

# Restore Redis data
redis-cli --pipe < redis_dump.rdb

# Restore vector DB
cp -r backup/chroma_db ./central_core_system/
```

#### Clean reinstall
```bash
# Clean temporary files
rm -f central_core.log agent_node.log
rm -f *.pid
rm -rf __pycache__

# Reinstall dependencies
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Reinitialize system
./start_central_core.sh start
./start_agent_node.sh start
```

### 10. Contact Support

If you're still having issues:

1. Collect all relevant logs
2. Save system information: `uname -a && python3 --version && pip3 list`
3. Create a GitHub issue with:
   - Clear problem description
   - Error messages
   - Steps to reproduce
   - System information
   - Log files

---

**Note**: This troubleshooting guide is not exhaustive. For complex issues, consult the [Architecture Overview](ARCHITECTURE_OVERVIEW.md) and the codebase documentation.
