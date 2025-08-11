"""
Advanced Handler implementing Chain of Responsibility pattern.
Handles advanced MCP tool operations like semantic search and knowledge graph analysis.
"""
from typing import Dict, Any, List
from .base_handler import BaseToolHandler, ToolRequest, ToolResponse, DatabaseMixin, ValidationMixin


class AdvancedHandler(BaseToolHandler, DatabaseMixin, ValidationMixin):
    """
    Handler for advanced MCP tools.
    Implements Chain of Responsibility pattern for advanced operations.
    """
    
    def __init__(self):
        super().__init__()
        self.supported_tools = [
            "search_semantic",
            "analyze_knowledge_graph", 
            "ingest_book"
        ]
    
    async def process_request(self, request: ToolRequest) -> ToolResponse:
        """Process advanced requests."""
        self.ensure_database()
        
        tool_name = request.name
        args = request.arguments
        
        try:
            if tool_name == "search_semantic":
                return await self._handle_search_semantic(args)
            elif tool_name == "analyze_knowledge_graph":
                return await self._handle_analyze_knowledge_graph(args)
            elif tool_name == "ingest_book":
                return await self._handle_ingest_book(args)
            else:
                return ToolResponse.error_response(f"Unsupported advanced tool: {tool_name}")
                
        except Exception as e:
            return ToolResponse.error_response(
                error=f"Advanced operation failed: {str(e)}",
                details={"tool": tool_name, "arguments": args}
            )
    
    async def _handle_search_semantic(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle semantic search."""
        self.validate_required_fields(args, ["query"])
        
        query = args["query"]
        limit = args.get("limit", 10)
        context_id = args.get("context_id")
        similarity_threshold = args.get("similarity_threshold", 0.3)
        
        # Validate parameters
        limit = self.validate_positive_integer(limit, "limit")
        similarity_threshold = self.validate_number_range(
            similarity_threshold, "similarity_threshold", 0.0, 1.0
        )
        
        if context_id is not None:
            context_id = self.validate_positive_integer(context_id, "context_id")
        
        results = await self.db.search_semantic(
            query=query,
            limit=limit,
            context_id=context_id,
            similarity_threshold=similarity_threshold
        )
        
        results_data = {
            "query": query,
            "results": [{
                "id": m.id,
                "title": m.title,
                "content": m.content,
                "context_id": m.context_id,
                "access_level": m.access_level,
                "created_at": m.created_at.isoformat(),
                "similarity_score": getattr(m, 'score', 0.0)
            } for m in results],
            "total_found": len(results)
        }
        
        return ToolResponse.success_response(results_data)
    
    async def _handle_analyze_knowledge_graph(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle knowledge graph analysis."""
        analysis_type = args.get("analysis_type", "overview")
        memory_id = args.get("memory_id")
        
        if memory_id is not None:
            memory_id = self.validate_positive_integer(memory_id, "memory_id")
        
        # Validate analysis type
        valid_types = ["overview", "centrality", "connections"]
        if analysis_type not in valid_types:
            return ToolResponse.error_response(
                f"Invalid analysis_type. Must be one of: {', '.join(valid_types)}"
            )
        
        result = await self.db.analyze_knowledge_graph(
            analysis_type=analysis_type,
            memory_id=memory_id
        )
        
        return ToolResponse.success_response(result)
    
    async def _handle_ingest_book(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle book ingestion."""
        self.validate_required_fields(args, ["book_path"])
        
        book_path = args["book_path"]
        owner_id = args.get("owner_id", "system")
        context_id = args.get("context_id", 1)
        enable_chunking = args.get("enable_chunking", True)
        chunk_size = args.get("chunk_size", 10000)
        
        # Validate parameters
        context_id = self.validate_positive_integer(context_id, "context_id")
        chunk_size = self.validate_positive_integer(chunk_size, "chunk_size")
        
        if not isinstance(enable_chunking, bool):
            return ToolResponse.error_response("enable_chunking must be a boolean")
        
        # The ingest_book method returns a dictionary, not a Memory object
        ingestion_result = await self.db.ingest_book(
            book_path=book_path,
            owner_id=owner_id,
            context_id=context_id,
            enable_chunking=enable_chunking,
            chunk_size=chunk_size
        )
        
        # Check if ingestion was successful
        if ingestion_result.get("error"):
            return ToolResponse.error_response(
                f"Book ingestion failed: {ingestion_result['error']}"
            )
        
        return ToolResponse.success_response({
            "book_path": ingestion_result.get("book_path"),
            "total_chapters": ingestion_result.get("total_chapters", 0),
            "created_memories": ingestion_result.get("created_memories", 0),
            "errors": ingestion_result.get("errors", []),
            "ingestion_complete": ingestion_result.get("ingestion_complete", False),
            "ingested_at": ingestion_result.get("ingested_at"),
            "message": "Book ingested successfully"
        })
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions for advanced tools."""
        return [
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