# MCP Multi-Context Memory System - Usage Guide

## Overview

The MCP Multi-Context Memory System is a hybrid storage solution that combines SQLite with JSONL to provide a robust memory management system for AI applications. It supports storing, retrieving, and relating memories across different contexts with advanced features like semantic search and relationship mapping.

## Key Features

### 1. Hybrid Storage Architecture
- **SQLite Backend**: Structured storage for memories, contexts, and relations
- **JSONL Compatibility**: Maintains backward compatibility with existing data
- **Efficient Querying**: Fast retrieval with indexing capabilities

### 2. Advanced Memory Management
- **Structured Storage**: Memories with metadata, tags, and access controls
- **Context Organization**: Group memories by projects, topics, or categories
- **Relationship Mapping**: Create and manage connections between memories
- **Semantic Search**: Find memories based on meaning, not just keywords

### 3. AI Integration
- **MCP Protocol**: Native support for Model Context Protocol
- **Vector Embeddings**: Automatic generation for semantic search
- **Knowledge Graphs**: Build interconnected knowledge networks

## Quick Start

### 1. Access the API

The system is running on `http://localhost:8000` and provides the following endpoints:

- **Health Check**: `GET /health`
- **Root Info**: `GET /`

### 2. API Documentation

Once the system is fully implemented, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Core Features

### 1. Memory Management

Store and retrieve memories with metadata:

```python
# Example: Create a memory
POST /api/memory/
{
    "title": "Project Meeting",
    "content": "Discussed the new feature requirements",
    "context_id": 1,
    "access_level": "user",
    "memory_metadata": {
        "tags": ["meeting", "project"],
        "importance": 8,
        "created_by": "user123"
    }
}
```

### 2. Context Management

Organize memories into contexts:

```python
# Example: Create a context
POST /api/context/
{
    "name": "Work Projects",
    "description": "All work-related memories",
    "access_level": "user",
    "context_metadata": {
        "category": "work",
        "priority": "high"
    }
}
```

### 3. Relation Management

Create relationships between memories:

```python
# Example: Create a relation
POST /api/relation/
{
    "name": "related_to",
    "source_memory_id": 1,
    "target_memory_id": 2,
    "strength": 0.8,
    "relation_metadata": {
        "type": "reference",
        "description": "This memory references the other"
    }
}
```

### 4. Semantic Search

Search memories using semantic similarity:

```python
# Example: Semantic search
POST /api/memory/search
{
    "query": "project requirements",
    "use_semantic": true,
    "limit": 10,
    "filters": {
        "context_id": 1,
        "access_level": "user"
    }
}
```

## Integration with AI Applications

### 1. As an MCP Server

The system can be used as an MCP (Model Context Protocol) server:

```python
# Example MCP client connection
import asyncio
from mcp import ClientSession, StdioServerParameters
import mcp

async def main():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", "mcm-prod", "python", "-m", mcp_server"]
    )
    
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the server
            await session.initialize()
            
            # List available resources
            resources = await session.list_resources()
            print("Available resources:", resources)
            
            # Read a resource
            memory_data = await session.read_resource({"uri": "memory://1"})
            print("Memory data:", memory_data)
            
            # Create a new memory
            await session.create_resource({
                "uri": "memory://new",
                "name": "New Memory",
                "description": "A new memory entry"
            })

asyncio.run(main())
```

### 2. Direct API Usage

```python
import requests
import json

# Create a memory
response = requests.post("http://localhost:8000/api/memory/", json={
    "title": "Test Memory",
    "content": "This is a test memory",
    "access_level": "user"
})

if response.status_code == 200:
    memory = response.json()
    print(f"Created memory with ID: {memory['id']}")

# Search memories
search_response = requests.post("http://localhost:8000/api/memory/search", json={
    "query": "test memory",
    "use_semantic": True
})

if search_response.status_code == 200:
    results = search_response.json()
    print(f"Found {len(results)} memories")
```

### 3. Knowledge Graph Integration

```python
# Create interconnected memories
memories = [
    {
        "title": "Machine Learning Basics",
        "content": "Introduction to ML concepts",
        "tags": ["ml", "ai", "basics"]
    },
    {
        "title": "Neural Networks",
        "content": "Deep learning architecture",
        "tags": ["ml", "ai", "neural-networks"]
    },
    {
        "title": "Natural Language Processing",
        "content": "NLP techniques and applications",
        "tags": ["ml", "ai", "nlp"]
    }
]

# Create memories and establish relationships
created_memories = []
for memory_data in memories:
    response = requests.post("http://localhost:8000/api/memory/", json=memory_data)
    if response.status_code == 200:
        created_memories.append(response.json())

# Create relationships between ML concepts
if len(created_memories) >= 2:
    requests.post("http://localhost:8000/api/relation/", json={
        "name": "builds_on",
        "source_memory_id": created_memories[0]["id"],
        "target_memory_id": created_memories[1]["id"],
        "strength": 0.9
    })
```

## Docker Management

### Basic Commands

```bash
# View running containers
docker ps

# View logs
docker logs mcm-prod

# Stop the container
docker stop mcm-prod

# Start the container
docker start mcm-prod

# Restart the container
docker restart mcm-prod

# Remove the container
docker rm -f mcm-prod

# View resource usage
docker stats mcm-prod
```

### Environment Variables

The system can be configured using environment variables:

```bash
# Run with custom configuration
docker run -d --name mcm-custom \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL="sqlite:///data/memories.db" \
  -e JSONL_DATA_PATH="./data" \
  -e LOG_LEVEL="INFO" \
  -e MAX_MEMORY_SIZE=10000 \
  mcp-multi-context-memory:latest
```

### Health Monitoring

```bash
# Check service health
curl http://localhost:8000/health

# Check container health status
docker inspect mcm-prod --format='{{.State.Health.Status}}'

# View recent logs
docker logs --tail 50 mcm-prod
```

## Data Persistence

### 1. SQLite Database

- **Location**: `/app/data/memories.db`
- **Stores**: Structured data including memories, contexts, and relations
- **Features**: Automatic indexing, foreign key constraints, and ACID compliance
- **Backup**: Automatically created on first run

### 2. JSONL Storage

- **Location**: `/app/data/`
- **Purpose**: Maintains backward compatibility with the original JSONL format
- **Usage**: Used for storing raw memory data and export functionality

### 3. Data Migration

```bash
# Migrate data from JSONL to SQLite
docker exec mcm-prod python migrate_to_enhanced.py

# Export data to JSONL
docker exec mcm-prod python -c "
from src.database.enhanced_memory_db import EnhancedMemoryDB
db = EnhancedMemoryDB()
db.export_to_jsonl('/app/data/exported_memories.jsonl')
"
```

## Development

### 1. Access the Container

```bash
# Get a shell in the running container
docker exec -it mcm-prod /bin/bash

# View application logs
docker exec mcm-prod tail -f /app/logs/app.log

# Access the database
docker exec -it mcm-prod sqlite3 /app/data/memories.db
```

### 2. Testing

```bash
# Run tests inside the container
docker exec mcm-prod python -m pytest

# Run specific test file
docker exec mcm-prod python -m pytest tests/test_memory.py

# Run with coverage
docker exec mcm-prod python -m pytest --cov=src
```

### 3. Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcp-multi-context-memory

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Advanced Features

### 1. Semantic Search with Embeddings

The system automatically generates embeddings for memories:

```python
# Search with semantic similarity
response = requests.post("http://localhost:8000/api/memory/search", json={
    "query": "machine learning algorithms",
    "use_semantic": True,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "limit": 5
})
```

### 2. Memory Relationships

Build knowledge graphs with interconnected memories:

```python
# Create complex relationships
relationships = [
    {
        "name": "contradicts",
        "source_memory_id": 1,
        "target_memory_id": 2,
        "strength": 0.7,
        "metadata": {"confidence": 0.8}
    },
    {
        "name": "expands_on",
        "source_memory_id": 1,
        "target_memory_id": 3,
        "strength": 0.9,
        "metadata": {"scope": "detailed"}
    }
]

for rel in relationships:
    requests.post("http://localhost:8000/api/relation/", json=rel)
```

### 3. Context-Based Organization

Organize memories by context for better management:

```python
# Create project contexts
projects = [
    {"name": "AI Research", "description": "AI and ML research projects"},
    {"name": "Development", "description": "Software development tasks"},
    {"name": "Personal", "description": "Personal notes and ideas"}
]

for project in projects:
    requests.post("http://localhost:8000/api/context/", json=project)
```

## Troubleshooting

### 1. Common Issues

**Service Not Starting**
```bash
# Check logs
docker logs mcm-prod

# Restart the container
docker restart mcm-prod

# Check for port conflicts
netstat -ano | findstr :8000
```

**Database Issues**
```bash
# Check database integrity
docker exec mcm-prod sqlite3 /app/data/memories.db "PRAGMA integrity_check;"

# Rebuild database if needed
docker exec mcm-prod rm /app/data/memories.db
docker restart mcm-prod
```

**Performance Issues**
```bash
# Monitor resource usage
docker stats mcm-prod

# Check database size
docker exec mcm-prod du -h /app/data/memories.db

# Optimize database
docker exec mcm-prod sqlite3 /app/data/memories.db "VACUUM;"
```

### 2. Debug Mode

Run the container in debug mode:

```bash
docker run -d --name mcm-debug \
  -p 8000:8000 \
  -e ENVIRONMENT=development \
  -e LOG_LEVEL=DEBUG \
  -e DEBUG=True \
  mcp-multi-context-memory:latest
```

## Best Practices

### 1. Memory Management

- Use descriptive titles and content
- Add relevant tags for better searchability
- Set appropriate access levels
- Regularly review and update memories

### 2. Context Organization

- Create meaningful context names
- Use hierarchical contexts when appropriate
- Set consistent access levels
- Regularly clean up unused contexts

### 3. Relationship Building

- Use meaningful relationship names
- Set appropriate strength values
- Add metadata for context
- Avoid creating circular references

### 4. Performance Optimization

- Use semantic search for complex queries
- Limit result sets with appropriate limits
- Use filters to narrow down searches
- Regular maintenance of the database

## Next Steps

1. **Complete API Implementation**: The current minimal version only includes health checks. The full API implementation needs to be completed.

2. **MCP Protocol Integration**: The system needs to be fully integrated with the MCP protocol for seamless AI application integration.

3. **VS Code Extension**: The VS Code extension needs to be updated to work with the new system.

4. **Data Migration**: If you have existing JSONL data, use the migration tools to transfer data to SQLite.

5. **Authentication**: Implement user authentication and authorization for multi-user support.

6. **Advanced Features**: Implement additional features like memory versioning, automated tagging, and intelligent recommendations.

For more detailed information, refer to the project documentation in the `docs/` directory.