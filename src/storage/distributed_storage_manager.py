"""
Distributed storage manager for the MCP Multi-Context Memory System.
"""
import asyncio
import logging
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
# Optional imports for distributed storage
try:
    import aiofiles
except ImportError:
    aiofiles = None

try:
    import aioboto3
except ImportError:
    aioboto3 = None

try:
    from azure.storage.blob.aio import BlobServiceClient
except ImportError:
    BlobServiceClient = None

try:
    from google.cloud import storage as gcs
except ImportError:
    gcs = None

try:
    import redis.asyncio as redis
except ImportError:
    redis = None
from dataclasses import dataclass, asdict
import uuid
import shutil
import zipfile
import tarfile

from ..database.models import Memory, Context, Relation
# from ..database.enhanced_memory_db import EnhancedMemoryDB
from ..utils.compression import ContentCompressor
from ..backup.backup_manager import BackupManager

logger = logging.getLogger(__name__)

@dataclass
class StorageBackend:
    """Configuration for a storage backend."""
    name: str
    type: str  # 'local', 's3', 'azure', 'gcs', 'redis'
    config: Dict[str, Any]
    priority: int  # Order of preference (0 = highest)
    enabled: bool = True
    redundancy_factor: int = 1  # Number of copies to maintain
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StorageBackend':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class StorageStats:
    """Storage statistics."""
    backend_name: str
    total_size: int
    file_count: int
    available_space: int
    last_accessed: datetime
    error_count: int
    latency_ms: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['last_accessed'] = self.last_accessed.isoformat()
        return data

class DistributedStorageManager:
    """Manage distributed storage across multiple backends."""
    
    def __init__(self, db, config: Dict = None):
        """
        Initialize the distributed storage manager.
        
        Args:
            db: Enhanced memory database instance
            config: Configuration dictionary
        """
        self.db = db
        self.config = config or {}
        
        # Configuration settings
        self.enabled = self.config.get("distributed_storage_enabled", True)
        self.local_cache_dir = Path(self.config.get("local_cache_directory", "./data/cache"))
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize compression manager
        compression_config = self.config.get("compression", {})
        self.compression_manager = ContentCompressor()
        
        # Initialize backup manager for safety
        self.backup_manager = BackupManager(str(self.local_cache_dir.parent / "backups"))
        
        # Storage backends
        self.backends = {}
        self._initialize_backends()
        
        # Redis client for caching and coordination
        self.redis_client = None
        self._initialize_redis()
        
        # File metadata tracking
        self.metadata_cache = {}
        self._load_metadata_cache()
        
        # Statistics
        self.stats = {
            "total_files": 0,
            "total_size": 0,
            "by_backend": {},
            "operations": {
                "read": 0,
                "write": 0,
                "delete": 0,
                "errors": 0
            },
            "last_operation": None
        }
        
        # Background tasks
        self.cleanup_task = None
        self.health_check_task = None
        
        logger.info(f"Distributed storage manager initialized with {len(self.backends)} backends")
        
    def _initialize_backends(self):
        """Initialize storage backends from configuration."""
        backends_config = self.config.get("backends", {})
        
        # Default backends
        default_backends = {
            "local": StorageBackend(
                name="local",
                type="local",
                config={"path": str(self.local_cache_dir)},
                priority=0,
                enabled=True,
                redundancy_factor=1
            )
        }
        
        # Add configured backends
        for name, config in backends_config.items():
            if "type" not in config:
                logger.warning(f"Backend {name} missing type, skipping")
                continue
                
            try:
                self.backends[name] = StorageBackend(
                    name=name,
                    type=config["type"],
                    config=config.get("config", {}),
                    priority=config.get("priority", 10),
                    enabled=config.get("enabled", True),
                    redundancy_factor=config.get("redundancy_factor", 1)
                )
            except Exception as e:
                logger.error(f"Error initializing backend {name}: {e}")
                
        # Add default backends if not already configured
        for name, backend in default_backends.items():
            if name not in self.backends:
                self.backends[name] = backend
                
        # Sort backends by priority
        self.backends = dict(sorted(self.backends.items(), key=lambda x: x[1].priority))
        
    async def _initialize_redis(self):
        """Initialize Redis client for caching and coordination."""
        redis_config = self.config.get("redis", {})
        
        if redis_config.get("enabled", True):
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.get("host", "localhost"),
                    port=redis_config.get("port", 6379),
                    db=redis_config.get("db", 0),
                    password=redis_config.get("password"),
                    decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Redis: {e}")
                self.redis_client = None
                
    def _load_metadata_cache(self):
        """Load file metadata cache from disk."""
        metadata_file = self.local_cache_dir / "metadata_cache.json"
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    
                self.metadata_cache = {
                    file_id: {
                        "id": info["id"],
                        "filename": info["filename"],
                        "size": info["size"],
                        "checksum": info["checksum"],
                        "backends": info["backends"],
                        "created_at": datetime.fromisoformat(info["created_at"]),
                        "accessed_at": datetime.fromisoformat(info["accessed_at"]),
                        "access_count": info["access_count"],
                        "compression": info.get("compression", {}),
                        "metadata": info.get("metadata", {})
                    }
                    for file_id, info in data.get("files", {}).items()
                }
                
                logger.info(f"Loaded {len(self.metadata_cache)} files from metadata cache")
            except Exception as e:
                logger.error(f"Error loading metadata cache: {e}")
                self.metadata_cache = {}
                
    def _save_metadata_cache(self):
        """Save file metadata cache to disk."""
        metadata_file = self.local_cache_dir / "metadata_cache.json"
        
        try:
            data = {
                "version": "1.0",
                "files": {
                    file_id: {
                        "id": info["id"],
                        "filename": info["filename"],
                        "size": info["size"],
                        "checksum": info["checksum"],
                        "backends": info["backends"],
                        "created_at": info["created_at"].isoformat(),
                        "accessed_at": info["accessed_at"].isoformat(),
                        "access_count": info["access_count"],
                        "compression": info.get("compression", {}),
                        "metadata": info.get("metadata", {})
                    }
                    for file_id, info in self.metadata_cache.items()
                },
                "updated_at": datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug("Metadata cache saved")
        except Exception as e:
            logger.error(f"Error saving metadata cache: {e}")
            
    def _calculate_checksum(self, data: Union[bytes, str]) -> str:
        """Calculate SHA256 checksum of data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        return hashlib.sha256(data).hexdigest()
        
    def _get_file_id(self, filename: str, content: Union[bytes, str] = None) -> str:
        """Generate a unique file ID."""
        if content:
            checksum = self._calculate_checksum(content)
            return f"{filename}_{checksum}"
        return str(uuid.uuid4())
        
    async def _get_backend_client(self, backend_name: str):
        """Get client for a specific backend."""
        backend = self.backends.get(backend_name)
        if not backend or not backend.enabled:
            raise ValueError(f"Backend not available: {backend_name}")
            
        if backend.type == "local":
            return LocalBackendClient(backend.config["path"])
        elif backend.type == "s3":
            if aioboto3 is None:
                raise RuntimeError("aioboto3 is required for S3 backend but not installed")
            return S3BackendClient(backend.config)
        elif backend.type == "azure":
            if BlobServiceClient is None:
                raise RuntimeError("azure-storage-blob is required for Azure backend but not installed")
            return AzureBackendClient(backend.config)
        elif backend.type == "gcs":
            if gcs is None:
                raise RuntimeError("google-cloud-storage is required for GCS backend but not installed")
            return GCSBackendClient(backend.config)
        elif backend.type == "redis":
            if redis is None:
                raise RuntimeError("redis is required for Redis backend but not installed")
            return RedisBackendClient(backend.config, self.redis_client)
        else:
            raise ValueError(f"Unsupported backend type: {backend.type}")
            
    async def _store_file(self, file_id: str, filename: str, content: bytes, 
                         metadata: Dict = None, compression: Dict = None) -> List[str]:
        """
        Store a file across multiple backends.
        
        Args:
            file_id: Unique file identifier
            filename: Original filename
            content: File content
            metadata: Additional metadata
            compression: Compression information
            
        Returns:
            List of backend names where file was stored
        """
        stored_backends = []
        
        # Apply compression if specified
        if compression and compression.get("enabled", False):
            algorithm = compression.get("algorithm", "zlib")
            level = compression.get("level", 6)
            
            original_size = len(content)
            compressed_content, is_compressed = self.compression_manager.compress(content)
            if is_compressed:
                content = compressed_content
            compressed_size = len(content)
            
            compression_info = {
                "enabled": True,
                "algorithm": algorithm,
                "level": level,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "ratio": (original_size - compressed_size) / original_size if original_size > 0 else 0
            }
        else:
            compression_info = {"enabled": False}
            
        # Calculate checksum
        checksum = self._calculate_checksum(content)
        
        # Store on each enabled backend
        for backend_name, backend in self.backends.items():
            if not backend.enabled:
                continue
                
            try:
                client = await self._get_backend_client(backend_name)
                
                # Store file
                await client.store_file(file_id, filename, content)
                
                # Update metadata
                if file_id not in self.metadata_cache:
                    self.metadata_cache[file_id] = {
                        "id": file_id,
                        "filename": filename,
                        "size": len(content),
                        "checksum": checksum,
                        "backends": [],
                        "created_at": datetime.now(),
                        "accessed_at": datetime.now(),
                        "access_count": 0,
                        "compression": compression_info,
                        "metadata": metadata or {}
                    }
                    
                self.metadata_cache[file_id]["backends"].append(backend_name)
                stored_backends.append(backend_name)
                
                logger.debug(f"File {file_id} stored on backend {backend_name}")
                
            except Exception as e:
                logger.error(f"Error storing file {file_id} on backend {backend_name}: {e}")
                
        # Create redundancy copies
        if len(stored_backends) < 2:
            # Try to store on additional backends for redundancy
            for backend_name, backend in self.backends.items():
                if backend_name in stored_backends or not backend.enabled:
                    continue
                    
                try:
                    client = await self._get_backend_client(backend_name)
                    await client.store_file(file_id, filename, content)
                    
                    if file_id in self.metadata_cache:
                        self.metadata_cache[file_id]["backends"].append(backend_name)
                    stored_backends.append(backend_name)
                    
                    logger.debug(f"Redundancy copy of {file_id} stored on {backend_name}")
                    
                except Exception as e:
                    logger.error(f"Error creating redundancy copy for {file_id} on {backend_name}: {e}")
                    
        # Save metadata cache
        self._save_metadata_cache()
        
        # Update statistics
        self.stats["total_files"] += 1
        self.stats["total_size"] += len(content)
        self.stats["operations"]["write"] += 1
        self.stats["last_operation"] = datetime.now()
        
        return stored_backends
        
    async def _retrieve_file(self, file_id: str, filename: str = None) -> Optional[bytes]:
        """
        Retrieve a file from storage.
        
        Args:
            file_id: File identifier
            filename: Expected filename (for verification)
            
        Returns:
            File content or None if not found
        """
        if file_id not in self.metadata_cache:
            logger.warning(f"File {file_id} not found in metadata cache")
            return None
            
        file_info = self.metadata_cache[file_id]
        
        # Try backends in order of priority
        for backend_name in file_info["backends"]:
            try:
                client = await self._get_backend_client(backend_name)
                
                # Retrieve file
                content = await client.retrieve_file(file_id)
                
                if content is not None:
                    # Verify checksum
                    calculated_checksum = self._calculate_checksum(content)
                    if calculated_checksum != file_info["checksum"]:
                        logger.warning(f"Checksum mismatch for {file_id} from {backend_name}")
                        continue
                        
                    # Update metadata
                    file_info["accessed_at"] = datetime.now()
                    file_info["access_count"] += 1
                    self._save_metadata_cache()
                    
                    # Update statistics
                    self.stats["operations"]["read"] += 1
                    self.stats["last_operation"] = datetime.now()
                    
                    # Cache locally if not already
                    local_path = self.local_cache_dir / file_id
                    if not local_path.exists():
                        if aiofiles:
                            async with aiofiles.open(local_path, 'wb') as f:
                                await f.write(content)
                        else:
                            # Fallback to synchronous file write
                            with open(local_path, 'wb') as f:
                                f.write(content)
                            
                    logger.debug(f"File {file_id} retrieved from {backend_name}")
                    return content
                    
            except Exception as e:
                logger.error(f"Error retrieving file {file_id} from {backend_name}: {e}")
                continue
                
        logger.error(f"File {file_id} not found on any backend")
        self.stats["operations"]["errors"] += 1
        return None
        
    async def _delete_file(self, file_id: str) -> bool:
        """
        Delete a file from all backends.
        
        Args:
            file_id: File identifier
            
        Returns:
            True if successful, False otherwise
        """
        if file_id not in self.metadata_cache:
            logger.warning(f"File {file_id} not found in metadata cache")
            return False
            
        file_info = self.metadata_cache[file_id]
        deleted_backends = []
        
        # Delete from all backends
        for backend_name in file_info["backends"]:
            try:
                client = await self._get_backend_client(backend_name)
                await client.delete_file(file_id)
                deleted_backends.append(backend_name)
                
            except Exception as e:
                logger.error(f"Error deleting file {file_id} from {backend_name}: {e}")
                
        # Remove from metadata cache if deleted from all backends
        if len(deleted_backends) == len(file_info["backends"]):
            del self.metadata_cache[file_id]
            self._save_metadata_cache()
            
            # Delete local cache
            local_path = self.local_cache_dir / file_id
            if local_path.exists():
                local_path.unlink()
                
            # Update statistics
            self.stats["total_files"] -= 1
            self.stats["total_size"] -= file_info["size"]
            self.stats["operations"]["delete"] += 1
            self.stats["last_operation"] = datetime.now()
            
            logger.info(f"File {file_id} deleted from all backends")
            return True
            
        logger.warning(f"File {file_id} partially deleted from {len(deleted_backends)}/{len(file_info['backends'])} backends")
        return False
        
    async def store_memory(self, memory: Memory) -> str:
        """
        Store a memory's content in distributed storage.
        
        Args:
            memory: Memory object
            
        Returns:
            File ID of the stored content
        """
        if not memory.content and not memory.file_path:
            return None
            
        # Prepare content
        if memory.file_path and Path(memory.file_path).exists():
            if aiofiles:
                async with aiofiles.open(memory.file_path, 'rb') as f:
                    content = await f.read()
            else:
                # Fallback to synchronous file read
                with open(memory.file_path, 'rb') as f:
                    content = f.read()
        else:
            content = memory.content.encode('utf-8')
            
        # Generate file ID
        filename = f"memory_{memory.id}"
        file_id = self._get_file_id(filename, content)
        
        # Store file
        await self._store_file(
            file_id,
            filename,
            content,
            metadata={
                "memory_id": memory.id,
                "memory_type": "content",
                "created_at": memory.created_at.isoformat(),
                "tags": memory.tags,
                "context_id": memory.context_id
            },
            compression={
                "enabled": memory.compressed,
                "algorithm": memory.compression_algorithm,
                "level": 6  # Default compression level
            }
        )
        
        # Update memory with file ID
        memory.file_path = file_id
        await self.db.update_memory(memory.id, file_path=file_id)
        
        return file_id
        
    async def retrieve_memory(self, memory: Memory) -> bool:
        """
        Retrieve a memory's content from distributed storage.
        
        Args:
            memory: Memory object
            
        Returns:
            True if successful, False otherwise
        """
        if not memory.file_path:
            return False
            
        # Retrieve file
        content = await self._retrieve_file(memory.file_path, f"memory_{memory.id}")
        
        if content is None:
            return False
            
        # Handle decompression
        if memory.compressed and memory.compression_algorithm:
            try:
                decompressed_content, is_decompressed = self.compression_manager.decompress(content)
                if is_decompressed:
                    content = decompressed_content
            except Exception as e:
                logger.error(f"Error decompressing memory {memory.id}: {e}")
                return False
                
        # Update memory content
        memory.content = content.decode('utf-8')
        
        # Update access statistics
        memory.last_accessed = datetime.now()
        memory.access_count += 1
        await self.db.update_memory(
            memory.id,
            content=memory.content,
            last_accessed=memory.last_accessed,
            access_count=memory.access_count
        )
        
        return True
        
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory's content from distributed storage.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if successful, False otherwise
        """
        # Get memory to find file path
        memory = await self.db.get_memory(memory_id)
        if not memory or not memory.file_path:
            return False
            
        # Delete file
        success = await self._delete_file(memory.file_path)
        
        if success:
            # Clear file path in memory
            await self.db.update_memory(memory_id, file_path=None)
            
        return success
        
    async def store_vector(self, vector_id: str, vector_data: bytes) -> str:
        """
        Store vector data in distributed storage.
        
        Args:
            vector_id: Vector identifier
            vector_data: Vector data
            
        Returns:
            File ID of the stored vector
        """
        filename = f"vector_{vector_id}"
        file_id = self._get_file_id(filename, vector_data)
        
        # Store file
        await self._store_file(
            file_id,
            filename,
            vector_data,
            metadata={
                "vector_id": vector_id,
                "vector_type": "embedding",
                "created_at": datetime.now().isoformat()
            }
        )
        
        return file_id
        
    async def retrieve_vector(self, vector_id: str) -> Optional[bytes]:
        """
        Retrieve vector data from distributed storage.
        
        Args:
            vector_id: Vector identifier
            
        Returns:
            Vector data or None if not found
        """
        filename = f"vector_{vector_id}"
        file_id = self._get_file_id(filename)
        
        # Check metadata cache
        if file_id not in self.metadata_cache:
            # Try to find by vector_id in metadata
            for fid, info in self.metadata_cache.items():
                if info.get("metadata", {}).get("vector_id") == vector_id:
                    file_id = fid
                    break
                    
        return await self._retrieve_file(file_id, filename)
        
    async def get_backend_stats(self) -> Dict[str, StorageStats]:
        """
        Get statistics for all backends.
        
        Returns:
            Dictionary mapping backend names to statistics
        """
        stats = {}
        
        for backend_name, backend in self.backends.items():
            if not backend.enabled:
                continue
                
            try:
                client = await self._get_backend_client(backend_name)
                backend_stats = await client.get_stats()
                
                stats[backend_name] = StorageStats(
                    backend_name=backend_name,
                    total_size=backend_stats.get("total_size", 0),
                    file_count=backend_stats.get("file_count", 0),
                    available_space=backend_stats.get("available_space", 0),
                    last_accessed=datetime.now(),
                    error_count=backend_stats.get("error_count", 0),
                    latency_ms=backend_stats.get("latency_ms", 0)
                )
                
            except Exception as e:
                logger.error(f"Error getting stats for backend {backend_name}: {e}")
                stats[backend_name] = StorageStats(
                    backend_name=backend_name,
                    total_size=0,
                    file_count=0,
                    available_space=0,
                    last_accessed=datetime.now(),
                    error_count=1,
                    latency_ms=0
                )
                
        return stats
        
    async def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all backends.
        
        Returns:
            Dictionary mapping backend names to health status
        """
        health_status = {}
        
        for backend_name, backend in self.backends.items():
            if not backend.enabled:
                health_status[backend_name] = False
                continue
                
            try:
                client = await self._get_backend_client(backend_name)
                await client.health_check()
                health_status[backend_name] = True
                
            except Exception as e:
                logger.error(f"Health check failed for backend {backend_name}: {e}")
                health_status[backend_name] = False
                
        return health_status
        
    async def cleanup_cache(self, max_age_days: int = 30):
        """
        Clean up old files from local cache.
        
        Args:
            max_age_days: Maximum age of files to keep
        """
        if not self.local_cache_dir.exists():
            return
            
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0
        cleaned_size = 0
        
        for file_path in self.local_cache_dir.iterdir():
            if file_path.is_file():
                try:
                    # Check if file is in metadata cache
                    file_id = file_path.name
                    if file_id in self.metadata_cache:
                        file_info = self.metadata_cache[file_id]
                        if file_info["accessed_at"] > cutoff_date:
                            continue
                            
                    # Delete old file
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    
                    cleaned_count += 1
                    cleaned_size += file_size
                    
                except Exception as e:
                    logger.error(f"Error cleaning up file {file_path}: {e}")
                    
        logger.info(f"Cleaned up {cleaned_count} files, {cleaned_size} bytes from local cache")
        
    async def start_background_tasks(self):
        """Start background maintenance tasks."""
        if not self.enabled:
            return
            
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        # Start health check task
        self.health_check_task = asyncio.create_task(self._periodic_health_check())
        
        logger.info("Background tasks started")
        
    async def stop_background_tasks(self):
        """Stop background maintenance tasks."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
                
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Background tasks stopped")
        
    async def _periodic_cleanup(self):
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self.cleanup_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                
    async def _periodic_health_check(self):
        """Periodic health check task."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")
                
    def get_storage_report(self) -> Dict:
        """
        Create a comprehensive storage report.
        
        Returns:
            Dictionary with storage statistics and findings
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "enabled": self.enabled,
                "local_cache_directory": str(self.local_cache_dir),
                "backends": {
                    name: backend.to_dict()
                    for name, backend in self.backends.items()
                }
            },
            "statistics": self.stats.copy(),
            "metadata_cache": {
                "total_files": len(self.metadata_cache),
                "total_size": sum(info["size"] for info in self.metadata_cache.values()),
                "by_backend": {
                    name: sum(1 for info in self.metadata_cache.values() if name in info["backends"])
                    for name in self.backends
                }
            },
            "recommendations": []
        }

# Backend client implementations
class LocalBackendClient:
    """Client for local filesystem backend."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    async def store_file(self, file_id: str, filename: str, content: bytes):
        file_path = self.base_path / file_id
        if aiofiles:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
        else:
            # Fallback to synchronous file write
            with open(file_path, 'wb') as f:
                f.write(content)
            
    async def retrieve_file(self, file_id: str) -> Optional[bytes]:
        file_path = self.base_path / file_id
        if not file_path.exists():
            return None
            
        if aiofiles:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        else:
            # Fallback to synchronous file read
            with open(file_path, 'rb') as f:
                return f.read()
            
    async def delete_file(self, file_id: str):
        file_path = self.base_path / file_id
        if file_path.exists():
            file_path.unlink()
            
    async def get_stats(self) -> Dict:
        total_size = 0
        file_count = 0
        
        for file_path in self.base_path.iterdir():
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
                
        return {
            "total_size": total_size,
            "file_count": file_count,
            "available_space": shutil.disk_usage(self.base_path).free,
            "error_count": 0,
            "latency_ms": 0
        }
        
    async def health_check(self):
        if not self.base_path.exists():
            raise RuntimeError("Base directory does not exist")
            
class S3BackendClient:
    """Client for AWS S3 backend."""
    
    def __init__(self, config: Dict):
        self.bucket_name = config["bucket_name"]
        self.region = config.get("region", "us-east-1")
        self.access_key = config.get("access_key_id")
        self.secret_key = config.get("secret_access_key")
        
        self.session = aioboto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )
        
    async def store_file(self, file_id: str, filename: str, content: bytes):
        async with self.session.client("s3") as s3:
            await s3.put_object(
                Bucket=self.bucket_name,
                Key=file_id,
                Body=content
            )
            
    async def retrieve_file(self, file_id: str) -> Optional[bytes]:
        async with self.session.client("s3") as s3:
            try:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=file_id
                )
                return await response["Body"].read()
            except Exception:
                return None
                
    async def delete_file(self, file_id: str):
        async with self.session.client("s3") as s3:
            try:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_id
                )
            except Exception:
                pass
                
    async def get_stats(self) -> Dict:
        # Simplified stats - in production you'd use S3 inventory or CloudWatch
        return {
            "total_size": 0,  # Would need to calculate
            "file_count": 0,  # Would need to calculate
            "available_space": float('inf'),  # S3 is effectively unlimited
            "error_count": 0,
            "latency_ms": 0
        }
        
    async def health_check(self):
        async with self.session.client("s3") as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket_name)
            except Exception as e:
                raise RuntimeError(f"S3 health check failed: {e}")

class AzureBackendClient:
    """Client for Azure Blob Storage backend."""
    
    def __init__(self, config: Dict):
        self.connection_string = config["connection_string"]
        self.container_name = config["container_name"]
        
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        
    async def store_file(self, file_id: str, filename: str, content: bytes):
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_id
        )
        await blob_client.upload_blob(content, overwrite=True)
        
    async def retrieve_file(self, file_id: str) -> Optional[bytes]:
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_id
        )
        
        try:
            stream = await blob_client.download_blob()
            return await stream.readall()
        except Exception:
            return None
            
    async def delete_file(self, file_id: str):
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_id
        )
        
        try:
            await blob_client.delete_blob()
        except Exception:
            pass
            
    async def get_stats(self) -> Dict:
        # Simplified stats
        return {
            "total_size": 0,
            "file_count": 0,
            "available_space": float('inf'),
            "error_count": 0,
            "latency_ms": 0
        }
        
    async def health_check(self):
        try:
            # Simple health check - list containers
            async for container in self.blob_service_client.list_containers():
                pass
        except Exception as e:
            raise RuntimeError(f"Azure health check failed: {e}")

class GCSBackendClient:
    """Client for Google Cloud Storage backend."""
    
    def __init__(self, config: Dict):
        self.bucket_name = config["bucket_name"]
        self.credentials_path = config.get("credentials_path")
        
        if self.credentials_path:
            self.storage_client = gcs.Client.from_service_account_json(self.credentials_path)
        else:
            self.storage_client = gcs.Client()
            
    async def store_file(self, file_id: str, filename: str, content: bytes):
        # GCS client is synchronous, so we run in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._store_file_sync,
            file_id,
            content
        )
        
    def _store_file_sync(self, file_id: str, content: bytes):
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(file_id)
        blob.upload_from_string(content)
        
    async def retrieve_file(self, file_id: str) -> Optional[bytes]:
        loop = asyncio.get_event_loop()
        
        try:
            return await loop.run_in_executor(
                None,
                self._retrieve_file_sync,
                file_id
            )
        except Exception:
            return None
            
    def _retrieve_file_sync(self, file_id: str) -> bytes:
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(file_id)
        return blob.download_as_bytes()
        
    async def delete_file(self, file_id: str):
        loop = asyncio.get_event_loop()
        
        try:
            await loop.run_in_executor(
                None,
                self._delete_file_sync,
                file_id
            )
        except Exception:
            pass
            
    def _delete_file_sync(self, file_id: str):
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(file_id)
        blob.delete()
        
    async def get_stats(self) -> Dict:
        # Simplified stats
        return {
            "total_size": 0,
            "file_count": 0,
            "available_space": float('inf'),
            "error_count": 0,
            "latency_ms": 0
        }
        
    async def health_check(self):
        try:
            # Simple health check - get bucket
            bucket = self.storage_client.bucket(self.bucket_name)
            bucket.reload()
        except Exception as e:
            raise RuntimeError(f"GCS health check failed: {e}")

class RedisBackendClient:
    """Client for Redis backend."""
    
    def __init__(self, config: Dict, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.key_prefix = config.get("key_prefix", "storage:")
        self.ttl = config.get("ttl", 3600)  # 1 hour TTL
        
    async def store_file(self, file_id: str, filename: str, content: bytes):
        key = f"{self.key_prefix}{file_id}"
        await self.redis_client.setex(key, self.ttl, content)
        
    async def retrieve_file(self, file_id: str) -> Optional[bytes]:
        key = f"{self.key_prefix}{file_id}"
        content = await self.redis_client.get(key)
        return content if content else None
        
    async def delete_file(self, file_id: str):
        key = f"{self.key_prefix}{file_id}"
        await self.redis_client.delete(key)
        
    async def get_stats(self) -> Dict:
        # Simplified stats
        return {
            "total_size": 0,
            "file_count": 0,
            "available_space": 0,  # Would need to check Redis memory usage
            "error_count": 0,
            "latency_ms": 0
        }
        
    async def health_check(self):
        if not self.redis_client:
            raise RuntimeError("Redis client not available")
            
        try:
            await self.redis_client.ping()
        except Exception as e:
            raise RuntimeError(f"Redis health check failed: {e}")