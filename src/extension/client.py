"""
VS Code extension client for the enhanced MCP Multi-Context Memory System.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed

from ...config.settings import settings
from ...utils.error_handling import ExtensionError, handle_extension_error

logger = logging.getLogger(__name__)

class MCPMemoryExtensionClient:
    """
    Client for the VS Code extension to interact with the MCP Multi-Context Memory System.
    """
    
    def __init__(self, 
                 server_url: str = None,
                 api_key: str = None,
                 use_websocket: bool = True,
                 timeout: int = 30):
        """
        Initialize the extension client.
        
        Args:
            server_url: URL of the MCP server
            api_key: API key for authentication
            use_websocket: Whether to use WebSocket for real-time updates
            timeout: Request timeout in seconds
        """
        self.server_url = server_url or settings.server_url
        self.api_key = api_key or settings.api_key
        self.use_websocket = use_websocket
        self.timeout = timeout
        
        # HTTP session
        self.http_session = None
        
        # WebSocket connection
        self.websocket = None
        self.websocket_connected = False
        
        # Event handlers
        self.event_handlers = {}
        
        # Initialize
        self._initialize()
        
    def _initialize(self):
        """
        Initialize the client.
        """
        # Create HTTP session
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        
        # Setup event handlers
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """
        Setup default event handlers.
        """
        # Memory event handlers
        self.event_handlers["memory.created"] = self._on_memory_created
        self.event_handlers["memory.updated"] = self._on_memory_updated
        self.event_handlers["memory.deleted"] = self._on_memory_deleted
        
        # Context event handlers
        self.event_handlers["context.created"] = self._on_context_created
        self.event_handlers["context.updated"] = self._on_context_updated
        self.event_handlers["context.deleted"] = self._on_context_deleted
        
        # Relation event handlers
        self.event_handlers["relation.created"] = self._on_relation_created
        self.event_handlers["relation.updated"] = self._on_relation_updated
        self.event_handlers["relation.deleted"] = self._on_relation_deleted
        
    async def connect_websocket(self):
        """
        Connect to the WebSocket server.
        """
        try:
            # WebSocket URL
            ws_url = self.server_url.replace("http", "ws") + "/ws"
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(ws_url)
            self.websocket_connected = True
            
            # Start listening for messages
            asyncio.create_task(self._listen_websocket())
            
            logger.info("WebSocket connected successfully")
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise ExtensionError(f"WebSocket connection failed: {e}", "connect_websocket")
            
    async def disconnect_websocket(self):
        """
        Disconnect from the WebSocket server.
        """
        try:
            if self.websocket and self.websocket_connected:
                await self.websocket.close()
                self.websocket_connected = False
                logger.info("WebSocket disconnected successfully")
                
        except Exception as e:
            logger.error(f"WebSocket disconnection failed: {e}")
            raise ExtensionError(f"WebSocket disconnection failed: {e}", "disconnect_websocket")
            
    async def _listen_websocket(self):
        """
        Listen for WebSocket messages.
        """
        try:
            async for message in self.websocket:
                try:
                    # Parse message
                    data = json.loads(message)
                    
                    # Handle message
                    await self._handle_websocket_message(data)
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message: {message}")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.websocket_connected = False
        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")
            self.websocket_connected = False
            
    async def _handle_websocket_message(self, data: Dict[str, Any]):
        """
        Handle a WebSocket message.
        
        Args:
            data: WebSocket message data
        """
        try:
            # Extract event type
            event_type = data.get("type")
            
            # Get event handler
            handler = self.event_handlers.get(event_type)
            
            if handler:
                # Call event handler
                await handler(data)
            else:
                logger.warning(f"No handler for event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            
    async def _on_memory_created(self, data: Dict[str, Any]):
        """
        Handle memory created event.
        
        Args:
            data: Event data
        """
        logger.info(f"Memory created: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("memory.created", data)
        
    async def _on_memory_updated(self, data: Dict[str, Any]):
        """
        Handle memory updated event.
        
        Args:
            data: Event data
        """
        logger.info(f"Memory updated: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("memory.updated", data)
        
    async def _on_memory_deleted(self, data: Dict[str, Any]):
        """
        Handle memory deleted event.
        
        Args:
            data: Event data
        """
        logger.info(f"Memory deleted: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("memory.deleted", data)
        
    async def _on_context_created(self, data: Dict[str, Any]):
        """
        Handle context created event.
        
        Args:
            data: Event data
        """
        logger.info(f"Context created: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("context.created", data)
        
    async def _on_context_updated(self, data: Dict[str, Any]):
        """
        Handle context updated event.
        
        Args:
            data: Event data
        """
        logger.info(f"Context updated: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("context.updated", data)
        
    async def _on_context_deleted(self, data: Dict[str, Any]):
        """
        Handle context deleted event.
        
        Args:
            data: Event data
        """
        logger.info(f"Context deleted: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("context.deleted", data)
        
    async def _on_relation_created(self, data: Dict[str, Any]):
        """
        Handle relation created event.
        
        Args:
            data: Event data
        """
        logger.info(f"Relation created: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("relation.created", data)
        
    async def _on_relation_updated(self, data: Dict[str, Any]):
        """
        Handle relation updated event.
        
        Args:
            data: Event data
        """
        logger.info(f"Relation updated: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("relation.updated", data)
        
    async def _on_relation_deleted(self, data: Dict[str, Any]):
        """
        Handle relation deleted event.
        
        Args:
            data: Event data
        """
        logger.info(f"Relation deleted: {data}")
        
        # Emit event to VS Code
        await self._emit_vscode_event("relation.deleted", data)
        
    async def _emit_vscode_event(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event to VS Code.
        
        Args:
            event_type: Event type
            data: Event data
        """
        try:
            # Create VS Code command
            command = {
                "command": "mcpMemory.emitEvent",
                "args": {
                    "type": event_type,
                    "data": data
                }
            }
            
            # Send command to VS Code
            await self._send_vscode_command(command)
            
        except Exception as e:
            logger.error(f"Error emitting VS Code event: {e}")
            
    async def _send_vscode_command(self, command: Dict[str, Any]):
        """
        Send a command to VS Code.
        
        Args:
            command: Command to send
        """
        try:
            # In a real implementation, this would send the command to VS Code
            # through the extension API
            logger.info(f"Sending VS Code command: {command}")
            
        except Exception as e:
            logger.error(f"Error sending VS Code command: {e}")
            
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the MCP server.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authentication result
        """
        try:
            # Prepare request data
            data = {
                "username": username,
                "password": password
            }
            
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/auth/login",
                json=data
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    
                    # Store token
                    self.api_key = result.get("access_token")
                    
                    return result
                else:
                    error = await response.text()
                    raise ExtensionError(f"Authentication failed: {error}", "authenticate")
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise ExtensionError(f"Authentication error: {e}", "authenticate")
            
    async def search_memories(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search memories.
        
        Args:
            query: Search query
            filters: Search filters
            
        Returns:
            Search results
        """
        try:
            # Prepare request data
            data = {
                "query": query,
                "filters": filters or {}
            }
            
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/memory/search",
                json=data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("memories", [])
                else:
                    error = await response.text()
                    raise ExtensionError(f"Memory search failed: {error}", "search_memories")
                    
        except Exception as e:
            logger.error(f"Memory search error: {e}")
            raise ExtensionError(f"Memory search error: {e}", "search_memories")
            
    async def create_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a memory.
        
        Args:
            memory_data: Memory data
            
        Returns:
            Created memory
        """
        try:
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/memory",
                json=memory_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 201:
                    result = await response.json()
                    return result.get("memory")
                else:
                    error = await response.text()
                    raise ExtensionError(f"Memory creation failed: {error}", "create_memory")
                    
        except Exception as e:
            logger.error(f"Memory creation error: {e}")
            raise ExtensionError(f"Memory creation error: {e}", "create_memory")
            
    async def update_memory(self, memory_id: int, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a memory.
        
        Args:
            memory_id: Memory ID
            memory_data: Memory data
            
        Returns:
            Updated memory
        """
        try:
            # Send request
            async with self.http_session.put(
                f"{self.server_url}/api/v1/memory/{memory_id}",
                json=memory_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("memory")
                else:
                    error = await response.text()
                    raise ExtensionError(f"Memory update failed: {error}", "update_memory")
                    
        except Exception as e:
            logger.error(f"Memory update error: {e}")
            raise ExtensionError(f"Memory update error: {e}", "update_memory")
            
    async def delete_memory(self, memory_id: int) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Whether the memory was deleted
        """
        try:
            # Send request
            async with self.http_session.delete(
                f"{self.server_url}/api/v1/memory/{memory_id}",
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    return True
                else:
                    error = await response.text()
                    raise ExtensionError(f"Memory deletion failed: {error}", "delete_memory")
                    
        except Exception as e:
            logger.error(f"Memory deletion error: {e}")
            raise ExtensionError(f"Memory deletion error: {e}", "delete_memory")
            
    async def search_contexts(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search contexts.
        
        Args:
            query: Search query
            filters: Search filters
            
        Returns:
            Search results
        """
        try:
            # Prepare request data
            data = {
                "query": query,
                "filters": filters or {}
            }
            
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/context/search",
                json=data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("contexts", [])
                else:
                    error = await response.text()
                    raise ExtensionError(f"Context search failed: {error}", "search_contexts")
                    
        except Exception as e:
            logger.error(f"Context search error: {e}")
            raise ExtensionError(f"Context search error: {e}", "search_contexts")
            
    async def create_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a context.
        
        Args:
            context_data: Context data
            
        Returns:
            Created context
        """
        try:
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/context",
                json=context_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 201:
                    result = await response.json()
                    return result.get("context")
                else:
                    error = await response.text()
                    raise ExtensionError(f"Context creation failed: {error}", "create_context")
                    
        except Exception as e:
            logger.error(f"Context creation error: {e}")
            raise ExtensionError(f"Context creation error: {e}", "create_context")
            
    async def update_context(self, context_id: int, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a context.
        
        Args:
            context_id: Context ID
            context_data: Context data
            
        Returns:
            Updated context
        """
        try:
            # Send request
            async with self.http_session.put(
                f"{self.server_url}/api/v1/context/{context_id}",
                json=context_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("context")
                else:
                    error = await response.text()
                    raise ExtensionError(f"Context update failed: {error}", "update_context")
                    
        except Exception as e:
            logger.error(f"Context update error: {e}")
            raise ExtensionError(f"Context update error: {e}", "update_context")
            
    async def delete_context(self, context_id: int) -> bool:
        """
        Delete a context.
        
        Args:
            context_id: Context ID
            
        Returns:
            Whether the context was deleted
        """
        try:
            # Send request
            async with self.http_session.delete(
                f"{self.server_url}/api/v1/context/{context_id}",
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    return True
                else:
                    error = await response.text()
                    raise ExtensionError(f"Context deletion failed: {error}", "delete_context")
                    
        except Exception as e:
            logger.error(f"Context deletion error: {e}")
            raise ExtensionError(f"Context deletion error: {e}", "delete_context")
            
    async def search_relations(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search relations.
        
        Args:
            query: Search query
            filters: Search filters
            
        Returns:
            Search results
        """
        try:
            # Prepare request data
            data = {
                "query": query,
                "filters": filters or {}
            }
            
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/relation/search",
                json=data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("relations", [])
                else:
                    error = await response.text()
                    raise ExtensionError(f"Relation search failed: {error}", "search_relations")
                    
        except Exception as e:
            logger.error(f"Relation search error: {e}")
            raise ExtensionError(f"Relation search error: {e}", "search_relations")
            
    async def create_relation(self, relation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a relation.
        
        Args:
            relation_data: Relation data
            
        Returns:
            Created relation
        """
        try:
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/relation",
                json=relation_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 201:
                    result = await response.json()
                    return result.get("relation")
                else:
                    error = await response.text()
                    raise ExtensionError(f"Relation creation failed: {error}", "create_relation")
                    
        except Exception as e:
            logger.error(f"Relation creation error: {e}")
            raise ExtensionError(f"Relation creation error: {e}", "create_relation")
            
    async def update_relation(self, relation_id: int, relation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a relation.
        
        Args:
            relation_id: Relation ID
            relation_data: Relation data
            
        Returns:
            Updated relation
        """
        try:
            # Send request
            async with self.http_session.put(
                f"{self.server_url}/api/v1/relation/{relation_id}",
                json=relation_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("relation")
                else:
                    error = await response.text()
                    raise ExtensionError(f"Relation update failed: {error}", "update_relation")
                    
        except Exception as e:
            logger.error(f"Relation update error: {e}")
            raise ExtensionError(f"Relation update error: {e}", "update_relation")
            
    async def delete_relation(self, relation_id: int) -> bool:
        """
        Delete a relation.
        
        Args:
            relation_id: Relation ID
            
        Returns:
            Whether the relation was deleted
        """
        try:
            # Send request
            async with self.http_session.delete(
                f"{self.server_url}/api/v1/relation/{relation_id}",
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    return True
                else:
                    error = await response.text()
                    raise ExtensionError(f"Relation deletion failed: {error}", "delete_relation")
                    
        except Exception as e:
            logger.error(f"Relation deletion error: {e}")
            raise ExtensionError(f"Relation deletion error: {e}", "delete_relation")
            
    async def get_config(self) -> Dict[str, Any]:
        """
        Get configuration.
        
        Returns:
            Configuration
        """
        try:
            # Send request
            async with self.http_session.get(
                f"{self.server_url}/api/v1/config",
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("config", {})
                else:
                    error = await response.text()
                    raise ExtensionError(f"Config retrieval failed: {error}", "get_config")
                    
        except Exception as e:
            logger.error(f"Config retrieval error: {e}")
            raise ExtensionError(f"Config retrieval error: {e}", "get_config")
            
    async def update_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update configuration.
        
        Args:
            config_data: Configuration data
            
        Returns:
            Updated configuration
        """
        try:
            # Send request
            async with self.http_session.put(
                f"{self.server_url}/api/v1/config",
                json=config_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result.get("config", {})
                else:
                    error = await response.text()
                    raise ExtensionError(f"Config update failed: {error}", "update_config")
                    
        except Exception as e:
            logger.error(f"Config update error: {e}")
            raise ExtensionError(f"Config update error: {e}", "update_config")
            
    async def export_data(self, format: str = "json") -> Dict[str, Any]:
        """
        Export data.
        
        Args:
            format: Export format
            
        Returns:
            Export result
        """
        try:
            # Send request
            async with self.http_session.get(
                f"{self.server_url}/api/v1/admin/export",
                params={"format": format},
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error = await response.text()
                    raise ExtensionError(f"Data export failed: {error}", "export_data")
                    
        except Exception as e:
            logger.error(f"Data export error: {e}")
            raise ExtensionError(f"Data export error: {e}", "export_data")
            
    async def backup_data(self) -> Dict[str, Any]:
        """
        Backup data.
        
        Returns:
            Backup result
        """
        try:
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/admin/backup",
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error = await response.text()
                    raise ExtensionError(f"Data backup failed: {error}", "backup_data")
                    
        except Exception as e:
            logger.error(f"Data backup error: {e}")
            raise ExtensionError(f"Data backup error: {e}", "backup_data")
            
    async def restore_data(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restore data.
        
        Args:
            backup_data: Backup data
            
        Returns:
            Restore result
        """
        try:
            # Send request
            async with self.http_session.post(
                f"{self.server_url}/api/v1/admin/restore",
                json=backup_data,
                headers=self._get_auth_headers()
            ) as response:
                # Handle response
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error = await response.text()
                    raise ExtensionError(f"Data restore failed: {error}", "restore_data")
                    
        except Exception as e:
            logger.error(f"Data restore error: {e}")
            raise ExtensionError(f"Data restore error: {e}", "restore_data")
            
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Authentication headers
        """
        headers = {}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        return headers
        
    async def close(self):
        """
        Close the client.
        """
        try:
            # Close WebSocket
            await self.disconnect_websocket()
            
            # Close HTTP session
            if self.http_session:
                await self.http_session.close()
                
            logger.info("Extension client closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing extension client: {e}")
            
    async def __aenter__(self):
        """
        Async context manager entry.
        """
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        """
        await self.close()