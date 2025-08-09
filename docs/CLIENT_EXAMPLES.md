# MCP Client Examples for Kilo Code

This document provides examples of how to connect to and use the MCP Multi-Context Memory System as Kilo Code.

## Prerequisites

1. Ensure the MCP server is running:
   ```bash
   docker run -d --name mcm-mcp -p 8000:8000 mcp-multi-context-memory:latest
   ```

2. Install the MCP client library:
   ```bash
   pip install mcp
   ```

## Basic Connection Example

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
import mcp

async def main():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", "mcm-mcp", "python", "-m", "src.mcp_server"]
    )
    
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the server
            await session.initialize()
            
            # List available resources
            resources = await session.list_resources()
            print("Available resources:", resources)
            
            # Read a specific memory
            if resources.get("resources"):
                first_resource = resources["resources"][0]
                memory_data = await session.read_resource({"uri": first_resource["uri"]})
                print("Memory data:", memory_data)

asyncio.run(main())
```

## Direct API Example

```python
import asyncio
import aiohttp
import json

class MCPMemoryClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def create_memory(self, title, content, context_id=None, access_level="user", metadata=None):
        """Create a new memory"""
        data = {
            "title": title,
            "content": content,
            "access_level": access_level
        }
        
        if context_id:
            data["context_id"] = context_id
        
        if metadata:
            data["memory_metadata"] = metadata
        
        async with self.session.post(f"{self.base_url}/api/memory/", json=data) as response:
            return await response.json()
    
    async def search_memories(self, query, use_semantic=False, limit=10, context_id=None, tags=None):
        """Search for memories"""
        data = {
            "query": query,
            "use_semantic": use_semantic,
            "limit": limit
        }
        
        if context_id:
            data["context_id"] = context_id
        
        if tags:
            data["tags"] = tags
        
        async with self.session.post(f"{self.base_url}/api/memory/search", json=data) as response:
            return await response.json()
    
    async def get_memory(self, memory_id):
        """Get a specific memory"""
        async with self.session.get(f"{self.base_url}/api/memory/{memory_id}") as response:
            return await response.json()
    
    async def update_memory(self, memory_id, title=None, content=None, metadata=None):
        """Update a memory"""
        data = {}
        
        if title:
            data["title"] = title
        
        if content:
            data["content"] = content
        
        if metadata:
            data["memory_metadata"] = metadata
        
        async with self.session.put(f"{self.base_url}/api/memory/{memory_id}", json=data) as response:
            return await response.json()
    
    async def delete_memory(self, memory_id):
        """Delete a memory"""
        async with self.session.delete(f"{self.base_url}/api/memory/{memory_id}") as response:
            return await response.json()
    
    async def create_context(self, name, description, access_level="user", metadata=None):
        """Create a new context"""
        data = {
            "name": name,
            "description": description,
            "access_level": access_level
        }
        
        if metadata:
            data["context_metadata"] = metadata
        
        async with self.session.post(f"{self.base_url}/api/context/", json=data) as response:
            return await response.json()
    
    async def create_relation(self, name, source_memory_id, target_memory_id, strength=0.5, metadata=None):
        """Create a relation between two memories"""
        data = {
            "name": name,
            "source_memory_id": source_memory_id,
            "target_memory_id": target_memory_id,
            "strength": strength
        }
        
        if metadata:
            data["relation_metadata"] = metadata
        
        async with self.session.post(f"{self.base_url}/api/relation/", json=data) as response:
            return await response.json()

# Usage example
async def example_usage():
    async with MCPMemoryClient() as client:
        # Create a memory
        memory = await client.create_memory(
            title="Project Meeting",
            content="Discussed the new feature requirements",
            context_id=1,
            metadata={"tags": ["meeting", "project"], "importance": 8}
        )
        print(f"Created memory: {memory}")
        
        # Search for memories
        results = await client.search_memories("project requirements", use_semantic=True)
        print(f"Search results: {results}")
        
        # Create a context
        context = await client.create_context(
            name="Work Projects",
            description="All work-related projects",
            metadata={"category": "work"}
        )
        print(f"Created context: {context}")
        
        # Create a relation
        relation = await client.create_relation(
            name="related_to",
            source_memory_id=memory["id"],
            target_memory_id=2,  # Another memory ID
            strength=0.8
        )
        print(f"Created relation: {relation}")

asyncio.run(example_usage())
```

## MCP Tool Usage Example

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
import mcp

async def use_mcp_tools():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", "mcm-mcp", "python", "-m", "src.mcp_server"]
    )
    
    async with mcp.stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the server
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", tools)
            
            # Use the create_memory tool
            if "create_memory" in [tool["name"] for tool in tools.get("tools", [])]:
                result = await session.call_tool("create_memory", {
                    "title": "Test Memory",
                    "content": "This is a test memory created via MCP tool",
                    "access_level": "user",
                    "memory_metadata": {
                        "tags": ["test", "mcp"],
                        "source": "tool_example"
                    }
                })
                print("Tool result:", result)
            
            # Use the search_memories tool
            if "search_memories" in [tool["name"] for tool in tools.get("tools", [])]:
                result = await session.call_tool("search_memories", {
                    "query": "test memory",
                    "use_semantic": True,
                    "limit": 5
                })
                print("Search result:", result)

asyncio.run(use_mcp_tools())
```

## WebSocket Example for Real-time Updates

```python
import asyncio
import websockets
import json

async def websocket_example():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Send a message
        await websocket.send(json.dumps({"type": "ping", "data": "Hello Server"}))
        
        # Receive messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received message: {data}")
            
            # Handle different message types
            if data.get("type") == "memory_created":
                print(f"New memory created: {data['memory']}")
            elif data.get("type") == "memory_updated":
                print(f"Memory updated: {data['memory']}")
            elif data.get("type") == "memory_deleted":
                print(f"Memory deleted: {data['memory_id']}")

asyncio.run(websocket_example())
```

## Kilo Code Integration Example

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
import mcp

class KiloCodeMemoryIntegration:
    def __init__(self):
        self.session = None
        self.connected = False
    
    async def connect(self):
        """Connect to the MCP memory server"""
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcm-mcp", "python", "-m", "src.mcp_server"]
        )
        
        self.session = await mcp.stdio_client(server_params)
        self.client_session = ClientSession(self.session[0], self.session[1])
        await self.client_session.initialize()
        self.connected = True
    
    async def disconnect(self):
        """Disconnect from the MCP memory server"""
        if self.session:
            await self.client_session.close()
            self.session[0].close()
            self.session[1].close()
            self.connected = False
    
    async def store_knowledge(self, title, content, context=None, tags=None, importance=5):
        """Store knowledge in the memory system"""
        if not self.connected:
            await self.connect()
        
        metadata = {}
        if tags:
            metadata["tags"] = tags
        if importance:
            metadata["importance"] = importance
        
        if context:
            metadata["context"] = context
        
        result = await self.client_session.call_tool("create_memory", {
            "title": title,
            "content": content,
            "access_level": "user",
            "memory_metadata": metadata
        })
        
        return result
    
    async def retrieve_knowledge(self, query, use_semantic=True, limit=5):
        """Retrieve knowledge from the memory system"""
        if not self.connected:
            await self.connect()
        
        result = await self.client_session.call_tool("search_memories", {
            "query": query,
            "use_semantic": use_semantic,
            "limit": limit
        })
        
        return result
    
    async def create_knowledge_context(self, name, description, category=None):
        """Create a context for organizing knowledge"""
        if not self.connected:
            await self.connect()
        
        metadata = {}
        if category:
            metadata["category"] = category
        
        result = await self.client_session.call_tool("create_context", {
            "name": name,
            "description": description,
            "access_level": "user",
            "context_metadata": metadata
        })
        
        return result
    
    async def relate_knowledge(self, source_title, target_title, relation_type="related_to", strength=0.7):
        """Create a relationship between two pieces of knowledge"""
        if not self.connected:
            await self.connect()
        
        # First, find the memories by title
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
        
        result = await self.client_session.call_tool("create_relation", {
            "name": relation_type,
            "source_memory_id": source_id,
            "target_memory_id": target_id,
            "strength": strength
        })
        
        return result

# Usage example for Kilo Code
async def kilo_code_example():
    memory_integration = KiloCodeMemoryIntegration()
    
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
        await memory_integration.create_knowledge_context(
            name="Technology Concepts",
            description="Fundamental technology concepts",
            category="education"
        )
        
        # Relate knowledge
        await memory_integration.relate_knowledge(
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

asyncio.run(kilo_code_example())
```

## Running the Examples

1. Make sure the MCP server is running in Docker:
   ```bash
   docker run -d --name mcm-mcp -p 8000:8000 mcp-multi-context-memory:latest
   ```

2. Install required dependencies:
   ```bash
   pip install mcp aiohttp
   ```

3. Save the examples to Python files and run them:
   ```bash
   python basic_connection.py
   python direct_api.py
   python mcp_tools.py
   python websocket_example.py
   python kilo_code_integration.py
   ```

These examples provide a comprehensive guide for integrating with the MCP Multi-Context Memory System as Kilo Code, covering various connection methods and usage patterns.