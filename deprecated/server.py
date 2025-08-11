"""
MCP server implementation for the enhanced MCP Multi-Context Memory System.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.database.enhanced_memory_db import EnhancedMemoryDB
from src.schemas.memory import MemoryCreate, MemoryUpdate
from src.schemas.context import ContextCreate, ContextUpdate
from src.schemas.relation import RelationCreate, RelationUpdate
from src.schemas.auth import TokenData
from src.utils.error_handling import handle_errors

logger = logging.getLogger(__name__)

class MCPMessage(BaseModel):
    """
    MCP message model.
    """
    id: str
    type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    """
    MCP response model.
    """
    id: str
    type: str
    data: Dict[str, Any]
    status: str = "success"
    error: Optional[str] = None

class MCPConnectionManager:
    """
    MCP connection manager for handling WebSocket connections.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Connect a new WebSocket.
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket.
        
        Args:
            websocket: WebSocket connection
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a personal message to a specific WebSocket.
        
        Args:
            message: Message to send
            websocket: WebSocket connection
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """
        Broadcast a message to all connected WebSockets.
        
        Args:
            message: Message to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

class MCPServer:
    """
    MCP server implementation.
    """
    def __init__(self, db: EnhancedMemoryDB):
        self.db = db
        self.connection_manager = MCPConnectionManager()
        self.message_handlers = {
            "memory.create": self.handle_memory_create,
            "memory.update": self.handle_memory_update,
            "memory.delete": self.handle_memory_delete,
            "memory.get": self.handle_memory_get,
            "memory.search": self.handle_memory_search,
            "context.create": self.handle_context_create,
            "context.update": self.handle_context_update,
            "context.delete": self.handle_context_delete,
            "context.get": self.handle_context_get,
            "context.search": self.handle_context_search,
            "relation.create": self.handle_relation_create,
            "relation.update": self.handle_relation_update,
            "relation.delete": self.handle_relation_delete,
            "relation.get": self.handle_relation_get,
            "relation.search": self.handle_relation_search,
            "system.health": self.handle_system_health,
            "system.info": self.handle_system_info,
            "auth.login": self.handle_auth_login,
            "auth.logout": self.handle_auth_logout,
            "auth.refresh": self.handle_auth_refresh,
            "config.get": self.handle_config_get,
            "config.set": self.handle_config_set,
            "migration.start": self.handle_migration_start,
            "migration.status": self.handle_migration_status,
            "migration.cancel": self.handle_migration_cancel,
            # Storage optimization handlers
            "storage.compression.enable": self.handle_compression_enable,
            "storage.compression.disable": self.handle_compression_disable,
            "storage.compression.status": self.handle_compression_status,
            "storage.chunked.enable": self.handle_chunked_storage_enable,
            "storage.chunked.disable": self.handle_chunked_storage_disable,
            "storage.chunked.status": self.handle_chunked_storage_status,
            "storage.hybrid.enable": self.handle_hybrid_storage_enable,
            "storage.hybrid.disable": self.handle_hybrid_storage_disable,
            "storage.hybrid.status": self.handle_hybrid_storage_status,
            "storage.distributed.enable": self.handle_distributed_storage_enable,
            "storage.distributed.disable": self.handle_distributed_storage_disable,
            "storage.distributed.status": self.handle_distributed_storage_status,
            # Advanced feature handlers
            "features.deduplication.enable": self.handle_deduplication_enable,
            "features.deduplication.disable": self.handle_deduplication_disable,
            "features.deduplication.status": self.handle_deduplication_status,
            "features.deduplication.find-duplicates": self.handle_find_duplicates,
            "features.deduplication.merge": self.handle_merge_duplicates,
            "features.archival.enable": self.handle_archival_enable,
            "features.archival.disable": self.handle_archival_disable,
            "features.archival.status": self.handle_archival_status,
            "features.archival.archive": self.handle_archive_memory,
            "features.archival.restore": self.handle_restore_memory,
            "features.archival.list": self.handle_list_archived_memories
        }

    async def handle_websocket(self, websocket: WebSocket):
        """
        Handle WebSocket connection.
        
        Args:
            websocket: WebSocket connection
        """
        await self.connection_manager.connect(websocket)
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message
                response = await self.process_message(message)
                
                # Send response
                await self.connection_manager.send_personal_message(
                    json.dumps(response.dict()), 
                    websocket
                )
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            self.connection_manager.disconnect(websocket)

    async def process_message(self, message: Dict[str, Any]) -> MCPResponse:
        """
        Process an MCP message.
        
        Args:
            message: MCP message
            
        Returns:
            MCP response
        """
        try:
            # Validate message
            if not all(key in message for key in ["id", "type", "data"]):
                raise ValueError("Invalid message format")
            
            message_id = message["id"]
            message_type = message["type"]
            message_data = message["data"]
            
            # Get message handler
            handler = self.message_handlers.get(message_type)
            if not handler:
                raise ValueError(f"Unknown message type: {message_type}")
            
            # Process message
            response_data = await handler(message_data)
            
            # Create response
            response = MCPResponse(
                id=message_id,
                type=f"{message_type}.response",
                data=response_data
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return MCPResponse(
                id=message.get("id", ""),
                type=message.get("type", "") + ".response",
                data={},
                status="error",
                error=str(e)
            )

    async def handle_memory_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory create message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Create memory
            memory_data = MemoryCreate(**data)
            memory = await self.db.create_memory(
                user_id=data.get("user_id"),
                **memory_data.dict()
            )
            
            return memory.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to create memory")
            raise

    async def handle_memory_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory update message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Update memory
            memory_id = data.pop("memory_id")
            memory_data = MemoryUpdate(**data)
            memory = await self.db.update_memory(
                memory_id=memory_id,
                user_id=data.get("user_id"),
                **memory_data.dict(exclude_unset=True)
            )
            
            return memory.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to update memory")
            raise

    async def handle_memory_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory delete message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Delete memory
            memory_id = data["memory_id"]
            await self.db.delete_memory(
                memory_id=memory_id,
                user_id=data.get("user_id")
            )
            
            return {"message": "Memory deleted successfully"}
            
        except Exception as e:
            handle_errors(e, "Failed to delete memory")
            raise

    async def handle_memory_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory get message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Get memory
            memory_id = data["memory_id"]
            memory = await self.db.get_memory(
                memory_id=memory_id,
                user_id=data.get("user_id")
            )
            
            return memory.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to get memory")
            raise

    async def handle_memory_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle memory search message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Search memories
            query = data.get("query", "")
            filters = data.get("filters", {})
            memories = await self.db.search_memories(
                query=query,
                filters=filters,
                user_id=data.get("user_id")
            )
            
            return {"memories": [memory.dict() for memory in memories]}
            
        except Exception as e:
            handle_errors(e, "Failed to search memories")
            raise

    async def handle_context_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle context create message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Create context
            context_data = ContextCreate(**data)
            context = await self.db.create_context(
                user_id=data.get("user_id"),
                **context_data.dict()
            )
            
            return context.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to create context")
            raise

    async def handle_context_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle context update message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Update context
            context_id = data.pop("context_id")
            context_data = ContextUpdate(**data)
            context = await self.db.update_context(
                context_id=context_id,
                user_id=data.get("user_id"),
                **context_data.dict(exclude_unset=True)
            )
            
            return context.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to update context")
            raise

    async def handle_context_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle context delete message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Delete context
            context_id = data["context_id"]
            await self.db.delete_context(
                context_id=context_id,
                user_id=data.get("user_id")
            )
            
            return {"message": "Context deleted successfully"}
            
        except Exception as e:
            handle_errors(e, "Failed to delete context")
            raise

    async def handle_context_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle context get message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Get context
            context_id = data["context_id"]
            context = await self.db.get_context(
                context_id=context_id,
                user_id=data.get("user_id")
            )
            
            return context.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to get context")
            raise

    async def handle_context_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle context search message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Search contexts
            query = data.get("query", "")
            filters = data.get("filters", {})
            contexts = await self.db.search_contexts(
                query=query,
                filters=filters,
                user_id=data.get("user_id")
            )
            
            return {"contexts": [context.dict() for context in contexts]}
            
        except Exception as e:
            handle_errors(e, "Failed to search contexts")
            raise

    async def handle_relation_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle relation create message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Create relation
            relation_data = RelationCreate(**data)
            relation = await self.db.create_relation(
                user_id=data.get("user_id"),
                **relation_data.dict()
            )
            
            return relation.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to create relation")
            raise

    async def handle_relation_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle relation update message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Update relation
            relation_id = data.pop("relation_id")
            relation_data = RelationUpdate(**data)
            relation = await self.db.update_relation(
                relation_id=relation_id,
                user_id=data.get("user_id"),
                **relation_data.dict(exclude_unset=True)
            )
            
            return relation.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to update relation")
            raise

    async def handle_relation_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle relation delete message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Delete relation
            relation_id = data["relation_id"]
            await self.db.delete_relation(
                relation_id=relation_id,
                user_id=data.get("user_id")
            )
            
            return {"message": "Relation deleted successfully"}
            
        except Exception as e:
            handle_errors(e, "Failed to delete relation")
            raise

    async def handle_relation_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle relation get message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Get relation
            relation_id = data["relation_id"]
            relation = await self.db.get_relation(
                relation_id=relation_id,
                user_id=data.get("user_id")
            )
            
            return relation.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to get relation")
            raise

    async def handle_relation_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle relation search message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Search relations
            query = data.get("query", "")
            filters = data.get("filters", {})
            relations = await self.db.search_relations(
                query=query,
                filters=filters,
                user_id=data.get("user_id")
            )
            
            return {"relations": [relation.dict() for relation in relations]}
            
        except Exception as e:
            handle_errors(e, "Failed to search relations")
            raise

    async def handle_system_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle system health message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Get system health
            health = await self.db.get_system_health()
            
            return health.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to get system health")
            raise

    async def handle_system_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle system info message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Get system info
            info = await self.db.get_system_info()
            
            return info.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to get system info")
            raise

    async def handle_auth_login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle auth login message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Login user
            username = data["username"]
            password = data["password"]
            
            user = await self.db.authenticate_user(username=username, password=password)
            
            return {
                "user_id": user.id,
                "username": user.username,
                "access_token": user.access_token,
                "refresh_token": user.refresh_token
            }
            
        except Exception as e:
            handle_errors(e, "Failed to login user")
            raise

    async def handle_auth_logout(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle auth logout message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Logout user
            user_id = data["user_id"]
            await self.db.logout_user(user_id=user_id)
            
            return {"message": "Logged out successfully"}
            
        except Exception as e:
            handle_errors(e, "Failed to logout user")
            raise

    async def handle_auth_refresh(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle auth refresh message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Refresh token
            refresh_token = data["refresh_token"]
            
            tokens = await self.db.refresh_token(refresh_token=refresh_token)
            
            return tokens.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to refresh token")
            raise

    async def handle_config_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle config get message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Get config
            key = data["key"]
            config = await self.db.get_config(key=key)
            
            return config.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to get config")
            raise

    async def handle_config_set(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle config set message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Set config
            key = data["key"]
            value = data["value"]
            config = await self.db.set_config(key=key, value=value)
            
            return config.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to set config")
            raise

    async def handle_migration_start(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle migration start message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Start migration
            migration_type = data["migration_type"]
            migration_id = await self.db.start_migration(migration_type=migration_type)
            
            return {"migration_id": migration_id}
            
        except Exception as e:
            handle_errors(e, "Failed to start migration")
            raise

    async def handle_migration_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle migration status message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Get migration status
            migration_id = data["migration_id"]
            status = await self.db.get_migration_status(migration_id=migration_id)
            
            return status.dict()
            
        except Exception as e:
            handle_errors(e, "Failed to get migration status")
            raise

    async def handle_migration_cancel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle migration cancel message.
        
        Args:
            data: Message data
            
        Returns:
            Response data
        """
        try:
            # Cancel migration
            migration_id = data["migration_id"]
            await self.db.cancel_migration(migration_id=migration_id)
            
            return {"message": "Migration cancelled successfully"}
            
        except Exception as e:
            handle_errors(e, "Failed to cancel migration")
            raise

    # Storage Optimization Handlers
    async def handle_compression_enable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle compression enable message."""
        try:
            await self.db.set_compression_enabled(True)
            return {"message": "Compression enabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to enable compression")
            raise

    async def handle_compression_disable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle compression disable message."""
        try:
            await self.db.set_compression_enabled(False)
            return {"message": "Compression disabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to disable compression")
            raise

    async def handle_compression_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle compression status message."""
        try:
            status = self.db.get_compression_status()
            return status
        except Exception as e:
            handle_errors(e, "Failed to get compression status")
            raise

    async def handle_chunked_storage_enable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chunked storage enable message."""
        try:
            config = data.get("config", {})
            await self.db.set_chunked_storage_enabled(True)
            await self.db.set_chunk_size(config.get("chunk_size", 1024))
            await self.db.set_max_chunks(config.get("max_chunks", 100))
            return {"message": "Chunked storage enabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to enable chunked storage")
            raise

    async def handle_chunked_storage_disable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chunked storage disable message."""
        try:
            await self.db.set_chunked_storage_enabled(False)
            return {"message": "Chunked storage disabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to disable chunked storage")
            raise

    async def handle_chunked_storage_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chunked storage status message."""
        try:
            status = self.db.get_chunked_storage_status()
            return status
        except Exception as e:
            handle_errors(e, "Failed to get chunked storage status")
            raise

    async def handle_hybrid_storage_enable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hybrid storage enable message."""
        try:
            config = data.get("config", {})
            await self.db.set_hybrid_storage_enabled(True)
            await self.db.set_hybrid_storage_config(config)
            return {"message": "Hybrid storage enabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to enable hybrid storage")
            raise

    async def handle_hybrid_storage_disable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hybrid storage disable message."""
        try:
            await self.db.set_hybrid_storage_enabled(False)
            return {"message": "Hybrid storage disabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to disable hybrid storage")
            raise

    async def handle_hybrid_storage_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hybrid storage status message."""
        try:
            status = self.db.get_hybrid_storage_status()
            return status
        except Exception as e:
            handle_errors(e, "Failed to get hybrid storage status")
            raise

    async def handle_distributed_storage_enable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle distributed storage enable message."""
        try:
            config = data.get("config", {})
            await self.db.set_distributed_storage_enabled(True)
            await self.db.set_distributed_storage_config(config)
            return {"message": "Distributed storage enabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to enable distributed storage")
            raise

    async def handle_distributed_storage_disable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle distributed storage disable message."""
        try:
            await self.db.set_distributed_storage_enabled(False)
            return {"message": "Distributed storage disabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to disable distributed storage")
            raise

    async def handle_distributed_storage_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle distributed storage status message."""
        try:
            status = self.db.get_distributed_storage_status()
            return status
        except Exception as e:
            handle_errors(e, "Failed to get distributed storage status")
            raise

    # Advanced Feature Handlers
    async def handle_deduplication_enable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deduplication enable message."""
        try:
            config = data.get("config", {})
            await self.db.set_deduplication_enabled(True)
            await self.db.set_deduplication_config(config)
            return {"message": "Deduplication enabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to enable deduplication")
            raise

    async def handle_deduplication_disable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deduplication disable message."""
        try:
            await self.db.set_deduplication_enabled(False)
            return {"message": "Deduplication disabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to disable deduplication")
            raise

    async def handle_deduplication_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deduplication status message."""
        try:
            status = self.db.get_deduplication_status()
            return status
        except Exception as e:
            handle_errors(e, "Failed to get deduplication status")
            raise

    async def handle_find_duplicates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle find duplicates message."""
        try:
            threshold = data.get("threshold", 0.9)
            limit = data.get("limit", 100)
            duplicates = await self.db.find_duplicate_memories(threshold=threshold, limit=limit)
            return {"duplicates": duplicates}
        except Exception as e:
            handle_errors(e, "Failed to find duplicates")
            raise

    async def handle_merge_duplicates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle merge duplicates message."""
        try:
            primary_id = data["primary_id"]
            duplicate_ids = data["duplicate_ids"]
            await self.db.merge_duplicate_memories(primary_id=primary_id, duplicate_ids=duplicate_ids)
            return {"message": "Duplicates merged successfully"}
        except Exception as e:
            handle_errors(e, "Failed to merge duplicates")
            raise

    async def handle_archival_enable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle archival enable message."""
        try:
            config = data.get("config", {})
            await self.db.set_archival_enabled(True)
            await self.db.set_archival_config(config)
            return {"message": "Archival enabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to enable archival")
            raise

    async def handle_archival_disable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle archival disable message."""
        try:
            await self.db.set_archival_enabled(False)
            return {"message": "Archival disabled successfully"}
        except Exception as e:
            handle_errors(e, "Failed to disable archival")
            raise

    async def handle_archival_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle archival status message."""
        try:
            status = self.db.get_archival_status()
            return status
        except Exception as e:
            handle_errors(e, "Failed to get archival status")
            raise

    async def handle_archive_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle archive memory message."""
        try:
            memory_id = data["memory_id"]
            await self.db.archive_memory(memory_id=memory_id)
            return {"message": "Memory archived successfully"}
        except Exception as e:
            handle_errors(e, "Failed to archive memory")
            raise

    async def handle_restore_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle restore memory message."""
        try:
            memory_id = data["memory_id"]
            await self.db.restore_memory(memory_id=memory_id)
            return {"message": "Memory restored successfully"}
        except Exception as e:
            handle_errors(e, "Failed to restore memory")
            raise

    async def handle_list_archived_memories(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list archived memories message."""
        try:
            skip = data.get("skip", 0)
            limit = data.get("limit", 100)
            memories = await self.db.get_archived_memories(skip=skip, limit=limit)
            return {"memories": [memory.dict() for memory in memories]}
        except Exception as e:
            handle_errors(e, "Failed to list archived memories")
            raise