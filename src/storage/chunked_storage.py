"""
Chunked storage system for the MCP Multi-Context Memory System.
"""
import asyncio
import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import math

from ..database.models import Memory, MemoryChunk
# from ..database.enhanced_memory_db import EnhancedMemoryDB
from ..utils.compression import ContentCompressor

logger = logging.getLogger(__name__)

class ChunkedStorageManager:
    """Manage chunked storage for large memories."""
    
    def __init__(self, db, chunk_size: int = 10000, max_chunks: int = 100):
        self.db = db
        self.chunk_size = chunk_size
        self.max_chunks = max_chunks
        self.compression_manager = ContentCompressor()
        
        # Cache for chunks
        self.chunk_cache = {}
        self.cache_size = 1000
        self.cache_hits = 0
        self.cache_misses = 0
    
    async def store_memory_in_chunks(self, memory_id: int, content: str, compress: bool = True) -> bool:
        """
        Store memory content in chunks.
        
        Args:
            memory_id: ID of the memory
            content: Content to store
            compress: Whether to compress chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate chunks
            chunks = self._split_content_into_chunks(content)
            
            # Store chunks
            chunk_ids = []
            for i, chunk_content in enumerate(chunks):
                # Compress chunk if requested
                if compress:
                    compressed_content, is_compressed = self.compression_manager.compress(chunk_content)
                    compression_ratio = self.compression_manager.get_compression_ratio(
                        chunk_content, compressed_content
                    ) if is_compressed else 0.0
                else:
                    compressed_content = chunk_content
                    compression_ratio = 0.0
                
                # Create chunk
                chunk_data = {
                    "memory_id": memory_id,
                    "chunk_index": i,
                    "content": compressed_content,
                    "original_size": len(chunk_content),
                    "compressed_size": len(compressed_content),
                    "compression_ratio": compression_ratio,
                    "hash": self._calculate_hash(chunk_content)
                }
                
                chunk = await self.db.create_memory_chunk(chunk_data)
                chunk_ids.append(chunk.id)
                
                # Cache chunk
                self._cache_chunk(chunk.id, chunk_content if not compress else compressed_content)
            
            # Update memory with chunk information
            await self.db.update_memory_chunks(memory_id, chunk_ids)
            
            logger.info(f"Stored memory {memory_id} in {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory {memory_id} in chunks: {e}")
            return False
    
    async def get_memory_from_chunks(self, memory_id: int, use_cache: bool = True) -> Optional[str]:
        """
        Get memory content from chunks.
        
        Args:
            memory_id: ID of the memory
            use_cache: Whether to use chunk cache
            
        Returns:
            Memory content or None if not found
        """
        try:
            # Get chunk information
            memory = await self.db.get_memory(memory_id)
            if not memory or not memory.chunks:
                return None
            
            # Get chunks
            chunks = await self.db.get_memory_chunks(memory_id)
            
            # Reconstruct content
            content_parts = []
            for chunk in sorted(chunks, key=lambda c: c.chunk_index):
                # Try to get from cache first
                chunk_content = None
                
                if use_cache:
                    chunk_content = self._get_cached_chunk(chunk.id)
                
                # If not in cache, get from database
                if not chunk_content:
                    chunk_content = chunk.content
                    self.cache_misses += 1
                    
                    # Cache the chunk
                    self._cache_chunk(chunk.id, chunk_content)
                else:
                    self.cache_hits += 1
                
                content_parts.append(chunk_content)
            
            # Decompress if needed
            content = "".join(content_parts)
            if memory.content_compressed:
                content = self.compression_manager.decompress(content)
            
            logger.info(f"Retrieved memory {memory_id} from {len(chunks)} chunks")
            return content
            
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id} from chunks: {e}")
            return None
    
    async def update_memory_chunks(self, memory_id: int, content: str, compress: bool = True) -> bool:
        """
        Update memory content in chunks.
        
        Args:
            memory_id: ID of the memory
            content: New content
            compress: Whether to compress chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete existing chunks
            await self.delete_memory_chunks(memory_id)
            
            # Store new chunks
            success = await self.store_memory_in_chunks(memory_id, content, compress)
            
            if success:
                logger.info(f"Updated memory {memory_id} in chunks")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id} in chunks: {e}")
            return False
    
    async def delete_memory_chunks(self, memory_id: int) -> bool:
        """
        Delete all chunks for a memory.
        
        Args:
            memory_id: ID of the memory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get chunks
            chunks = await self.db.get_memory_chunks(memory_id)
            
            # Delete chunks
            for chunk in chunks:
                await self.db.delete_memory_chunk(chunk.id)
                # Remove from cache
                self._remove_cached_chunk(chunk.id)
            
            # Update memory
            await self.db.update_memory_chunks(memory_id, [])
            
            logger.info(f"Deleted chunks for memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chunks for memory {memory_id}: {e}")
            return False
    
    def _split_content_into_chunks(self, content: str) -> List[str]:
        """
        Split content into chunks.
        
        Args:
            content: Content to split
            
        Returns:
            List of chunks
        """
        # Calculate number of chunks needed
        content_length = len(content)
        num_chunks = math.ceil(content_length / self.chunk_size)
        
        # Limit number of chunks
        if num_chunks > self.max_chunks:
            logger.warning(f"Content requires {num_chunks} chunks, limiting to {self.max_chunks}")
            num_chunks = self.max_chunks
            self.chunk_size = math.ceil(content_length / num_chunks)
        
        # Split content
        chunks = []
        for i in range(num_chunks):
            start = i * self.chunk_size
            end = start + self.chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_hash(self, content: str) -> str:
        """
        Calculate SHA-256 hash of content.
        
        Args:
            content: Content to hash
            
        Returns:
            Hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _cache_chunk(self, chunk_id: int, content: str):
        """
        Cache a chunk.
        
        Args:
            chunk_id: ID of the chunk
            content: Chunk content
        """
        # Check cache size
        if len(self.chunk_cache) >= self.cache_size:
            # Remove oldest chunk
            oldest_key = next(iter(self.chunk_cache))
            del self.chunk_cache[oldest_key]
        
        # Add to cache
        self.chunk_cache[chunk_id] = content
    
    def _get_cached_chunk(self, chunk_id: int) -> Optional[str]:
        """
        Get a chunk from cache.
        
        Args:
            chunk_id: ID of the chunk
            
        Returns:
            Chunk content or None if not found
        """
        return self.chunk_cache.get(chunk_id)
    
    def _remove_cached_chunk(self, chunk_id: int):
        """
        Remove a chunk from cache.
        
        Args:
            chunk_id: ID of the chunk
        """
        if chunk_id in self.chunk_cache:
            del self.chunk_cache[chunk_id]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.chunk_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "max_cache_size": self.cache_size
        }
    
    async def get_chunk_stats(self, memory_id: int) -> Dict[str, Any]:
        """
        Get chunk statistics for a memory.
        
        Args:
            memory_id: ID of the memory
            
        Returns:
            Chunk statistics
        """
        try:
            # Get chunks
            chunks = await self.db.get_memory_chunks(memory_id)
            
            if not chunks:
                return {}
            
            # Calculate statistics
            total_original_size = sum(chunk.original_size for chunk in chunks)
            total_compressed_size = sum(chunk.compressed_size for chunk in chunks)
            avg_compression_ratio = sum(chunk.compression_ratio for chunk in chunks) / len(chunks)
            
            return {
                "num_chunks": len(chunks),
                "total_original_size": total_original_size,
                "total_compressed_size": total_compressed_size,
                "compression_ratio": (total_original_size - total_compressed_size) / total_original_size if total_original_size > 0 else 0,
                "avg_compression_ratio": avg_compression_ratio,
                "avg_chunk_size": total_original_size / len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Failed to get chunk stats for memory {memory_id}: {e}")
            return {}
    
    async def optimize_chunk_storage(self) -> Dict[str, Any]:
        """
        Optimize chunk storage.
        
        Returns:
            Optimization results
        """
        try:
            # Get all memories with chunks
            memories = await self.db.get_memories_with_chunks()
            
            optimized_count = 0
            total_savings = 0
            
            for memory in memories:
                # Get chunk stats
                stats = await self.get_chunk_stats(memory.id)
                
                # Check if optimization is needed
                if stats.get("num_chunks", 0) > self.max_chunks:
                    # Rechunk with larger chunk size
                    content = await self.get_memory_from_chunks(memory.id)
                    if content:
                        # Calculate new chunk size
                        new_chunk_size = math.ceil(len(content) / self.max_chunks)
                        
                        # Temporarily store old settings
                        old_chunk_size = self.chunk_size
                        old_max_chunks = self.max_chunks
                        
                        # Set new settings
                        self.chunk_size = new_chunk_size
                        self.max_chunks = self.max_chunks
                        
                        # Update chunks
                        await self.update_memory_chunks(memory.id, content)
                        
                        # Restore old settings
                        self.chunk_size = old_chunk_size
                        self.max_chunks = old_max_chunks
                        
                        optimized_count += 1
                        total_savings += stats.get("num_chunks", 0) - self.max_chunks
            
            return {
                "optimized_memories": optimized_count,
                "total_chunks_saved": total_savings,
                "cache_stats": self.get_cache_stats()
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize chunk storage: {e}")
            return {}