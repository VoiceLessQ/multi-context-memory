"""
Refactored MCP Server using Command and Factory patterns.
Replaces the monolithic 1,050-line server.py with clean architecture.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .command_factory import CommandFactory, CommandInvoker, CommandPipeline
from .commands.base_command import CommandContext, CommandResult
from src.database.refactored_memory_db import RefactoredMemoryDB
from src.utils.error_handling import handle_errors

logger = logging.getLogger(__name__)


class MCPMessage(BaseModel):
    """MCP message model with validation."""
    id: str
    type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP response model with status handling."""
    id: str
    type: str
    data: Dict[str, Any]
    status: str = "success"
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConnectionManager:
    """
    WebSocket connection manager with improved error handling.
    Implements Observer pattern for connection lifecycle.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.message_stats: Dict[str, int] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, metadata: Optional[Dict] = None):
        """Connect a new WebSocket with metadata tracking."""
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = metadata or {}
            self.message_stats[connection_id] = 0
            
            logger.info(f"WebSocket connected: {connection_id}. Total: {len(self.active_connections)}")
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket {connection_id}: {e}")
            raise
    
    def disconnect(self, connection_id: str) -> bool:
        """Disconnect WebSocket and cleanup resources."""
        try:
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                del self.connection_metadata[connection_id]
                del self.message_stats[connection_id]
                
                logger.info(f"WebSocket disconnected: {connection_id}. Total: {len(self.active_connections)}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {connection_id}: {e}")
            return False
    
    async def send_message(self, connection_id: str, message: str) -> bool:
        """Send message to specific connection with error handling."""
        try:
            websocket = self.active_connections.get(connection_id)
            if not websocket:
                logger.warning(f"Connection not found: {connection_id}")
                return False
            
            await websocket.send_text(message)
            self.message_stats[connection_id] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.disconnect(connection_id)
            return False
    
    async def broadcast_message(self, message: str, exclude: Optional[List[str]] = None) -> int:
        """Broadcast message to all connections with exclusion support."""
        exclude = exclude or []
        sent_count = 0
        failed_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            if connection_id in exclude:
                continue
            
            try:
                await websocket.send_text(message)
                self.message_stats[connection_id] += 1
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                failed_connections.append(connection_id)
        
        # Cleanup failed connections
        for connection_id in failed_connections:
            self.disconnect(connection_id)
        
        return sent_count
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get comprehensive connection information."""
        return {
            "total_connections": len(self.active_connections),
            "connections": {
                conn_id: {
                    "metadata": self.connection_metadata.get(conn_id, {}),
                    "messages_sent": self.message_stats.get(conn_id, 0)
                }
                for conn_id in self.active_connections.keys()
            }
        }


class MessageProcessor:
    """
    Message processor implementing Strategy pattern.
    Handles different message processing strategies.
    """
    
    def __init__(self, command_invoker: CommandInvoker):
        self.invoker = command_invoker
        self.processing_strategies = {
            "immediate": self._process_immediate,
            "batch": self._process_batch,
            "pipeline": self._process_pipeline
        }
    
    async def process_message(
        self,
        message: MCPMessage,
        context: CommandContext,
        strategy: str = "immediate"
    ) -> MCPResponse:
        """Process message using specified strategy."""
        try:
            processor = self.processing_strategies.get(strategy, self._process_immediate)
            return await processor(message, context)
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            return MCPResponse(
                id=message.id,
                type=f"{message.type}.response",
                data={},
                status="error",
                error=str(e)
            )
    
    async def _process_immediate(self, message: MCPMessage, context: CommandContext) -> MCPResponse:
        """Process message immediately."""
        result = await self.invoker.invoke_command(
            command_name=message.type,
            context=context,
            data=message.data,
            immediate=True
        )
        
        return MCPResponse(
            id=message.id,
            type=f"{message.type}.response",
            data=result.data,
            status="success" if result.success else "error",
            error=result.error,
            metadata=result.metadata
        )
    
    async def _process_batch(self, message: MCPMessage, context: CommandContext) -> MCPResponse:
        """Queue message for batch processing."""
        result = await self.invoker.invoke_command(
            command_name=message.type,
            context=context,
            data=message.data,
            immediate=False
        )
        
        return MCPResponse(
            id=message.id,
            type=f"{message.type}.response",
            data=result.data,
            status="queued",
            metadata=result.metadata
        )
    
    async def _process_pipeline(self, message: MCPMessage, context: CommandContext) -> MCPResponse:
        """Process message as part of pipeline."""
        # This would be used for complex multi-step operations
        # For now, fallback to immediate processing
        return await self._process_immediate(message, context)


class RefactoredMCPServer:
    """
    Refactored MCP Server using Command and Factory patterns.
    Replaces monolithic 1,050-line server with clean architecture.
    """
    
    def __init__(self, db: RefactoredMemoryDB):
        self.db = db
        self.connection_manager = ConnectionManager()
        
        # Initialize command processing components
        self.command_factory = CommandFactory()
        self.command_invoker = CommandInvoker(self.command_factory)
        self.message_processor = MessageProcessor(self.command_invoker)
        self.command_pipeline = CommandPipeline(self.command_invoker)
        
        # Server configuration
        self.config = {
            "max_connections": 100,
            "message_timeout": 30,
            "batch_processing": False,
            "enable_metrics": True
        }
        
        logger.info("RefactoredMCPServer initialized with command-based architecture")
    
    async def handle_websocket(self, websocket: WebSocket, connection_id: str):
        """
        Handle WebSocket connection using clean architecture.
        Much simpler than the original 50+ line method.
        """
        await self.connection_manager.connect(websocket, connection_id)
        
        try:
            while True:
                # Receive and validate message
                raw_data = await websocket.receive_text()
                message = self._parse_message(raw_data)
                
                # Create command context
                context = CommandContext(
                    user_id=connection_id,  # In real app, extract from auth
                    session_id=connection_id,
                    metadata={"connection_id": connection_id}
                )
                
                # Process message using strategy pattern
                response = await self.message_processor.process_message(
                    message=message,
                    context=context,
                    strategy="batch" if self.config["batch_processing"] else "immediate"
                )
                
                # Send response
                await self.connection_manager.send_message(
                    connection_id=connection_id,
                    message=json.dumps(response.dict())
                )
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket {connection_id} disconnected")
            
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
            
        finally:
            self.connection_manager.disconnect(connection_id)
    
    def _parse_message(self, raw_data: str) -> MCPMessage:
        """Parse and validate incoming message."""
        try:
            data = json.loads(raw_data)
            return MCPMessage(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid message format: {e}")
    
    async def execute_command_pipeline(
        self,
        steps: List[Dict[str, Any]],
        context: CommandContext
    ) -> List[CommandResult]:
        """Execute a series of commands in pipeline."""
        pipeline = self.command_pipeline
        pipeline.clear()
        
        for step in steps:
            pipeline.add_step(
                command_name=step["command"],
                data=step.get("data", {}),
                condition=step.get("condition")
            )
        
        return await pipeline.execute_pipeline(context)
    
    async def process_batch_commands(self) -> List[CommandResult]:
        """Process queued batch commands."""
        return await self.command_invoker.process_batch()
    
    def register_custom_command(self, command_class) -> bool:
        """Register custom command with the factory."""
        return self.command_factory.register_custom_command(command_class)
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get comprehensive server status."""
        return {
            "server_info": {
                "version": "2.0.0-refactored",
                "architecture": "Command + Factory Pattern",
                "active": True
            },
            "connections": self.connection_manager.get_connection_info(),
            "commands": {
                "available": self.command_factory.get_supported_commands(),
                "queue_status": self.command_invoker.get_queue_status()
            },
            "configuration": self.config,
            "database_status": "connected"  # Would check actual DB connection
        }
    
    def get_supported_commands(self) -> List[str]:
        """Get list of all supported commands."""
        return self.command_factory.get_supported_commands()
    
    def get_command_help(self, command_name: Optional[str] = None) -> Dict[str, Any]:
        """Get help information for commands."""
        return self.command_factory.get_command_help(command_name)
    
    async def shutdown(self):
        """Gracefully shutdown the server."""
        try:
            logger.info("Shutting down RefactoredMCPServer...")
            
            # Process any remaining batch commands
            await self.process_batch_commands()
            
            # Close all connections
            for connection_id in list(self.connection_manager.active_connections.keys()):
                self.connection_manager.disconnect(connection_id)
            
            # Clear command caches
            self.command_factory.clear_cache()
            self.command_invoker.clear_queue()
            
            logger.info("RefactoredMCPServer shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")


class MCPServerBuilder:
    """
    Builder pattern for creating configured MCP servers.
    Provides fluent interface for server configuration.
    """
    
    def __init__(self):
        self.db = None
        self.config = {}
        self.custom_commands = []
    
    def with_database(self, db: RefactoredMemoryDB) -> 'MCPServerBuilder':
        """Set the database instance."""
        self.db = db
        return self
    
    def with_config(self, **config) -> 'MCPServerBuilder':
        """Set server configuration."""
        self.config.update(config)
        return self
    
    def with_custom_command(self, command_class) -> 'MCPServerBuilder':
        """Add custom command class."""
        self.custom_commands.append(command_class)
        return self
    
    def with_batch_processing(self, enabled: bool = True, batch_size: int = 10) -> 'MCPServerBuilder':
        """Configure batch processing."""
        self.config.update({
            "batch_processing": enabled,
            "batch_size": batch_size
        })
        return self
    
    def with_connection_limits(self, max_connections: int = 100, timeout: int = 30) -> 'MCPServerBuilder':
        """Configure connection limits."""
        self.config.update({
            "max_connections": max_connections,
            "message_timeout": timeout
        })
        return self
    
    def build(self) -> RefactoredMCPServer:
        """Build the configured MCP server."""
        if not self.db:
            raise ValueError("Database instance is required")
        
        server = RefactoredMCPServer(self.db)
        
        # Apply configuration
        server.config.update(self.config)
        
        # Configure batch processing
        if self.config.get("batch_processing"):
            server.command_invoker.set_batch_size(self.config.get("batch_size", 10))
        
        # Register custom commands
        for command_class in self.custom_commands:
            server.register_custom_command(command_class)
        
        return server


# Factory function for backward compatibility
def create_mcp_server(db: RefactoredMemoryDB, **config) -> RefactoredMCPServer:
    """
    Factory function to create MCP server with configuration.
    Provides backward compatibility with existing code.
    """
    builder = MCPServerBuilder()
    builder.with_database(db)
    
    if config:
        builder.with_config(**config)
    
    return builder.build()