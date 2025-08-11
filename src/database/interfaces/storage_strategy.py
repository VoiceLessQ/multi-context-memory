"""
Storage strategy interfaces for flexible storage backends.
Implements the Strategy pattern for different storage approaches.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..models import Memory, MemoryChunk


class StorageStrategy(ABC):
    """
    Base storage strategy interface.
    Defines the contract for different storage implementations.
    """
    
    @abstractmethod
    async def store(self, memory: Memory, content: str, **kwargs) -> bool:
        """Store memory content using this strategy."""
        pass
    
    @abstractmethod
    async def retrieve(self, memory_id: int, **kwargs) -> Optional[str]:
        """Retrieve memory content using this strategy."""
        pass
    
    @abstractmethod
    async def update(self, memory_id: int, content: str, **kwargs) -> bool:
        """Update memory content using this strategy."""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: int, **kwargs) -> bool:
        """Delete memory content using this strategy."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get strategy-specific statistics."""
        pass


class CompressionStrategy(ABC):
    """
    Compression strategy interface for content compression.
    """
    
    @abstractmethod
    def compress(self, content: str) -> tuple[str, bool]:
        """Compress content. Returns (compressed_content, was_compressed)."""
        pass
    
    @abstractmethod
    def decompress(self, compressed_content: str) -> str:
        """Decompress content."""
        pass
    
    @abstractmethod
    def get_compression_ratio(self, original: str, compressed: str) -> float:
        """Calculate compression ratio."""
        pass


class ChunkedStorageStrategy(StorageStrategy):
    """
    Strategy interface for chunked storage implementations.
    """
    
    @abstractmethod
    async def store_in_chunks(
        self, 
        memory_id: int, 
        content: str, 
        chunk_size: int,
        compress: bool = True
    ) -> List[MemoryChunk]:
        """Store content in chunks."""
        pass
    
    @abstractmethod
    async def retrieve_from_chunks(self, memory_id: int) -> Optional[str]:
        """Retrieve content from chunks."""
        pass
    
    @abstractmethod
    async def update_chunks(
        self, 
        memory_id: int, 
        content: str,
        chunk_size: int,
        compress: bool = True
    ) -> List[MemoryChunk]:
        """Update chunked content."""
        pass
    
    @abstractmethod
    async def delete_chunks(self, memory_id: int) -> bool:
        """Delete all chunks for a memory."""
        pass


class HybridStorageStrategy(StorageStrategy):
    """
    Strategy interface for hybrid storage backends.
    Combines multiple storage backends based on content characteristics.
    """
    
    @abstractmethod
    async def initialize_backends(self, config: Dict[str, Any]) -> None:
        """Initialize storage backends."""
        pass
    
    @abstractmethod
    async def select_backend(self, memory: Memory, content: str) -> str:
        """Select appropriate backend for storage."""
        pass
    
    @abstractmethod
    async def get_backend_info(self, backend_name: str) -> Dict[str, Any]:
        """Get information about a specific backend."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all backends."""
        pass


class DistributedStorageStrategy(StorageStrategy):
    """
    Strategy interface for distributed storage implementations.
    """
    
    @abstractmethod
    async def replicate(self, memory_id: int, content: str, replicas: int = 3) -> bool:
        """Replicate content across nodes."""
        pass
    
    @abstractmethod
    async def get_nodes(self) -> List[Dict[str, Any]]:
        """Get available storage nodes."""
        pass
    
    @abstractmethod
    async def rebalance(self) -> Dict[str, Any]:
        """Rebalance data across nodes."""
        pass
    
    @abstractmethod
    async def get_storage_report(self) -> Dict[str, Any]:
        """Get distributed storage report."""
        pass


class CachingStrategy(ABC):
    """
    Caching strategy interface for performance optimization.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class IndexingStrategy(ABC):
    """
    Indexing strategy interface for search optimization.
    """
    
    @abstractmethod
    async def index_memory(self, memory: Memory) -> bool:
        """Index a memory for search."""
        pass
    
    @abstractmethod
    async def update_index(self, memory_id: int, memory: Memory) -> bool:
        """Update memory index."""
        pass
    
    @abstractmethod
    async def remove_from_index(self, memory_id: int) -> bool:
        """Remove memory from index."""
        pass
    
    @abstractmethod
    async def search_index(self, query: str, filters: Dict[str, Any]) -> List[int]:
        """Search index and return memory IDs."""
        pass
    
    @abstractmethod
    async def rebuild_index(self) -> bool:
        """Rebuild the entire index."""
        pass


class EncryptionStrategy(ABC):
    """
    Encryption strategy interface for content security.
    """
    
    @abstractmethod
    def encrypt(self, content: str, key: Optional[str] = None) -> tuple[str, str]:
        """Encrypt content. Returns (encrypted_content, encryption_key)."""
        pass
    
    @abstractmethod
    def decrypt(self, encrypted_content: str, key: str) -> str:
        """Decrypt content using key."""
        pass
    
    @abstractmethod
    def generate_key(self) -> str:
        """Generate encryption key."""
        pass
    
    @abstractmethod
    def is_encrypted(self, content: str) -> bool:
        """Check if content is encrypted."""
        pass


class StorageStrategyFactory(ABC):
    """
    Factory interface for creating storage strategies.
    Implements the Abstract Factory pattern.
    """
    
    @abstractmethod
    def create_compression_strategy(self, algorithm: str = "zstd") -> CompressionStrategy:
        """Create compression strategy."""
        pass
    
    @abstractmethod
    def create_chunked_storage_strategy(
        self, 
        chunk_size: int = 10000,
        max_chunks: int = 100
    ) -> ChunkedStorageStrategy:
        """Create chunked storage strategy."""
        pass
    
    @abstractmethod
    def create_hybrid_storage_strategy(
        self, 
        config: Dict[str, Any]
    ) -> HybridStorageStrategy:
        """Create hybrid storage strategy."""
        pass
    
    @abstractmethod
    def create_distributed_storage_strategy(
        self, 
        config: Dict[str, Any]
    ) -> DistributedStorageStrategy:
        """Create distributed storage strategy."""
        pass
    
    @abstractmethod
    def create_caching_strategy(
        self, 
        backend: str = "memory",
        config: Dict[str, Any] = None
    ) -> CachingStrategy:
        """Create caching strategy."""
        pass
    
    @abstractmethod
    def create_indexing_strategy(
        self, 
        engine: str = "sqlite",
        config: Dict[str, Any] = None
    ) -> IndexingStrategy:
        """Create indexing strategy."""
        pass
    
    @abstractmethod
    def create_encryption_strategy(
        self, 
        algorithm: str = "AES256",
        config: Dict[str, Any] = None
    ) -> EncryptionStrategy:
        """Create encryption strategy."""
        pass