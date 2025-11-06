#!/usr/bin/env python3
"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

"""
Refactored Stdio-based MCP Server using Handler Chain of Responsibility pattern.
Replaces the monolithic 845-line mcp_stdio_server.py with clean architecture.
"""

import asyncio
import json
import sys
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.refactored_memory_db import RefactoredMemoryDB
from database.models import Base
from database.session import engine, SessionLocal

# Import handlers
from .handlers.base_handler import HandlerChain, ToolRequest, ToolResponse
from .handlers.memory_handler import MemoryHandler
from .handlers.context_handler import ContextHandler
from .handlers.relations_handler import RelationsHandler
from .handlers.advanced_handler import AdvancedHandler

# Create database tables
Base.metadata.create_all(bind=engine)

# Set up logging to stderr (not stdout, which is used for MCP communication)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages MCP resources using Strategy pattern.
    Handles resource listing and reading operations.
    """
    
    def __init__(self, db: RefactoredMemoryDB):
        self.db = db
        self.resource_strategies = {
            "memory://summary": self._get_summary_resource,
            "memory://": self._get_memory_resource
        }
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources."""
        resources = []
        
        try:
            # Get memory count for summary resource
            memory_count = await self.db.get_memory_count()
            
            resources.append({
                "uri": "memory://summary",
                "name": f"Memory Summary ({memory_count})",
                "description": f"Total number of memories stored in the system: {memory_count}.",
                "mimeType": "application/json"
            })
            
        except Exception as e:
            logger.error(f"Error listing resources: {e}")
            # Return minimal resource list on error
            resources.append({
                "uri": "memory://summary",
                "name": "Memory Summary",
                "description": "System memory summary (unavailable)",
                "mimeType": "application/json"
            })
        
        return {"resources": resources}
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource."""
        try:
            if uri == "memory://summary":
                return await self._get_summary_resource()
            elif uri.startswith("memory://") and len(uri) > 9:
                memory_id_str = uri.split("://")[1]
                return await self._get_memory_resource(int(memory_id_str))
            else:
                raise ValueError(f"Unsupported resource URI: {uri}")
                
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise ValueError(f"Failed to read resource {uri}: {str(e)}")
    
    async def _get_summary_resource(self) -> Dict[str, Any]:
        """Get memory summary resource."""
        try:
            stats = await self.db.get_memory_statistics()
            
            summary_data = {
                "total_memories": stats.get("total_memories", 0),
                "category_breakdown": stats.get("categories", {}),
                "oldest_memory_date": stats.get("oldest_memory_date"),
                "newest_memory_date": stats.get("newest_memory_date"),
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "contents": [{
                    "uri": "memory://summary",
                    "mimeType": "application/json",
                    "text": json.dumps(summary_data, indent=2)
                }]
            }
            
        except Exception as e:
            logger.error(f"Error generating summary resource: {e}")
            error_data = {
                "error": "Failed to generate summary",
                "details": str(e),
                "generated_at": datetime.now().isoformat()
            }
            return {
                "contents": [{
                    "uri": "memory://summary",
                    "mimeType": "application/json",
                    "text": json.dumps(error_data, indent=2)
                }]
            }
    
    async def _get_memory_resource(self, memory_id: int) -> Dict[str, Any]:
        """Get individual memory resource."""
        memory = await self.db.get_memory_by_id(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
        
        memory_data = {
            "id": memory.id,
            "title": memory.title,
            "content": memory.content,
            "context_id": memory.context_id,
            "access_level": memory.access_level,
            "created_at": memory.created_at.isoformat(),
            "accessed_at": datetime.now().isoformat()
        }
        
        return {
            "contents": [{
                "uri": f"memory://{memory_id}",
                "mimeType": "application/json",
                "text": json.dumps(memory_data, indent=2)
            }]
        }


class MCPRequestProcessor:
    """
    Processes MCP requests using Strategy pattern.
    Handles different MCP protocol operations.
    """
    
    def __init__(self, handler_chain: HandlerChain, resource_manager: ResourceManager):
        self.handler_chain = handler_chain
        self.resource_manager = resource_manager
        self.request_handlers = {
            "initialize": self._handle_initialize,
            "resources/list": self._handle_list_resources,
            "resources/read": self._handle_read_resource,
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
            "resources/templates/list": self._handle_list_templates
        }
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process an MCP request and return response."""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method not in self.request_handlers:
                raise ValueError(f"Unknown method: {method}")
            
            handler = self.request_handlers[method]
            result = await handler(params)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }
    
    async def _handle_initialize(self, params: Dict) -> Dict:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "resources": {
                    "subscribe": True,
                    "listChanged": True
                },
                "tools": {
                    "subscribe": True,
                    "listChanged": True
                }
            },
            "serverInfo": {
                "name": "multi-context-memory-mcp-refactored",
                "version": "2.0.0",
                "architecture": "Handler Chain Pattern"
            }
        }
    
    async def _handle_list_resources(self, params: Dict) -> Dict:
        """Handle list resources request."""
        return await self.resource_manager.list_resources()
    
    async def _handle_read_resource(self, params: Dict) -> Dict:
        """Handle read resource request."""
        uri = params.get("uri")
        if not uri:
            raise ValueError("Missing required parameter: uri")
        return await self.resource_manager.read_resource(uri)
    
    async def _handle_list_tools(self, params: Dict) -> Dict:
        """Handle list tools request."""
        tool_definitions = self.handler_chain.get_all_tool_definitions()
        return {"tools": tool_definitions}
    
    async def _handle_call_tool(self, params: Dict) -> Dict:
        """Handle tool call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Missing required parameter: name")
        
        # Create tool request
        tool_request = ToolRequest(
            name=tool_name,
            arguments=arguments,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        # Process through handler chain
        response = await self.handler_chain.handle_request(tool_request)
        
        if not response.success and response.error:
            raise ValueError(response.error)
        
        return response.to_dict()
    
    async def _handle_list_templates(self, params: Dict) -> Dict:
        """Handle list resource templates request."""
        return {"resourceTemplates": []}


class RefactoredMCPStdioServer:
    """
    Refactored MCP Stdio Server using Handler Chain of Responsibility pattern.
    Replaces monolithic 845-line server with clean, modular architecture.
    """
    
    def __init__(self):
        # Initialize database
        self.db = RefactoredMemoryDB("sqlite:///./data/sqlite/memory.db", SessionLocal())
        
        # Configure database settings
        self._configure_database()
        
        # Build handler chain
        self.handler_chain = self._build_handler_chain()
        
        # Initialize resource manager and request processor
        self.resource_manager = ResourceManager(self.db)
        self.request_processor = MCPRequestProcessor(self.handler_chain, self.resource_manager)
        
        logger.info("RefactoredMCPStdioServer initialized with handler chain architecture")
    
    def _configure_database(self):
        """Configure database with optimal settings."""
        try:
            self.db.set_chunked_storage_enabled(True)
            self.db.chunk_size = 10000
            self.db.max_chunks = 100
            logger.info("Database configured successfully")
        except Exception as e:
            logger.error(f"Database configuration error: {e}")
            # Continue with defaults if configuration fails
    
    def _build_handler_chain(self) -> HandlerChain:
        """Build the handler chain using Chain of Responsibility pattern."""
        chain = HandlerChain()
        
        # Add handlers in order of processing preference
        handlers = [
            MemoryHandler(),
            ContextHandler(),
            RelationsHandler(),
            AdvancedHandler()
        ]
        
        # Configure database for all handlers and add to chain
        chain.add_handlers(handlers).configure_database(self.db)
        
        logger.info(f"Handler chain built with {len(handlers)} handlers")
        logger.info(f"Supported tools: {', '.join(chain.get_supported_tools())}")
        
        return chain
    
    async def run(self):
        """Main server loop - read from stdin, write to stdout."""
        logger.info("Starting RefactoredMCPStdioServer")
        logger.info(f"Chain info: {self.handler_chain.get_chain_info()}")
        
        try:
            while True:
                # Read a line from stdin
                line = sys.stdin.readline()
                if not line:
                    logger.info("EOF received, shutting down server")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse JSON request
                    request = json.loads(line)
                    logger.info(f"Received request: {request.get('method')}")
                    
                    # Process request through the system
                    response = await self.request_processor.process_request(request)
                    
                    # Send JSON response to stdout
                    print(json.dumps(response, default=str), flush=True)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    self._send_parse_error()
                    
                except Exception as e:
                    logger.error(f"Request processing error: {e}")
                    self._send_internal_error()
                    
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            await self._shutdown()
    
    def _send_parse_error(self):
        """Send JSON parse error response."""
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }
        print(json.dumps(error_response), flush=True)
    
    def _send_internal_error(self):
        """Send internal error response."""
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        print(json.dumps(error_response), flush=True)
    
    async def _shutdown(self):
        """Graceful shutdown cleanup."""
        try:
            logger.info("Shutting down RefactoredMCPStdioServer...")
            
            # Clear handler chain
            self.handler_chain.clear()
            
            # Close database connections if needed
            # Note: Database cleanup would be implemented here
            
            logger.info("Server shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get comprehensive server information."""
        return {
            "server": {
                "name": "RefactoredMCPStdioServer",
                "version": "2.0.0",
                "architecture": "Handler Chain + Strategy Pattern",
                "protocol_version": "2024-11-05"
            },
            "handlers": self.handler_chain.get_chain_info(),
            "database": {
                "type": "SQLite",
                "chunked_storage": True,
                "chunk_size": getattr(self.db, 'chunk_size', 10000),
                "max_chunks": getattr(self.db, 'max_chunks', 100)
            }
        }


# Factory function for server creation
def create_stdio_server() -> RefactoredMCPStdioServer:
    """Factory function to create a configured stdio server."""
    return RefactoredMCPStdioServer()


async def main():
    """Main entry point."""
    try:
        server = create_stdio_server()
        await server.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())