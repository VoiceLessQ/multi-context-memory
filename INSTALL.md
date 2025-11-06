# MCP Multi-Context Memory - Installation Guide

**Version**: 2.0.0
**Last Updated**: 2025-11-06

Complete installation guide for the MCP Multi-Context Memory System.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Local Development Setup](#local-development-setup)
4. [MCP Client Integration](#mcp-client-integration)
5. [Verification](#verification)
6. [Post-Installation](#post-installation)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Python 3.8+** (Python 3.11+ recommended)
- **Docker & Docker Compose** (for containerized deployment)
- **Git** (for cloning repository)

### Optional

- **Redis** (included in Docker setup, needed for caching)
- **MCP-compatible client** (Claude Code, Kilo Code, etc.)

### System Requirements

- **RAM**: 2GB minimum, 4GB+ recommended
- **Disk**: 1GB for system + storage for your memories
- **OS**: Linux, macOS, or Windows (with WSL/Git Bash)

---

## Quick Start (Docker)

### Step 1: Clone Repository

```bash
git clone https://github.com/VoiceLessQ/multi-context-memory.git
cd multi-context-memory
```

### Step 2: Create Data Directories

```bash
mkdir -p data/sqlite data/chroma data/jsonl logs
chmod -R 755 data/ logs/
```

### Step 3: Start Services

```bash
docker-compose up -d --build
```

This will start:
- **Redis** (caching layer) on port 6379
- **API Server** (REST API) on port 8002
- **Memory Server** (MCP stdio server)

### Step 4: Verify Installation

```bash
# Check services are running
docker-compose ps

# Should show 3 services running:
# - redis (healthy)
# - api-server (running)
# - memory-server (running)

# Test API health
curl http://localhost:8002/health

# Expected: {"status": "healthy", ...}
```

### Step 5: Run Verification Script

```bash
# On Linux/Mac
docker exec mcp-multi-context-memory-memory-server-1 \
  python scripts/verify_mcp_connection.py

# On Windows (Git Bash)
docker exec mcp-multi-context-memory-memory-server-1 python scripts/verify_mcp_connection.py
```

Expected output:
```
✓ All verification tests passed!
Your MCP server is ready to use.
```

---

## Local Development Setup

For development or if you prefer running without Docker:

### Step 1: Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/VoiceLessQ/multi-context-memory.git
cd multi-context-memory

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 3: Create Data Directories

```bash
mkdir -p data/sqlite data/chroma data/jsonl logs config
```

### Step 4: Configure Environment

Create `.env` file (optional, for custom configuration):

```bash
# Database
DATABASE_URL=sqlite:///./data/sqlite/memory.db

# Redis (optional - start Redis separately)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# Vector Search
CHROMA_ENABLED=true
CHROMA_PERSIST_DIRECTORY=./data/chroma
VECTOR_SEARCH_ENABLED=true
EMBEDDING_PROVIDER=local

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

### Step 5: Start Redis (Optional)

```bash
# Using Docker
docker run -d -p 6379:6379 --name redis redis:7-alpine

# OR install Redis locally and start it
redis-server
```

### Step 6: Run MCP Server

```bash
python src/mcp_stdio_server.py
```

Or run API server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --reload
```

---

## MCP Client Integration

### Claude Code Integration

Add to your Claude Code settings or MCP configuration:

```json
{
  "mcpServers": {
    "multi-context-memory": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-multi-context-memory-memory-server-1",
        "python",
        "src/mcp_stdio_server.py"
      ]
    }
  }
}
```

### Kilo Code Integration

Configure in `~/.kilo/mcp.json`:

```json
{
  "mcm-mcpglobal": {
    "command": "python",
    "args": ["src/mcp_stdio_server.py"],
    "cwd": "/path/to/multi-context-memory",
    "env": {
      "DATABASE_URL": "sqlite:///./data/sqlite/memory.db",
      "REDIS_ENABLED": "true",
      "REDIS_HOST": "localhost",
      "REDIS_PORT": "6379",
      "CHROMA_ENABLED": "true",
      "VECTOR_SEARCH_ENABLED": "true",
      "EMBEDDING_PROVIDER": "local"
    }
  }
}
```

### Local Development Integration

For local Python execution:

```json
{
  "multi-context-memory": {
    "command": "python",
    "args": ["/full/path/to/multi-context-memory/src/mcp_stdio_server.py"],
    "env": {
      "DATABASE_URL": "sqlite:////full/path/to/multi-context-memory/data/sqlite/memory.db",
      "REDIS_ENABLED": "false",
      "CHROMA_ENABLED": "true",
      "VECTOR_SEARCH_ENABLED": "true"
    }
  }
}
```

---

## Verification

### Automated Verification

Run the provided verification scripts:

```bash
# Health check (Docker)
chmod +x scripts/health_check.sh
./scripts/health_check.sh

# Connection verification (Docker)
docker exec mcp-multi-context-memory-memory-server-1 \
  python scripts/verify_mcp_connection.py

# Connection verification (Local)
python scripts/verify_mcp_connection.py
```

### Manual Verification

#### 1. Check Docker Services

```bash
docker-compose ps

# All services should show "running" or "healthy"
```

#### 2. Check API Server

```bash
curl http://localhost:8002/health

# Expected response:
# {"status": "healthy", "version": "2.0.0", ...}
```

#### 3. Check Database

```bash
docker exec mcp-multi-context-memory-memory-server-1 \
  python -c "import sqlite3; conn = sqlite3.connect('/app/data/sqlite/memory.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM memories'); print(f'Memories: {cursor.fetchone()[0]}'); conn.close()"
```

#### 4. Check MCP Server Logs

```bash
docker logs mcp-multi-context-memory-memory-server-1 --tail=20

# Should see:
# ✓ "RefactoredMCPStdioServer initialized"
# ✓ "Handler chain built with 4 handlers"
# ✓ "Supported tools: create_memory, search_memories, ..."
```

#### 5. Verify MCP Client Connection

In your MCP client (Claude Code, Kilo Code, etc.):
- **Expected tools**: 19
- **Expected resources**: 1 (memory://summary)
- **Expected errors**: 0

---

## Post-Installation

### Configure Security (Production)

For production deployments, **MUST** configure security:

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to docker-compose.yml or .env:
SECRET_KEY=<your-generated-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Enable Vector Search (Optional)

Vector search is enabled by default with local embeddings.

For OpenAI embeddings:

```bash
# In docker-compose.yml or .env:
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
```

### Configure Backups (Recommended)

```bash
# Create backup script
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="./data/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
cp data/sqlite/memory.db "$BACKUP_DIR/memory_$DATE.db"
echo "Backup created: memory_$DATE.db"
EOF

chmod +x scripts/backup.sh

# Add to crontab for automatic backups
# crontab -e
# 0 2 * * * /path/to/multi-context-memory/scripts/backup.sh
```

### Optimize Database

```bash
# Optimize SQLite database
docker exec mcp-multi-context-memory-memory-server-1 \
  sqlite3 /app/data/sqlite/memory.db "VACUUM; ANALYZE;"
```

### Monitor Performance

```bash
# View logs in real-time
docker-compose logs -f memory-server

# Check resource usage
docker stats mcp-multi-context-memory-memory-server-1

# Check Redis cache stats
docker exec mcp-multi-context-memory-redis-1 redis-cli INFO stats
```

---

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Full rebuild
docker-compose down
docker-compose up -d --build
```

#### MCP Connection Fails with Zod Validation Error

This issue has been **fixed in version 2.0.0** (2025-11-06).

If you're still seeing this error:

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed fix.

#### Database Connection Issues

```bash
# Verify database path
docker exec mcp-multi-context-memory-memory-server-1 \
  python -c "import os; print(os.getenv('DATABASE_URL'))"

# Should output: sqlite:///./data/sqlite/memory.db

# Check database file exists
docker exec mcp-multi-context-memory-memory-server-1 \
  ls -la /app/data/sqlite/memory.db
```

#### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker exec mcp-multi-context-memory-redis-1 redis-cli ping

# Expected: PONG
```

### Get Help

For more detailed troubleshooting:

1. **Check full troubleshooting guide**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. **Run diagnostics**:
   ```bash
   ./scripts/health_check.sh
   docker-compose logs > debug_logs.txt
   ```
3. **Report issue**: https://github.com/VoiceLessQ/multi-context-memory/issues

---

## Next Steps

Once installation is complete:

1. **Connect your MCP client** (Claude Code, Kilo Code, etc.)
2. **Verify 19 tools are available** in your client
3. **Try creating your first memory**:
   - Use the `create_memory` tool
   - Store some knowledge
   - Search for it with `search_memories`

4. **Explore advanced features**:
   - Semantic search with `search_semantic`
   - Knowledge graphs with `create_relation`
   - Bulk operations with `bulk_create_memories`

5. **Read documentation**:
   - [README.md](./README.md) - Full feature overview
   - [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Problem solutions
   - [API Docs](http://localhost:8002/docs) - Interactive API documentation

---

## Uninstallation

To completely remove the system:

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (THIS DELETES ALL DATA)
docker-compose down -v

# Remove images
docker rmi mcp-multi-context-memory-api-server
docker rmi mcp-multi-context-memory-memory-server

# Remove data directory (CAUTION: PERMANENT)
# rm -rf data/
```

---

## Support

- **Documentation**: [README.md](./README.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Issues**: https://github.com/VoiceLessQ/multi-context-memory/issues
- **Repository**: https://github.com/VoiceLessQ/multi-context-memory

---

**Installation complete! Enjoy using MCP Multi-Context Memory!** 🎉
