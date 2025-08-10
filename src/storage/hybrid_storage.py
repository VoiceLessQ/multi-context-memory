"""
Hybrid storage implementation for the MCP Multi-Context Memory System.
Combines multiple storage backends for optimal performance and scalability.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..database.models import Memory
from ..utils.compression import ContentCompressor
from ..utils.error_handling import log_error

logger = logging.getLogger(__name__)

@dataclass
class StorageStats:
    """Statistics for storage backends."""
    name: str
    total_size: int
    memory_count: int
    compression_ratio: float
    access_time: float
    error_rate: float

class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.priority = config.get("priority", 1)
    
    @abstractmethod
    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory in this backend."""
        pass
    
    @abstractmethod
    async def retrieve_memory(self, memory_id: int) -> Optional[Memory]:
        """Retrieve a memory from this backend."""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory from this backend."""
        pass
    
    @abstractmethod
    async def list_memories(self, filters: Dict[str, Any]) -> List[Memory]:
        """List memories in this backend."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> StorageStats:
        """Get statistics for this backend."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if this backend is healthy."""
        pass

class SQLiteBackend(StorageBackend):
    """SQLite storage backend."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.db_path = Path(config.get("db_path", "./data/memories.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
    
    async def initialize(self):
        """Initialize the SQLite backend."""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        
        # Create tables if they don't exist
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                owner_id INTEGER,
                context_id INTEGER,
                title TEXT,
                content TEXT,
                content_size INTEGER,
                content_compressed BOOLEAN,
                access_level TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                metadata TEXT
            )
        """)
        self.connection.commit()
    
    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory in SQLite."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO memories (
                    id, owner_id, context_id, title, content, content_size,
                    content_compressed, access_level, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id, memory.owner_id, memory.context_id, memory.title,
                memory.content, memory.content_size, memory.content_compressed,
                memory.access_level, memory.created_at, memory.updated_at,
                json.dumps(memory.memory_metadata) if memory.memory_metadata else None
            ))
            self.connection.commit()
            return True
        except Exception as e:
            log_error(e, f"Failed to store memory {memory.id} in SQLite")
            return False
    
    async def retrieve_memory(self, memory_id: int) -> Optional[Memory]:
        """Retrieve a memory from SQLite."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if row:
                memory_metadata = json.loads(row["metadata"]) if row["metadata"] else None
                return Memory(
                    id=row["id"],
                    owner_id=row["owner_id"],
                    context_id=row["context_id"],
                    title=row["title"],
                    content=row["content"],
                    content_size=row["content_size"],
                    content_compressed=bool(row["content_compressed"]),
                    access_level=row["access_level"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    memory_metadata=memory_metadata
                )
            return None
        except Exception as e:
            log_error(e, f"Failed to retrieve memory {memory_id} from SQLite")
            return None
    
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory from SQLite."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            log_error(e, f"Failed to delete memory {memory_id} from SQLite")
            return False
    
    async def list_memories(self, filters: Dict[str, Any]) -> List[Memory]:
        """List memories in SQLite."""
        try:
            query = "SELECT * FROM memories"
            params = []
            
            if filters:
                conditions = []
                if "owner_id" in filters:
                    conditions.append("owner_id = ?")
                    params.append(filters["owner_id"])
                if "context_id" in filters:
                    conditions.append("context_id = ?")
                    params.append(filters["context_id"])
                if "access_level" in filters:
                    conditions.append("access_level = ?")
                    params.append(filters["access_level"])
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memory_metadata = json.loads(row["metadata"]) if row["metadata"] else None
                memory = Memory(
                    id=row["id"],
                    owner_id=row["owner_id"],
                    context_id=row["context_id"],
                    title=row["title"],
                    content=row["content"],
                    content_size=row["content_size"],
                    content_compressed=bool(row["content_compressed"]),
                    access_level=row["access_level"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    memory_metadata=memory_metadata
                )
                memories.append(memory)
            
            return memories
        except Exception as e:
            log_error(e, "Failed to list memories from SQLite")
            return []
    
    async def get_stats(self) -> StorageStats:
        """Get statistics for SQLite."""
        try:
            cursor = self.connection.cursor()
            
            # Get total size
            cursor.execute("SELECT SUM(content_size) FROM memories")
            total_size = cursor.fetchone()[0] or 0
            
            # Get memory count
            cursor.execute("SELECT COUNT(*) FROM memories")
            memory_count = cursor.fetchone()[0]
            
            # Get compression ratio
            cursor.execute("SELECT AVG(CASE WHEN content_compressed THEN 1 ELSE 0 END) FROM memories")
            compression_ratio = cursor.fetchone()[0] or 0.0
            
            # Estimate access time (SQLite is typically fast)
            access_time = 0.01  # 10ms average
            
            # Error rate (SQLite is reliable)
            error_rate = 0.001  # 0.1%
            
            return StorageStats(
                name=self.name,
                total_size=total_size,
                memory_count=memory_count,
                compression_ratio=compression_ratio,
                access_time=access_time,
                error_rate=error_rate
            )
        except Exception as e:
            log_error(e, "Failed to get SQLite stats")
            return StorageStats(
                name=self.name,
                total_size=0,
                memory_count=0,
                compression_ratio=0.0,
                access_time=0.0,
                error_rate=1.0
            )
    
    async def health_check(self) -> bool:
        """Check if SQLite is healthy."""
        try:
            if not self.connection:
                await self.initialize()
            
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            return cursor.fetchone() is not None
        except Exception as e:
            log_error(e, "SQLite health check failed")
            return False

class JSONLBackend(StorageBackend):
    """JSONL storage backend."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.file_path = Path(config.get("file_path", "./data/memories.jsonl"))
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = None
    
    async def initialize(self):
        """Initialize the JSONL backend."""
        if not self.file_path.exists():
            self.file_path.touch()
    
    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory in JSONL."""
        try:
            if not self.file_handle:
                await self.initialize()
            
            with open(self.file_path, "a") as f:
                f.write(json.dumps(memory.dict()) + "\n")
            
            return True
        except Exception as e:
            log_error(e, f"Failed to store memory {memory.id} in JSONL")
            return False
    
    async def retrieve_memory(self, memory_id: int) -> Optional[Memory]:
        """Retrieve a memory from JSONL."""
        try:
            if not self.file_path.exists():
                return None
            
            with open(self.file_path, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    if data.get("id") == memory_id:
                        return Memory(**data)
            
            return None
        except Exception as e:
            log_error(e, f"Failed to retrieve memory {memory_id} from JSONL")
            return None
    
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory from JSONL."""
        try:
            if not self.file_path.exists():
                return False
            
            # Read all memories except the one to delete
            memories = []
            deleted = False
            
            with open(self.file_path, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    if data.get("id") == memory_id:
                        deleted = True
                    else:
                        memories.append(data)
            
            if deleted:
                # Write back all memories except the deleted one
                with open(self.file_path, "w") as f:
                    for memory in memories:
                        f.write(json.dumps(memory) + "\n")
            
            return deleted
        except Exception as e:
            log_error(e, f"Failed to delete memory {memory_id} from JSONL")
            return False
    
    async def list_memories(self, filters: Dict[str, Any]) -> List[Memory]:
        """List memories in JSONL."""
        try:
            if not self.file_path.exists():
                return []
            
            memories = []
            with open(self.file_path, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    
                    # Apply filters
                    match = True
                    for key, value in filters.items():
                        if key in data and data[key] != value:
                            match = False
                            break
                    
                    if match:
                        memories.append(Memory(**data))
            
            return memories
        except Exception as e:
            log_error(e, "Failed to list memories from JSONL")
            return []
    
    async def get_stats(self) -> StorageStats:
        """Get statistics for JSONL."""
        try:
            if not self.file_path.exists():
                return StorageStats(
                    name=self.name,
                    total_size=0,
                    memory_count=0,
                    compression_ratio=0.0,
                    access_time=0.0,
                    error_rate=1.0
                )
            
            total_size = 0
            memory_count = 0
            compressed_count = 0
            
            with open(self.file_path, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    memory_count += 1
                    
                    # Calculate size
                    content = data.get("content", "")
                    total_size += len(content.encode('utf-8'))
                    
                    # Count compressed
                    if data.get("content_compressed", False):
                        compressed_count += 1
            
            compression_ratio = compressed_count / memory_count if memory_count > 0 else 0.0
            
            # Estimate access time (JSONL is slower than SQLite)
            access_time = 0.05  # 50ms average
            
            # Error rate (JSONL is less reliable than SQLite)
            error_rate = 0.01  # 1%
            
            return StorageStats(
                name=self.name,
                total_size=total_size,
                memory_count=memory_count,
                compression_ratio=compression_ratio,
                access_time=access_time,
                error_rate=error_rate
            )
        except Exception as e:
            log_error(e, "Failed to get JSONL stats")
            return StorageStats(
                name=self.name,
                total_size=0,
                memory_count=0,
                compression_ratio=0.0,
                access_time=0.0,
                error_rate=1.0
            )
    
    async def health_check(self) -> bool:
        """Check if JSONL is healthy."""
        try:
            if not self.file_path.exists():
                return False
            
            # Try to read the file
            with open(self.file_path, "r") as f:
                # Just check if we can open it
                pass
            
            return True
        except Exception as e:
            log_error(e, "JSONL health check failed")
            return False

class HybridStorage:
    """Hybrid storage manager that combines multiple backends."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backends: Dict[str, StorageBackend] = {}
        self.primary_backend = None
        self.secondary_backends = []
        # Initialize compression manager
        self.compression_manager = ContentCompressor()
        self.compression_enabled = config.get("compression", {}).get("enabled", True)
        self.compression_threshold = config.get("compression", {}).get("threshold", 1024)
        self._initialized = False # Flag to track initialization state
        
        # Initialize backends
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize storage backends."""
        backend_configs = self.config.get("backends", {})
        
        # Create SQLite backend
        if "sqlite" in backend_configs:
            self.backends["sqlite"] = SQLiteBackend("sqlite", backend_configs["sqlite"])
        
        # Create JSONL backend
        if "jsonl" in backend_configs:
            self.backends["jsonl"] = JSONLBackend("jsonl", backend_configs["jsonl"])
        
        # Set primary backend (SQLite if available)
        if "sqlite" in self.backends:
            self.primary_backend = self.backends["sqlite"]
        
        # Set secondary backends
        for name, backend in self.backends.items():
            if backend != self.primary_backend:
                self.secondary_backends.append(backend)
        
        # Sort secondary backends by priority
        self.secondary_backends.sort(key=lambda b: b.priority)
    
    async def initialize(self):
        """Initialize all backends."""
        if self._initialized:
            logger.info("HybridStorage already initialized. Skipping.")
            return

        for backend in self.backends.values():
            if hasattr(backend, "initialize"):
                await backend.initialize()
        
        self._initialized = True
        logger.info("HybridStorage initialized successfully.")
    
    async def store_memory(self, memory: Memory) -> bool:
        """Store a memory in the hybrid storage system."""
        try:
            # Compress content if needed
            if self.compression_enabled and memory.content_size > self.compression_threshold:
                compressed_content, is_compressed = self.compression_manager.compress(memory.content)
                if is_compressed:
                    memory.content = compressed_content
                    memory.content_compressed = True
            
            # Store in primary backend
            if self.primary_backend:
                success = await self.primary_backend.store_memory(memory)
                if not success:
                    log_error(None, f"Failed to store memory {memory.id} in primary backend")
                    return False
                
                # Replicate to secondary backends
                for backend in self.secondary_backends:
                    if backend.enabled:
                        await backend.store_memory(memory)
            
            return True
        except Exception as e:
            log_error(e, f"Failed to store memory {memory.id} in hybrid storage")
            return False
    
    async def retrieve_memory(self, memory_id: int) -> Optional[Memory]:
        """Retrieve a memory from the hybrid storage system."""
        try:
            # Try primary backend first
            if self.primary_backend:
                memory = await self.primary_backend.retrieve_memory(memory_id)
                if memory:
                    # Decompress content if needed
                    if memory.content_compressed:
                        decompressed_content, is_decompressed = self.compression_manager.decompress(memory.content)
                        if is_decompressed:
                            memory.content = decompressed_content
                    return memory
            
            # Try secondary backends
            for backend in self.secondary_backends:
                if backend.enabled:
                    memory = await backend.retrieve_memory(memory_id)
                    if memory:
                        # Decompress content if needed
                        if memory.content_compressed:
                            decompressed_content, is_decompressed = self.compression_manager.decompress(memory.content)
                            if is_decompressed:
                                memory.content = decompressed_content
                        
                        # Store in primary backend for faster future access
                        if self.primary_backend:
                            await self.primary_backend.store_memory(memory)
                        
                        return memory
            
            return None
        except Exception as e:
            log_error(e, f"Failed to retrieve memory {memory_id} from hybrid storage")
            return None
    
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory from the hybrid storage system."""
        try:
            # Delete from primary backend
            if self.primary_backend:
                success = await self.primary_backend.delete_memory(memory_id)
                if not success:
                    log_error(None, f"Memory {memory_id} not found in primary backend")
            
            # Delete from secondary backends
            for backend in self.secondary_backends:
                if backend.enabled:
                    await backend.delete_memory(memory_id)
            
            return True
        except Exception as e:
            log_error(e, f"Failed to delete memory {memory_id} from hybrid storage")
            return False
    
    async def list_memories(self, filters: Dict[str, Any]) -> List[Memory]:
        """List memories from the hybrid storage system."""
        try:
            memories = []
            
            # Get from primary backend
            if self.primary_backend:
                memories.extend(await self.primary_backend.list_memories(filters))
            
            # Get from secondary backends (avoid duplicates)
            for backend in self.secondary_backends:
                if backend.enabled:
                    secondary_memories = await backend.list_memories(filters)
                    
                    # Add unique memories
                    for memory in secondary_memories:
                        if memory.id not in [m.id for m in memories]:
                            memories.append(memory)
            
            return memories
        except Exception as e:
            log_error(e, "Failed to list memories from hybrid storage")
            return []
    
    async def get_stats(self) -> Dict[str, StorageStats]:
        """Get statistics for all backends."""
        stats = {}
        for name, backend in self.backends.items():
            stats[name] = await backend.get_stats()
        return stats
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all backends."""
        health = {}
        for name, backend in self.backends.items():
            health[name] = await backend.health_check()
        return health
    
    async def optimize_storage(self):
        """Optimize storage across all backends."""
        try:
            # Get statistics
            stats = await self.get_stats()
            
            # Find the most efficient backend
            most_efficient = None
            best_score = 0
            
            for name, stat in stats.items():
                # Calculate efficiency score (lower is better)
                score = stat.access_time * (1 + stat.error_rate) / (1 + stat.compression_ratio)
                
                if score > best_score:
                    best_score = score
                    most_efficient = name
            
            # Migrate memories to the most efficient backend
            if most_efficient and most_efficient != self.primary_backend.name:
                logger.info(f"Migrating to most efficient backend: {most_efficient}")
                
                # Get all memories
                memories = await self.list_memories({})
                
                # Store in new primary backend
                new_primary = self.backends[most_efficient]
                for memory in memories:
                    await new_primary.store_memory(memory)
                
                # Update primary backend
                old_primary_name = self.primary_backend.name
                self.primary_backend = new_primary
                
                # Remove from old primary backend
                if most_efficient != "sqlite":  # Keep SQLite for redundancy
                    self.secondary_backends = [
                        b for b in self.secondary_backends
                        if b.name != old_primary_name
                    ]
                    self.secondary_backends.append(self.backends[old_primary_name])
            
            logger.info("Storage optimization completed")
        except Exception as e:
            log_error(e, "Failed to optimize storage")