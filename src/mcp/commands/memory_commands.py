"""
Memory-related MCP commands using Command pattern.
Extracts command logic from the monolithic mcp/server.py.
"""
import logging
from typing import Dict, Any, List
import json

from .base_command import Command, CommandContext, CommandResult, ValidationError, validate_required_fields, validate_field_type
from ...schemas.memory import MemoryCreate, MemoryUpdate
from ...utils.error_handling import handle_errors

logger = logging.getLogger(__name__)


class CreateMemoryCommand(Command):
    """Command to create a new memory."""
    
    @property
    def command_name(self) -> str:
        return "memory.create"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:create"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate create memory input."""
        validate_required_fields(data, ["title", "content"])
        validate_field_type(data, "title", str)
        validate_field_type(data, "content", str)
        validate_field_type(data, "context_id", int)
        validate_field_type(data, "access_level", str)
        
        if len(data["title"]) > 500:
            raise ValidationError("Title too long (max 500 characters)", "title")
        
        if len(data["content"]) > 10_000_000:
            raise ValidationError("Content too large (max 10MB)", "content")
        
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute create memory command."""
        try:
            self.validate_input(data)
            
            # Create memory using refactored database
            memory = await context.db.create_memory(
                title=data["title"],
                content=data["content"],
                owner_id=context.user_id or "system",
                context_id=data.get("context_id"),
                access_level=data.get("access_level", "public"),
                memory_metadata=data.get("memory_metadata", {}),
                compress_content=data.get("compress_content", True),
                use_chunked_storage=data.get("use_chunked_storage", False)
            )
            
            result_data = {
                "memory_id": memory.id,
                "title": memory.title,
                "message": "Memory created successfully"
            }
            
            logger.info(f"Memory created via command: {memory.id}")
            return CommandResult(success=True, data=result_data)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in CreateMemoryCommand: {e}")
            handle_errors(e, "Failed to create memory")
            return CommandResult(success=False, data={}, error=str(e))


class GetMemoryCommand(Command):
    """Command to retrieve a memory by ID."""
    
    @property
    def command_name(self) -> str:
        return "memory.get"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:read"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate get memory input."""
        validate_required_fields(data, ["memory_id"])
        validate_field_type(data, "memory_id", int)
        
        if data["memory_id"] <= 0:
            raise ValidationError("Memory ID must be positive", "memory_id")
        
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute get memory command."""
        try:
            self.validate_input(data)
            
            memory = await context.db.get_memory(
                memory_id=data["memory_id"],
                decompress=data.get("decompress", True),
                use_lazy_loading=data.get("use_lazy_loading")
            )
            
            if not memory:
                return CommandResult(success=False, data={}, error="Memory not found")
            
            result_data = {
                "id": memory.id,
                "title": memory.title,
                "content": memory.content,
                "context_id": memory.context_id,
                "access_level": memory.access_level,
                "created_at": memory.created_at.isoformat() if memory.created_at else None
            }
            
            return CommandResult(success=True, data=result_data)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in GetMemoryCommand: {e}")
            return CommandResult(success=False, data={}, error=str(e))


class UpdateMemoryCommand(Command):
    """Command to update a memory."""
    
    @property
    def command_name(self) -> str:
        return "memory.update"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:update"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate update memory input."""
        validate_required_fields(data, ["memory_id"])
        validate_field_type(data, "memory_id", int)
        
        if data["memory_id"] <= 0:
            raise ValidationError("Memory ID must be positive", "memory_id")
        
        # Validate optional fields
        if "title" in data:
            validate_field_type(data, "title", str)
            if len(data["title"]) > 500:
                raise ValidationError("Title too long (max 500 characters)", "title")
        
        if "content" in data:
            validate_field_type(data, "content", str)
            if len(data["content"]) > 10_000_000:
                raise ValidationError("Content too large (max 10MB)", "content")
        
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute update memory command."""
        try:
            self.validate_input(data)
            
            memory_id = data.pop("memory_id")
            updates = {k: v for k, v in data.items() if k != "memory_id"}
            
            memory = await context.db.update_memory(
                memory_id=memory_id,
                **updates
            )
            
            if not memory:
                return CommandResult(success=False, data={}, error="Memory not found")
            
            result_data = {
                "memory_id": memory.id,
                "title": memory.title,
                "message": "Memory updated successfully"
            }
            
            return CommandResult(success=True, data=result_data)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in UpdateMemoryCommand: {e}")
            return CommandResult(success=False, data={}, error=str(e))


class DeleteMemoryCommand(Command):
    """Command to delete a memory."""
    
    @property
    def command_name(self) -> str:
        return "memory.delete"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:delete"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate delete memory input."""
        validate_required_fields(data, ["memory_id"])
        validate_field_type(data, "memory_id", int)
        
        if data["memory_id"] <= 0:
            raise ValidationError("Memory ID must be positive", "memory_id")
        
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute delete memory command."""
        try:
            self.validate_input(data)
            
            success = await context.db.delete_memory(data["memory_id"])
            
            if not success:
                return CommandResult(success=False, data={}, error="Memory not found or deletion failed")
            
            result_data = {"message": "Memory deleted successfully"}
            return CommandResult(success=True, data=result_data)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in DeleteMemoryCommand: {e}")
            return CommandResult(success=False, data={}, error=str(e))


class SearchMemoriesCommand(Command):
    """Command to search memories."""
    
    @property
    def command_name(self) -> str:
        return "memory.search"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:read"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate search memories input."""
        validate_field_type(data, "query", str)
        validate_field_type(data, "limit", int)
        validate_field_type(data, "filters", dict)
        
        query = data.get("query", "")
        if len(query) > 1000:
            raise ValidationError("Query too long (max 1000 characters)", "query")
        
        limit = data.get("limit", 100)
        if limit <= 0 or limit > 1000:
            raise ValidationError("Limit must be between 1 and 1000", "limit")
        
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute search memories command."""
        try:
            self.validate_input(data)
            
            query = data.get("query", "")
            filters = data.get("filters", {})
            limit = data.get("limit", 100)
            
            memories = await context.db.search_memories(
                query=query,
                owner_id=filters.get("owner_id"),
                context_id=filters.get("context_id"),
                access_level=filters.get("access_level"),
                limit=limit
            )
            
            result_data = {
                "memories": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "content": m.content,
                        "context_id": m.context_id,
                        "access_level": m.access_level,
                        "created_at": m.created_at.isoformat() if m.created_at else None
                    }
                    for m in memories
                ],
                "total_found": len(memories)
            }
            
            return CommandResult(success=True, data=result_data)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in SearchMemoriesCommand: {e}")
            return CommandResult(success=False, data={}, error=str(e))


class GetMemoryStatisticsCommand(Command):
    """Command to get memory statistics."""
    
    @property
    def command_name(self) -> str:
        return "memory.statistics"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:read", "system:stats"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate statistics input."""
        validate_field_type(data, "include_content_analysis", bool)
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute get statistics command."""
        try:
            self.validate_input(data)
            
            include_analysis = data.get("include_content_analysis", True)
            stats = await context.db.get_statistics()
            
            return CommandResult(success=True, data=stats)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in GetMemoryStatisticsCommand: {e}")
            return CommandResult(success=False, data={}, error=str(e))


class CreateLargeMemoryCommand(Command):
    """Command to create large memory without chunking."""
    
    @property
    def command_name(self) -> str:
        return "memory.create_large"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:create", "memory:large_content"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate large memory input."""
        validate_required_fields(data, ["title", "content"])
        validate_field_type(data, "title", str)
        validate_field_type(data, "content", str)
        
        if len(data["title"]) > 500:
            raise ValidationError("Title too long (max 500 characters)", "title")
        
        # Allow larger content for this command
        if len(data["content"]) > 100_000_000:  # 100MB limit
            raise ValidationError("Content too large (max 100MB)", "content")
        
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute create large memory command."""
        try:
            self.validate_input(data)
            
            # Use the create_large_memory method from refactored database
            memory = await context.db.create_memory(
                title=data["title"],
                content=data["content"],
                owner_id=context.user_id or "system",
                context_id=data.get("context_id"),
                access_level=data.get("access_level", "private"),
                memory_metadata=data.get("memory_metadata", {}),
                compress_content=data.get("compress_content", True),
                use_chunked_storage=False  # Important: Don't chunk large content
            )
            
            result_data = {
                "memory_id": memory.id,
                "title": memory.title,
                "content_size": len(data["content"]),
                "compressed": memory.content_compressed,
                "chunked": False,
                "message": "Large memory created successfully without chunking"
            }
            
            return CommandResult(success=True, data=result_data)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in CreateLargeMemoryCommand: {e}")
            return CommandResult(success=False, data={}, error=str(e))


class BulkCreateMemoriesCommand(Command):
    """Command to create multiple memories in batch."""
    
    @property
    def command_name(self) -> str:
        return "memory.bulk_create"
    
    @property
    def required_permissions(self) -> List[str]:
        return ["memory:create", "memory:bulk"]
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate bulk create input."""
        validate_required_fields(data, ["memories"])
        validate_field_type(data, "memories", list)
        
        memories = data["memories"]
        if not memories:
            raise ValidationError("Memories list cannot be empty", "memories")
        
        if len(memories) > 100:
            raise ValidationError("Too many memories (max 100 per batch)", "memories")
        
        # Validate each memory
        for i, memory_data in enumerate(memories):
            if not isinstance(memory_data, dict):
                raise ValidationError(f"Memory {i} must be an object", f"memories[{i}]")
            
            if "title" not in memory_data or "content" not in memory_data:
                raise ValidationError(f"Memory {i} missing required fields", f"memories[{i}]")
        
        return True
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute bulk create memories command."""
        try:
            self.validate_input(data)
            
            memories_data = data["memories"]
            created_memories = []
            failed_memories = []
            
            for i, memory_data in enumerate(memories_data):
                try:
                    memory = await context.db.create_memory(
                        title=memory_data["title"],
                        content=memory_data["content"],
                        owner_id=context.user_id or "system",
                        context_id=memory_data.get("context_id"),
                        access_level=memory_data.get("access_level", "public"),
                        memory_metadata=memory_data.get("metadata", {}),
                        compress_content=True,
                        use_chunked_storage=False
                    )
                    
                    created_memories.append({
                        "id": memory.id,
                        "title": memory.title,
                        "index": i
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to create memory {i}: {e}")
                    failed_memories.append({
                        "index": i,
                        "error": str(e)
                    })
            
            result_data = {
                "created_count": len(created_memories),
                "failed_count": len(failed_memories),
                "created_memories": created_memories,
                "failed_memories": failed_memories
            }
            
            return CommandResult(success=True, data=result_data)
            
        except ValidationError as e:
            return CommandResult(success=False, data={}, error=str(e))
        except Exception as e:
            logger.error(f"Error in BulkCreateMemoriesCommand: {e}")
            return CommandResult(success=False, data={}, error=str(e))