# MCP Multi-Context Memory System

A functional Model Context Protocol (MCP) server implementation with memory management capabilities, designed for integration with AI development tools like Kilo Code.

## 🎯 Current Status

**✅ OPERATIONAL**: MCP server is fully functional with Kilo Code integration showing **14 advanced tools**
- **Persistent SQLite database** - All memories survive VS Code restarts
- **Enterprise-grade memory management** with CRUD operations
- **Relationship intelligence** with graph analytics
- **Content analytics engine** with multi-dimensional analysis
- **Auto-categorization system** with intelligent tagging
- **Advanced semantic search** with similarity scoring
- **Knowledge graph analytics** with connectivity metrics
- **Bulk operations** for efficient memory handling
- Docker-based deployment with reliable containerization

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-multi-context-memory.git
cd mcp-multi-context-memory

# Start with Docker Compose
docker-compose up -d

# Verify container is running
docker ps | grep mcp-memory-system
```

### Option 2: Local Development

```bash
# Install minimal dependencies
pip install -r requirements-minimal.txt

# Run the MCP server directly
python src/mcp_stdio_server.py
```

### Kilo Code Integration

1. **Add MCP Server Configuration**:
   - Open Kilo Code settings
   - Add server configuration:

```json
{
  "mcm-mcpglobal": {
    "command": "docker",
    "args": ["exec", "-i", "mcp-memory-system", "python", "-m", "src.mcp_stdio_server"],
    "transport": "stdio"
  }
}
```

2. **Verify Connection**:
   - Check Kilo Code shows: **Tools (14), Resources (2), Errors (0)**
   - All 14 advanced tools available with persistent SQLite database

## 🏗️ Architecture

### Working Components

```
mcp-multi-context-memory/
├── src/
│   ├── mcp_stdio_server.py      # ✅ MAIN MCP SERVER (Working)
│   ├── api/                     # ✅ FastAPI web interface
│   ├── database/                # ✅ SQLite storage backend
│   ├── graph/                   # ✅ Knowledge graph analytics
│   ├── search/                  # ✅ Full-text and semantic search
│   ├── telemetry/               # ✅ Privacy-first analytics
│   ├── context/                 # ✅ Context management
│   └── ...
├── docker-compose.yml           # ✅ Docker deployment config
├── requirements-minimal.txt     # ✅ Working dependencies
└── docs/                        # 📚 Documentation (organized)
    ├── setup/                   # Setup guides
    ├── troubleshooting/         # Debug guides  
    └── architecture/            # System design
```

### System Flow

1. **MCP Protocol**: `src/mcp_stdio_server.py` handles stdio-based MCP communication
2. **Persistent Storage**: SQLite database (`/app/data/memory.db`) survives restarts
3. **Docker Container**: `mcp-memory-system` runs the server with volume persistence
4. **Kilo Code**: Connects via Docker exec for seamless tool access
5. **Enterprise Features**: Auto-categorization, content analytics, relationship intelligence

## 🛠️ Available Tools (14 Advanced Tools)

### Core Memory Operations
| Tool | Description | Status |
|------|-------------|---------|
| `create_memory` | Create new memory entries with metadata | ✅ Working |
| `search_memories` | Basic text search across memories | ✅ Working |
| `create_context` | Organize memories into contexts | ✅ Working |

### Advanced Memory Management
| Tool | Description | Status |
|------|-------------|---------|
| `update_memory` | Update existing memories with new content | ✅ Working |
| `delete_memory` | Delete memories and their relations | ✅ Working |
| `bulk_create_memories` | Efficient bulk memory creation | ✅ Working |

### Relationship Intelligence
| Tool | Description | Status |
|------|-------------|---------|
| `create_relation` | Create typed relationships with strength | ✅ Working |
| `get_memory_relations` | Explore memory relationship networks | ✅ Working |

### Advanced Search & Discovery
| Tool | Description | Status |
|------|-------------|---------|
| `search_semantic` | AI-powered semantic search with scoring | ✅ Working |
| `analyze_knowledge_graph` | Graph analytics and insights | ✅ Working |

### Content Analytics Engine
| Tool | Description | Status |
|------|-------------|---------|
| `analyze_content` | Multi-dimensional content analysis | ✅ Working |
| `summarize_memory` | Intelligent memory summarization | ✅ Working |
| `categorize_memories` | Auto-categorization with tagging | ✅ Working |

### System Analytics
| Tool | Description | Status |
|------|-------------|---------|
| `get_memory_statistics` | Comprehensive system statistics | ✅ Working |

## 📋 Requirements

- **Python 3.8+**
- **Docker & Docker Compose** (for containerized deployment)
- **Kilo Code** (for MCP integration)

### Dependencies (Minimal)
```
mcp==1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
sqlite3 (built-in)
```

### Key Features
- **✅ Persistent Memory** - SQLite database survives VS Code restarts
- **✅ 14 Advanced Tools** - Complete memory management suite
- **✅ Relationship Intelligence** - Graph-based memory connections
- **✅ Content Analytics** - Multi-dimensional analysis engine
- **✅ Auto-categorization** - Intelligent content classification
- **✅ Knowledge Graph** - Connectivity and centrality analysis

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```env
# Database
DATABASE_PATH=./data/sqlite/memory.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# MCP
MCP_SERVER_NAME=mcm-mcpglobal
MCP_TRANSPORT=stdio
```

### Docker Configuration

The `docker-compose.yml` configures:
- Container name: `mcp-memory-system`
- Volume mapping for persistent data
- Port exposure for FastAPI interface

## 📚 Documentation

### Setup Guides
- [Kilo Integration](docs/setup/KILO_INTEGRATION.md) - Connect with Kilo Code
- [Docker Setup](docs/setup/MCP_DOCKER_SETUP.md) - Container deployment

### Troubleshooting  
- [Debug Guide](docs/troubleshooting/DEBUG_LOG.md) - Common issues
- [Fix Tools](docs/troubleshooting/FIX_TOOL_USAGE.md) - Tool problems

### Architecture
- [Project Structure](docs/architecture/project-structure.md) - Code organization
- [Implementation Summary](docs/architecture/final-implementation-summary.md) - Technical details

## 🧪 Testing

```bash
# Test MCP connection
python test_kilo_integration.py

# Start FastAPI interface
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔄 System Capabilities

### Database Backend
- **SQLite Storage**: Persistent, serverless database with ACID compliance
- **Schema Design**: Normalized tables for memories, contexts, relations, and clusters
- **Advanced Features**: Vector embeddings, versioning, access control, metadata

### API Server
- **FastAPI Framework**: High-performance async API with automatic documentation
- **REST Endpoints**: Comprehensive CRUD operations for all entities
- **WebSocket Support**: Real-time updates and bidirectional communication
- **Authentication**: Role-based access control and security measures

### MCP Protocol Implementation
- **Stdio Transport**: Efficient process-to-process communication
- **Tool Registration**: 14 advanced tools exposed to MCP clients
- **Message Handling**: JSON-RPC 2.0 compliant message processing
- **Connection Management**: Robust client connection handling

### Knowledge Graph Engine
- **Graph Analytics**: Entity and relation management with advanced metrics
- **Pathfinding**: Shortest path algorithms between related concepts
- **Connectivity Analysis**: Centrality measures and graph statistics
- **Import/Export**: Data portability with validation

### Search Capabilities
- **Full-Text Search**: Indexed search across memory content
- **Semantic Search**: AI-powered similarity scoring and ranking
- **Advanced Filtering**: Context, category, tag-based filtering
- **Performance Optimization**: Caching and indexing strategies

### Context Management
- **Project Detection**: Automatic identification of project contexts
- **Path Resolution**: Dynamic memory path resolution based on context
- **Isolation**: Ensures data separation between contexts
- **Configuration**: Context-specific settings and preferences

### Telemetry System
- **Privacy-First**: Anonymous usage statistics with zero-knowledge principles
- **Performance Monitoring**: Tracks tool usage and response times
- **Error Tracking**: Captures and reports system errors
- **User Analytics**: Understands feature adoption patterns

## 🚨 Known Issues

- Some advanced AI features require additional dependencies
- Migration tools need enhancement for large datasets  
- TypeScript MCP server is experimental

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test with the working MCP setup
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- [GitHub Issues](https://github.com/yourusername/mcp-multi-context-memory/issues)
- [Documentation](./docs/)
- [MCP Protocol Reference](https://modelcontextprotocol.io/)

## 🙏 Acknowledgments

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Kilo Code](https://kilo-code.com/) - MCP client integration
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Docker](https://docker.com/) - Containerization
