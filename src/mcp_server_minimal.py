#!/usr/bin/env python3
"""
Minimal MCP Server for MCP Multi-Context Memory System
This version avoids problematic dependencies and focuses on core MCP functionality.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Simple in-memory storage (bypasses database dependencies)
MEMORIES = {}
CONTEXTS = {}
RELATIONS = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MemoryCreate(BaseModel):
    title: str
    content: str
    context_id: Optional[int] = None
    access_level: str = "public"
    memory_metadata: Optional[Dict] = None

class ContextCreate(BaseModel):
    name: str
    description: str
    access_level: str = "public"
    context_metadata: Optional[Dict] = None

class RelationCreate(BaseModel):
    name: str
    source_memory_id: int
    target_memory_id: int
    strength: float = 1.0
    relation_metadata: Optional[Dict] = None

# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

class MinimalMCPServer:
    def __init__(self):
        self.app = FastAPI(title="MCP Multi-Context Memory Server (Minimal)", version="1.0.0")
        self.setup_routes()

    def setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"name": "MCP Memory System", "version": "2.0.0", "status": "running"}

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    await manager.send_personal_message(f"Message received: {data}", websocket)
            except WebSocketDisconnect:
                manager.disconnect(websocket)

        # MCP Resources
        @self.app.get("/mcp/resources")
        async def list_resources():
            """List available MCP resources"""
            try:
                resources = []
                for memory_id, memory in MEMORIES.items():
                    resources.append({
                        "uri": f"memory://{memory_id}",
                        "name": memory.get('title', f'Memory {memory_id}'),
                        "description": memory.get('content', '')[:100] + "..." if len(memory.get('content', '')) > 100 else memory.get('content', ''),
                        "mimeType": "application/json"
                    })
                return {"resources": resources}
            except Exception as e:
                logger.error(f"Error listing resources: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/mcp/resources/{resource_uri}")
        async def read_resource(resource_uri: str):
            """Read a specific MCP resource"""
            try:
                if resource_uri.startswith("memory://"):
                    memory_id = int(resource_uri.split("://")[1])
                    memory = MEMORIES.get(memory_id)
                    
                    if memory:
                        return {
                            "uri": resource_uri,
                            "contents": [{
                                "type": "text",
                                "text": json.dumps(memory, indent=2)
                            }]
                        }
                    else:
                        raise HTTPException(status_code=404, detail="Memory not found")
                else:
                    raise HTTPException(status_code=400, detail="Unsupported resource type")
            except Exception as e:
                logger.error(f"Error reading resource {resource_uri}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # MCP Tools
        @self.app.post("/mcp/tools")
        async def list_tools():
            """List available MCP tools"""
            return {
                "tools": [
                    {
                        "name": "create_memory",
                        "description": "Create a new memory entry",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Title of the memory"},
                                "content": {"type": "string", "description": "Content of the memory"},
                                "context_id": {"type": "integer", "description": "ID of the context"},
                                "access_level": {"type": "string", "description": "Access level (public, private, user)"},
                                "memory_metadata": {"type": "object", "description": "Additional metadata"}
                            },
                            "required": ["title", "content"]
                        }
                    },
                    {
                        "name": "search_memories",
                        "description": "Search for memories using various criteria",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Search query"},
                                "limit": {"type": "integer", "description": "Maximum number of results"},
                                "context_id": {"type": "integer", "description": "Filter by context ID"}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "create_context",
                        "description": "Create a new context",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Name of the context"},
                                "description": {"type": "string", "description": "Description of the context"},
                                "access_level": {"type": "string", "description": "Access level"}
                            },
                            "required": ["name", "description"]
                        }
                    },
                    {
                        "name": "create_relation",
                        "description": "Create a relation between two memories",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Name of the relation"},
                                "source_memory_id": {"type": "integer", "description": "Source memory ID"},
                                "target_memory_id": {"type": "integer", "description": "Target memory ID"},
                                "strength": {"type": "number", "description": "Relation strength (0-1)"}
                            },
                            "required": ["name", "source_memory_id", "target_memory_id"]
                        }
                    }
                ]
            }

        @self.app.post("/mcp/tools/{tool_name}")
        async def call_tool(tool_name: str, params: Dict[str, Any]):
            """Call an MCP tool"""
            try:
                if tool_name == "create_memory":
                    memory_id = len(MEMORIES) + 1
                    memory = {
                        "id": memory_id,
                        "title": params["title"],
                        "content": params["content"],
                        "context_id": params.get("context_id"),
                        "access_level": params.get("access_level", "public"),
                        "memory_metadata": params.get("memory_metadata", {}),
                        "created_at": "2025-01-01T00:00:00Z"
                    }
                    MEMORIES[memory_id] = memory
                    
                    await manager.broadcast(json.dumps({
                        "type": "memory_created",
                        "memory": memory
                    }))
                    
                    return {"result": memory}
                
                elif tool_name == "search_memories":
                    query = params["query"].lower()
                    limit = params.get("limit", 10)
                    context_id = params.get("context_id")
                    
                    results = []
                    for memory_id, memory in MEMORIES.items():
                        if context_id and memory.get("context_id") != context_id:
                            continue
                        if query in memory.get("title", "").lower() or query in memory.get("content", "").lower():
                            results.append(memory)
                        if len(results) >= limit:
                            break
                    
                    return {"result": results}
                
                elif tool_name == "create_context":
                    context_id = len(CONTEXTS) + 1
                    context = {
                        "id": context_id,
                        "name": params["name"],
                        "description": params["description"],
                        "access_level": params.get("access_level", "public"),
                        "created_at": "2025-01-01T00:00:00Z"
                    }
                    CONTEXTS[context_id] = context
                    return {"result": context}
                
                elif tool_name == "create_relation":
                    relation_id = len(RELATIONS) + 1
                    relation = {
                        "id": relation_id,
                        "name": params["name"],
                        "source_memory_id": params["source_memory_id"],
                        "target_memory_id": params["target_memory_id"],
                        "strength": params.get("strength", 1.0),
                        "created_at": "2025-01-01T00:00:00Z"
                    }
                    RELATIONS[relation_id] = relation
                    return {"result": relation}
                
                else:
                    raise HTTPException(status_code=400, detail="Unknown tool")
            
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

async def main():
    """Main entry point for the minimal MCP server"""
    logger.info("Starting Minimal MCP Multi-Context Memory Server")
    
    # Create the MCP server instance
    mcp_server = MinimalMCPServer()
    
    # Start the server
    config = uvicorn.Config(
        mcp_server.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())