#!/usr/bin/env python3
"""
Stdio-based MCP Server for MCP Multi-Context Memory System
This implements the proper MCP protocol over stdio transport.
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

from src.database.enhanced_memory_db import EnhancedMemoryDB
from src.database.models import Base
from src.database.session import engine, SessionLocal

# Create database tables
Base.metadata.create_all(bind=engine)

# Set up logging to stderr (not stdout, which is used for MCP communication)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

class MCPStdioServer:
    def __init__(self):
        self.request_id = 0
        # Initialize database on startup
        self.db = EnhancedMemoryDB("sqlite:///./data/memories.db", SessionLocal())
        self.db.set_chunked_storage_enabled(True)
        self.db.chunk_size = 10000
        self.db.max_chunks = 100

    async def handle_initialize(self, params: Dict) -> Dict:
        """Handle MCP initialize request"""
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
                "name": "multi-context-memory-mcp",
                "version": "1.0.0"
            }
        }

    async def handle_list_resources(self) -> Dict:
        """Handle list resources request"""
        resources = []
        
        # Get memory count from enhanced database
        memory_count = await self.db.get_memory_count()
        
        resources.append({
            "uri": "memory://summary",
            "name": f"Resources ({memory_count})",
            "description": f"Total number of memories stored in the system: {memory_count}.",
            "mimeType": "application/json"
        })
        
        return {"resources": resources}

    async def handle_read_resource(self, uri: str) -> Dict:
        """Handle read resource request"""
        if uri == "memory://summary":
            # Get summary data from enhanced database
            stats = await self.db.get_memory_statistics()
            
            summary_data = {
                "total_memories": stats.get("total_memories", 0),
                "category_breakdown": stats.get("categories", {}),
                "oldest_memory_date": stats.get("oldest_memory_date"),
                "newest_memory_date": stats.get("newest_memory_date")
            }
            
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(summary_data, indent=2)
                }]
            }
        elif uri.startswith("memory://"):
            # Existing logic for individual memory resources
            memory_id = int(uri.split("://")[1])
            
            memory = await self.db.get_memory_by_id(memory_id)
            if memory:
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps({
                            "id": memory.id,
                            "title": memory.title,
                            "content": memory.content,
                            "context_id": memory.context_id,
                            "access_level": memory.access_level,
                            "created_at": memory.created_at.isoformat()
                        }, indent=2)
                    }]
                }
            else:
                raise ValueError(f"Memory {memory_id} not found")
        else:
            raise ValueError(f"Unsupported resource URI: {uri}")

    async def handle_list_tools(self) -> Dict:
        """Handle list tools request"""
        return {
            "tools": [
                {
                    "name": "create_context",
                    "description": "Create a new context",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Context name"},
                            "description": {"type": "string", "description": "Context description"}
                        },
                        "required": ["name", "description"]
                    }
                },
                {
                    "name": "create_memory",
                    "description": "Create a new memory entry",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the memory"},
                            "content": {"type": "string", "description": "Content of the memory"},
                            "context_id": {"type": "integer", "description": "ID of the context"},
                            "access_level": {"type": "string", "description": "Access level"}
                        },
                        "required": ["title", "content"]
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
                            "strength": {"type": "number", "description": "Relation strength (0-1)", "default": 1.0},
                            "relation_metadata": {"type": "object", "description": "Additional metadata"}
                        },
                        "required": ["name", "source_memory_id", "target_memory_id"]
                    }
                },
                {
                    "name": "get_memory_relations",
                    "description": "Get all relations for a specific memory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to get relations for"}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "search_semantic",
                    "description": "Perform AI-powered semantic search across memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum results", "default": 10},
                            "context_id": {"type": "integer", "description": "Filter by context ID"},
                            "similarity_threshold": {"type": "number", "description": "Minimum similarity score (0-1)", "default": 0.3}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "bulk_create_memories",
                    "description": "Create multiple memories at once",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memories": {
                                "type": "array",
                                "description": "Array of memory objects",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "content": {"type": "string"},
                                        "tags": {"type": "string"},
                                        "category": {"type": "string"},
                                        "importance": {"type": "integer", "default": 1}
                                    },
                                    "required": ["title", "content"]
                                }
                            }
                        },
                        "required": ["memories"]
                    }
                },
                {
                    "name": "get_memory_statistics",
                    "description": "Get comprehensive statistics about memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "include_content_analysis": {"type": "boolean", "description": "Include content analysis", "default": True}
                        },
                        "required": []
                    }
                },
                {
                    "name": "update_memory",
                    "description": "Update an existing memory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to update"},
                            "title": {"type": "string", "description": "New title"},
                            "content": {"type": "string", "description": "New content"},
                            "tags": {"type": "string", "description": "Comma-separated tags"},
                            "category": {"type": "string", "description": "Memory category"},
                            "importance": {"type": "integer", "description": "Importance level (1-10)", "default": 1}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "analyze_content",
                    "description": "Perform advanced content analysis on memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Specific memory to analyze"},
                            "analysis_type": {"type": "string", "description": "Type: 'keywords', 'sentiment', 'complexity', 'readability'", "default": "keywords"}
                        },
                        "required": []
                    }
                },
                {
                    "name": "categorize_memories",
                    "description": "Automatically categorize and tag memories based on content analysis",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "context_id": {"type": "integer", "description": "Filter by context ID"},
                            "auto_generate_tags": {"type": "boolean", "description": "Auto-generate tags from content", "default": True}
                        },
                        "required": []
                    }
                },
                {
                    "name": "summarize_memory",
                    "description": "Generate or update summary for a memory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to summarize"},
                            "max_length": {"type": "integer", "description": "Maximum summary length in words", "default": 50}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "search_memories",
                    "description": "Search for memories",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "delete_memory",
                    "description": "Delete a memory and its relations",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "integer", "description": "Memory ID to delete"}
                        },
                        "required": ["memory_id"]
                    }
                },
                {
                    "name": "analyze_knowledge_graph",
                    "description": "Analyze the knowledge graph and provide insights",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {"type": "string", "description": "Type of analysis: 'overview', 'centrality', 'connections'", "default": "overview"},
                            "memory_id": {"type": "integer", "description": "Specific memory ID for focused analysis"}
                        },
                        "required": []
                    }
                },
                {
                    "name": "bulk_create_relations",
                    "description": "Create multiple relations at once",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "relations": {
                                "type": "array",
                                "description": "Array of relation objects",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "source_memory_id": {"type": "integer"},
                                        "target_memory_id": {"type": "integer"},
                                        "strength": {"type": "number", "default": 1.0},
                                        "relation_metadata": {"type": "object"}
                                    },
                                    "required": ["name", "source_memory_id", "target_memory_id"]
                                }
                            }
                        },
                        "required": ["relations"]
                    }
                },
                {
                    "name": "create_large_memory",
                    "description": "Create a memory for large content without splitting into chunks",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the memory"},
                            "content": {"type": "string", "description": "Large content to store without chunking"},
                            "context_id": {"type": "integer", "description": "ID of the context"},
                            "access_level": {"type": "string", "description": "Access level", "default": "private"},
                            "compress_content": {"type": "boolean", "description": "Whether to compress content", "default": True}
                        },
                        "required": ["title", "content"]
                    }
                },
                {
                    "name": "ingest_book",
                    "description": "Ingest a book file, parse it into chapters, and store in the database",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "book_path": {"type": "string", "description": "Path to the book file"},
                            "owner_id": {"type": "string", "description": "Owner ID for the book", "default": "system"},
                            "context_id": {"type": "integer", "description": "Context ID for the book", "default": 1},
                            "enable_chunking": {"type": "boolean", "description": "Enable chunked storage for large chapters", "default": True},
                            "chunk_size": {"type": "integer", "description": "Maximum size of chunks in characters", "default": 10000}
                        },
                        "required": ["book_path"]
                    }
                }
            ]
        }

    async def handle_call_tool(self, name: str, arguments: Dict) -> Dict:
        """Handle tool call request"""
        if name == "create_memory":
            # Create memory using enhanced database
            memory = await self.db.create_memory(
                title=arguments["title"],
                content=arguments["content"],
                context_id=arguments.get("context_id"),
                access_level=arguments.get("access_level", "public"),
                memory_metadata=arguments.get("memory_metadata", {}),
                compress_content=arguments.get("compress_content", True),
                use_chunked_storage=arguments.get("use_chunked_storage", False)
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "memory_id": memory.id,
                        "title": memory.title,
                        "message": "Memory created successfully"
                    }, indent=2)
                }]
            }
        
        elif name == "search_memories":
            query = arguments["query"]
            limit = arguments.get("limit", 10)
            context_id = arguments.get("context_id")
            
            # Use enhanced database search
            results = await self.db.search_memories(
                query=query,
                limit=limit,
                context_id=context_id
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps([{
                        "id": m.id,
                        "title": m.title,
                        "content": m.content,
                        "context_id": m.context_id,
                        "access_level": m.access_level,
                        "created_at": m.created_at.isoformat()
                    } for m in results], indent=2)
                }]
            }
        
        elif name == "create_context":
            # Create context using enhanced database
            context = await self.db.create_context(
                name=arguments["name"],
                description=arguments["description"],
                metadata=arguments.get("metadata", {})
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "context_id": context.id,
                        "name": context.name,
                        "description": context.description,
                        "message": "Context created successfully"
                    }, indent=2)
                }]
            }
        
        elif name == "create_relation":
            source_id = arguments["source_memory_id"]
            target_id = arguments["target_memory_id"]
            
            # Validate that both memories exist using enhanced database
            source_memory = await self.db.get_memory_by_id(source_id)
            target_memory = await self.db.get_memory_by_id(target_id)
            
            if not source_memory or not target_memory:
                raise ValueError("Source or target memory does not exist")
            
            # Create relation using enhanced database
            relation = await self.db.create_relation(
                source_memory_id=source_id,
                target_memory_id=target_id,
                relation_type=arguments["name"],
                strength=arguments.get("strength", 1.0),
                metadata=arguments.get("relation_metadata", {})
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "relation_id": relation.id,
                        "name": relation.relation_type,
                        "source_memory_id": source_id,
                        "target_memory_id": target_id,
                        "message": "Relation created successfully"
                    }, indent=2)
                }]
            }
        
        elif name == "get_memory_relations":
            memory_id = arguments["memory_id"]
            
            # Check if memory exists using enhanced database
            memory = await self.db.get_memory_by_id(memory_id)
            if not memory:
                raise ValueError(f"Memory {memory_id} does not exist")
            
            # Get relations using enhanced database
            relations = await self.db.get_memory_relations(memory_id)
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "memory_id": memory_id,
                        "memory_title": memory.title,
                        "relations": relations,
                        "total_relations": len(relations)
                    }, indent=2)
                }]
            }
        
        elif name == "search_semantic":
            query = arguments["query"]
            limit = arguments.get("limit", 10)
            context_id = arguments.get("context_id")
            similarity_threshold = arguments.get("similarity_threshold", 0.3)
            
            # Use enhanced database semantic search
            results = await self.db.search_semantic(
                query=query,
                limit=limit,
                context_id=context_id,
                similarity_threshold=similarity_threshold
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "query": query,
                        "results": [{
                            "id": m.id,
                            "title": m.title,
                            "content": m.content,
                            "context_id": m.context_id,
                            "access_level": m.access_level,
                            "created_at": m.created_at.isoformat(),
                            "similarity_score": m.score if hasattr(m, 'score') else 0.0
                        } for m in results],
                        "total_found": len(results)
                    }, indent=2)
                }]
            }
        
        elif name == "analyze_knowledge_graph":
            analysis_type = arguments.get("analysis_type", "overview")
            memory_id = arguments.get("memory_id")
            
            # Use enhanced database to analyze knowledge graph
            result = await self.db.analyze_knowledge_graph(
                analysis_type=analysis_type,
                memory_id=memory_id
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }
        
        elif name == "summarize_memory":
            memory_id = arguments["memory_id"]
            max_length = arguments.get("max_length", 50)
            
            # Use enhanced database to summarize memory
            result = await self.db.summarize_memory(
                memory_id=memory_id,
                max_length=max_length
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }

        elif name == "update_memory":
            memory_id = arguments["memory_id"]
            title = arguments.get("title")
            content = arguments.get("content")
            tags = arguments.get("tags")
            category = arguments.get("category")
            importance = arguments.get("importance")
            
            # Use enhanced database to update memory
            result = await self.db.update_memory(
                memory_id=memory_id,
                title=title,
                content=content,
                tags=tags,
                category=category,
                importance=importance
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }

        elif name == "delete_memory":
            memory_id = arguments["memory_id"]
            
            # Use enhanced database to delete memory
            result = await self.db.delete_memory(memory_id=memory_id)
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }

        elif name == "get_memory_statistics":
            include_content_analysis = arguments.get("include_content_analysis", True)
            
            # Use enhanced database to get statistics
            stats = await self.db.get_memory_statistics(include_content_analysis=include_content_analysis)
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(stats, indent=2)
                }]
            }

        elif name == "bulk_create_memories":
            memories_data = arguments["memories"]
            
            # Use enhanced database to create memories
            created_memories = await self.db.bulk_create_memories(memories_data)
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "created_count": len(created_memories),
                        "memories": created_memories
                    }, indent=2)
                }]
            }

        elif name == "categorize_memories":
            context_id = arguments.get("context_id")
            auto_generate_tags = arguments.get("auto_generate_tags", True)
            
            # Use enhanced database to categorize memories
            result = await self.db.categorize_memories(
                context_id=context_id,
                auto_generate_tags=auto_generate_tags
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }

        elif name == "analyze_content":
            analysis_type = arguments.get("analysis_type", "keywords")
            memory_id = arguments.get("memory_id")
            
            # Use enhanced database to analyze content
            results = await self.db.analyze_content(
                analysis_type=analysis_type,
                memory_id=memory_id
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "analysis_type": analysis_type,
                        "analyzed_memories": len(results),
                        "results": results
                    }, indent=2)
                }]
            }

        elif name == "bulk_create_relations":
            relations_data = arguments["relations"]
            
            # Use enhanced database to create relations
            created_relations = await self.db.bulk_create_relations(relations_data)
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "created_count": len(created_relations),
                        "relations": created_relations
                    }, indent=2)
                }]
            }

        elif name == "create_large_memory":
            # Create large memory without chunking
            memory = await self.db.create_large_memory(
                title=arguments["title"],
                content=arguments["content"],
                owner_id="system",  # Default owner
                context_id=arguments.get("context_id"),
                access_level=arguments.get("access_level", "private"),
                compress_content=arguments.get("compress_content", True)
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "memory_id": memory.id,
                        "title": memory.title,
                        "content_size": len(arguments["content"]),
                        "compressed": memory.content_compressed,
                        "chunked": False,
                        "message": "Large memory created successfully without chunking"
                    }, indent=2)
                }]
            }

        elif name == "ingest_book":
            book_path = arguments["book_path"]
            owner_id = arguments.get("owner_id", "system")
            context_id = arguments.get("context_id", 1)
            enable_chunking = arguments.get("enable_chunking", True)
            chunk_size = arguments.get("chunk_size", 10000)
            
            # Use enhanced database to ingest book
            book_memory = await self.db.ingest_book(
                book_path=book_path,
                owner_id=owner_id,
                context_id=context_id,
                enable_chunking=enable_chunking,
                chunk_size=chunk_size
            )
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "book_id": book_memory.id,
                        "title": book_memory.title,
                        "chapters_count": book_memory.memory_metadata.get("total_chapters", 0),
                        "message": "Book ingested successfully"
                    }, indent=2)
                }]
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

    async def process_request(self, request: Dict) -> Dict:
        """Process an MCP request and return response"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "resources/list":
                result = await self.handle_list_resources()
            elif method == "resources/read":
                result = await self.handle_read_resource(params["uri"])
            elif method == "tools/list":
                result = await self.handle_list_tools()
            elif method == "tools/call":
                result = await self.handle_call_tool(params["name"], params.get("arguments", {}))
            elif method == "resources/templates/list":
                result = {"resourceTemplates": []}
            else:
                raise ValueError(f"Unknown method: {method}")

            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            # Return the JSON response directly - json.dumps handles boolean conversion
            return response

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }
            
            # Return the JSON response directly - json.dumps handles boolean conversion
            return error_response

    async def run(self):
        """Main server loop - read from stdin, write to stdout"""
        logger.info("Starting MCP stdio server")
        
        while True:
            try:
                # Read a line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue

                # Parse JSON request
                request = json.loads(line)
                logger.info(f"Received request: {request.get('method')}")

                # Process request
                response = await self.process_request(request)
                
                # Send JSON response to stdout
                print(json.dumps(response, default=str), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error"
                    }
                }
                print(json.dumps(error_response), flush=True)

async def main():
    """Main entry point"""
    server = MCPStdioServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())