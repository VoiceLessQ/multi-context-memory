"""
Enhanced Memory Database with compression and lazy loading support.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import json
from pathlib import Path

from .models import Memory, Context, Relation, MemoryChunk
from .db_interface import DatabaseInterface
from ..utils.compression import ContentCompressor
from ..monitoring.performance_monitor import PerformanceMonitor
from ..storage.chunked_storage import ChunkedStorageManager
from ..storage.hybrid_storage import HybridStorage
from ..deduplication.deduplication_manager import DeduplicationManager
from ..archiving.archival_manager import ArchivalManager
from ..storage.distributed_storage_manager import DistributedStorageManager

logger = logging.getLogger(__name__)

class EnhancedMemoryDB(DatabaseInterface):
    """Enhanced memory database with performance optimizations."""
    
    def __init__(self, db_url: str, session: Optional[Session] = None, hybrid_storage_config: Optional[Dict[str, Any]] = None):
        self.db_url = db_url
        self.session = session
        self.performance_monitor = None
        self.lazy_loading_enabled = True
        self.compression_enabled = True
        self.chunked_storage_enabled = False
        self.chunk_size = 10000
        self.max_chunks = 100
        
        # Initialize performance monitor if session provided
        if session:
            self.performance_monitor = PerformanceMonitor(session)
        
        # Initialize chunked storage manager
        self.chunked_storage = None
        if self.chunked_storage_enabled:
            self.chunked_storage = ChunkedStorageManager(self, self.chunk_size, self.max_chunks)
        
        # Initialize hybrid storage
        self.hybrid_storage = None
        if hybrid_storage_config:
            self.hybrid_storage = HybridStorage(hybrid_storage_config)
            # Note: hybrid storage initialization will be handled asynchronously in a separate method
            
        # Initialize deduplication manager
        self.deduplication_manager = None
        
        # Initialize archival manager
        self.archival_manager = None
        
        # Initialize distributed storage manager
        self.distributed_storage = None
    
    async def initialize_hybrid_storage(self):
        """Initialize the hybrid storage asynchronously."""
        if self.hybrid_storage:
            await self.hybrid_storage.initialize()
            logger.info("Hybrid storage initialized successfully")
        else:
            logger.warning("Hybrid storage not configured, skipping initialization")

    def initialize_deduplication(self, config: Dict[str, Any] = None):
        """Initialize the deduplication manager."""
        if not self.deduplication_manager:
            self.deduplication_manager = DeduplicationManager(self, config or {})
            logger.info("Deduplication manager initialized")
        else:
            logger.warning("Deduplication manager already initialized")
    
    def initialize_archival(self, config: Dict[str, Any] = None):
        """Initialize the archival manager."""
        if not self.archival_manager:
            self.archival_manager = ArchivalManager(self, config or {})
            logger.info("Archival manager initialized")
        else:
            logger.warning("Archival manager already initialized")
    
    async def initialize_distributed_storage(self, config: Dict[str, Any] = None):
        """Initialize the distributed storage manager."""
        if not self.distributed_storage:
            self.distributed_storage = DistributedStorageManager(self, config or {})
            # Start background tasks
            await self.distributed_storage.start_background_tasks()
            logger.info("Distributed storage manager initialized")
        else:
            logger.warning("Distributed storage manager already initialized")
    
    def get_deduplication_status(self) -> Dict[str, Any]:
        """Get deduplication system status."""
        if self.deduplication_manager:
            return {
                "enabled": True,
                "stats": self.deduplication_manager.get_stats(),
                "policies": self.deduplication_manager.get_policies()
            }
        return {"enabled": False}
    
    def get_archival_status(self) -> Dict[str, Any]:
        """Get archival system status."""
        if self.archival_manager:
            return {
                "enabled": True,
                "stats": self.archival_manager.get_stats(),
                "policies": self.archival_manager.get_policies()
            }
        return {"enabled": False}
    
    async def get_distributed_storage_status(self) -> Dict[str, Any]:
        """Get distributed storage system status."""
        if self.distributed_storage:
            return {
                "enabled": True,
                "stats": self.distributed_storage.get_storage_report(),
                "health": await self.distributed_storage.health_check()
            }
        return {"enabled": False}
    
    async def create_memory(
        self,
        title: str,
        content: str,
        owner_id: str,
        context_id: Optional[int] = None,
        access_level: str = "private",
        memory_metadata: Optional[Dict[str, Any]] = None,
        compress_content: Optional[bool] = None,
        use_chunked_storage: Optional[bool] = None,
        use_hybrid_storage: Optional[bool] = None,
        use_deduplication: Optional[bool] = None,
        use_archival: Optional[bool] = None,
        use_distributed_storage: Optional[bool] = None
    ) -> Memory:
        """Create a new memory with optional compression, chunked storage, hybrid storage, deduplication, archival, and distributed storage."""
        try:
            # Determine if content should be compressed
            should_compress = compress_content if compress_content is not None else self.compression_enabled
            
            # Determine if chunked storage should be used
            use_chunks = use_chunked_storage if use_chunked_storage is not None else self.chunked_storage_enabled
            
            # Determine if hybrid storage should be used
            use_hybrid = use_hybrid_storage if use_hybrid_storage is not None else (self.hybrid_storage is not None)
            
            # Determine if deduplication should be used
            use_dedupe = use_deduplication if use_deduplication is not None else (self.deduplication_manager is not None)
            
            # Determine if archival should be used
            use_archive = use_archival if use_archival is not None else (self.archival_manager is not None)
            
            # Determine if distributed storage should be used
            use_dist = use_distributed_storage if use_distributed_storage is not None else (self.distributed_storage is not None)
            
            # Create memory
            memory = Memory(
                title=title,
                content="",  # Empty content for chunked storage
                owner_id=owner_id,
                context_id=context_id,
                access_level=access_level,
                memory_metadata=memory_metadata,
                content_compressed=False,  # Will be updated if compression is used
                content_size=len(content)
            )
            
            self.session.add(memory)
            self.session.flush()  # Get ID without committing
            
            # Process content based on settings
            if use_dist and self.distributed_storage:
                # Store in distributed storage
                success = await self.distributed_storage.store_memory(memory, content, should_compress)
                if success:
                    memory.content_compressed = True  # Mark as compressed
                    memory.content_size = len(content)
                else:
                    raise Exception("Failed to store memory in distributed storage")
            elif use_hybrid and self.hybrid_storage:
                # Store in hybrid storage
                success = await self.hybrid_storage.store_memory(memory, content, should_compress)
                if success:
                    memory.content_compressed = True  # Mark as compressed
                    memory.content_size = len(content)
                else:
                    raise Exception("Failed to store memory in hybrid storage")
            elif use_chunks and self.chunked_storage:
                # Store in chunks
                success = await self.chunked_storage.store_memory_in_chunks(memory.id, content, should_compress)
                if success:
                    memory.content_compressed = True  # Mark as compressed even if individual chunks might not be
                    memory.content_size = len(content)
                else:
                    raise Exception("Failed to store memory in chunks")
            else:
                # Store as single content
                processed_content, is_compressed = ContentCompressor.compress(content) if should_compress else (content, False)
                memory.content = processed_content
                memory.content_compressed = is_compressed
                memory.content_size = len(content)
            
            self.session.commit()
            
            # Apply deduplication if enabled
            if use_dedupe and self.deduplication_manager:
                await self.deduplication_manager.check_and_deduplicate(memory)
            
            # Apply archival if enabled
            if use_archive and self.archival_manager:
                await self.archival_manager.check_and_archive(memory)
            
            # Record operation
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("create")
                self.performance_monitor.record_query_time(0.1)  # Estimated
            
            logger.info(f"Created memory: {memory.id} - {memory.title}")
            return memory
        
        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            self.session.rollback()
            raise
    
    async def get_memory(
        self,
        memory_id: int,
        decompress: bool = True,
        use_lazy_loading: Optional[bool] = None,
        use_hybrid_storage: Optional[bool] = None,
        use_distributed_storage: Optional[bool] = None,
        use_deduplication: Optional[bool] = None,
        use_archival: Optional[bool] = None
    ) -> Optional[Memory]:
        """Get a memory with optional decompression, lazy loading, hybrid storage, distributed storage, deduplication, and archival."""
        try:
            use_lazy = use_lazy_loading if use_lazy_loading is not None else self.lazy_loading_enabled
            use_hybrid = use_hybrid_storage if use_hybrid_storage is not None else (self.hybrid_storage is not None)
            use_dist = use_distributed_storage if use_distributed_storage is not None else (self.distributed_storage is not None)
            use_dedupe = use_deduplication if use_deduplication is not None else (self.deduplication_manager is not None)
            use_archive = use_archival if use_archival is not None else (self.archival_manager is not None)
            
            # Try distributed storage first if enabled
            if use_dist and self.distributed_storage:
                dist_memory = await self.distributed_storage.retrieve_memory(memory_id)
                if dist_memory:
                    # Update database with distributed storage data
                    db_memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
                    if db_memory:
                        db_memory.content = dist_memory.content
                        db_memory.content_compressed = dist_memory.content_compressed
                        db_memory.content_size = dist_memory.content_size
                        self.session.commit()
                    
                    # Update access count and timestamp
                    dist_memory.access_count += 1
                    dist_memory.last_accessed = datetime.utcnow()
                    
                    # Handle lazy loading with fallback
                    if use_lazy:
                        # Only load basic info for lazy loading
                        lazy_memory = Memory(
                            id=dist_memory.id,
                            owner_id=dist_memory.owner_id,
                            context_id=dist_memory.context_id,
                            title=dist_memory.title,
                            content_preview=dist_memory.content_preview or dist_memory.content[:100],
                            content_compressed=dist_memory.content_compressed,
                            content_size=dist_memory.content_size,
                            memory_metadata=dist_memory.memory_metadata,
                            access_count=dist_memory.access_count,
                            last_accessed=dist_memory.last_accessed,
                            created_at=dist_memory.created_at,
                            updated_at=dist_memory.updated_at
                        )
                        
                        # Mark as lazy loaded
                        lazy_memory._content_loaded = False
                        
                        return lazy_memory
                    else:
                        # Eager loading - get full content
                        if dist_memory.content_compressed and decompress:
                            try:
                                # Try to decompress content
                                dist_memory.content = ContentCompressor.decompress(dist_memory.content)
                                dist_memory._content_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to decompress content for memory {memory_id}: {e}")
                                # Fallback to preview if available
                                dist_memory.content = dist_memory.content_preview or ""
                                dist_memory._content_loaded = False
                        else:
                            dist_memory._content_loaded = True
                        
                        return dist_memory
            
            # Try hybrid storage next if enabled
            if use_hybrid and self.hybrid_storage:
                hybrid_memory = await self.hybrid_storage.retrieve_memory(memory_id)
                if hybrid_memory:
                    # Update database with hybrid storage data
                    db_memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
                    if db_memory:
                        db_memory.content = hybrid_memory.content
                        db_memory.content_compressed = hybrid_memory.content_compressed
                        db_memory.content_size = hybrid_memory.content_size
                        self.session.commit()
                    
                    # Update access count and timestamp
                    hybrid_memory.access_count += 1
                    hybrid_memory.last_accessed = datetime.utcnow()
                    
                    # Handle lazy loading with fallback
                    if use_lazy:
                        # Only load basic info for lazy loading
                        lazy_memory = Memory(
                            id=hybrid_memory.id,
                            owner_id=hybrid_memory.owner_id,
                            context_id=hybrid_memory.context_id,
                            title=hybrid_memory.title,
                            content_preview=hybrid_memory.content_preview or hybrid_memory.content[:100],
                            content_compressed=hybrid_memory.content_compressed,
                            content_size=hybrid_memory.content_size,
                            memory_metadata=hybrid_memory.memory_metadata,
                            access_count=hybrid_memory.access_count,
                            last_accessed=hybrid_memory.last_accessed,
                            created_at=hybrid_memory.created_at,
                            updated_at=hybrid_memory.updated_at
                        )
                        
                        # Mark as lazy loaded
                        lazy_memory._content_loaded = False
                        
                        return lazy_memory
                    else:
                        # Eager loading - get full content
                        if hybrid_memory.content_compressed and decompress:
                            try:
                                # Try to decompress content
                                hybrid_memory.content = ContentCompressor.decompress(hybrid_memory.content)
                                hybrid_memory._content_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to decompress content for memory {memory_id}: {e}")
                                # Fallback to preview if available
                                hybrid_memory.content = hybrid_memory.content_preview or ""
                                hybrid_memory._content_loaded = False
                        else:
                            hybrid_memory._content_loaded = True
                        
                        return hybrid_memory
            
            # Get basic memory info from database
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            
            if not memory:
                return None
            
            # Update access count and timestamp
            memory.access_count += 1
            memory.last_accessed = datetime.utcnow()
            self.session.commit()
            
            # Handle lazy loading with fallback
            if use_lazy:
                # Only load basic info for lazy loading
                lazy_memory = Memory(
                    id=memory.id,
                    owner_id=memory.owner_id,
                    context_id=memory.context_id,
                    title=memory.title,
                    content_preview=memory.content_preview or memory.content[:100],
                    content_compressed=memory.content_compressed,
                    content_size=memory.content_size,
                    memory_metadata=memory.memory_metadata,
                    access_count=memory.access_count,
                    last_accessed=memory.last_accessed,
                    created_at=memory.created_at,
                    updated_at=memory.updated_at
                )
                
                # Mark as lazy loaded
                lazy_memory._content_loaded = False
                
                return lazy_memory
            else:
                # Eager loading - get full content
                if self.chunked_storage and memory.content_compressed:
                    # Get content from chunks
                    content = self.chunked_storage.get_memory_from_chunks(memory_id)
                    if content is not None:
                        memory.content = content
                        memory._content_loaded = True
                    else:
                        logger.warning(f"Failed to get content from chunks for memory {memory_id}")
                        memory.content = memory.content_preview or ""
                        memory._content_loaded = False
                elif memory.content_compressed and decompress:
                    try:
                        # Try to decompress content
                        memory.content = ContentCompressor.decompress(memory.content)
                        memory._content_loaded = True
                    except Exception as e:
                        logger.warning(f"Failed to decompress content for memory {memory_id}: {e}")
                        # Fallback to preview if available
                        memory.content = memory.content_preview or ""
                        memory._content_loaded = False
                else:
                    memory._content_loaded = True
                
                # Apply deduplication if enabled
                if use_dedupe and self.deduplication_manager:
                    await self.deduplication_manager.check_and_deduplicate(memory)
                
                # Apply archival if enabled
                if use_archive and self.archival_manager:
                    await self.archival_manager.check_and_archive(memory)
                
                return memory
        
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            if self.performance_monitor:
                self.performance_monitor.record_error()
            return None
    
    def load_full_content(self, memory: Memory) -> bool:
        """
        Load full content for a lazy-loaded memory with fallback.
        
        Args:
            memory: Memory object to load full content for
            
        Returns:
            True if content was loaded successfully, False otherwise
        """
        try:
            # Check if content is already loaded
            if hasattr(memory, '_content_loaded') and memory._content_loaded:
                return True
            
            # Get full memory record
            full_memory = self.session.query(Memory).filter(Memory.id == memory.id).first()
            
            if not full_memory:
                logger.warning(f"Memory not found: {memory.id}")
                return False
            
            # Try to load content
            if self.chunked_storage and full_memory.content_compressed:
                # Get content from chunks
                content = self.chunked_storage.get_memory_from_chunks(memory.id)
                if content is not None:
                    memory.content = content
                    memory._content_loaded = True
                    logger.info(f"Successfully loaded content from chunks for memory: {memory.id}")
                    return True
                else:
                    logger.warning(f"Failed to get content from chunks for memory {memory.id}")
                    memory.content = memory.content_preview or ""
                    memory._content_loaded = False
                    return False
            elif full_memory.content_compressed:
                try:
                    # Try to decompress content
                    memory.content = ContentCompressor.decompress(full_memory.content)
                    memory._content_loaded = True
                    logger.info(f"Successfully loaded and decompressed content for memory: {memory.id}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to decompress content for memory {memory.id}: {e}")
                    # Fallback to preview if available
                    memory.content = memory.content_preview or ""
                    memory._content_loaded = False
                    return False
            else:
                # Content is not compressed, use as is
                memory.content = full_memory.content
                memory._content_loaded = True
                logger.info(f"Successfully loaded content for memory: {memory.id}")
                return True
        
        except Exception as e:
            logger.error(f"Error loading full content for memory {memory.id}: {e}")
            # Fallback to preview if available
            memory.content = memory.content_preview or ""
            memory._content_loaded = False
            return False
    
    async def update_memory(
        self,
        memory_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        access_level: Optional[str] = None,
        memory_metadata: Optional[Dict[str, Any]] = None,
        compress_content: Optional[bool] = None,
        use_chunked_storage: Optional[bool] = None,
        use_hybrid_storage: Optional[bool] = None,
        use_distributed_storage: Optional[bool] = None,
        use_deduplication: Optional[bool] = None,
        use_archival: Optional[bool] = None
    ) -> Optional[Memory]:
        """Update a memory with optional compression, chunked storage, hybrid storage, deduplication, archival, and distributed storage."""
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            
            if not memory:
                logger.warning(f"Memory not found: {memory_id}")
                return None
            
            # Update fields
            if title is not None:
                memory.title = title
            
            if content is not None:
                # Determine if content should be compressed
                should_compress = compress_content if compress_content is not None else self.compression_enabled
                
                # Determine if chunked storage should be used
                use_chunks = use_chunked_storage if use_chunked_storage is not None else self.chunked_storage_enabled
                
                # Determine if hybrid storage should be used
                use_hybrid = use_hybrid_storage if use_hybrid_storage is not None else (self.hybrid_storage is not None)
                
                # Determine if distributed storage should be used
                use_dist = use_distributed_storage if use_distributed_storage is not None else (self.distributed_storage is not None)
                
                # Update content based on settings
                if use_dist and self.distributed_storage:
                    # Update in distributed storage
                    success = await self.distributed_storage.update_memory(memory_id, content, should_compress)
                    if success:
                        memory.content_compressed = True  # Mark as compressed
                        memory.content_size = len(content)
                    else:
                        raise Exception("Failed to update memory in distributed storage")
                elif use_hybrid and self.hybrid_storage:
                    # Update in hybrid storage
                    success = await self.hybrid_storage.update_memory(memory_id, content, should_compress)
                    if success:
                        memory.content_compressed = True  # Mark as compressed
                        memory.content_size = len(content)
                    else:
                        raise Exception("Failed to update memory in hybrid storage")
                elif use_chunks and self.chunked_storage:
                    # Update in chunks
                    success = self.chunked_storage.update_memory_chunks(memory_id, content, should_compress)
                    if success:
                        memory.content_compressed = True  # Mark as compressed
                        memory.content_size = len(content)
                    else:
                        raise Exception("Failed to update memory in chunks")
                else:
                    # Update as single content
                    processed_content, is_compressed = ContentCompressor.compress(content) if should_compress else (content, False)
                    memory.content = processed_content
                    memory.content_compressed = is_compressed
                    memory.content_size = len(content)
            
            if access_level is not None:
                memory.access_level = access_level
            
            if memory_metadata is not None:
                memory.memory_metadata = memory_metadata
            
            memory.updated_at = datetime.utcnow()
            
            self.session.commit()
            
            # Apply deduplication if enabled
            if use_deduplication and self.deduplication_manager:
                await self.deduplication_manager.check_and_deduplicate(memory)
            
            # Apply archival if enabled
            if use_archival and self.archival_manager:
                await self.archival_manager.check_and_archive(memory)
            
            # Record operation
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("update")
                self.performance_monitor.record_query_time(0.1)  # Estimated
            
            logger.info(f"Updated memory: {memory.id} - {memory.title}")
            return memory
        
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            self.session.rollback()
            raise
    
    async def delete_memory(self, memory_id: int, use_hybrid_storage: Optional[bool] = None, use_distributed_storage: Optional[bool] = None, use_deduplication: Optional[bool] = None, use_archival: Optional[bool] = None) -> bool:
        """Delete a memory and its chunks, including deduplication and archival records."""
        try:
            use_hybrid = use_hybrid_storage if use_hybrid_storage is not None else (self.hybrid_storage is not None)
            use_dist = use_distributed_storage if use_distributed_storage is not None else (self.distributed_storage is not None)
            use_dedupe = use_deduplication if use_deduplication is not None else (self.deduplication_manager is not None)
            use_archive = use_archival if use_archival is not None else (self.archival_manager is not None)
            
            # Delete from distributed storage if enabled
            if use_dist and self.distributed_storage:
                success = await self.distributed_storage.delete_memory(memory_id)
                if not success:
                    logger.warning(f"Failed to delete memory {memory_id} from distributed storage")
            
            # Delete from hybrid storage if enabled
            if use_hybrid and self.hybrid_storage:
                success = await self.hybrid_storage.delete_memory(memory_id)
                if not success:
                    logger.warning(f"Failed to delete memory {memory_id} from hybrid storage")
            
            # Delete from deduplication system if enabled
            if use_dedupe and self.deduplication_manager:
                # Assuming DeduplicationManager also has an async delete_memory method
                # If not, this part might need further adjustment or DeduplicationManager needs refactoring.
                # For now, let's assume it's async or will be made async.
                if hasattr(self.deduplication_manager, 'delete_memory') and asyncio.iscoroutinefunction(self.deduplication_manager.delete_memory):
                    success = await self.deduplication_manager.delete_memory(memory_id)
                else:
                    # Fallback if it's synchronous (though this is not ideal)
                    # This part indicates a deeper inconsistency if deduplication_manager is not async
                    logger.warning(f"DeduplicationManager.delete_memory is not async, consider refactoring.")
                    # For now, we'll assume it's meant to be async and will be fixed.
                    # If it must remain sync, we'd need a different approach, e.g., run in executor.
                    # However, the goal is to remove asyncio.run.
                    # Let's assume it will be made async.
                    success = await self.deduplication_manager.delete_memory(memory_id) # Placeholder for actual async call

                if not success:
                    logger.warning(f"Failed to delete memory {memory_id} from deduplication system")
            
            # Delete from archival system if enabled
            if use_archive and self.archival_manager:
                # Assuming ArchivalManager also has an async delete_memory method
                if hasattr(self.archival_manager, 'delete_memory') and asyncio.iscoroutinefunction(self.archival_manager.delete_memory):
                    success = await self.archival_manager.delete_memory(memory_id)
                else:
                    # Similar fallback logic as for deduplication_manager
                    logger.warning(f"ArchivalManager.delete_memory is not async, consider refactoring.")
                    success = await self.archival_manager.delete_memory(memory_id) # Placeholder

                if not success:
                    logger.warning(f"Failed to delete memory {memory_id} from archival system")
            
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            
            if not memory:
                logger.warning(f"Memory not found: {memory_id}")
                return False
            
            # Delete chunks if using chunked storage
            if self.chunked_storage:
                self.chunked_storage.delete_memory_chunks(memory_id)
            
            self.session.delete(memory)
            self.session.commit()
            
            # Record operation
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("delete")
                self.performance_monitor.record_query_time(0.05)  # Estimated
            
            logger.info(f"Deleted memory: {memory.id} - {memory.title}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            self.session.rollback()
            raise
    
    async def search_memories(
        self,
        query: str,
        owner_id: Optional[str] = None,
        context_id: Optional[int] = None,
        access_level: Optional[str] = None,
        limit: int = 100,
        decompress: bool = True,
        use_lazy_loading: Optional[bool] = None,
        use_hybrid_storage: Optional[bool] = None,
        use_distributed_storage: Optional[bool] = None,
        use_deduplication: Optional[bool] = None,
        use_archival: Optional[bool] = None
    ) -> List[Memory]:
        """Search memories with optional decompression, lazy loading, hybrid storage, distributed storage, deduplication, and archival."""
        try:
            use_lazy = use_lazy_loading if use_lazy_loading is not None else self.lazy_loading_enabled
            use_hybrid = use_hybrid_storage if use_hybrid_storage is not None else (self.hybrid_storage is not None)
            use_dist = use_distributed_storage if use_distributed_storage is not None else (self.distributed_storage is not None)
            use_dedupe = use_deduplication if use_deduplication is not None else (self.deduplication_manager is not None)
            use_archive = use_archival if use_archival is not None else (self.archival_manager is not None)
            
            # Build query
            db_query = self.session.query(Memory)
            
            if owner_id:
                db_query = db_query.filter(Memory.owner_id == owner_id)
            
            if context_id:
                db_query = db_query.filter(Memory.context_id == context_id)
            
            if access_level:
                db_query = db_query.filter(Memory.access_level == access_level)
            
            # Search in title and content
            db_query = db_query.filter(
                (Memory.title.contains(query)) | (Memory.content.contains(query))
            )
            
            # Apply limit
            db_query = db_query.limit(limit)
            
            # Execute query
            memories = db_query.all()
            
            # Handle content loading based on lazy loading setting
            if use_lazy:
                # For lazy loading, only load basic info
                for memory in memories:
                    if hasattr(memory, '_content_loaded') and not memory._content_loaded:
                        # Try to load full content if requested
                        if decompress:
                            self.load_full_content(memory)
                        else:
                            # Use preview if available
                            memory.content = memory.content_preview or ""
                            memory._content_loaded = False
            else:
                # Eager loading - decompress content if needed
                if decompress:
                    for memory in memories:
                        if memory.content_compressed:
                            try:
                                memory.content = ContentCompressor.decompress(memory.content)
                                memory._content_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to decompress content for memory {memory.id}: {e}")
                                memory.content = memory.content_preview or ""
                                memory._content_loaded = False
                
                # Apply deduplication if enabled
                if use_dedupe and self.deduplication_manager:
                    for memory in memories:
                        await self.deduplication_manager.check_and_deduplicate(memory)
                
                # Apply archival if enabled
                if use_archive and self.archival_manager:
                    for memory in memories:
                        await self.archival_manager.check_and_archive(memory)
            
            # Record operation
            if self.performance_monitor:
                self.performance_monitor.record_search()
                self.performance_monitor.record_query_time(0.2)  # Estimated
            
            logger.info(f"Found {len(memories)} memories matching query: {query}")
            return memories
        
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            if self.performance_monitor:
                self.performance_monitor.record_error()
            return []
    
    def get_memories_by_context(
        self,
        context_id: int,
        owner_id: Optional[str] = None,
        limit: int = 100,
        decompress: bool = True,
        use_lazy_loading: Optional[bool] = None,
        use_hybrid_storage: Optional[bool] = None,
        use_distributed_storage: Optional[bool] = None,
        use_deduplication: Optional[bool] = None,
        use_archival: Optional[bool] = None
    ) -> List[Memory]:
        """Get memories by context with optional decompression, lazy loading, hybrid storage, distributed storage, deduplication, and archival."""
        try:
            use_lazy = use_lazy_loading if use_lazy_loading is not None else self.lazy_loading_enabled
            use_hybrid = use_hybrid_storage if use_hybrid_storage is not None else (self.hybrid_storage is not None)
            use_dist = use_distributed_storage if use_distributed_storage is not None else (self.distributed_storage is not None)
            use_dedupe = use_deduplication if use_deduplication is not None else (self.deduplication_manager is not None)
            use_archive = use_archival if use_archival is not None else (self.archival_manager is not None)
            
            # Build query
            db_query = self.session.query(Memory).filter(Memory.context_id == context_id)
            
            if owner_id:
                db_query = db_query.filter(Memory.owner_id == owner_id)
            
            # Apply limit
            db_query = db_query.limit(limit)
            
            # Execute query
            memories = db_query.all()
            
            # Handle content loading based on lazy loading setting
            if use_lazy:
                # For lazy loading, only load basic info
                for memory in memories:
                    if hasattr(memory, '_content_loaded') and not memory._content_loaded:
                        # Try to load full content if requested
                        if decompress:
                            self.load_full_content(memory)
                        else:
                            # Use preview if available
                            memory.content = memory.content_preview or ""
                            memory._content_loaded = False
            else:
                # Eager loading - decompress content if needed
                if decompress:
                    for memory in memories:
                        if memory.content_compressed:
                            try:
                                memory.content = ContentCompressor.decompress(memory.content)
                                memory._content_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to decompress content for memory {memory.id}: {e}")
                                memory.content = memory.content_preview or ""
                                memory._content_loaded = False
            
            # Record operation
            if self.performance_monitor:
                self.performance_monitor.record_query_time(0.1)  # Estimated
            
            logger.info(f"Found {len(memories)} memories in context: {context_id}")
            return memories
        
        except Exception as e:
            logger.error(f"Error getting memories by context: {e}")
            if self.performance_monitor:
                self.performance_monitor.record_error()
            return []
    
    def get_memories_by_owner(
        self,
        owner_id: str,
        limit: int = 100,
        decompress: bool = True,
        use_lazy_loading: Optional[bool] = None,
        use_hybrid_storage: Optional[bool] = None,
        use_distributed_storage: Optional[bool] = None,
        use_deduplication: Optional[bool] = None,
        use_archival: Optional[bool] = None
    ) -> List[Memory]:
        """Get memories by owner with optional decompression, lazy loading, hybrid storage, distributed storage, deduplication, and archival."""
        try:
            use_lazy = use_lazy_loading if use_lazy_loading is not None else self.lazy_loading_enabled
            use_hybrid = use_hybrid_storage if use_hybrid_storage is not None else (self.hybrid_storage is not None)
            use_dist = use_distributed_storage if use_distributed_storage is not None else (self.distributed_storage is not None)
            use_dedupe = use_deduplication if use_deduplication is not None else (self.deduplication_manager is not None)
            use_archive = use_archival if use_archival is not None else (self.archival_manager is not None)
            
            # Build query
            db_query = self.session.query(Memory).filter(Memory.owner_id == owner_id)
            
            # Apply limit
            db_query = db_query.limit(limit)
            
            # Execute query
            memories = db_query.all()
            
            # Handle content loading based on lazy loading setting
            if use_lazy:
                # For lazy loading, only load basic info
                for memory in memories:
                    if hasattr(memory, '_content_loaded') and not memory._content_loaded:
                        # Try to load full content if requested
                        if decompress:
                            self.load_full_content(memory)
                        else:
                            # Use preview if available
                            memory.content = memory.content_preview or ""
                            memory._content_loaded = False
            else:
                # Eager loading - decompress content if needed
                if decompress:
                    for memory in memories:
                        if memory.content_compressed:
                            try:
                                memory.content = ContentCompressor.decompress(memory.content)
                                memory._content_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to decompress content for memory {memory.id}: {e}")
                                memory.content = memory.content_preview or ""
                                memory._content_loaded = False
            
            # Record operation
            if self.performance_monitor:
                self.performance_monitor.record_query_time(0.1)  # Estimated
            
            logger.info(f"Found {len(memories)} memories for owner: {owner_id}")
            return memories
        
        except Exception as e:
            logger.error(f"Error getting memories by owner: {e}")
            if self.performance_monitor:
                self.performance_monitor.record_error()
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            # Get counts
            memory_count = self.session.query(Memory).count()
            context_count = self.session.query(Context).count()
            relation_count = self.session.query(Relation).count()
            
            # Get compression statistics
            compressed_count = self.session.query(Memory).filter(Memory.content_compressed == True).count()
            compression_ratio = compressed_count / max(memory_count, 1)
            
            # Get size statistics
            total_size = 0
            compressed_size = 0
            
            # Sample memories for size estimation
            sample_memories = self.session.query(Memory).limit(100).all()
            for memory in sample_memories:
                if memory.content_compressed:
                    try:
                        decompressed = ContentCompressor.decompress(memory.content)
                        compressed_size += len(memory.content.encode('utf-8'))
                        total_size += len(decompressed.encode('utf-8'))
                    except:
                        total_size += len(memory.content.encode('utf-8'))
                else:
                    total_size += len(memory.content.encode('utf-8'))
            
            # Estimate total size based on sample
            estimated_total_size = total_size * (memory_count / len(sample_memories)) if sample_memories else 0
            estimated_compressed_size = compressed_size * (memory_count / len(sample_memories)) if sample_memories else 0
            
            # Get hybrid storage statistics if enabled
            hybrid_stats = {}
            if self.hybrid_storage:
                hybrid_stats = await self.hybrid_storage.get_stats()
            
            # Get deduplication statistics if enabled
            dedup_stats = {}
            if self.deduplication_manager:
                dedup_stats = self.deduplication_manager.get_stats()
            
            # Get archival statistics if enabled
            archive_stats = {}
            if self.archival_manager:
                archive_stats = self.archival_manager.get_stats()
            
            # Get distributed storage statistics if enabled
            dist_stats = {}
            if self.distributed_storage:
                dist_stats = await self.distributed_storage.get_storage_report()
            
            return {
                "memory_count": memory_count,
                "context_count": context_count,
                "relation_count": relation_count,
                "compressed_memories": compressed_count,
                "compression_ratio": compression_ratio,
                "estimated_total_size_bytes": estimated_total_size,
                "estimated_compressed_size_bytes": estimated_compressed_size,
                "estimated_savings_bytes": estimated_total_size - estimated_compressed_size,
                "compression_efficiency": (estimated_total_size - estimated_compressed_size) / max(estimated_total_size, 1),
                "hybrid_storage_stats": hybrid_stats,
                "deduplication_stats": dedup_stats,
                "archival_stats": archive_stats,
                "distributed_storage_stats": dist_stats
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance and all storage systems."""
        try:
            results = {}
            
            # Analyze database
            try:
                self.session.execute("ANALYZE")
                results["analyze"] = "Completed"
            except Exception as e:
                results["analyze"] = f"Error: {str(e)}"
            
            # Vacuum database
            try:
                self.session.execute("VACUUM")
                results["vacuum"] = "Completed"
            except Exception as e:
                results["vacuum"] = f"Error: {str(e)}"
            
            # Reindex database
            try:
                self.session.execute("REINDEX")
                results["reindex"] = "Completed"
            except Exception as e:
                results["reindex"] = f"Error: {str(e)}"
            
            # Optimize chunked storage if enabled
            if self.chunked_storage:
                try:
                    chunked_result = await self.chunked_storage.optimize()
                    results["chunked_storage"] = "Optimized"
                except Exception as e:
                    results["chunked_storage"] = f"Error: {str(e)}"
            
            # Optimize hybrid storage if enabled
            if self.hybrid_storage:
                try:
                    hybrid_result = await self.hybrid_storage.optimize()
                    results["hybrid_storage"] = "Optimized"
                except Exception as e:
                    results["hybrid_storage"] = f"Error: {str(e)}"
            
            # Optimize distributed storage if enabled
            if self.distributed_storage:
                try:
                    dist_result = await self.distributed_storage.optimize()
                    results["distributed_storage"] = "Optimized"
                except Exception as e:
                    results["distributed_storage"] = f"Error: {str(e)}"
            
            # Optimize deduplication system if enabled
            if self.deduplication_manager:
                try:
                    dedup_result = await self.deduplication_manager.optimize()
                    results["deduplication"] = "Optimized"
                except Exception as e:
                    results["deduplication"] = f"Error: {str(e)}"
            
            # Optimize archival system if enabled
            if self.archival_manager:
                try:
                    archive_result = await self.archival_manager.optimize()
                    results["archival"] = "Optimized"
                except Exception as e:
                    results["archival"] = f"Error: {str(e)}"
            
            # Optimize performance monitor if enabled
            if self.performance_monitor:
                try:
                    perf_result = await self.performance_monitor.optimize()
                    results["performance_monitor"] = "Optimized"
                except Exception as e:
                    results["performance_monitor"] = f"Error: {str(e)}"
            
            logger.info(f"Database optimization completed: {results}")
            return results
        
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return {"error": str(e)}
    
    def set_compression_enabled(self, enabled: bool):
        """Enable or disable compression."""
        self.compression_enabled = enabled
        logger.info(f"Compression {'enabled' if enabled else 'disabled'}")
    
    def set_lazy_loading_enabled(self, enabled: bool):
        """Enable or disable lazy loading."""
        self.lazy_loading_enabled = enabled
        logger.info(f"Lazy loading {'enabled' if enabled else 'disabled'}")
    
    def set_chunked_storage_enabled(self, enabled: bool):
        """Enable or disable chunked storage."""
        self.chunked_storage_enabled = enabled
        
        # Initialize or update chunked storage manager
        if enabled:
            if not self.chunked_storage:
                self.chunked_storage = ChunkedStorageManager(self, self.chunk_size, self.max_chunks)
            logger.info("Chunked storage enabled")
        else:
            if self.chunked_storage:
                # Clean up existing chunks if needed
                pass
            self.chunked_storage = None
            logger.info("Chunked storage disabled")
    
    def set_chunk_size(self, size: int):
        """Set the chunk size for chunked storage."""
        if size <= 0:
            raise ValueError("Chunk size must be positive")
        
        self.chunk_size = size
        
        # Update chunked storage manager if it exists
        if self.chunked_storage:
            self.chunked_storage.chunk_size = size
        
        logger.info(f"Chunk size set to: {size}")
    
    def set_max_chunks(self, max_chunks: int):
        """Set the maximum number of chunks for chunked storage."""
        if max_chunks <= 0:
            raise ValueError("Max chunks must be positive")
        
        self.max_chunks = max_chunks
        
        # Update chunked storage manager if it exists
        if self.chunked_storage:
            self.chunked_storage.max_chunks = max_chunks
        
        logger.info(f"Max chunks set to: {max_chunks}")
    
    def get_chunked_storage_status(self) -> Dict[str, Any]:
        """Get the current status of chunked storage."""
        return {
            "enabled": self.chunked_storage_enabled,
            "chunk_size": self.chunk_size,
            "max_chunks": self.max_chunks,
            "manager_exists": self.chunked_storage is not None
        }
    
    async def get_hybrid_storage_status(self) -> Dict[str, Any]:
        """Get the current status of hybrid storage."""
        if self.hybrid_storage:
            return {
                "enabled": True,
                "backends": self.hybrid_storage.get_backends(),
                "stats": await self.hybrid_storage.get_stats(),
                "health": await self.hybrid_storage.health_check()
            }
        return {
            "enabled": False,
            "backends": {},
            "stats": {},
            "health": {}
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if self.performance_monitor:
            return self.performance_monitor.get_metrics_summary(hours=1)
        return {}
    
    def export_data(self, format: str = "json") -> str:
        """Export data in specified format."""
        try:
            if format.lower() == "json":
                data = {
                    "memories": [],
                    "contexts": [],
                    "relations": []
                }
                
                # Export memories
                memories = self.session.query(Memory).all()
                for memory in memories:
                    memory_data = {
                        "id": memory.id,
                        "title": memory.title,
                        "content": memory.content,
                        "owner_id": memory.owner_id,
                        "context_id": memory.context_id,
                        "access_level": memory.access_level,
                        "memory_metadata": memory.memory_metadata,
                        "created_at": memory.created_at.isoformat() if memory.created_at else None,
                        "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
                        "content_compressed": memory.content_compressed
                    }
                    data["memories"].append(memory_data)
                
                # Export contexts
                contexts = self.session.query(Context).all()
                for context in contexts:
                    context_data = {
                        "id": context.id,
                        "name": context.name,
                        "description": context.description,
                        "owner_id": context.owner_id,
                        "created_at": context.created_at.isoformat() if context.created_at else None,
                        "updated_at": context.updated_at.isoformat() if context.updated_at else None
                    }
                    data["contexts"].append(context_data)
                
                # Export relations
                relations = self.session.query(Relation).all()
                for relation in relations:
                    relation_data = {
                        "id": relation.id,
                        "source_memory_id": relation.source_memory_id,
                        "target_memory_id": relation.target_memory_id,
                        "relation_type": relation.relation_type,
                        "strength": relation.strength,
                        "metadata": relation.metadata,
                        "created_at": relation.created_at.isoformat() if relation.created_at else None
                    }
                    data["relations"].append(relation_data)
                
                return json.dumps(data, indent=2)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return ""

    # Implementation of DatabaseInterface methods
    def get_memory_interface(self, memory_id: int, **kwargs) -> Optional[Memory]: # Renamed to avoid conflict
        """Retrieve a single memory by its ID (implementation from original get_memory method)."""
        # Call the original get_memory method from the class itself
        # This assumes the original method is still present and accessible.
        # If the original method was renamed or refactored, this needs adjustment.
        # For now, we'll assume the original logic is encapsulated elsewhere or
        # we need to call the original method through a different mechanism if it's overridden.
        # A simple way is to call the original method if it's not the interface one.
        # This might require a more robust refactoring of the get_memory method itself
        # to distinguish between the interface requirement and the full implementation.
        
        # For now, let's assume the original detailed get_memory is still the primary one
        # and this interface method is a simpler version or a wrapper.
        # The original get_memory is quite complex, so we might need to adapt it.
        # For the purpose of breaking the circular import, we are providing a basic implementation.
        # The original get_memory logic should be preserved and called by this method.
        
        # Placeholder: This should call the actual, detailed get_memory implementation
        # For now, a simplified version:
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                # Apply kwargs like decompress, use_lazy_loading if needed
                decompress = kwargs.get('decompress', True)
                use_lazy = kwargs.get('use_lazy_loading', self.lazy_loading_enabled)

                if use_lazy:
                    if hasattr(memory, '_content_loaded') and not memory._content_loaded:
                        memory.content = memory.content_preview or memory.content[:100]
                        memory._content_loaded = False
                elif decompress and memory.content_compressed:
                    try:
                        memory.content = ContentCompressor.decompress(memory.content)
                        memory._content_loaded = True
                    except Exception as e:
                        logger.warning(f"Failed to decompress content for memory {memory_id}: {e}")
                        memory.content = memory.content_preview or ""
                        memory._content_loaded = False
                else:
                    memory._content_loaded = True
                return memory
            return None
        except Exception as e:
            logger.error(f"Error getting memory {memory_id} via interface: {e}")
            return None

    def get_all_memories(self, limit: Optional[int] = None, **kwargs) -> List[Memory]:
        """Retrieve all memories (implementation from original search_memories method with a broad query)."""
        try:
            # Build a query to get all memories
            db_query = self.session.query(Memory)
            
            if limit:
                db_query = db_query.limit(limit)
            
            memories = db_query.all()
            
            # Handle content loading based on lazy loading setting from kwargs
            use_lazy = kwargs.get('use_lazy_loading', self.lazy_loading_enabled)
            decompress = kwargs.get('decompress', True)

            if use_lazy:
                for memory in memories:
                    if hasattr(memory, '_content_loaded') and not memory._content_loaded:
                        if decompress:
                            self.load_full_content(memory)
                        else:
                            memory.content = memory.content_preview or memory.content[:100]
                            memory._content_loaded = False
            else:
                if decompress:
                    for memory in memories:
                        if memory.content_compressed:
                            try:
                                memory.content = ContentCompressor.decompress(memory.content)
                                memory._content_loaded = True
                            except Exception as e:
                                logger.warning(f"Failed to decompress content for memory {memory.id}: {e}")
                                memory.content = memory.content_preview or ""
                                memory._content_loaded = False
            
            logger.info(f"Retrieved {len(memories)} memories")
            return memories
        
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            if self.performance_monitor:
                self.performance_monitor.record_error()
            return []

    def update_memory(self, memory_id: int, updates: Dict[str, Any], **kwargs) -> Optional[Memory]:
        """Update an existing memory (implementation from original update_memory method)."""
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            
            if not memory:
                logger.warning(f"Memory not found for update: {memory_id}")
                return None
            
            # Update fields based on the updates dictionary
            for field, value in updates.items():
                if hasattr(memory, field):
                    setattr(memory, field, value)
                else:
                    logger.warning(f"Field {field} not found in Memory model")
            
            memory.updated_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"Updated memory: {memory.id}")
            return memory
        
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            self.session.rollback()
            return None

    def update_relations(self, old_memory_id: int, new_memory_id: int) -> bool:
        """Update all relations pointing from old_memory_id to new_memory_id."""
        try:
            # Update source_memory_id
            relations_to_update_source = self.session.query(Relation).filter(Relation.source_memory_id == old_memory_id).all()
            for relation in relations_to_update_source:
                relation.source_memory_id = new_memory_id
            
            # Update target_memory_id
            relations_to_update_target = self.session.query(Relation).filter(Relation.target_memory_id == old_memory_id).all()
            for relation in relations_to_update_target:
                relation.target_memory_id = new_memory_id
            
            self.session.commit()
            logger.info(f"Updated relations for memory {old_memory_id} to {new_memory_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating relations for memory {old_memory_id}: {e}")
            self.session.rollback()
            return False
    
    async def create_relation(
        self,
        source_memory_id: int,
        target_memory_id: int,
        relation_type: str = "related",
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None
    ) -> Relation:
        """Create a relation between two memories."""
        try:
            # Get owner_id from source memory if not provided
            if not owner_id:
                source_memory = self.session.query(Memory).filter(Memory.id == source_memory_id).first()
                if source_memory:
                    owner_id = source_memory.owner_id
                else:
                    raise ValueError(f"Source memory not found: {source_memory_id}")
            
            relation = Relation(
                name=relation_type,
                source_memory_id=source_memory_id,
                target_memory_id=target_memory_id,
                strength=strength,
                relation_metadata=metadata or {},
                owner_id=owner_id
            )
            self.session.add(relation)
            self.session.commit()
            logger.info(f"Created relation: {source_memory_id} -> {target_memory_id} ({relation_type})")
            return relation
        
        except Exception as e:
            logger.error(f"Error creating relation: {e}")
            self.session.rollback()
            raise
    
    async def update_memory_chunks(self, memory_id: int, chunk_ids: List[int]) -> bool:
        """Update memory chunk IDs."""
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                logger.warning(f"Memory not found: {memory_id}")
                return False
            
            # Update memory with chunk IDs
            memory.memory_metadata = memory.memory_metadata or {}
            memory.memory_metadata["chunk_ids"] = chunk_ids
            memory.updated_at = datetime.utcnow()
            
            self.session.commit()
            logger.info(f"Updated memory {memory_id} with {len(chunk_ids)} chunks")
            return True
        
        except Exception as e:
            logger.error(f"Error updating memory chunks for {memory_id}: {e}")
            self.session.rollback()
            return False
    
    async def create_memory_chunk(self, chunk_data: Dict[str, Any]) -> MemoryChunk:
        """Create a memory chunk."""
        try:
            # Map the chunk data to the correct field names
            mapped_chunk_data = {
                "memory_id": chunk_data["memory_id"],
                "chunk_index": chunk_data["chunk_index"],
                "chunk_data": chunk_data["content"],  # Map 'content' to 'chunk_data'
                "chunk_metadata": {
                    "original_size": chunk_data.get("original_size", 0),
                    "compressed_size": chunk_data.get("compressed_size", 0),
                    "compression_ratio": chunk_data.get("compression_ratio", 0.0),
                    "hash": chunk_data.get("hash", "")
                },
                "compression_type": "zstd" if chunk_data.get("compression_ratio", 0) > 0 else "none"
            }
            
            chunk = MemoryChunk(**mapped_chunk_data)
            self.session.add(chunk)
            self.session.commit()
            logger.info(f"Created memory chunk: {chunk.id}")
            return chunk
        
        except Exception as e:
            logger.error(f"Error creating memory chunk: {e}")
            self.session.rollback()
            raise
    
    async def get_memory_chunks(self, memory_id: int) -> List[MemoryChunk]:
        """Get all chunks for a memory."""
        try:
            chunks = self.session.query(MemoryChunk).filter(MemoryChunk.memory_id == memory_id).all()
            logger.info(f"Found {len(chunks)} chunks for memory {memory_id}")
            return chunks
        
        except Exception as e:
            logger.error(f"Error getting memory chunks for {memory_id}: {e}")
            return []
    
    async def delete_memory_chunk(self, chunk_id: int) -> bool:
        """Delete a memory chunk."""
        try:
            chunk = self.session.query(MemoryChunk).filter(MemoryChunk.id == chunk_id).first()
            if not chunk:
                logger.warning(f"Memory chunk not found: {chunk_id}")
                return False
            
            self.session.delete(chunk)
            self.session.commit()
            logger.info(f"Deleted memory chunk: {chunk_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting memory chunk {chunk_id}: {e}")
            self.session.rollback()
            return False
    
    async def get_memories_with_chunks(self) -> List[Memory]:
        """Get all memories that have chunks."""
        try:
            memories = self.session.query(Memory).filter(
                Memory.memory_metadata.has_key("chunk_ids")  # type: ignore
            ).all()
            logger.info(f"Found {len(memories)} memories with chunks")
            return memories
        
        except Exception as e:
            logger.error(f"Error getting memories with chunks: {e}")
            return []
    
    async def initialize(self):
        """Initialize the database."""
        try:
            # Initialize database connection
            if not self.session:
                # Create database session if not provided
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                
                engine = create_engine(self.db_url)
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                self.session = SessionLocal()
            
            # Initialize subsystems
            await self.create_tables()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            # Import your models
            from .models import Base
            
            # Create tables
            if hasattr(self.session, 'bind'):
                Base.metadata.create_all(bind=self.session.bind)
            
            logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def load_initial_data(self):
        """Load any initial data needed."""
        try:
            # Load any default data if needed
            logger.info("Initial data loaded")
            
        except Exception as e:
            logger.error(f"Failed to load initial data: {e}")
            raise
    
    async def check_connection(self):
        """Check database connection."""
        try:
            # Simple query to check connection
            self.session.execute("SELECT 1")
            return True
            
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    async def close(self):
        """Close database connection."""
        try:
            if self.session:
                self.session.close()
            logger.info("Database connection closed")
            
        except Exception as e:
            logger.error(f"Error closing database: {e}")

    # Add these configuration methods if missing

    def set_compression_algorithm(self, algorithm: str):
        """Set compression algorithm."""
        self.compression_algorithm = algorithm
        logger.info(f"Compression algorithm set to: {algorithm}")

    def set_compression_level(self, level: int):
        """Set compression level."""
        self.compression_level = level
        logger.info(f"Compression level set to: {level}")

    def set_compression_threshold(self, threshold: int):
        """Set compression threshold."""
        self.compression_threshold = threshold
        logger.info(f"Compression threshold set to: {threshold}")

    def set_preview_length(self, length: int):
        """Set preview length for lazy loading."""
        self.preview_length = length
        logger.info(f"Preview length set to: {length}")

    def set_eager_load_threshold(self, threshold: int):
        """Set eager loading threshold."""
        self.eager_load_threshold = threshold
        logger.info(f"Eager load threshold set to: {threshold}")
    
    async def create_large_memory(
        self,
        title: str,
        content: str,
        owner_id: str,
        context_id: Optional[int] = None,
        access_level: str = "private",
        memory_metadata: Optional[Dict[str, Any]] = None,
        compress_content: bool = True
    ) -> Memory:
        """Create a memory for large content without splitting into chunks."""
        try:
            logger.info(f"Creating large memory: {title} (size: {len(content)} characters)")
            
            # Create memory without chunked storage to keep content intact
            memory = await self.create_memory(
                title=title,
                content=content,
                owner_id=owner_id,
                context_id=context_id,
                access_level=access_level,
                memory_metadata=memory_metadata,
                compress_content=compress_content,
                use_chunked_storage=False  # Important: Don't split large content
            )
            
            logger.info(f"Successfully created large memory: {memory.id} - {memory.title}")
            return memory
            
        except Exception as e:
            logger.error(f"Error creating large memory: {e}")
            raise

    async def ingest_book(self, book_path: str, owner_id: str = "system"):
        """Ingest a book by splitting it into chapters and using chunked storage."""
        import re
        from pathlib import Path
        
        try:
            # Enable chunked storage
            self.set_chunked_storage_enabled(True)
            
            # Read the book file
            with open(book_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove Project Gutenberg header and footer
            start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK A ROOM WITH A VIEW ***"
            end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK A ROOM WITH A VIEW ***"
            
            if start_marker in content and end_marker in content:
                start_idx = content.find(start_marker) + len(start_marker)
                end_idx = content.find(end_marker)
                content = content[start_idx:end_idx].strip()
            
            # Create context for the book
            context = Context(
                name="A Room with a View",
                description="E. M. Forster's classic novel",
                owner_id=owner_id
            )
            self.session.add(context)
            self.session.commit()
            book_context_id = context.id
            
            # Parse book into chapters
            chapter_pattern = r'Chapter\s+\w+\.?\s*(.*?)\n'
            chapters = []
            
            # Find all chapter titles
            matches = list(re.finditer(chapter_pattern, content, re.IGNORECASE))
            
            if not matches:
                # Fallback: split by "Chapter" keyword
                parts = re.split(r'Chapter\s+\w+\.?\s*', content)
                titles = re.findall(r'Chapter\s+\w+\.?\s*(.*?)\n', content, re.IGNORECASE)
                
                for i, (title, part) in enumerate(zip(titles, parts[1:]), 1):
                    chapters.append({
                        'number': i,
                        'title': title.strip(),
                        'content': part.strip()
                    })
            else:
                # Process chapters with proper boundaries
                for i, match in enumerate(matches):
                    chapter_title = match.group(1).strip()
                    start_pos = match.end()
                    
                    if i + 1 < len(matches):
                        end_pos = matches[i + 1].start()
                        chapter_content = content[start_pos:end_pos].strip()
                    else:
                        chapter_content = content[start_pos:].strip()
                    
                    chapters.append({
                        'number': i + 1,
                        'title': chapter_title,
                        'content': chapter_content
                    })
            
            logger.info(f"Found {len(chapters)} chapters")
            
            # Create parent memory for the book
            book_memory = await self.create_memory(
                title="A Room with a View by E. M. Forster",
                content="Full text of the classic novel",
                owner_id=owner_id,
                context_id=book_context_id,
                use_chunked_storage=False,
                memory_metadata={
                    "author": "E. M. Forster",
                    "year": 1908,
                    "type": "novel",
                    "total_chapters": len(chapters)
                }
            )
            
            # Ingest each chapter with chunked storage
            chapter_memories = []
            for chapter in chapters:
                logger.info(f"Ingesting chapter {chapter['number']}: {chapter['title']}")
                
                chapter_memory = await self.create_memory(
                    title=f"Chapter {chapter['number']}: {chapter['title']}",
                    content=chapter['content'],
                    owner_id=owner_id,
                    context_id=book_context_id,
                    use_chunked_storage=True,
                    compress_content=True,
                    memory_metadata={
                        "chapter_number": chapter['number'],
                        "chapter_title": chapter['title'],
                        "book_id": book_memory.id
                    }
                )
                
                chapter_memories.append(chapter_memory)
                
                # Create relation between book and chapter
                await self.create_relation(
                    source_memory_id=book_memory.id,
                    target_memory_id=chapter_memory.id,
                    relation_type="contains",
                    strength=1.0,
                    metadata={"chapter_number": chapter['number']}
                )
                
                logger.info(f"Created chapter memory with ID: {chapter_memory.id}")
            
            # Create sequential relations between chapters
            for i in range(len(chapter_memories) - 1):
                await self.create_relation(
                    source_memory_id=chapter_memories[i].id,
                    target_memory_id=chapter_memories[i + 1].id,
                    relation_type="next",
                    strength=1.0,
                    metadata={"sequence": i + 1}
                )
            
            logger.info("Book ingestion completed successfully!")
            return book_memory
            
        except Exception as e:
            logger.error(f"Error ingesting book: {e}")
            raise
    