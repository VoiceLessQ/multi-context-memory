# MCP Multi-Context Memory - Troubleshooting Guide

**Last Updated**: 2025-11-06
**Version**: 2.0.0

This comprehensive troubleshooting guide covers common issues, their causes, and solutions for the MCP Multi-Context Memory System.

---

## Table of Contents

1. [MCP Connection Issues](#mcp-connection-issues)
2. [Database Issues](#database-issues)
3. [Docker Issues](#docker-issues)
4. [Redis Issues](#redis-issues)
5. [Vector Search Issues](#vector-search-issues)
6. [Performance Issues](#performance-issues)
7. [Security & Authentication](#security--authentication)
8. [Diagnostic Tools](#diagnostic-tools)

---

## MCP Connection Issues

### Issue 1: Zod Validation Error - "Expected string, received null"

**Error Message**:
```json
{
  "code": "invalid_union",
  "unionErrors": [
    {
      "issues": [
        {
          "code": "invalid_type",
          "expected": "string",
          "received": "null",
          "path": ["id"],
          "message": "Expected string, received null"
        }
      ]
    }
  ]
}
```

**Cause**: The MCP server is sending `null` for the `id` field in JSON-RPC error responses, but the MCP protocol requires a string or number.

**Solution**: This has been fixed in the latest version (2025-11-06). Update your code:

**File**: `src/mcp/refactored_stdio_server.py`

```python
# OLD (BROKEN):
def _send_parse_error(self):
    error_response = {
        "jsonrpc": "2.0",
        "id": None,  # ❌ This causes the error
        "error": {...}
    }

# NEW (FIXED):
def _send_parse_error(self, request_id=None):
    error_response = {
        "jsonrpc": "2.0",
        "id": request_id if request_id is not None else "unknown",  # ✅ Always a string
        "error": {...}
    }
```

**Apply the fix**:
```bash
# Pull latest changes
git pull origin main

# Rebuild Docker containers
docker-compose down
docker-compose up -d --build

# Verify connection
# In your MCP client, you should now see 19 tools and 0 errors
```

---

### Issue 2: MCP Server Not Responding

**Symptoms**:
- MCP client shows "connection failed"
- No tools available
- Server appears to hang

**Diagnostic Steps**:
```bash
# Check if memory-server container is running
docker-compose ps memory-server

# Check server logs
docker logs mcp-multi-context-memory-memory-server-1 --tail=50

# Look for initialization messages:
# ✅ "RefactoredMCPStdioServer initialized"
# ✅ "Handler chain built with 4 handlers"
# ✅ "Supported tools: create_memory, search_memories, ..."
```

**Solutions**:

1. **Restart the MCP server**:
   ```bash
   docker-compose restart memory-server
   ```

2. **Check for port conflicts**:
   ```bash
   # MCP stdio server doesn't use ports, but check API server
   lsof -i :8002
   ```

3. **Verify database connection**:
   ```bash
   docker exec mcp-multi-context-memory-memory-server-1 \
     python -c "from src.database.session import settings; print(settings.database_url)"

   # Should output: sqlite:///./data/sqlite/memory.db
   ```

---

### Issue 3: MCP Tools Not Listed

**Symptoms**:
- Connection established but 0 tools shown
- `tools/list` returns empty array

**Cause**: Handler chain not initialized properly

**Solution**:
```bash
# Check handler initialization in logs
docker logs mcp-multi-context-memory-memory-server-1 2>&1 | grep "Handler chain"

# Should see:
# "Handler chain built with 4 handlers"
# "Supported tools: create_memory, search_memories, ..."

# If not, rebuild:
docker-compose up -d --build memory-server
```

---

## Database Issues

### Issue 4: Database Path Mismatch

**Error Message**:
```
sqlite3.OperationalError: unable to open database file
```

**Cause**: The database path in `session.py` doesn't match the environment variable in `docker-compose.yml`.

**Solution** (Fixed in latest version):

**File**: `src/database/session.py`

```python
# OLD (BROKEN):
settings = type('Settings', (), {
    'database_url': 'sqlite:///./memory.db',  # ❌ Wrong path
    ...
})()

# NEW (FIXED):
import os
settings = type('Settings', (), {
    'database_url': os.getenv('DATABASE_URL', 'sqlite:///./data/sqlite/memory.db'),  # ✅ Uses env var
    'debug': os.getenv('DEBUG', 'false').lower() == 'true',
    'max_connections': int(os.getenv('MAX_CONNECTIONS', '10')),
    'query_timeout': int(os.getenv('QUERY_TIMEOUT', '30'))
})()
```

**Verify the fix**:
```bash
# Check environment variable in container
docker exec mcp-multi-context-memory-memory-server-1 \
  python -c "import os; print('DATABASE_URL:', os.getenv('DATABASE_URL'))"

# Should output: DATABASE_URL: sqlite:///./data/sqlite/memory.db

# Check database file exists
docker exec mcp-multi-context-memory-memory-server-1 ls -la /app/data/sqlite/

# Should show: memory.db
```

---

### Issue 5: Database Locked Error

**Error Message**:
```
sqlite3.OperationalError: database is locked
```

**Causes**:
- Multiple processes accessing database simultaneously
- Previous connection not closed properly
- SQLite limitations with concurrent access

**Solutions**:

1. **Enable WAL mode** (Write-Ahead Logging):
   ```bash
   sqlite3 data/sqlite/memory.db "PRAGMA journal_mode=WAL;"
   ```

2. **Check for hanging connections**:
   ```bash
   # On Linux/Mac:
   lsof data/sqlite/memory.db

   # On Windows:
   # Use Process Explorer to find processes with handle to memory.db
   ```

3. **Restart all services**:
   ```bash
   docker-compose restart
   ```

4. **For production, use PostgreSQL instead**:
   - See `docker-compose.yml` for PostgreSQL configuration
   - Update `DATABASE_URL` to PostgreSQL connection string

---

### Issue 6: Empty Database After Restart

**Symptoms**:
- Database exists but contains no data after restart
- Memory count shows 0

**Cause**: Docker volume not persisted

**Solution**:
```bash
# Check volumes
docker volume ls | grep mcp-multi-context-memory

# Ensure data directory is mounted
docker-compose exec memory-server ls -la /app/data/sqlite/

# Verify volume configuration in docker-compose.yml
# Should have:
#   volumes:
#     - ./data:/app/data

# If data lost, restore from backup:
cp data/backups/memory.db.backup data/sqlite/memory.db
```

---

## Docker Issues

### Issue 7: Container Build Fails

**Error Message**:
```
ERROR: Cannot locate specified Dockerfile: Dockerfile
```

**Cause**: Missing Dockerfile

**Solution**:

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libmagic1 \
    python3-magic \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/sqlite \
    /app/data/chroma \
    /app/data/jsonl \
    /app/logs \
    /app/config

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Default command (can be overridden in docker-compose)
CMD ["python", "src/mcp_stdio_server.py"]
```

Then rebuild:
```bash
docker-compose up -d --build
```

---

### Issue 8: Permission Denied Errors

**Error Message**:
```
PermissionError: [Errno 13] Permission denied: '/app/data/sqlite/memory.db'
```

**Solutions**:

1. **Fix directory permissions**:
   ```bash
   # On host machine
   mkdir -p data/sqlite data/chroma data/jsonl logs
   chmod -R 755 data/ logs/
   ```

2. **Fix Docker user permissions**:
   ```bash
   # If using Docker on Linux
   sudo chown -R 1000:1000 data/ logs/
   ```

3. **Check Docker volume mounts**:
   ```bash
   docker-compose config | grep volumes -A 5
   ```

---

### Issue 9: Container Keeps Restarting

**Diagnostic**:
```bash
# Check container status
docker-compose ps

# View recent logs
docker-compose logs memory-server --tail=100

# Check for errors
docker-compose logs memory-server 2>&1 | grep -i error
```

**Common Causes & Solutions**:

1. **Import errors**:
   ```bash
   # Rebuild with no cache
   docker-compose build --no-cache memory-server
   docker-compose up -d memory-server
   ```

2. **Missing dependencies**:
   ```bash
   # Update requirements.txt
   # Then rebuild
   docker-compose up -d --build
   ```

3. **Database initialization fails**:
   ```bash
   # Remove corrupted database
   rm data/sqlite/memory.db

   # Restart to recreate
   docker-compose restart memory-server
   ```

---

## Redis Issues

### Issue 10: Redis Connection Failed

**Error Message**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Diagnostic Steps**:
```bash
# 1. Check if Redis container is running
docker-compose ps redis

# 2. Check Redis health
docker-compose exec redis redis-cli ping
# Expected: PONG

# 3. View Redis logs
docker-compose logs redis --tail=50

# 4. Test connection from memory-server
docker-compose exec memory-server \
  python -c "import redis; r = redis.Redis(host='redis', port=6379); print(r.ping())"
# Expected: True
```

**Solutions**:

1. **Restart Redis**:
   ```bash
   docker-compose restart redis
   ```

2. **Check network connectivity**:
   ```bash
   docker network ls | grep mcp-network
   docker network inspect mcp-multi-context-memory_mcp-network
   ```

3. **Disable Redis temporarily** (for testing):
   ```bash
   # In docker-compose.yml or .env:
   # REDIS_ENABLED=false
   ```

4. **Clear Redis cache**:
   ```bash
   docker-compose exec redis redis-cli FLUSHALL
   ```

---

## Vector Search Issues

### Issue 11: ChromaDB Permission Issues

**Error Message**:
```
PermissionError: [Errno 13] Permission denied: './data/chroma'
```

**Solution**:
```bash
# Create directory with proper permissions
mkdir -p data/chroma
chmod 755 data/chroma

# If using Docker
sudo chown -R 1000:1000 data/chroma/

# Restart services
docker-compose restart memory-server
```

---

### Issue 12: Embedding Model Download Fails

**Error Message**:
```
Unable to download model 'all-MiniLM-L6-v2'
```

**Solutions**:

1. **Manually download model**:
   ```bash
   docker-compose exec memory-server \
     python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```

2. **Use OpenAI embeddings instead**:
   ```bash
   # In docker-compose.yml or .env:
   EMBEDDING_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   ```

3. **Check disk space**:
   ```bash
   df -h
   docker system df
   ```

---

## Performance Issues

### Issue 13: Slow Query Response

**Symptoms**:
- Queries taking >5 seconds
- High memory usage
- CPU spikes

**Diagnostic**:
```bash
# Check Redis cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace

# Check memory usage
docker stats mcp-multi-context-memory-memory-server-1

# Enable debug logging
# In docker-compose.yml:
# LOG_LEVEL=DEBUG
```

**Solutions**:

1. **Enable caching**:
   ```bash
   # In docker-compose.yml:
   CACHE_ENABLED=true
   CACHE_TTL=3600
   ```

2. **Optimize database**:
   ```bash
   sqlite3 data/sqlite/memory.db "VACUUM;"
   sqlite3 data/sqlite/memory.db "ANALYZE;"
   ```

3. **Increase connection pool**:
   ```bash
   # In docker-compose.yml:
   MAX_CONNECTIONS=20
   ```

---

## Security & Authentication

### Issue 14: Authentication 501 Error

**Error Message**:
```
HTTPException: 501 User retrieval not fully implemented
```

**Explanation**: This is expected behavior. Authentication requires configuration.

**Solution**:

1. **Generate secure secret key**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Configure environment**:
   ```bash
   # In .env or docker-compose.yml:
   SECRET_KEY=your-generated-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. **For development, authentication can be bypassed** (not recommended for production)

---

## Diagnostic Tools

### Health Check Script

Create `scripts/health_check.sh`:

```bash
#!/bin/bash
echo "=== MCP Multi-Context Memory Health Check ==="

# Check Docker containers
echo -e "\n1. Container Status:"
docker-compose ps

# Check API health
echo -e "\n2. API Server Health:"
curl -s http://localhost:8002/health | jq '.'

# Check Redis
echo -e "\n3. Redis Status:"
docker-compose exec redis redis-cli ping

# Check Database
echo -e "\n4. Database Status:"
docker exec mcp-multi-context-memory-memory-server-1 \
  python -c "import sqlite3; conn = sqlite3.connect('/app/data/sqlite/memory.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM memories'); print(f'Memories: {cursor.fetchone()[0]}'); conn.close()"

# Check MCP Server
echo -e "\n5. MCP Server Status:"
docker logs mcp-multi-context-memory-memory-server-1 2>&1 | grep "Handler chain built"

echo -e "\n=== Health Check Complete ==="
```

Run it:
```bash
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

---

### Database Connection Test

Use the included `test_db_connection.py`:

```bash
docker exec mcp-multi-context-memory-memory-server-1 python test_db_connection.py
```

Expected output:
```
✓ MCP Server can access database
✓ Found 31 memories in database
✓ Database statistics retrieved successfully
  - Total memories: 31
  - Categories: {...}
✓ Retrieved 5 recent memories
✅ All database connection tests passed!
```

---

### Log Analysis

```bash
# View all errors
docker-compose logs 2>&1 | grep -i error

# View MCP server initialization
docker logs mcp-multi-context-memory-memory-server-1 2>&1 | grep "INFO"

# Monitor in real-time
docker-compose logs -f memory-server

# Export logs for analysis
docker-compose logs > debug_logs.txt
```

---

## Getting Help

If you're still experiencing issues:

1. **Check logs**:
   ```bash
   docker-compose logs > full_logs.txt
   ```

2. **Run diagnostics**:
   ```bash
   ./scripts/health_check.sh > diagnostics.txt
   ```

3. **Create an issue**: https://github.com/VoiceLessQ/multi-context-memory/issues
   - Include: logs, diagnostics, docker-compose.yml (redact secrets!)
   - Describe: what you were doing, what happened, what you expected

4. **Join community**: [Link to Discord/discussions if available]

---

## Changelog

### 2025-11-06
- ✅ Fixed Zod validation error for null `id` fields in JSON-RPC responses
- ✅ Fixed database path configuration to use environment variables
- ✅ Added comprehensive troubleshooting documentation

### 2025-11-05
- Initial troubleshooting guide created
