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
Context Handler implementing Chain of Responsibility pattern.
Handles all context-related MCP tool operations.
"""
from typing import Dict, Any, List
from .base_handler import BaseToolHandler, ToolRequest, ToolResponse, DatabaseMixin, ValidationMixin


class ContextHandler(BaseToolHandler, DatabaseMixin, ValidationMixin):
    """
    Handler for context-related MCP tools.
    Implements Chain of Responsibility pattern for context operations.
    """
    
    def __init__(self):
        super().__init__()
        self.supported_tools = ["create_context"]
    
    async def process_request(self, request: ToolRequest) -> ToolResponse:
        """Process context-related requests."""
        self.ensure_database()
        
        tool_name = request.name
        args = request.arguments
        
        try:
            if tool_name == "create_context":
                return await self._handle_create_context(args)
            else:
                return ToolResponse.error_response(f"Unsupported context tool: {tool_name}")
                
        except Exception as e:
            return ToolResponse.error_response(
                error=f"Context operation failed: {str(e)}",
                details={"tool": tool_name, "arguments": args}
            )
    
    async def _handle_create_context(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle context creation."""
        self.validate_required_fields(args, ["name", "description"])
        
        # Debug: Log what arguments we received
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG: create_context received args: {args}")
        
        # Filter out any metadata that might be accidentally included
        filtered_args = {
            "name": args["name"],
            "description": args["description"],
            "owner_id": args.get("owner_id", 1),
            "access_level": args.get("access_level", "user")
        }
        
        logger.error(f"DEBUG: create_context calling db with: {filtered_args}")
        
        context = await self.db.create_context(**filtered_args)
        
        return ToolResponse.success_response({
            "context_id": context.id,
            "name": context.name,
            "description": context.description,
            "message": "Context created successfully"
        })
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions for context tools."""
        return [
            {
                "name": "create_context",
                "description": "Create a new context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Context name"},
                        "description": {"type": "string", "description": "Context description"},
                        "owner_id": {"type": "integer", "description": "Owner ID (default: 1)"},
                        "access_level": {"type": "string", "description": "Access level (default: 'user')"}
                    },
                    "required": ["name", "description"]
                }
            }
        ]