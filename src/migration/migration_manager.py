"""
Migration manager for the MCP Multi-Context Memory System.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import time
from pathlib import Path

from ..database.enhanced_memory_db import EnhancedMemoryDB
from ..utils.compression import CompressionManager
from ..monitoring.memory_monitor import MemoryMonitor
from ..backup.backup_manager import BackupManager
from ..rollback.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manage data migration from old format to new format."""
    
    def __init__(self, db_url: str, batch_size: int = 100, dry_run: bool = False):
        self.db_url = db_url
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.db = EnhancedMemoryDB(db_url)
        self.compression_manager = CompressionManager()
        self.memory_monitor = MemoryMonitor(db_url)
        self.backup_manager = BackupManager()
        self.rollback_manager = RollbackManager()
        
        # Migration status
        self.migration_id = None
        self.total_memories = 0
        self.migrated_memories = 0
        self.failed_memories = 0
        self.start_time = None
        self.end_time = None
        
        # Migration statistics
        self.compression_stats = {
            "total_memories": 0,
            "compressed_memories": 0,
            "compression_ratio": 0.0,
            "total_original_size": 0,
            "total_compressed_size": 0
        }
        
        self.lazy_loading_stats = {
            "total_memories": 0,
            "lazy_loaded_memories": 0,
            "average_load_time": 0.0
        }
        
        self.performance_stats = {
            "total_time": 0.0,
            "average_time_per_memory": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0
        }
    
    async def initialize(self):
        """Initialize migration manager."""
        await self.db.initialize()
        await self.db.create_tables()
        
        # Create migration record
        migration_data = {
            "name": "Existing Data Migration",
            "description": "Migrate existing data to new format with compression and lazy loading",
            "status": "initialized",
            "batch_size": self.batch_size,
            "dry_run": self.dry_run
        }
        
        migration = await self.db.create_migration(migration_data)
        self.migration_id = migration.id
        
        logger.info(f"Migration initialized: {self.migration_id}")
    
    async def start_migration(self):
        """Start the migration process."""
        self.start_time = time.time()
        
        # Update migration status
        await self.db.update_migration_status(
            self.migration_id,
            "started",
            f"Migration started at {datetime.utcnow().isoformat()}"
        )
        
        logger.info(f"Migration started: {self.migration_id}")
        
        # Create backup before migration
        if not self.dry_run:
            backup_path = self.backup_manager.create_backup(self.db_url)
            logger.info(f"Backup created: {backup_path}")
            
            # Add backup to migration record
            await self.db.add_migration_backup(self.migration_id, backup_path)
        
        # Get total number of memories to migrate
        self.total_memories = await self.db.get_memory_count()
        logger.info(f"Total memories to migrate: {self.total_memories}")
        
        # Update migration record with total count
        await self.db.update_migration_total(self.migration_id, self.total_memories)
    
    async def migrate_batch(self, offset: int, limit: int) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Migrate a batch of memories.
        
        Args:
            offset: Offset for batch
            limit: Limit for batch
            
        Returns:
            Tuple of (migrated_count, failed_count, batch_stats)
        """
        batch_start_time = time.time()
        migrated_count = 0
        failed_count = 0
        batch_stats = []
        
        # Get batch of memories
        memories = await self.db.get_memories(offset=offset, limit=limit)
        
        logger.info(f"Processing batch of {len(memories)} memories (offset: {offset}, limit: {limit})")
        
        for memory in memories:
            try:
                memory_start_time = time.time()
                
                # Check if memory already has new format
                if hasattr(memory, 'content_compressed') and memory.content_compressed is not None:
                    logger.info(f"Memory {memory.id} already in new format, skipping")
                    migrated_count += 1
                    continue
                
                # Migrate memory
                migrated_memory = await self._migrate_memory(memory)
                
                # Update statistics
                migrated_count += 1
                memory_end_time = time.time()
                memory_time = memory_end_time - memory_start_time
                
                batch_stats.append({
                    "memory_id": memory.id,
                    "title": memory.title,
                    "original_size": len(memory.content),
                    "compressed_size": len(migrated_memory.content) if migrated_memory.content_compressed else len(migrated_memory.content),
                    "compression_ratio": self._calculate_compression_ratio(len(memory.content), len(migrated_memory.content) if migrated_memory.content_compressed else len(migrated_memory.content)),
                    "migration_time": memory_time,
                    "success": True
                })
                
                # Update performance stats
                self.performance_stats["total_time"] += memory_time
                self.performance_stats["average_time_per_memory"] = self.performance_stats["total_time"] / migrated_count
                self.performance_stats["min_time"] = min(self.performance_stats["min_time"], memory_time)
                self.performance_stats["max_time"] = max(self.performance_stats["max_time"], memory_time)
                
                logger.info(f"Migrated memory {memory.id} in {memory_time:.4f} seconds")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to migrate memory {memory.id}: {e}")
                
                batch_stats.append({
                    "memory_id": memory.id,
                    "title": memory.title,
                    "error": str(e),
                    "success": False
                })
        
        batch_end_time = time.time()
        batch_time = batch_end_time - batch_start_time
        
        logger.info(f"Batch processed in {batch_time:.4f} seconds: {migrated_count} migrated, {failed_count} failed")
        
        return migrated_count, failed_count, batch_stats
    
    async def _migrate_memory(self, memory) -> Any:
        """
        Migrate a single memory to new format.
        
        Args:
            memory: Memory object to migrate
            
        Returns:
            Migrated memory object
        """
        # Create new memory data
        memory_data = {
            "title": memory.title,
            "content": memory.content,
            "context_id": memory.context_id,
            "owner_id": memory.owner_id,
            "access_level": memory.access_level,
            "tags": memory.tags,
            "metadata": memory.metadata
        }
        
        # Create new memory with compression
        migrated_memory = await self.db.create_memory(memory_data)
        
        # Copy relations
        relations = await self.db.get_memory_relations(memory.id)
        for relation in relations:
            await self.db.create_relation({
                "source_memory_id": migrated_memory.id,
                "target_memory_id": relation.target_memory_id,
                "name": relation.name,
                "strength": relation.strength,
                "metadata": relation.metadata
            })
        
        # Copy embeddings if available
        if hasattr(memory, 'embeddings') and memory.embeddings:
            await self.db.update_memory_embeddings(migrated_memory.id, memory.embeddings)
        
        # Copy summary if available
        if hasattr(memory, 'summary') and memory.summary:
            await self.db.update_memory_summary(migrated_memory.id, memory.summary)
        
        # Copy chunks if available
        if hasattr(memory, 'chunks') and memory.chunks:
            await self.db.update_memory_chunks(migrated_memory.id, memory.chunks)
        
        # Update compression statistics
        self.compression_stats["total_memories"] += 1
        self.compression_stats["total_original_size"] += len(memory.content)
        
        if migrated_memory.content_compressed:
            self.compression_stats["compressed_memories"] += 1
            self.compression_stats["total_compressed_size"] += len(migrated_memory.content)
        
        # Update lazy loading statistics
        self.lazy_loading_stats["total_memories"] += 1
        
        if hasattr(migrated_memory, '_content_loaded') and not migrated_memory._content_loaded:
            self.lazy_loading_stats["lazy_loaded_memories"] += 1
        
        return migrated_memory
    
    def _calculate_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio."""
        if original_size == 0:
            return 0.0
        
        return (original_size - compressed_size) / original_size
    
    async def get_migration_progress(self) -> Dict[str, Any]:
        """Get migration progress."""
        progress = {
            "migration_id": self.migration_id,
            "total_memories": self.total_memories,
            "migrated_memories": self.migrated_memories,
            "failed_memories": self.failed_memories,
            "progress_percentage": (self.migrated_memories / self.total_memories * 100) if self.total_memories > 0 else 0,
            "compression_stats": self.compression_stats,
            "lazy_loading_stats": self.lazy_loading_stats,
            "performance_stats": self.performance_stats,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_time": time.time() - self.start_time if self.start_time else 0
        }
        
        return progress
    
    async def complete_migration(self):
        """Complete the migration process."""
        self.end_time = time.time()
        
        # Update migration status
        await self.db.update_migration_status(
            self.migration_id,
            "completed",
            f"Migration completed at {datetime.utcnow().isoformat()}"
        )
        
        # Generate migration report
        report = await self._generate_migration_report()
        
        # Save report to migration record
        await self.db.add_migration_report(self.migration_id, report)
        
        logger.info(f"Migration completed: {self.migration_id}")
        logger.info(f"Report: {report}")
        
        return report
    
    async def cancel_migration(self):
        """Cancel the migration process."""
        self.end_time = time.time()
        
        # Update migration status
        await self.db.update_migration_status(
            self.migration_id,
            "cancelled",
            f"Migration cancelled at {datetime.utcnow().isoformat()}"
        )
        
        # Perform rollback if not dry run
        if not self.dry_run:
            await self.rollback_manager.rollback(self.migration_id)
        
        logger.info(f"Migration cancelled: {self.migration_id}")
    
    async def _generate_migration_report(self) -> Dict[str, Any]:
        """Generate migration report."""
        report = {
            "migration_id": self.migration_id,
            "total_memories": self.total_memories,
            "migrated_memories": self.migrated_memories,
            "failed_memories": self.failed_memories,
            "success_rate": (self.migrated_memories / self.total_memories * 100) if self.total_memories > 0 else 0,
            "compression_stats": self.compression_stats,
            "lazy_loading_stats": self.lazy_loading_stats,
            "performance_stats": self.performance_stats,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_time": self.end_time - self.start_time if self.start_time else 0,
            "average_time_per_memory": self.performance_stats["average_time_per_memory"],
            "min_migration_time": self.performance_stats["min_time"],
            "max_migration_time": self.performance_stats["max_time"],
            "compression_ratio": self.compression_stats["compression_ratio"],
            "lazy_loading_ratio": (self.lazy_loading_stats["lazy_loaded_memories"] / self.lazy_loading_stats["total_memories"] * 100) if self.lazy_loading_stats["total_memories"] > 0 else 0
        }
        
        return report
    
    async def run_migration(self):
        """Run the complete migration process."""
        try:
            await self.initialize()
            await self.start_migration()
            
            # Process batches
            offset = 0
            while offset < self.total_memories:
                migrated_count, failed_count, batch_stats = await self.migrate_batch(offset, self.batch_size)
                
                self.migrated_memories += migrated_count
                self.failed_memories += failed_count
                
                # Update migration progress
                await self.db.update_migration_progress(
                    self.migration_id,
                    self.migrated_memories,
                    self.failed_memories
                )
                
                offset += self.batch_size
                
                # Log batch statistics
                logger.info(f"Batch statistics: {batch_stats}")
            
            # Complete migration
            report = await self.complete_migration()
            
            return report
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await self.cancel_migration()
            raise