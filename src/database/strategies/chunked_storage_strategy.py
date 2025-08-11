"""
Chunked storage strategy implementation.
Extracts chunked storage logic from enhanced_memory_db.py.
"""
import logging
import hashlib
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..interfaces.storage_strategy import ChunkedStorageStrategy, CompressionStrategy
from ..interfaces.repository import ChunkRepository
from ..models import Memory, MemoryChunk
from .compression_strategy import ZstdCompressionStrategy

logger = logging.getLogger(__name__)


class SQLAlchemyChunkedStorageStrategy(ChunkedStorageStrategy):
    """
    SQLAlchemy-based chunked storage implementation.
    Handles large content by splitting into manageable chunks.
    """
    
    def __init__(
        self, 
        chunk_repository: ChunkRepository,
        session: Session,
        chunk_size: int = 10000,
        max_chunks: int = 100,
        compression_strategy: Optional[CompressionStrategy] = None
    ):
        self.chunk_repository = chunk_repository
        self.session = session
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.compression_strategy = compression_strategy or ZstdCompressionStrategy()
    
    async def store(self, memory: Memory, content: str, **kwargs) -> bool:
        """Store memory content using chunked storage."""
        try:
            compress = kwargs.get('compress', True)
            return await self.store_in_chunks(memory.id, content, self.chunk_size, compress)
        except Exception as e:
            logger.error(f"Error storing memory {memory.id} in chunks: {e}")
            return False
    
    async def retrieve(self, memory_id: int, **kwargs) -> Optional[str]:
        """Retrieve memory content from chunks."""
        return await self.retrieve_from_chunks(memory_id)
    
    async def update(self, memory_id: int, content: str, **kwargs) -> bool:
        """Update memory content in chunked storage."""
        try:
            compress = kwargs.get('compress', True)
            # Delete existing chunks first
            await self.delete_chunks(memory_id)
            # Store new chunks
            chunks = await self.store_in_chunks(memory_id, content, self.chunk_size, compress)
            return len(chunks) > 0
        except Exception as e:
            logger.error(f"Error updating chunked memory {memory_id}: {e}")
            return False
    
    async def delete(self, memory_id: int, **kwargs) -> bool:
        """Delete memory chunks."""
        return await self.delete_chunks(memory_id)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get chunked storage statistics."""
        try:
            # Get all chunks
            all_chunks = []
            chunk_count = 0
            total_original_size = 0
            total_compressed_size = 0
            
            # This would need to be implemented in the chunk repository
            # For now, return basic stats
            return {
                "strategy": "chunked_storage",
                "chunk_size": self.chunk_size,
                "max_chunks": self.max_chunks,
                "total_chunks": chunk_count,
                "compression_enabled": self.compression_strategy is not None,
                "total_original_size": total_original_size,
                "total_compressed_size": total_compressed_size,
                "compression_ratio": (total_original_size - total_compressed_size) / max(total_original_size, 1)
            }
        except Exception as e:
            logger.error(f"Error getting chunked storage stats: {e}")
            return {}
    
    async def store_in_chunks(
        self, 
        memory_id: int, 
        content: str, 
        chunk_size: int,
        compress: bool = True
    ) -> List[MemoryChunk]:
        """Store content in chunks with optional compression."""
        try:
            if len(content) <= chunk_size:
                # Content is small enough for a single chunk
                chunk = await self._create_single_chunk(memory_id, content, 0, compress)
                return [chunk] if chunk else []
            
            # Split content into chunks
            chunks = []
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            for i in range(0, len(content), chunk_size):
                chunk_content = content[i:i + chunk_size]
                chunk_index = i // chunk_size
                
                # Check chunk limit
                if len(chunks) >= self.max_chunks:
                    logger.warning(f"Reached maximum chunks ({self.max_chunks}) for memory {memory_id}")
                    break
                
                chunk = await self._create_single_chunk(
                    memory_id, 
                    chunk_content, 
                    chunk_index, 
                    compress,
                    content_hash
                )
                
                if chunk:
                    chunks.append(chunk)
                else:
                    logger.error(f"Failed to create chunk {chunk_index} for memory {memory_id}")
                    # Clean up created chunks on failure
                    for created_chunk in chunks:
                        await self.chunk_repository.delete(created_chunk.id)
                    return []
            
            # Update memory metadata with chunk information
            chunk_ids = [chunk.id for chunk in chunks]
            
            # This would need to be done at the service layer
            # For now, just log the chunk creation
            logger.info(f"Created {len(chunks)} chunks for memory {memory_id}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error storing content in chunks for memory {memory_id}: {e}")
            return []
    
    async def retrieve_from_chunks(self, memory_id: int) -> Optional[str]:
        """Retrieve and reassemble content from chunks."""
        try:
            chunks = await self.chunk_repository.find_by_memory(memory_id)
            
            if not chunks:
                logger.warning(f"No chunks found for memory {memory_id}")
                return None
            
            # Sort chunks by index
            sorted_chunks = sorted(chunks, key=lambda x: x.chunk_index)
            
            # Reassemble content
            content_parts = []
            for chunk in sorted_chunks:
                chunk_content = chunk.chunk_data
                
                # Decompress if needed
                if chunk.compression_type and chunk.compression_type != "none":
                    try:
                        chunk_content = self.compression_strategy.decompress(chunk_content)
                    except Exception as e:
                        logger.error(f"Failed to decompress chunk {chunk.id}: {e}")
                        return None
                
                content_parts.append(chunk_content)
            
            # Join all parts
            full_content = "".join(content_parts)
            
            logger.info(f"Successfully retrieved {len(full_content)} characters from {len(chunks)} chunks for memory {memory_id}")
            return full_content
            
        except Exception as e:
            logger.error(f"Error retrieving content from chunks for memory {memory_id}: {e}")
            return None
    
    async def update_chunks(
        self, 
        memory_id: int, 
        content: str,
        chunk_size: int,
        compress: bool = True
    ) -> List[MemoryChunk]:
        """Update chunks for existing memory."""
        try:
            # Delete existing chunks
            success = await self.delete_chunks(memory_id)
            if not success:
                logger.warning(f"Failed to delete existing chunks for memory {memory_id}")
            
            # Create new chunks
            return await self.store_in_chunks(memory_id, content, chunk_size, compress)
            
        except Exception as e:
            logger.error(f"Error updating chunks for memory {memory_id}: {e}")
            return []
    
    async def delete_chunks(self, memory_id: int) -> bool:
        """Delete all chunks for a memory."""
        try:
            return await self.chunk_repository.delete_by_memory(memory_id)
        except Exception as e:
            logger.error(f"Error deleting chunks for memory {memory_id}: {e}")
            return False
    
    async def _create_single_chunk(
        self, 
        memory_id: int, 
        content: str, 
        chunk_index: int,
        compress: bool = True,
        content_hash: Optional[str] = None
    ) -> Optional[MemoryChunk]:
        """Create a single chunk with optional compression."""
        try:
            original_size = len(content.encode('utf-8'))
            compressed_content = content
            compression_type = "none"
            compressed_size = original_size
            compression_ratio = 0.0
            
            # Apply compression if enabled
            if compress and self.compression_strategy:
                try:
                    compressed_content, was_compressed = self.compression_strategy.compress(content)
                    if was_compressed:
                        compression_type = "zstd"  # Or detect dynamically
                        compressed_size = len(compressed_content.encode('utf-8'))
                        compression_ratio = self.compression_strategy.get_compression_ratio(content, compressed_content)
                except Exception as e:
                    logger.warning(f"Compression failed for chunk {chunk_index}, storing uncompressed: {e}")
            
            # Generate chunk hash
            chunk_hash = content_hash or hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Create chunk data
            chunk_data = {
                "memory_id": memory_id,
                "chunk_index": chunk_index,
                "content": compressed_content,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "hash": chunk_hash
            }
            
            # Create chunk entity
            chunk = MemoryChunk(
                memory_id=memory_id,
                chunk_index=chunk_index,
                chunk_data=compressed_content,
                chunk_metadata={
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": compression_ratio,
                    "hash": chunk_hash
                },
                compression_type=compression_type
            )
            
            # Save chunk
            saved_chunk = await self.chunk_repository.create(chunk)
            
            logger.debug(f"Created chunk {chunk_index} for memory {memory_id} (size: {original_size} -> {compressed_size})")
            return saved_chunk
            
        except Exception as e:
            logger.error(f"Error creating chunk {chunk_index} for memory {memory_id}: {e}")
            return None
    
    def configure_chunk_size(self, chunk_size: int):
        """Configure chunk size."""
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        self.chunk_size = chunk_size
        logger.info(f"Chunk size configured to: {chunk_size}")
    
    def configure_max_chunks(self, max_chunks: int):
        """Configure maximum chunks."""
        if max_chunks <= 0:
            raise ValueError("Max chunks must be positive")
        self.max_chunks = max_chunks
        logger.info(f"Max chunks configured to: {max_chunks}")
    
    def configure_compression_strategy(self, strategy: CompressionStrategy):
        """Configure compression strategy."""
        self.compression_strategy = strategy
        logger.info(f"Compression strategy configured: {type(strategy).__name__}")
    
    async def get_chunk_info(self, memory_id: int) -> Dict[str, Any]:
        """Get information about chunks for a memory."""
        try:
            chunks = await self.chunk_repository.find_by_memory(memory_id)
            
            total_original_size = 0
            total_compressed_size = 0
            compression_types = set()
            
            for chunk in chunks:
                metadata = chunk.chunk_metadata or {}
                total_original_size += metadata.get('original_size', 0)
                total_compressed_size += metadata.get('compressed_size', 0)
                compression_types.add(chunk.compression_type or 'none')
            
            return {
                "memory_id": memory_id,
                "chunk_count": len(chunks),
                "total_original_size": total_original_size,
                "total_compressed_size": total_compressed_size,
                "compression_ratio": (total_original_size - total_compressed_size) / max(total_original_size, 1),
                "compression_types": list(compression_types),
                "average_chunk_size": total_original_size / max(len(chunks), 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting chunk info for memory {memory_id}: {e}")
            return {}
    
    async def optimize_chunks(self, memory_id: int) -> Dict[str, Any]:
        """Optimize chunks by recompressing or reorganizing."""
        try:
            # Retrieve current content
            content = await self.retrieve_from_chunks(memory_id)
            if not content:
                return {"error": "Could not retrieve content for optimization"}
            
            # Get current stats
            old_info = await self.get_chunk_info(memory_id)
            
            # Re-chunk with current settings (this may use better compression)
            new_chunks = await self.update_chunks(memory_id, content, self.chunk_size, True)
            
            # Get new stats
            new_info = await self.get_chunk_info(memory_id)
            
            return {
                "memory_id": memory_id,
                "optimization_result": "success",
                "old_chunks": old_info.get('chunk_count', 0),
                "new_chunks": new_info.get('chunk_count', 0),
                "old_size": old_info.get('total_compressed_size', 0),
                "new_size": new_info.get('total_compressed_size', 0),
                "size_savings": old_info.get('total_compressed_size', 0) - new_info.get('total_compressed_size', 0)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing chunks for memory {memory_id}: {e}")
            return {"error": str(e)}