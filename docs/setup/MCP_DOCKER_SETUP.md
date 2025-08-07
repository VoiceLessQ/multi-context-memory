# MCP Multi-Context Memory - Docker Hybrid Setup

## 🎯 Overview

This setup provides a **hybrid architecture** that combines:
- **TypeScript MCP Server** (proper MCP protocol) - for AI clients like Claude Desktop
- **Python FastAPI Server** (HTTP/WebSocket APIs) - for web dashboards and REST APIs
- **Shared Storage** - both services access the same memory data

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│                                                         │
│  ┌─────────────────────┐    ┌─────────────────────────┐ │
│  │   TypeScript MCP    │    │    Python FastAPI      │ │
│  │      Server         │    │       Server           │ │
│  │                     │    │                         │ │
│  │ • MCP Protocol      │    │ • HTTP REST APIs       │ │
│  │ • stdio transport   │    │ • WebSocket endpoints  │ │
│  │ • AI Client Ready   │    │ • Web Dashboard Ready  │ │
│  │                     │    │                         │ │
│  │ Port: Internal      │    │ Port: 8000 (exposed)   │ │
│  └─────────────────────┘    └─────────────────────────┘ │
│           │                            │                │
│           └────────────┬───────────────┘                │
│                        │                                │
│                ┌───────▼────────┐                       │
│                │  Shared Storage │                       │
│                │ (/app/data)     │                       │
│                └────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Build and Start Services

```bash
# Build and start the hybrid architecture
docker-compose -f docker-compose.hybrid.yml up --build -d

# Check service status
docker-compose -f docker-compose.hybrid.yml ps
```

### 2. Test the Setup

```bash
# Run the connection test
python test_mcp_connection.py

# Or check manually:
curl http://localhost:8000/health
curl http://localhost:8000/mcp/resources
```

### 3. Use with MCP Clients

For AI clients (Claude Desktop, etc.), add this to your MCP client config:

```json
{
  "mcpServers": {
    "mcp-multi-context-memory": {
      "command": "docker",
      "args": [
        "exec", "-i", "mcp-typescript-server", 
        "node", "dist/index.js"
      ]
    }
  }
}
```

## 📁 File Structure

```
├── Dockerfile.mcp-ts          # TypeScript MCP server container
├── Dockerfile                 # Python API server container  
├── docker-compose.hybrid.yml  # Hybrid architecture config
├── test_mcp_connection.py     # Connection test script
├── index.ts                   # TypeScript MCP server (main)
├── src/mcp_server.py          # Python API server (fixed imports)
└── MCP_DOCKER_SETUP.md        # This file
```

## 🔧 Services

### TypeScript MCP Server (`mcp-typescript`)
- **Purpose**: True MCP protocol implementation
- **Port**: Internal (not exposed)
- **Protocol**: stdio transport (standard MCP)
- **Usage**: AI clients, MCP tools
- **Health**: Process-based monitoring

### Python API Server (`mcp-python-api`)
- **Purpose**: HTTP/WebSocket APIs
- **Port**: 8000 (exposed)
- **Protocol**: HTTP REST + WebSocket
- **Usage**: Web dashboards, API integrations
- **Health**: HTTP endpoint `/health`

### Redis Cache (`redis`)
- **Purpose**: Optional caching layer
- **Port**: 6379 (exposed)
- **Usage**: Performance optimization

## 🛠️ Development

### View Logs
```bash
# All services
docker-compose -f docker-compose.hybrid.yml logs -f

# Specific service
docker-compose -f docker-compose.hybrid.yml logs -f mcp-typescript
docker-compose -f docker-compose.hybrid.yml logs -f mcp-python-api
```

### Access Containers
```bash
# TypeScript server
docker exec -it mcp-typescript-server sh

# Python server  
docker exec -it mcp-python-api-server bash
```

### Shared Data
Both services share data via the volume `mcp_shared_data` mounted at `/app/data/`

## 🐛 Troubleshooting

### Connection Refused Error
1. Check if services are running:
   ```bash
   docker-compose -f docker-compose.hybrid.yml ps
   ```

2. Check service logs:
   ```bash
   docker-compose -f docker-compose.hybrid.yml logs mcp-python-api
   ```

3. Test network connectivity:
   ```bash
   docker network inspect mcp-hybrid-network
   ```

### MCP Client Issues
1. Ensure TypeScript server is running:
   ```bash
   docker exec mcp-typescript-server pgrep -f "node.*index"
   ```

2. Test MCP server directly:
   ```bash
   docker exec -i mcp-typescript-server node dist/index.js
   ```

### Import Errors in Python
All Python import issues have been fixed in this setup. If you encounter any:
1. Check the container logs
2. Verify all required files are copied to the container
3. Check Python path configuration

## 🔄 Migration from Old Setup

If migrating from the old setup:

1. **Backup your data**:
   ```bash
   docker cp mcp-memory-system:/app/data ./backup_data
   ```

2. **Stop old containers**:
   ```bash
   docker-compose down
   ```

3. **Start new hybrid setup**:
   ```bash
   docker-compose -f docker-compose.hybrid.yml up --build -d
   ```

4. **Restore data** (if needed):
   ```bash
   docker cp ./backup_data mcp-typescript-server:/app/data
   docker cp ./backup_data mcp-python-api-server:/app/data
   ```

## ✅ Success Indicators

When everything works correctly:
- ✅ `docker-compose -f docker-compose.hybrid.yml ps` shows all services as "Up"
- ✅ `curl http://localhost:8000/health` returns `{"status": "healthy"}`
- ✅ `python test_mcp_connection.py` passes all tests
- ✅ MCP clients can connect to the TypeScript server
- ✅ Web applications can use the Python API endpoints

## 📚 API Endpoints

### Python FastAPI Server (Port 8000)

**Health & Info:**
- `GET /health` - Health check
- `GET /` - Server info

**MCP-Style Endpoints:**
- `GET /mcp/resources` - List MCP resources
- `GET /mcp/resources/{uri}` - Get specific resource
- `POST /mcp/tools` - List available tools
- `POST /mcp/tools/{tool_name}` - Execute tool

**Legacy API Endpoints:**
- `POST /api/memory/` - Create memory
- `GET /api/memory/` - List memories
- `GET /api/memory/{id}` - Get memory
- `POST /api/memory/search` - Search memories

**WebSocket:**
- `WS /ws` - Real-time updates

Now your MCP setup should work perfectly with both AI clients and web applications! 🚀