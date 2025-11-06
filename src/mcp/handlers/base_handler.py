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
Base Handler classes implementing Chain of Responsibility pattern.
Provides foundation for modular MCP tool handling.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolRequest:
    """
    Encapsulates a tool request with metadata and context.
    """
    
    def __init__(
        self, 
        name: str, 
        arguments: Dict[str, Any], 
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.arguments = arguments
        self.request_id = request_id or f"req_{datetime.now().isoformat()}"
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary for logging/debugging."""
        return {
            "name": self.name,
            "arguments": self.arguments,
            "request_id": self.request_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class ToolResponse:
    """
    Standardized response format for MCP tools.
    """
    
    def __init__(
        self,
        content: List[Dict[str, Any]],
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.success = success
        self.error = error
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to MCP-compliant format."""
        result = {"content": self.content}
        
        if self.metadata:
            result["_metadata"] = self.metadata
            
        return result
    
    @classmethod
    def success_response(
        cls,
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ToolResponse':
        """Create a success response with formatted data."""
        content_text = json.dumps(data, indent=2) if data else ""
        if message:
            content_text = f"{message}\n\n{content_text}" if content_text else message
        
        return cls(
            content=[{"type": "text", "text": content_text}],
            success=True,
            metadata=metadata
        )
    
    @classmethod
    def error_response(
        cls,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> 'ToolResponse':
        """Create an error response."""
        error_data = {"error": error}
        if details:
            error_data["details"] = details
        
        return cls(
            content=[{"type": "text", "text": json.dumps(error_data, indent=2)}],
            success=False,
            error=error
        )


class BaseToolHandler(ABC):
    """
    Abstract base class for tool handlers using Chain of Responsibility pattern.
    """
    
    def __init__(self):
        self._next_handler: Optional['BaseToolHandler'] = None
        self.supported_tools: List[str] = []
    
    def set_next(self, handler: 'BaseToolHandler') -> 'BaseToolHandler':
        """Set the next handler in the chain."""
        self._next_handler = handler
        return handler
    
    def can_handle(self, request: ToolRequest) -> bool:
        """Check if this handler can process the request."""
        return request.name in self.supported_tools
    
    async def handle(self, request: ToolRequest) -> Optional[ToolResponse]:
        """
        Handle the request using Chain of Responsibility pattern.
        """
        try:
            if self.can_handle(request):
                logger.info(f"Handler {self.__class__.__name__} processing tool: {request.name}")
                response = await self.process_request(request)
                logger.info(f"Handler {self.__class__.__name__} completed tool: {request.name}")
                return response
            elif self._next_handler:
                logger.debug(f"Handler {self.__class__.__name__} passing to next handler")
                return await self._next_handler.handle(request)
            else:
                logger.warning(f"No handler found for tool: {request.name}")
                return None
                
        except Exception as e:
            logger.error(f"Error in handler {self.__class__.__name__}: {e}")
            return ToolResponse.error_response(
                error=f"Handler error: {str(e)}",
                details={"handler": self.__class__.__name__, "tool": request.name}
            )
    
    @abstractmethod
    async def process_request(self, request: ToolRequest) -> ToolResponse:
        """Process the actual request. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions for supported tools."""
        pass
    
    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about this handler."""
        return {
            "name": self.__class__.__name__,
            "supported_tools": self.supported_tools,
            "has_next_handler": self._next_handler is not None
        }


class DatabaseMixin:
    """
    Mixin providing database access for handlers.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = None  # Will be injected by the server
    
    def set_database(self, db):
        """Inject database dependency."""
        self.db = db
        return self
    
    def ensure_database(self):
        """Ensure database is available."""
        if not self.db:
            raise RuntimeError("Database not configured for handler")


class ValidationMixin:
    """
    Mixin providing common validation utilities.
    """
    
    def validate_required_fields(self, arguments: Dict[str, Any], required: List[str]) -> None:
        """Validate that required fields are present."""
        missing = [field for field in required if field not in arguments]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
    
    def validate_positive_integer(self, value: Any, field_name: str) -> int:
        """Validate and convert to positive integer."""
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError(f"{field_name} must be positive")
            return int_value
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a positive integer")
    
    def validate_number_range(self, value: Any, field_name: str, min_val: float, max_val: float) -> float:
        """Validate number is within range."""
        try:
            float_value = float(value)
            if not (min_val <= float_value <= max_val):
                raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
            return float_value
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a number between {min_val} and {max_val}")


class HandlerChain:
    """
    Manages the chain of responsibility for tool handlers.
    """
    
    def __init__(self):
        self.handlers: List[BaseToolHandler] = []
        self._head_handler: Optional[BaseToolHandler] = None
    
    def add_handler(self, handler: BaseToolHandler) -> 'HandlerChain':
        """Add a handler to the end of the chain."""
        if self.handlers:
            self.handlers[-1].set_next(handler)
        else:
            self._head_handler = handler
        
        self.handlers.append(handler)
        logger.info(f"Added handler: {handler.__class__.__name__}")
        return self
    
    def add_handlers(self, handlers: List[BaseToolHandler]) -> 'HandlerChain':
        """Add multiple handlers to the chain."""
        for handler in handlers:
            self.add_handler(handler)
        return self
    
    async def handle_request(self, request: ToolRequest) -> ToolResponse:
        """Process request through the handler chain."""
        if not self._head_handler:
            return ToolResponse.error_response("No handlers configured")
        
        try:
            response = await self._head_handler.handle(request)
            if response is None:
                return ToolResponse.error_response(f"No handler found for tool: {request.name}")
            return response
            
        except Exception as e:
            logger.error(f"Chain processing error: {e}")
            return ToolResponse.error_response(
                error=f"Chain processing error: {str(e)}",
                details={"request": request.to_dict()}
            )
    
    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions from all handlers."""
        definitions = []
        for handler in self.handlers:
            definitions.extend(handler.get_tool_definitions())
        return definitions
    
    def get_supported_tools(self) -> List[str]:
        """Get all supported tool names."""
        tools = []
        for handler in self.handlers:
            tools.extend(handler.supported_tools)
        return tools
    
    def get_chain_info(self) -> Dict[str, Any]:
        """Get information about the entire handler chain."""
        return {
            "total_handlers": len(self.handlers),
            "handlers": [handler.get_handler_info() for handler in self.handlers],
            "supported_tools": self.get_supported_tools()
        }
    
    def configure_database(self, db) -> 'HandlerChain':
        """Configure database for all handlers that need it."""
        for handler in self.handlers:
            if hasattr(handler, 'set_database'):
                handler.set_database(db)
        return self
    
    def clear(self) -> 'HandlerChain':
        """Clear all handlers from the chain."""
        self.handlers.clear()
        self._head_handler = None
        return self