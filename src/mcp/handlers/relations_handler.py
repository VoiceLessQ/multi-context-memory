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
Relations Handler implementing Chain of Responsibility pattern.
Handles all relation-related MCP tool operations.
"""
from typing import Dict, Any, List
from .base_handler import BaseToolHandler, ToolRequest, ToolResponse, DatabaseMixin, ValidationMixin


class RelationsHandler(BaseToolHandler, DatabaseMixin, ValidationMixin):
    """
    Handler for relation-related MCP tools.
    Implements Chain of Responsibility pattern for relation operations.
    """
    
    def __init__(self):
        super().__init__()
        self.supported_tools = [
            "create_relation",
            "get_memory_relations",
            "bulk_create_relations"
        ]
    
    async def process_request(self, request: ToolRequest) -> ToolResponse:
        """Process relation-related requests."""
        self.ensure_database()
        
        tool_name = request.name
        args = request.arguments
        
        try:
            if tool_name == "create_relation":
                return await self._handle_create_relation(args)
            elif tool_name == "get_memory_relations":
                return await self._handle_get_memory_relations(args)
            elif tool_name == "bulk_create_relations":
                return await self._handle_bulk_create_relations(args)
            else:
                return ToolResponse.error_response(f"Unsupported relation tool: {tool_name}")
                
        except Exception as e:
            return ToolResponse.error_response(
                error=f"Relation operation failed: {str(e)}",
                details={"tool": tool_name, "arguments": args}
            )
    
    async def _handle_create_relation(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle relation creation."""
        self.validate_required_fields(args, ["name", "source_memory_id", "target_memory_id"])
        
        source_id = self.validate_positive_integer(args["source_memory_id"], "source_memory_id")
        target_id = self.validate_positive_integer(args["target_memory_id"], "target_memory_id")
        
        # Validate that both memories exist
        source_memory = await self.db.get_memory_by_id(source_id)
        target_memory = await self.db.get_memory_by_id(target_id)
        
        if not source_memory or not target_memory:
            return ToolResponse.error_response("Source or target memory does not exist")
        
        # Validate strength if provided
        strength = args.get("strength", 1.0)
        strength = self.validate_number_range(strength, "strength", 0.0, 1.0)
        
        relation = await self.db.create_relation(
            name=args["name"],
            source_memory_id=source_id,
            target_memory_id=target_id,
            strength=strength,
            relation_metadata=args.get("relation_metadata", {})
        )
        
        return ToolResponse.success_response({
            "relation_id": relation.id,
            "name": relation.name,
            "source_memory_id": source_id,
            "target_memory_id": target_id,
            "message": "Relation created successfully"
        })
    
    async def _handle_get_memory_relations(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle getting memory relations."""
        self.validate_required_fields(args, ["memory_id"])
        
        memory_id = self.validate_positive_integer(args["memory_id"], "memory_id")
        
        # Check if memory exists
        memory = await self.db.get_memory_by_id(memory_id)
        if not memory:
            return ToolResponse.error_response(f"Memory {memory_id} does not exist")
        
        relations = await self.db.get_memory_relations(memory_id)
        
        return ToolResponse.success_response({
            "memory_id": memory_id,
            "memory_title": memory.title,
            "relations": relations,
            "total_relations": len(relations)
        })
    
    async def _handle_bulk_create_relations(self, args: Dict[str, Any]) -> ToolResponse:
        """Handle bulk relation creation."""
        self.validate_required_fields(args, ["relations"])
        
        relations_data = args["relations"]
        if not isinstance(relations_data, list):
            return ToolResponse.error_response("relations must be a list")
        
        # Validate each relation
        for i, relation in enumerate(relations_data):
            try:
                self.validate_required_fields(relation, ["name", "source_memory_id", "target_memory_id"])
                self.validate_positive_integer(relation["source_memory_id"], "source_memory_id")
                self.validate_positive_integer(relation["target_memory_id"], "target_memory_id")
                
                if "strength" in relation:
                    self.validate_number_range(relation["strength"], "strength", 0.0, 1.0)
            except ValueError as e:
                return ToolResponse.error_response(f"Invalid relation at index {i}: {str(e)}")
        
        created_relations = await self.db.bulk_create_relations(relations_data)
        
        return ToolResponse.success_response({
            "created_count": len(created_relations),
            "relations": created_relations
        })
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions for relation tools."""
        return [
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
            }
        ]