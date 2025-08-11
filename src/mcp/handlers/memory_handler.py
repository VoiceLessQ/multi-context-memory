"""
Memory Handler implementing Chain of Responsibility pattern.
Handles all memory-related MCP tool operations.
"""
import json
from typing import Dict, Any, List
from .base_handler import BaseToolHandler, ToolRequest, ToolResponse, DatabaseMixin, ValidationMixin


class MemoryHandler(BaseToolHandler, DatabaseMixin, ValidationMixin):
    """
    Handler for memory-related MCP tools.
    Implements Chain of Responsibility pattern for memory operations.
    """
    
    def __init__(self):
        super().__init__()
        self.supported_tools = [
            "create_memory",
            "search_memories", 
            "update_memory",
            "delete_memory",
            "get_memory_statistics",
            "bulk_create_memories",
            "create_large_memory",
            "categorize_memories",
            "analyze_content",
            "summarize_memory"
        ]
    
    async def process_request(self, request: ToolRequest) -> ToolResponse:
        """Process memory-related requests."""
        self.ensure_database()
        
        tool_name = request.name
        args = request.arguments
        
        try:
            if tool_name == "create_memory":
                return await self._handle_create_memory(args)
            elif tool_name == "search_memories":
                return await self._handle_search_memories(args)
            elif tool_name == "update_memory":
                return await self._handle_update_memory(args)
            elif tool_name == "delete_memory":
                return await self._handle_delete_memory(args)
            elif tool_name == "get_memory_statistics":
                return await self._handle_get_memory_statistics(args)
            elif tool_name == "bulk_create_memories":
                return await self._handle_bulk_create_memories(args)
            elif tool_name == "create_large_memory":
                return await self._handle_create_large_memory(args)
            elif tool_name == "categorize_memories":
                return await self._handle_categorize_memories(args)
            elif tool_name == "analyze_content":
                return await self._handle_analyze_content(args)
            elif tool_name == "summarize_memory":
                return await self._handle_summarize_memory(args)
            else:
                return ToolResponse.error_response(f"Unsupported memory tool: {tool_name}")
                
        except Exception as e:
            return ToolResponse.error_response(
                error=f"Memory operation failed: {str(e)}",
                details={"tool": tool_name, "arguments": args}
            )
    
    async def _handle_create_memory(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle memory creation."""
        self.validate_required_fields(args, ["title", "content"])
        
        memory = await self.db.create_memory(
            title=args["title"],
            content=args["content"],
            owner_id=args.get("owner_id", "system"),  # Use system as default owner
            context_id=args.get("context_id"),
            access_level=args.get("access_level", "public"),
            memory_metadata=args.get("memory_metadata", {}),
            compress_content=args.get("compress_content", True),
            use_chunked_storage=args.get("use_chunked_storage", False)
        )
        
        return ToolResponse.success_response({
            "memory_id": memory.id,
            "title": memory.title,
            "message": "Memory created successfully"
        })
    
    async def _handle_search_memories(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle memory search."""
        self.validate_required_fields(args, ["query"])
        
        query = args["query"]
        limit = args.get("limit", 10)
        context_id = args.get("context_id")
        
        results = await self.db.search_memories(
            query=query,
            limit=limit,
            context_id=context_id
        )
        
        memories_data = [{
            "id": m.id,
            "title": m.title,
            "content": m.content,
            "context_id": m.context_id,
            "access_level": m.access_level,
            "created_at": m.created_at.isoformat()
        } for m in results]
        
        return ToolResponse.success_response(memories_data)
    
    async def _handle_update_memory(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle memory update."""
        self.validate_required_fields(args, ["memory_id"])
        
        memory_id = self.validate_positive_integer(args["memory_id"], "memory_id")
        
        # Build memory_metadata from tags, category, importance
        memory_metadata = {}
        if args.get("tags"):
            memory_metadata["tags"] = args["tags"]
        if args.get("category"):
            memory_metadata["category"] = args["category"]
        if args.get("importance"):
            memory_metadata["importance"] = args["importance"]
        
        result = await self.db.update_memory(
            memory_id=memory_id,
            title=args.get("title"),
            content=args.get("content"),
            access_level=args.get("access_level"),
            memory_metadata=memory_metadata if memory_metadata else None
        )
        
        if result:
            return ToolResponse.success_response({
                "memory_id": result.id,
                "title": result.title,
                "updated_at": result.updated_at.isoformat(),
                "message": "Memory updated successfully"
            })
        else:
            return ToolResponse.error_response(f"Failed to update memory {memory_id}")
    
    async def _handle_delete_memory(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle memory deletion."""
        self.validate_required_fields(args, ["memory_id"])
        
        memory_id = self.validate_positive_integer(args["memory_id"], "memory_id")
        
        result = await self.db.delete_memory(memory_id=memory_id)
        
        return ToolResponse.success_response(result)
    
    async def _handle_get_memory_statistics(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle memory statistics request."""
        include_content_analysis = args.get("include_content_analysis", True)
        
        # Use get_statistics method instead of get_memory_statistics
        stats = await self.db.get_statistics()
        
        return ToolResponse.success_response(stats)
    
    async def _handle_bulk_create_memories(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle bulk memory creation."""
        self.validate_required_fields(args, ["memories"])
        
        memories_data = args["memories"]
        if not isinstance(memories_data, list):
            raise ValueError("memories must be a list")
        
        # Since bulk_create_memories doesn't exist, create memories one by one
        created_memories = []
        for memory_data in memories_data:
            memory = await self.db.create_memory(
                title=memory_data["title"],
                content=memory_data["content"],
                owner_id=memory_data.get("owner_id", "system"),
                context_id=memory_data.get("context_id"),
                access_level=memory_data.get("access_level", "private"),
                memory_metadata=memory_data.get("memory_metadata", {})
            )
            created_memories.append({
                "id": memory.id,
                "title": memory.title,
                "content": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
            })
        
        return ToolResponse.success_response({
            "created_count": len(created_memories),
            "memories": created_memories
        })
    
    async def _handle_create_large_memory(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle large memory creation without chunking."""
        self.validate_required_fields(args, ["title", "content"])
        
        # Use regular create_memory since create_large_memory doesn't exist
        memory = await self.db.create_memory(
            title=args["title"],
            content=args["content"],
            owner_id=args.get("owner_id", "system"),
            context_id=args.get("context_id"),
            access_level=args.get("access_level", "private"),
            memory_metadata=args.get("memory_metadata", {}),
            compress_content=args.get("compress_content", True),
            use_chunked_storage=False  # Don't use chunks for large memory
        )
        
        return ToolResponse.success_response({
            "memory_id": memory.id,
            "title": memory.title,
            "content_size": len(args["content"]),
            "compressed": getattr(memory, 'content_compressed', False),
            "chunked": False,
            "message": "Large memory created successfully without chunking"
        })
    
    async def _handle_categorize_memories(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle memory categorization."""
        context_id = args.get("context_id")
        auto_generate_tags = args.get("auto_generate_tags", True)
        
        # Since categorize_memories doesn't exist, provide a placeholder implementation
        memories = await self.db.get_all_memories(limit=100)
        categorized_count = len(memories)
        
        result = {
            "message": "Memory categorization completed",
            "categorized_count": categorized_count,
            "auto_generate_tags": auto_generate_tags,
            "context_id": context_id,
            "note": "This is a placeholder implementation - actual categorization logic not yet implemented"
        }
        
        return ToolResponse.success_response(result)
    
    async def _handle_analyze_content(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle content analysis."""
        analysis_type = args.get("analysis_type", "keywords")
        memory_id = args.get("memory_id")
        
        # Since analyze_content doesn't exist, provide a placeholder implementation
        if memory_id:
            memory = await self.db.get_memory(memory_id)
            if not memory:
                raise ValueError(f"Memory {memory_id} not found")
            analyzed_memories = 1
            sample_results = {
                "memory_id": memory_id,
                "title": memory.title,
                "analysis": f"Sample {analysis_type} analysis results"
            }
        else:
            memories = await self.db.get_all_memories(limit=10)
            analyzed_memories = len(memories)
            sample_results = [
                {
                    "memory_id": memory.id,
                    "title": memory.title,
                    "analysis": f"Sample {analysis_type} analysis"
                } for memory in memories[:3]  # Show first 3 as sample
            ]
        
        return ToolResponse.success_response({
            "analysis_type": analysis_type,
            "analyzed_memories": analyzed_memories,
            "results": sample_results,
            "note": "This is a placeholder implementation - actual content analysis logic not yet implemented"
        })
    
    async def _handle_summarize_memory(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle memory summarization."""
        self.validate_required_fields(args, ["memory_id"])
        
        memory_id = self.validate_positive_integer(args["memory_id"], "memory_id")
        max_length = args.get("max_length", 50)
        
        # Since summarize_memory doesn't exist, provide a basic implementation
        memory = await self.db.get_memory(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")
        
        # Simple summarization - take first max_length words
        words = memory.content.split()
        summary = " ".join(words[:max_length])
        if len(words) > max_length:
            summary += "..."
        
        result = {
            "memory_id": memory_id,
            "title": memory.title,
            "summary": summary,
            "original_length": len(words),
            "summary_length": min(len(words), max_length),
            "note": "This is a basic word-truncation summary - advanced summarization logic not yet implemented"
        }
        
        return ToolResponse.success_response(result)
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions for memory tools."""
        return [
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
            }
        ]