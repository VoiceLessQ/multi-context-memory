#!/usr/bin/env python3
"""
MCP Server for MCP Multi-Context Memory System

This module implements the Model Context Protocol (MCP) server for the
MCP Multi-Context Memory System, allowing AI applications to interact
with the memory system.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.database.enhanced_memory_db import EnhancedMemoryDB
from src.schemas.memory import MemoryCreate, MemoryUpdate
from src.schemas.context import ContextCreate
from src.schemas.relation import RelationCreate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/mcp_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global database instance
db = EnhancedMemoryDB()

# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass

manager = ConnectionManager()

class MCPServer:
    def __init__(self):
        self.db = db
        self.app = FastAPI(title="MCP Multi-Context Memory Server", version="1.0.0")
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
                    # Handle incoming WebSocket messages if needed
                    await manager.send_personal_message(f"Message received: {data}", websocket)
            except WebSocketDisconnect:
                manager.disconnect(websocket)

        # MCP Resources
        @self.app.get("/mcp/resources")
        async def list_resources():
            """List available MCP resources"""
            try:
                # Get all memories as resources
                memories = await self.db.get_memories()
                resources = []
                
                for memory in memories:
                    resources.append({
                        "uri": f"memory://{memory['id']}",
                        "name": memory['title'],
                        "description": memory['content'][:100] + "..." if len(memory['content']) > 100 else memory['content'],
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
                    memory = await self.db.get_memory(memory_id)
                    
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
                                "use_semantic": {"type": "boolean", "description": "Use semantic search"},
                                "limit": {"type": "integer", "description": "Maximum number of results"},
                                "context_id": {"type": "integer", "description": "Filter by context ID"},
                                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"}
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
                                "access_level": {"type": "string", "description": "Access level"},
                                "context_metadata": {"type": "object", "description": "Additional metadata"}
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
                                "strength": {"type": "number", "description": "Relation strength (0-1)"},
                                "relation_metadata": {"type": "object", "description": "Additional metadata"}
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
                    memory_data = MemoryCreate(**params)
                    memory = await self.db.create_memory(memory_data)
                    
                    # Broadcast update
                    await manager.broadcast(json.dumps({
                        "type": "memory_created",
                        "memory": memory
                    }))
                    
                    return {"result": memory}
                
                elif tool_name == "search_memories":
                    # Build search parameters
                    search_params = {
                        "query": params["query"],
                        "use_semantic": params.get("use_semantic", False),
                        "limit": params.get("limit", 10)
                    }
                    
                    if "context_id" in params:
                        search_params["context_id"] = params["context_id"]
                    
                    if "tags" in params:
                        search_params["tags"] = params["tags"]
                    
                    memories = await self.db.search_memories(**search_params)
                    return {"result": memories}
                
                elif tool_name == "create_context":
                    context_data = ContextCreate(**params)
                    context = await self.db.create_context(context_data)
                    return {"result": context}
                
                elif tool_name == "create_relation":
                    relation_data = RelationCreate(**params)
                    relation = await self.db.create_relation(relation_data)
                    return {"result": relation}
                
                else:
                    raise HTTPException(status_code=400, detail="Unknown tool")
            
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Legacy API endpoints for backward compatibility
        @self.app.post("/api/memory/")
        async def create_memory_endpoint(memory: MemoryCreate):
            memory = await self.db.create_memory(memory)
            
            # Broadcast update
            await manager.broadcast(json.dumps({
                "type": "memory_created",
                "memory": memory
            }))
            
            return memory

        @self.app.get("/api/memory/")
        async def get_memories_endpoint(
            skip: int = 0,
            limit: int = 100,
            context_id: Optional[int] = None,
            tags: Optional[List[str]] = None
        ):
            memories = await self.db.get_memories(
                skip=skip,
                limit=limit,
                context_id=context_id,
                tags=tags
            )
            return memories

        @self.app.get("/api/memory/{memory_id}")
        async def get_memory_endpoint(memory_id: int):
            memory = await self.db.get_memory(memory_id)
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            return memory

        @self.app.put("/api/memory/{memory_id}")
        async def update_memory_endpoint(memory_id: int, memory: MemoryUpdate):
            updated_memory = await self.db.update_memory(memory_id, memory)
            if not updated_memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            # Broadcast update
            await manager.broadcast(json.dumps({
                "type": "memory_updated",
                "memory": updated_memory
            }))
            
            return updated_memory

        @self.app.delete("/api/memory/{memory_id}")
        async def delete_memory_endpoint(memory_id: int):
            deleted = await self.db.delete_memory(memory_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            # Broadcast update
            await manager.broadcast(json.dumps({
                "type": "memory_deleted",
                "memory_id": memory_id
            }))
            
            return {"message": "Memory deleted successfully"}

        @self.app.post("/api/memory/search")
        async def search_memories_endpoint(
            query: str,
            use_semantic: bool = False,
            limit: int = 10,
            context_id: Optional[int] = None,
            tags: Optional[List[str]] = None
        ):
            memories = await self.db.search_memories(
                query=query,
                use_semantic=use_semantic,
                limit=limit,
                context_id=context_id,
                tags=tags
            )
            return memories

        @self.app.post("/api/context/")
        async def create_context_endpoint(context: ContextCreate):
            context = await self.db.create_context(context)
            return context

        @self.app.get("/api/context/")
        async def get_contexts_endpoint():
            contexts = await self.db.get_contexts()
            return contexts

        @self.app.get("/api/context/{context_id}")
        async def get_context_endpoint(context_id: int):
            context = await self.db.get_context(context_id)
            if not context:
                raise HTTPException(status_code=404, detail="Context not found")
            return context

        @self.app.post("/api/relation/")
        async def create_relation_endpoint(relation: RelationCreate):
            relation = await self.db.create_relation(relation)
            return relation

        @self.app.get("/api/relation/")
        async def get_relations_endpoint():
            relations = await self.db.get_relations()
            return relations

        @self.app.get("/api/relation/{relation_id}")
        async def get_relation_endpoint(relation_id: int):
            relation = await self.db.get_relation(relation_id)
            if not relation:
                raise HTTPException(status_code=404, detail="Relation not found")
            return relation

        @self.app.get("/api/memory/{memory_id}/relations")
        async def get_memory_relations_endpoint(memory_id: int):
            relations = await self.db.get_memory_relations(memory_id)
            return relations

        @self.app.get("/api/context/{context_id}/memories")
        async def get_context_memories_endpoint(context_id: int):
            memories = await self.db.get_context_memories(context_id)
            return memories

async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting MCP Multi-Context Memory Server")
    
    # Initialize database
    try:
        await db.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        sys.exit(1)
    
    # Create the MCP server instance
    mcp_server = MCPServer()
    
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