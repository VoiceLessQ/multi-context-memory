# Kilo Code Integration Guide

This guide explains how to integrate Kilo Code with the MCP Multi-Context Memory System using the configuration file.

## Prerequisites

1. Ensure the MCP server is running:
   ```bash
   docker run -d --name mcm-mcp -p 8000:8000 mcp-multi-context-memory:latest
   ```

2. Install the MCP client library:
   ```bash
   pip install mcp
   ```

## Configuration

### 1. Kilo Configuration File

Create or update your Kilo configuration file (`kilo_config.json`) with the following content:

```json
{
  "mcpServers": {
    "memory-system": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcm-mcp",
        "python",
        "-m",
        "src.mcp_server"
      ],
      "env": {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "sqlite:///data/memories.db",
        "JSONL_DATA_PATH": "./data"
      }
    }
  },
  "mcpClients": {
    "memory-system": {
      "server": "memory-system",
      "capabilities": {
        "resources": [
          "memory://*"
        ],
        "tools": [
          "create_memory",
          "search_memories",
          "create_context",
          "create_relation"
        ]
      }
    }
  },
  "settings": {
    "memory-system": {
      "autoConnect": true,
      "defaultContext": "general",
      "maxResults": 10,
      "enableSemanticSearch": true,
      "defaultTags": ["kilo", "memory-system"],
      "logLevel": "INFO"
    }
  }
}
```

### 2. Configuration Options

#### MCP Server Configuration
- `command`: The command to start the MCP server (in this case, Docker)
- `args`: Arguments for the Docker command
- `env`: Environment variables to pass to the container

#### MCP Client Configuration
- `server`: References the server defined in `mcpServers`
- `capabilities`: Specifies which resources and tools the client can access

#### Settings
- `autoConnect`: Automatically connect to the memory system
- `defaultContext`: Default context for new memories
- `maxResults`: Maximum number of results for searches
- `enableSemanticSearch`: Enable semantic search by default
- `defaultTags`: Default tags to apply to new memories
- `logLevel`: Logging level for the integration

## Usage Examples

### 1. Basic Connection

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
import mcp

async def connect_to_memory_system():
    # Load configuration from kilo_config.json
    with open("kilo_config.json", "r") as f:
        config = json.load(f)
    
    # Get server configuration
    server_config = config["mcpServers"]["memory-system"]
    
    # Create server parameters
    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"]
    )
    
    # Connect to the server
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to memory system")
            return session

asyncio.run(connect_to_memory_system())
```

### 2. Storing Knowledge

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
import mcp

async def store_knowledge(title, content, tags=None, context=None):
    # Load configuration
    with open("kilo_config.json", "r") as f:
        config = json.load(f)
    
    server_config = config["mcpServers"]["memory-system"]
    settings = config["settings"]["memory-system"]
    
    # Connect to server
    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"]
    )
    
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Prepare memory data
            memory_data = {
                "title": title,
                "content": content,
                "access_level": "user",
                "memory_metadata": {
                    "tags": tags or settings["defaultTags"],
                    "context": context or settings["defaultContext"]
                }
            }
            
            # Create memory
            result = await session.call_tool("create_memory", memory_data)
            print(f"Stored knowledge: {result}")
            return result

# Example usage
asyncio.run(store_knowledge(
    title="Python Programming",
    content="Python is a high-level programming language",
    tags=["programming", "python"],
    context="technology"
))
```

### 3. Retrieving Knowledge

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
import mcp

async def retrieve_knowledge(query, use_semantic=None, limit=None):
    # Load configuration
    with open("kilo_config.json", "r") as f:
        config = json.load(f)
    
    server_config = config["mcpServers"]["memory-system"]
    settings = config["settings"]["memory-system"]
    
    # Use settings defaults if not specified
    if use_semantic is None:
        use_semantic = settings["enableSemanticSearch"]
    if limit is None:
        limit = settings["maxResults"]
    
    # Connect to server
    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"]
    )
    
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Search for memories
            result = await session.call_tool("search_memories", {
                "query": query,
                "use_semantic": use_semantic,
                "limit": limit
            })
            
            print(f"Retrieved knowledge: {result}")
            return result

# Example usage
asyncio.run(retrieve_knowledge("programming language"))
```

### 4. Creating Contexts

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
import mcp

async def create_context(name, description, category=None):
    # Load configuration
    with open("kilo_config.json", "r") as f:
        config = json.load(f)
    
    server_config = config["mcpServers"]["memory-system"]
    
    # Connect to server
    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"]
    )
    
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Create context
            context_data = {
                "name": name,
                "description": description,
                "access_level": "user"
            }
            
            if category:
                context_data["context_metadata"] = {"category": category}
            
            result = await session.call_tool("create_context", context_data)
            print(f"Created context: {result}")
            return result

# Example usage
asyncio.run(create_context(
    name="Work Projects",
    description="All work-related projects",
    category="work"
))
```

### 5. Creating Relations

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
import mcp

async def create_relation(source_title, target_title, relation_type="related_to", strength=0.7):
    # Load configuration
    with open("kilo_config.json", "r") as f:
        config = json.load(f)
    
    server_config = config["mcpServers"]["memory-system"]
    
    # Connect to server
    server_params = StdioServerParameters(
        command=server_config["command"],
        args=server_config["args"]
    )
    
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Find memories by title
            source_result = await session.call_tool("search_memories", {
                "query": source_title,
                "use_semantic": False,
                "limit": 1
            })
            
            target_result = await session.call_tool("search_memories", {
                "query": target_title,
                "use_semantic": False,
                "limit": 1
            })
            
            if not source_result.get("result") or not target_result.get("result"):
                print("Could not find one or both memories")
                return None
            
            source_id = source_result["result"][0]["id"]
            target_id = target_result["result"][0]["id"]
            
            # Create relation
            relation_data = {
                "name": relation_type,
                "source_memory_id": source_id,
                "target_memory_id": target_id,
                "strength": strength
            }
            
            result = await session.call_tool("create_relation", relation_data)
            print(f"Created relation: {result}")
            return result

# Example usage
asyncio.run(create_relation(
    source_title="Python Programming",
    target_title="Machine Learning",
    relation_type="enables",
    strength=0.8
))
```

### 6. Complete Integration Class

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
import mcp

class KiloMemoryIntegration:
    def __init__(self, config_path="kilo_config.json"):
        self.config_path = config_path
        self.config = None
        self.session = None
        self.connected = False
    
    async def load_config(self):
        """Load configuration from file"""
        with open(self.config_path, "r") as f:
            self.config = json.load(f)
    
    async def connect(self):
        """Connect to the memory system"""
        if not self.config:
            await self.load_config()
        
        server_config = self.config["mcpServers"]["memory-system"]
        
        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config["args"]
        )
        
        self.session = await mcp.stdio_client(server_params)
        self.client_session = ClientSession(self.session[0], self.session[1])
        await self.client_session.initialize()
        self.connected = True
    
    async def disconnect(self):
        """Disconnect from the memory system"""
        if self.session:
            await self.client_session.close()
            self.session[0].close()
            self.session[1].close()
            self.connected = False
    
    async def store_knowledge(self, title, content, tags=None, context=None, importance=None):
        """Store knowledge in the memory system"""
        if not self.connected:
            await self.connect()
        
        settings = self.config["settings"]["memory-system"]
        
        memory_data = {
            "title": title,
            "content": content,
            "access_level": "user",
            "memory_metadata": {
                "tags": tags or settings["defaultTags"],
                "context": context or settings["defaultContext"]
            }
        }
        
        if importance:
            memory_data["memory_metadata"]["importance"] = importance
        
        result = await self.client_session.call_tool("create_memory", memory_data)
        return result
    
    async def retrieve_knowledge(self, query, use_semantic=None, limit=None):
        """Retrieve knowledge from the memory system"""
        if not self.connected:
            await self.connect()
        
        settings = self.config["settings"]["memory-system"]
        
        if use_semantic is None:
            use_semantic = settings["enableSemanticSearch"]
        if limit is None:
            limit = settings["maxResults"]
        
        result = await self.client_session.call_tool("search_memories", {
            "query": query,
            "use_semantic": use_semantic,
            "limit": limit
        })
        
        return result
    
    async def create_context(self, name, description, category=None):
        """Create a context for organizing knowledge"""
        if not self.connected:
            await self.connect()
        
        context_data = {
            "name": name,
            "description": description,
            "access_level": "user"
        }
        
        if category:
            context_data["context_metadata"] = {"category": category}
        
        result = await self.client_session.call_tool("create_context", context_data)
        return result
    
    async def create_relation(self, source_title, target_title, relation_type="related_to", strength=0.7):
        """Create a relationship between two pieces of knowledge"""
        if not self.connected:
            await self.connect()
        
        # Find memories by title
        source_result = await self.client_session.call_tool("search_memories", {
            "query": source_title,
            "use_semantic": False,
            "limit": 1
        })
        
        target_result = await self.client_session.call_tool("search_memories", {
            "query": target_title,
            "use_semantic": False,
            "limit": 1
        })
        
        if not source_result.get("result") or not target_result.get("result"):
            return None
        
        source_id = source_result["result"][0]["id"]
        target_id = target_result["result"][0]["id"]
        
        # Create relation
        relation_data = {
            "name": relation_type,
            "source_memory_id": source_id,
            "target_memory_id": target_id,
            "strength": strength
        }
        
        result = await self.client_session.call_tool("create_relation", relation_data)
        return result

# Usage example
async def kilo_integration_example():
    memory_integration = KiloMemoryIntegration()
    
    try:
        # Connect to the memory system
        await memory_integration.connect()
        
        # Store some knowledge
        await memory_integration.store_knowledge(
            title="Python Programming",
            content="Python is a high-level programming language known for its readability",
            tags=["programming", "python", "language"],
            importance=8
        )
        
        # Store more knowledge
        await memory_integration.store_knowledge(
            title="Machine Learning",
            content="Machine learning is a subset of artificial intelligence",
            tags=["ai", "ml", "technology"],
            importance=9
        )
        
        # Create a context
        await memory_integration.create_context(
            name="Technology Concepts",
            description="Fundamental technology concepts",
            category="education"
        )
        
        # Relate knowledge
        await memory_integration.create_relation(
            source_title="Python Programming",
            target_title="Machine Learning",
            relation_type="enables",
            strength=0.8
        )
        
        # Retrieve knowledge
        results = await memory_integration.retrieve_knowledge("programming language")
        print("Retrieved knowledge:", results)
        
    finally:
        # Disconnect
        await memory_integration.disconnect()

asyncio.run(kilo_integration_example())
```

## Setup Instructions

1. **Save the Configuration**
   - Save the `kilo_config.json` file in your Kilo Code project directory
   - Modify the configuration as needed for your setup

2. **Install Dependencies**
   ```bash
   pip install mcp
   ```

3. **Run the Memory System**
   ```bash
   docker run -d --name mcm-mcp -p 8000:8000 mcp-multi-context-memory:latest
   ```

4. **Use the Integration**
   - Import the `KiloMemoryIntegration` class
   - Initialize it with your configuration file
   - Use the methods to store and retrieve knowledge

This integration provides a seamless way for Kilo Code to connect to and use the MCP Multi-Context Memory System, with configurable settings to match your specific needs.