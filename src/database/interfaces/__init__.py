"""
Database interfaces and abstractions for the enhanced memory system.
Clean exports for all interface contracts.
"""

from .repository import (
    MemoryRepository,
    ContextRepository, 
    RelationRepository,
    ChunkRepository,
    UnitOfWork
)

from .storage_strategy import (
    StorageStrategy,
    CompressionStrategy,
    ChunkedStorageStrategy,
    HybridStorageStrategy,
    DistributedStorageStrategy,
    CachingStrategy,
    IndexingStrategy,
    EncryptionStrategy,
    StorageStrategyFactory
)

from .service import (
    MemoryService,
    ContextService,
    RelationService,
    DeduplicationService,
    ArchivalService,
    AnalyticsService,
    ConfigurationService
)

__all__ = [
    # Repository interfaces
    'MemoryRepository',
    'ContextRepository',
    'RelationRepository', 
    'ChunkRepository',
    'UnitOfWork',
    
    # Storage strategy interfaces
    'StorageStrategy',
    'CompressionStrategy',
    'ChunkedStorageStrategy',
    'HybridStorageStrategy',
    'DistributedStorageStrategy',
    'CachingStrategy',
    'IndexingStrategy',
    'EncryptionStrategy',
    'StorageStrategyFactory',
    
    # Service interfaces
    'MemoryService',
    'ContextService',
    'RelationService',
    'DeduplicationService',
    'ArchivalService',
    'AnalyticsService',
    'ConfigurationService'
]