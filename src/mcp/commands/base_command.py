"""
Base Command interface and abstract classes.
Implements Command pattern for MCP message handling.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ...database.refactored_memory_db import RefactoredMemoryDB


@dataclass
class CommandContext:
    """
    Context object passed to all commands.
    Contains shared dependencies and request information.
    """
    db: RefactoredMemoryDB
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CommandResult:
    """
    Standardized command result structure.
    """
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "data": self.data
        }
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class Command(ABC):
    """
    Base Command interface following Command pattern.
    Each command encapsulates a specific MCP operation.
    """
    
    @property
    @abstractmethod
    def command_name(self) -> str:
        """Return the command name/identifier."""
        pass
    
    @property
    @abstractmethod
    def required_permissions(self) -> list[str]:
        """Return required permissions for this command."""
        pass
    
    @abstractmethod
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """
        Execute the command with given context and data.
        
        Args:
            context: Command execution context
            data: Command-specific data from the request
            
        Returns:
            CommandResult with success status and data
        """
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.
        
        Args:
            data: Input data to validate
            
        Returns:
            True if valid, raises exception if invalid
        """
        pass
    
    async def can_execute(self, context: CommandContext) -> bool:
        """
        Check if command can be executed in the given context.
        Default implementation checks permissions.
        
        Args:
            context: Command execution context
            
        Returns:
            True if command can be executed
        """
        # In a real implementation, you'd check user permissions here
        # For now, allow all commands
        return True
    
    def get_command_info(self) -> Dict[str, Any]:
        """Get command metadata for introspection."""
        return {
            "name": self.command_name,
            "required_permissions": self.required_permissions,
            "description": self.__doc__ or "",
            "class": self.__class__.__name__
        }


class AsyncCommand(Command):
    """
    Base class for asynchronous commands.
    Provides common async functionality.
    """
    
    async def execute_with_timeout(
        self, 
        context: CommandContext, 
        data: Dict[str, Any], 
        timeout_seconds: int = 30
    ) -> CommandResult:
        """Execute command with timeout."""
        import asyncio
        
        try:
            return await asyncio.wait_for(
                self.execute(context, data),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            return CommandResult(
                success=False,
                data={},
                error=f"Command {self.command_name} timed out after {timeout_seconds} seconds"
            )


class BatchCommand(Command):
    """
    Base class for commands that support batch operations.
    """
    
    @abstractmethod
    async def execute_batch(
        self, 
        context: CommandContext, 
        batch_data: list[Dict[str, Any]]
    ) -> list[CommandResult]:
        """Execute command for multiple data items."""
        pass
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Single execution delegates to batch with one item."""
        results = await self.execute_batch(context, [data])
        return results[0] if results else CommandResult(
            success=False,
            data={},
            error="No results from batch execution"
        )


class CacheableCommand(Command):
    """
    Base class for commands that support result caching.
    """
    
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, tuple[datetime, CommandResult]] = {}
    
    def get_cache_key(self, context: CommandContext, data: Dict[str, Any]) -> str:
        """Generate cache key for the request."""
        import hashlib
        import json
        
        cache_data = {
            "command": self.command_name,
            "user_id": context.user_id,
            "data": data
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    async def execute(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute with caching support."""
        cache_key = self.get_cache_key(context, data)
        
        # Check cache
        if cache_key in self._cache:
            cached_time, cached_result = self._cache[cache_key]
            age_seconds = (datetime.utcnow() - cached_time).total_seconds()
            
            if age_seconds < self.cache_ttl_seconds:
                # Return cached result with metadata
                cached_result.metadata = cached_result.metadata or {}
                cached_result.metadata["cached"] = True
                cached_result.metadata["cache_age_seconds"] = age_seconds
                return cached_result
        
        # Execute and cache result
        result = await self.execute_uncached(context, data)
        
        if result.success:
            self._cache[cache_key] = (datetime.utcnow(), result)
        
        return result
    
    @abstractmethod
    async def execute_uncached(self, context: CommandContext, data: Dict[str, Any]) -> CommandResult:
        """Execute without caching - to be implemented by subclasses."""
        pass
    
    def clear_cache(self):
        """Clear the command cache."""
        self._cache.clear()


class ValidationError(Exception):
    """Exception raised when command input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.message = message


class CommandExecutionError(Exception):
    """Exception raised when command execution fails."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        self.message = message


def validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> None:
    """
    Utility function to validate required fields in command data.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required field is missing
    """
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Required field '{field}' is missing", field)
        
        if data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            raise ValidationError(f"Field '{field}' cannot be empty", field)


def validate_field_type(data: Dict[str, Any], field: str, expected_type: type) -> None:
    """
    Utility function to validate field type.
    
    Args:
        data: Data to validate
        field: Field name to check
        expected_type: Expected type
        
    Raises:
        ValidationError: If field type is incorrect
    """
    if field in data and not isinstance(data[field], expected_type):
        raise ValidationError(
            f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}",
            field
        )