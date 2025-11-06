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
Configuration schemas for the enhanced MCP Multi-Context Memory System.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class CompressionConfig(BaseModel):
    """Configuration for content compression."""
    enabled: bool = Field(default=True, description="Enable content compression")
    algorithm: str = Field(default="gzip", pattern="^(gzip|lz4|zstd|brotli)$")
    level: int = Field(default=6, ge=1, le=9, description="Compression level")
    threshold: int = Field(default=1024, ge=0, description="Minimum size to compress (bytes)")

class LazyLoadingConfig(BaseModel):
    """Configuration for lazy loading."""
    enabled: bool = Field(default=True, description="Enable lazy loading")
    preview_length: int = Field(default=100, ge=0, description="Preview text length")
    eager_load_threshold: int = Field(default=5000, ge=0, description="Size threshold for eager loading")

class ChunkedStorageConfig(BaseModel):
    """Configuration for chunked storage."""
    enabled: bool = Field(default=False, description="Enable chunked storage")
    chunk_size: int = Field(default=10000, ge=1000, description="Chunk size in characters")
    max_chunks: int = Field(default=100, ge=1, description="Maximum number of chunks per memory")
    
    # Helper method to configure for large single content
    @classmethod
    def for_large_single_content(cls, max_size: int = 1000000):
        """Configure chunked storage to store large content as a single chunk."""
        return cls(
            enabled=True,
            chunk_size=max_size,  # Very large chunk size
            max_chunks=1          # Force single chunk
        )

class HybridStorageConfig(BaseModel):
    """Configuration for hybrid storage."""
    enabled: bool = Field(default=False, description="Enable hybrid storage")
    local_threshold: int = Field(default=50000, description="Threshold for local storage (bytes)")
    remote_threshold: int = Field(default=1000000, description="Threshold for remote storage (bytes)")
    backends: List[str] = Field(default=["filesystem"], description="Available storage backends")
    compression_enabled: bool = Field(default=True, description="Enable compression for hybrid storage")

class DeduplicationConfig(BaseModel):
    """Configuration for deduplication."""
    enabled: bool = Field(default=False, description="Enable deduplication")
    strategy: str = Field(default="content_hash", pattern="^(content_hash|fuzzy|semantic)$")
    threshold: float = Field(default=0.95, ge=0.0, le=1.0, description="Similarity threshold")
    batch_size: int = Field(default=1000, ge=1, description="Batch size for processing")

class ArchivalConfig(BaseModel):
    """Configuration for archival."""
    enabled: bool = Field(default=False, description="Enable archival")
    retention_days: int = Field(default=365, ge=1, description="Retention period in days")
    archive_format: str = Field(default="tar.gz", pattern="^(zip|tar\\.gz|tar\\.bz2)$")
    compression_level: int = Field(default=6, ge=1, le=9, description="Archive compression level")

class DistributedStorageConfig(BaseModel):
    """Configuration for distributed storage."""
    enabled: bool = Field(default=False, description="Enable distributed storage")
    replication_factor: int = Field(default=2, ge=1, description="Number of replicas")
    consistency_level: str = Field(default="eventual", pattern="^(strong|eventual|weak)$")
    nodes: List[str] = Field(default=[], description="Storage node addresses")

class MonitoringConfig(BaseModel):
    """Configuration for monitoring."""
    enabled: bool = Field(default=True, description="Enable monitoring")
    metrics_interval: int = Field(default=60, ge=1, description="Metrics collection interval (seconds)")
    retention_hours: int = Field(default=24, ge=1, description="Metrics retention period (hours)")
    alerts_enabled: bool = Field(default=True, description="Enable alerts")

class SecurityConfig(BaseModel):
    """Configuration for security."""
    encryption_enabled: bool = Field(default=False, description="Enable encryption at rest")
    encryption_algorithm: str = Field(default="AES-256", description="Encryption algorithm")
    access_logging: bool = Field(default=True, description="Enable access logging")
    rate_limiting: bool = Field(default=True, description="Enable rate limiting")

class SystemConfig(BaseModel):
    """Overall system configuration."""
    compression: CompressionConfig = Field(default_factory=CompressionConfig)
    lazy_loading: LazyLoadingConfig = Field(default_factory=LazyLoadingConfig)
    chunked_storage: ChunkedStorageConfig = Field(default_factory=ChunkedStorageConfig)
    hybrid_storage: HybridStorageConfig = Field(default_factory=HybridStorageConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    archival: ArchivalConfig = Field(default_factory=ArchivalConfig)
    distributed_storage: DistributedStorageConfig = Field(default_factory=DistributedStorageConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)