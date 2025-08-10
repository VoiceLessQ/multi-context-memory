"""
Archival system for the MCP Multi-Context Memory System.
"""
import logging
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import sqlite3
import zipfile
import gzip
import tarfile
from dataclasses import dataclass, asdict
import hashlib
import uuid

from ..database.models import Memory, Context, Relation
from ..database.db_interface import DatabaseInterface
from ..utils.compression import CompressionManager
from ..backup.backup_manager import BackupManager

logger = logging.getLogger(__name__)

@dataclass
class ArchivePolicy:
    """Policy for archival operations."""
    name: str
    description: str
    retention_days: int
    compression_enabled: bool
    compression_level: int
    archive_format: str  # 'zip', 'tar.gz', 'tar.bz2', 'directory'
    include_metadata: bool
    include_relations: bool
    include_contexts: bool
    max_archive_size: int  # in MB
    split_large_archives: bool
    checksum_verification: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ArchivePolicy':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class ArchiveInfo:
    """Information about an archive."""
    archive_id: str
    name: str
    policy_name: str
    created_at: datetime
    size_bytes: int
    memory_count: int
    checksum: str
    file_path: str
    status: str  # 'active', 'partial', 'completed', 'verified', 'corrupted'
    compression_ratio: float
    retention_until: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['retention_until'] = self.retention_until.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ArchiveInfo':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['retention_until'] = datetime.fromisoformat(data['retention_until'])
        return cls(**data)

class ArchivalManager:
    """Manage memory archival with configurable policies."""
    
    def __init__(self, db: DatabaseInterface, config: Dict = None):
        """
        Initialize the archival manager.
        
        Args:
            db: Enhanced memory database instance
            config: Configuration dictionary
        """
        self.db = db
        self.config = config or {}
        
        # Configuration settings
        self.enabled = self.config.get("archival_enabled", True)
        self.archive_dir = Path(self.config.get("archive_directory", "./data/archives"))
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize compression manager
        self.compression_manager = CompressionManager(self.config.get("compression", {}))
        
        # Initialize backup manager for safety
        self.backup_manager = BackupManager(str(self.archive_dir.parent / "backups"))
        
        # Default policies
        self.policies = self._load_default_policies()
        
        # Load custom policies from config
        custom_policies = self.config.get("policies", {})
        for name, policy_data in custom_policies.items():
            self.policies[name] = ArchivePolicy.from_dict(policy_data)
            
        # Archive registry
        self.registry = {}
        self._load_registry()
        
        # Statistics
        self.stats = {
            "total_archives": 0,
            "total_size": 0,
            "total_memories": 0,
            "policies": {name: {"count": 0, "size": 0} for name in self.policies},
            "last_archival": None
        }
        
        logger.info(f"Archival manager initialized with {len(self.policies)} policies")
        
    def _load_default_policies(self) -> Dict[str, ArchivePolicy]:
        """Load default archival policies."""
        return {
            "short_term": ArchivePolicy(
                name="short_term",
                description="Archive memories older than 30 days",
                retention_days=30,
                compression_enabled=True,
                compression_level=6,
                archive_format="tar.gz",
                include_metadata=True,
                include_relations=True,
                include_contexts=True,
                max_archive_size=100,  # 100MB
                split_large_archives=True,
                checksum_verification=True
            ),
            "medium_term": ArchivePolicy(
                name="medium_term",
                description="Archive memories older than 90 days",
                retention_days=90,
                compression_enabled=True,
                compression_level=6,
                archive_format="tar.gz",
                include_metadata=True,
                include_relations=True,
                include_contexts=True,
                max_archive_size=500,  # 500MB
                split_large_archives=True,
                checksum_verification=True
            ),
            "long_term": ArchivePolicy(
                name="long_term",
                description="Archive memories older than 365 days",
                retention_days=365,
                compression_enabled=True,
                compression_level=9,
                archive_format="tar.gz",
                include_metadata=True,
                include_relations=True,
                include_contexts=True,
                max_archive_size=1000,  # 1GB
                split_large_archives=True,
                checksum_verification=True
            ),
            "permanent": ArchivePolicy(
                name="permanent",
                description="Permanent archive for critical memories",
                retention_days=0,  # Never delete
                compression_enabled=True,
                compression_level=9,
                archive_format="tar.gz",
                include_metadata=True,
                include_relations=True,
                include_contexts=True,
                max_archive_size=0,  # No limit
                split_large_archives=False,
                checksum_verification=True
            )
        }
        
    def _load_registry(self):
        """Load archive registry from disk."""
        registry_file = self.archive_dir / "registry.json"
        
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    data = json.load(f)
                    
                self.registry = {
                    archive_id: ArchiveInfo.from_dict(info)
                    for archive_id, info in data.get("archives", {}).items()
                }
                
                # Update statistics
                self._update_statistics()
                
                logger.info(f"Loaded {len(self.registry)} archives from registry")
            except Exception as e:
                logger.error(f"Error loading archive registry: {e}")
                self.registry = {}
                
    def _save_registry(self):
        """Save archive registry to disk."""
        registry_file = self.archive_dir / "registry.json"
        
        try:
            data = {
                "version": "1.0",
                "archives": {
                    archive_id: info.to_dict()
                    for archive_id, info in self.registry.items()
                },
                "updated_at": datetime.now().isoformat()
            }
            
            with open(registry_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug("Archive registry saved")
        except Exception as e:
            logger.error(f"Error saving archive registry: {e}")
            
    def _update_statistics(self):
        """Update archival statistics."""
        self.stats["total_archives"] = len(self.registry)
        self.stats["total_size"] = sum(info.size_bytes for info in self.registry.values())
        self.stats["total_memories"] = sum(info.memory_count for info in self.registry.values())
        
        # Update policy-specific statistics
        for policy_name in self.policies:
            self.stats["policies"][policy_name] = {"count": 0, "size": 0}
            
        for info in self.registry.values():
            if info.policy_name in self.stats["policies"]:
                self.stats["policies"][info.policy_name]["count"] += 1
                self.stats["policies"][info.policy_name]["size"] += info.size_bytes
                
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
        
    def _create_archive_filename(self, policy: ArchivePolicy, archive_id: str) -> str:
        """Create filename for an archive."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{policy.name}_{archive_id}_{timestamp}.{policy.archive_format}"
        
    def _create_archive_directory(self, archive_id: str) -> Path:
        """Create directory for archive files."""
        archive_dir = self.archive_dir / archive_id
        archive_dir.mkdir(parents=True, exist_ok=True)
        return archive_dir
        
    def _compress_directory(self, source_dir: Path, output_file: Path, policy: ArchivePolicy) -> float:
        """
        Compress a directory into an archive file.
        
        Args:
            source_dir: Directory to compress
            output_file: Output archive file
            policy: Archive policy with compression settings
            
        Returns:
            Compression ratio (0-1)
        """
        original_size = sum(f.stat().st_size for f in source_dir.rglob('*') if f.is_file())
        
        if policy.archive_format == "zip":
            with zipfile.ZipFile(
                output_file,
                'w',
                zipfile.ZIP_DEFLATED if policy.compression_enabled else zipfile.ZIP_STORED,
                compresslevel=policy.compression_level if policy.compression_enabled else 0
            ) as zipf:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)
                        
        elif policy.archive_format in ["tar.gz", "tgz"]:
            mode = "w:gz"
            if policy.compression_level > 0:
                # Custom compression level for gzip
                import gzip
                with open(output_file, 'wb') as f:
                    with gzip.GzipFile(
                        fileobj=f,
                        mode='wb',
                        compresslevel=policy.compression_level
                    ) as gz_file:
                        with tarfile.open(
                            fileobj=gz_file,
                            mode='w'
                        ) as tar:
                            tar.add(source_dir, arcname=os.path.basename(source_dir))
            else:
                with tarfile.open(output_file, mode) as tar:
                    tar.add(source_dir, arcname=os.path.basename(source_dir))
                    
        elif policy.archive_format == "tar.bz2":
            with tarfile.open(output_file, f"w:bz2", compresslevel=policy.compression_level) as tar:
                tar.add(source_dir, arcname=os.path.basename(source_dir))
                
        else:
            # Directory format - just copy files
            output_dir = output_file
            output_dir.mkdir(parents=True, exist_ok=True)
            for item in source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, output_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, output_dir / item.name)
                    
        compressed_size = output_file.stat().st_size if output_file.is_file() else sum(
            f.stat().st_size for f in output_file.rglob('*') if f.is_file()
        )
        
        compression_ratio = (original_size - compressed_size) / original_size if original_size > 0 else 0
        return compression_ratio
        
    def _export_memories_to_json(self, memories: List[Memory], output_dir: Path):
        """Export memories to JSON files."""
        memories_dir = output_dir / "memories"
        memories_dir.mkdir(parents=True, exist_ok=True)
        
        for memory in memories:
            memory_file = memories_dir / f"memory_{memory.id}.json"
            with open(memory_file, 'w') as f:
                json.dump({
                    "id": memory.id,
                    "content": memory.content,
                    "metadata": memory.metadata,
                    "created_at": memory.created_at.isoformat(),
                    "updated_at": memory.updated_at.isoformat(),
                    "access_count": memory.access_count,
                    "last_accessed": memory.last_accessed.isoformat() if memory.last_accessed else None,
                    "tags": memory.tags,
                    "context_id": memory.context_id,
                    "vector_id": memory.vector_id,
                    "chunk_ids": memory.chunk_ids,
                    "compressed": memory.compressed,
                    "compression_algorithm": memory.compression_algorithm,
                    "compression_ratio": memory.compression_ratio,
                    "file_path": memory.file_path,
                    "file_size": memory.file_size,
                    "file_type": memory.file_type,
                    "checksum": memory.checksum
                }, f, indent=2)
                
    def _export_contexts_to_json(self, contexts: List[Context], output_dir: Path):
        """Export contexts to JSON files."""
        contexts_dir = output_dir / "contexts"
        contexts_dir.mkdir(parents=True, exist_ok=True)
        
        for context in contexts:
            context_file = contexts_dir / f"context_{context.id}.json"
            with open(context_file, 'w') as f:
                json.dump({
                    "id": context.id,
                    "name": context.name,
                    "description": context.description,
                    "created_at": context.created_at.isoformat(),
                    "updated_at": context.updated_at.isoformat(),
                    "metadata": context.metadata,
                    "tags": context.tags
                }, f, indent=2)
                
    def _export_relations_to_json(self, relations: List[Relation], output_dir: Path):
        """Export relations to JSON files."""
        relations_dir = output_dir / "relations"
        relations_dir.mkdir(parents=True, exist_ok=True)
        
        # Group relations by source memory
        relations_by_source = {}
        for relation in relations:
            if relation.source_memory_id not in relations_by_source:
                relations_by_source[relation.source_memory_id] = []
            relations_by_source[relation.source_memory_id].append(relation)
            
        for source_id, rel_list in relations_by_source.items():
            relation_file = relations_dir / f"relations_{source_id}.json"
            with open(relation_file, 'w') as f:
                json.dump({
                    "source_memory_id": source_id,
                    "relations": [
                        {
                            "id": rel.id,
                            "target_memory_id": rel.target_memory_id,
                            "relation_type": rel.relation_type,
                            "strength": rel.strength,
                            "metadata": rel.metadata,
                            "created_at": rel.created_at.isoformat(),
                            "updated_at": rel.updated_at.isoformat()
                        }
                        for rel in rel_list
                    ]
                }, f, indent=2)
                
    def _export_metadata_to_json(self, archive_info: ArchiveInfo, memories: List[Memory], output_dir: Path):
        """Export archive metadata to JSON."""
        metadata = {
            "archive_info": archive_info.to_dict(),
            "export_timestamp": datetime.now().isoformat(),
            "system_info": {
                "version": "2.0.0",
                "total_memories": len(memories),
                "total_size": sum(m.file_size or 0 for m in memories),
                "date_range": {
                    "earliest": min(m.created_at for m in memories).isoformat(),
                    "latest": max(m.created_at for m in memories).isoformat()
                }
            },
            "memories": [
                {
                    "id": m.id,
                    "content_preview": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                    "created_at": m.created_at.isoformat(),
                    "tags": m.tags,
                    "context_id": m.context_id,
                    "file_size": m.file_size,
                    "file_type": m.file_type
                }
                for m in memories
            ]
        }
        
        with open(output_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
            
    def _split_large_archive(self, source_file: Path, policy: ArchivePolicy, archive_id: str) -> List[Path]:
        """Split a large archive into smaller parts."""
        if policy.archive_format not in ["zip", "tar.gz", "tar.bz2"]:
            return [source_file]
            
        max_size_bytes = policy.max_archive_size * 1024 * 1024  # Convert MB to bytes
        parts = []
        
        if source_file.stat().st_size <= max_size_bytes:
            return [source_file]
            
        # For simplicity, we'll just split into equal-sized parts
        # In a real implementation, you might want to split by content
        part_size = max_size_bytes
        
        if policy.archive_format == "zip":
            # Create a new zip for each part
            with zipfile.ZipFile(source_file, 'r') as zipf:
                file_list = zipf.namelist()
                current_part = 1
                current_size = 0
                current_files = []
                
                for file_name in file_list:
                    file_info = zipf.getinfo(file_name)
                    if current_size + file_info.file_size > part_size and current_files:
                        # Create current part
                        part_file = source_file.parent / f"{source_file.stem}_part{current_part}{source_file.suffix}"
                        with zipfile.ZipFile(part_file, 'w') as part_zip:
                            for f in current_files:
                                part_zip.writestr(f, zipf.read(f))
                        parts.append(part_file)
                        
                        # Start new part
                        current_part += 1
                        current_size = 0
                        current_files = []
                        
                    current_files.append(file_name)
                    current_size += file_info.file_size
                    
                # Create final part
                if current_files:
                    part_file = source_file.parent / f"{source_file.stem}_part{current_part}{source_file.suffix}"
                    with zipfile.ZipFile(part_file, 'w') as part_zip:
                        for f in current_files:
                            part_zip.writestr(f, zipf.read(f))
                    parts.append(part_file)
                    
        else:
            # For tar files, we'll use a simpler approach
            # In practice, you might want to use tarfile's addfile with custom filtering
            part_number = 1
            part_file = source_file.parent / f"{source_file.stem}_part{part_number}{source_file.suffix}"
            
            with open(source_file, 'rb') as src, open(part_file, 'wb') as dst:
                while True:
                    chunk = src.read(part_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    
            parts.append(part_file)
            
        return parts
        
    def create_archive(self, policy_name: str, memory_ids: List[str] = None, 
                      date_range: Tuple[datetime, datetime] = None) -> str:
        """
        Create an archive using the specified policy.
        
        Args:
            policy_name: Name of the archival policy to use
            memory_ids: Optional list of memory IDs to archive
            date_range: Optional tuple of (start_date, end_date) to archive memories from
            
        Returns:
            Archive ID of the created archive
        """
        if not self.enabled:
            raise RuntimeError("Archival is disabled")
            
        if policy_name not in self.policies:
            raise ValueError(f"Unknown policy: {policy_name}")
            
        policy = self.policies[policy_name]
        archive_id = str(uuid.uuid4())
        
        logger.info(f"Creating archive {archive_id} with policy {policy_name}")
        
        # Create temporary directory for archival
        temp_dir = Path("/tmp") / f"archive_{archive_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get memories to archive
            if memory_ids:
                memories = [self.db.get_memory(mid) for mid in memory_ids if self.db.get_memory(mid)]
            elif date_range:
                start_date, end_date = date_range
                memories = self.db.get_memories_by_date_range(start_date, end_date)
            else:
                # Get memories older than retention period
                cutoff_date = datetime.now() - timedelta(days=policy.retention_days)
                memories = self.db.get_memories_before_date(cutoff_date)
                
            if not memories:
                logger.info("No memories found for archival")
                return archive_id
                
            # Export data to JSON
            export_dir = temp_dir / "export"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export memories
            self._export_memories_to_json(memories, export_dir)
            
            # Export contexts if requested
            if policy.include_contexts:
                context_ids = list(set(m.context_id for m in memories if m.context_id))
                contexts = [self.db.get_context(cid) for cid in context_ids if self.db.get_context(cid)]
                self._export_contexts_to_json(contexts, export_dir)
                
            # Export relations if requested
            if policy.include_relations:
                all_memory_ids = [m.id for m in memories]
                relations = self.db.get_relations_by_memory_ids(all_memory_ids)
                self._export_relations_to_json(relations, export_dir)
                
            # Export metadata
            archive_info = ArchiveInfo(
                archive_id=archive_id,
                name=f"{policy_name}_archive_{datetime.now().strftime('%Y%m%d')}",
                policy_name=policy_name,
                created_at=datetime.now(),
                size_bytes=0,  # Will be calculated later
                memory_count=len(memories),
                checksum="",
                file_path="",
                status="partial",
                compression_ratio=0.0,
                retention_until=datetime.now() + timedelta(days=policy.retention_days)
            )
            
            self._export_metadata_to_json(archive_info, memories, export_dir)
            
            # Create archive file
            archive_filename = self._create_archive_filename(policy, archive_id)
            archive_file = self.archive_dir / archive_filename
            
            # Compress the directory
            compression_ratio = self._compress_directory(export_dir, archive_file, policy)
            
            # Split large archives if needed
            if policy.split_large_archives and policy.max_archive_size > 0:
                archive_parts = self._split_large_archive(archive_file, policy, archive_id)
                archive_file = archive_parts[0]  # Use first part as primary
                
            # Calculate checksum if requested
            checksum = ""
            if policy.checksum_verification:
                checksum = self._calculate_checksum(archive_file)
                
            # Update archive info
            archive_info.size_bytes = archive_file.stat().st_size
            archive_info.checksum = checksum
            archive_info.file_path = str(archive_file)
            archive_info.compression_ratio = compression_ratio
            archive_info.status = "completed"
            
            # Register the archive
            self.registry[archive_id] = archive_info
            self._save_registry()
            self._update_statistics()
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            # Update statistics
            self.stats["last_archival"] = datetime.now()
            
            logger.info(f"Archive {archive_id} created successfully: {archive_file}")
            logger.info(f"Compression ratio: {compression_ratio:.2%}")
            
            return archive_id
            
        except Exception as e:
            logger.error(f"Error creating archive {archive_id}: {e}")
            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
            
    def restore_archive(self, archive_id: str, restore_memory: bool = True, 
                       restore_context: bool = True, restore_relations: bool = True) -> Dict:
        """
        Restore an archive back to the database.
        
        Args:
            archive_id: ID of the archive to restore
            restore_memory: Whether to restore memories
            restore_context: Whether to restore contexts
            restore_relations: Whether to restore relations
            
        Returns:
            Dictionary with restoration results
        """
        if archive_id not in self.registry:
            raise ValueError(f"Archive not found: {archive_id}")
            
        archive_info = self.registry[archive_id]
        archive_file = Path(archive_info.file_path)
        
        if not archive_file.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_file}")
            
        logger.info(f"Restoring archive {archive_id}")
        
        # Create temporary directory for extraction
        temp_dir = Path("/tmp") / f"restore_{archive_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "memories_restored": 0,
            "contexts_restored": 0,
            "relations_restored": 0,
            "errors": []
        }
        
        try:
            # Extract archive
            if archive_info.policy_name in self.policies:
                policy = self.policies[archive_info.policy_name]
                
                if policy.archive_format == "zip":
                    with zipfile.ZipFile(archive_file, 'r') as zipf:
                        zipf.extractall(temp_dir)
                elif policy.archive_format in ["tar.gz", "tgz"]:
                    with tarfile.open(archive_file, 'r:gz') as tar:
                        tar.extractall(temp_dir)
                elif policy.archive_format == "tar.bz2":
                    with tarfile.open(archive_file, 'r:bz2') as tar:
                        tar.extractall(temp_dir)
                else:
                    # Directory format - already extracted
                    pass
                    
            # Load metadata
            metadata_file = temp_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    
            # Restore contexts if requested
            if restore_context:
                contexts_dir = temp_dir / "contexts"
                if contexts_dir.exists():
                    for context_file in contexts_dir.glob("*.json"):
                        try:
                            with open(context_file, 'r') as f:
                                context_data = json.load(f)
                                
                            context = Context(
                                id=context_data["id"],
                                name=context_data["name"],
                                description=context_data["description"],
                                metadata=context_data.get("metadata", {}),
                                tags=context_data.get("tags", [])
                            )
                            
                            # Set dates manually
                            context.created_at = datetime.fromisoformat(context_data["created_at"])
                            context.updated_at = datetime.fromisoformat(context_data["updated_at"])
                            
                            self.db.create_context(context)
                            results["contexts_restored"] += 1
                            
                        except Exception as e:
                            error_msg = f"Error restoring context from {context_file}: {e}"
                            logger.error(error_msg)
                            results["errors"].append(error_msg)
                            
            # Restore memories if requested
            if restore_memory:
                memories_dir = temp_dir / "memories"
                if memories_dir.exists():
                    for memory_file in memories_dir.glob("*.json"):
                        try:
                            with open(memory_file, 'r') as f:
                                memory_data = json.load(f)
                                
                            memory = Memory(
                                id=memory_data["id"],
                                content=memory_data["content"],
                                metadata=memory_data.get("metadata", {}),
                                context_id=memory_data.get("context_id"),
                                vector_id=memory_data.get("vector_id"),
                                chunk_ids=memory_data.get("chunk_ids", []),
                                compressed=memory_data.get("compressed", False),
                                compression_algorithm=memory_data.get("compression_algorithm"),
                                compression_ratio=memory_data.get("compression_ratio"),
                                file_path=memory_data.get("file_path"),
                                file_size=memory_data.get("file_size"),
                                file_type=memory_data.get("file_type"),
                                checksum=memory_data.get("checksum")
                            )
                            
                            # Set dates manually
                            memory.created_at = datetime.fromisoformat(memory_data["created_at"])
                            memory.updated_at = datetime.fromisoformat(memory_data["updated_at"])
                            memory.access_count = memory_data.get("access_count", 0)
                            memory.last_accessed = datetime.fromisoformat(memory_data["last_accessed"]) if memory_data.get("last_accessed") else None
                            memory.tags = memory_data.get("tags", [])
                            
                            self.db.create_memory(memory)
                            results["memories_restored"] += 1
                            
                        except Exception as e:
                            error_msg = f"Error restoring memory from {memory_file}: {e}"
                            logger.error(error_msg)
                            results["errors"].append(error_msg)
                            
            # Restore relations if requested
            if restore_relations:
                relations_dir = temp_dir / "relations"
                if relations_dir.exists():
                    for relation_file in relations_dir.glob("*.json"):
                        try:
                            with open(relation_file, 'r') as f:
                                relation_data = json.load(f)
                                
                            for rel_data in relation_data["relations"]:
                                relation = Relation(
                                    id=rel_data["id"],
                                    source_memory_id=relation_data["source_memory_id"],
                                    target_memory_id=rel_data["target_memory_id"],
                                    relation_type=rel_data["relation_type"],
                                    strength=rel_data["strength"],
                                    metadata=rel_data.get("metadata", {})
                                )
                                
                                # Set dates manually
                                relation.created_at = datetime.fromisoformat(rel_data["created_at"])
                                relation.updated_at = datetime.fromisoformat(rel_data["updated_at"])
                                
                                self.db.create_relation(relation)
                                results["relations_restored"] += 1
                                
                        except Exception as e:
                            error_msg = f"Error restoring relations from {relation_file}: {e}"
                            logger.error(error_msg)
                            results["errors"].append(error_msg)
                            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            logger.info(f"Archive {archive_id} restored: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error restoring archive {archive_id}: {e}")
            # Clean up on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
            
    def delete_archive(self, archive_id: str, verify_checksum: bool = True) -> bool:
        """
        Delete an archive from storage.
        
        Args:
            archive_id: ID of the archive to delete
            verify_checksum: Whether to verify checksum before deletion
            
        Returns:
            True if successful, False otherwise
        """
        if archive_id not in self.registry:
            logger.warning(f"Archive not found: {archive_id}")
            return False
            
        archive_info = self.registry[archive_id]
        archive_file = Path(archive_info.file_path)
        
        if not archive_file.exists():
            logger.warning(f"Archive file not found: {archive_file}")
            del self.registry[archive_id]
            self._save_registry()
            self._update_statistics()
            return True
            
        try:
            # Verify checksum if requested
            if verify_checksum and archive_info.checksum:
                calculated_checksum = self._calculate_checksum(archive_file)
                if calculated_checksum != archive_info.checksum:
                    logger.error(f"Checksum verification failed for archive {archive_id}")
                    return False
                    
            # Delete archive file
            archive_file.unlink()
            
            # Delete from registry
            del self.registry[archive_id]
            self._save_registry()
            self._update_statistics()
            
            logger.info(f"Archive {archive_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting archive {archive_id}: {e}")
            return False
            
    def list_archives(self, policy_name: str = None, status: str = None) -> List[ArchiveInfo]:
        """
        List archives with optional filtering.
        
        Args:
            policy_name: Filter by policy name
            status: Filter by status
            
        Returns:
            List of archive information
        """
        archives = list(self.registry.values())
        
        if policy_name:
            archives = [a for a in archives if a.policy_name == policy_name]
            
        if status:
            archives = [a for a in archives if a.status == status]
            
        return sorted(archives, key=lambda a: a.created_at, reverse=True)
        
    def get_archive_info(self, archive_id: str) -> Optional[ArchiveInfo]:
        """
        Get information about a specific archive.
        
        Args:
            archive_id: ID of the archive
            
        Returns:
            Archive information or None if not found
        """
        return self.registry.get(archive_id)
        
    def verify_archive(self, archive_id: str) -> bool:
        """
        Verify an archive's integrity.
        
        Args:
            archive_id: ID of the archive to verify
            
        Returns:
            True if verification passes, False otherwise
        """
        if archive_id not in self.registry:
            return False
            
        archive_info = self.registry[archive_id]
        archive_file = Path(archive_info.file_path)
        
        if not archive_file.exists():
            archive_info.status = "corrupted"
            self._save_registry()
            return False
            
        try:
            # Verify checksum
            if archive_info.checksum:
                calculated_checksum = self._calculate_checksum(archive_file)
                if calculated_checksum != archive_info.checksum:
                    archive_info.status = "corrupted"
                    self._save_registry()
                    return False
                    
            # Try to extract the archive
            temp_dir = Path("/tmp") / f"verify_{archive_id}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                if archive_info.policy_name in self.policies:
                    policy = self.policies[archive_info.policy_name]
                    
                    if policy.archive_format == "zip":
                        with zipfile.ZipFile(archive_file, 'r') as zipf:
                            # Test archive
                            zipf.testzip()
                    elif policy.archive_format in ["tar.gz", "tgz"]:
                        with tarfile.open(archive_file, 'r:gz') as tar:
                            # Test archive
                            tar.testall()
                    elif policy.archive_format == "tar.bz2":
                        with tarfile.open(archive_file, 'r:bz2') as tar:
                            # Test archive
                            tar.testall()
                            
                # Update status
                archive_info.status = "verified"
                self._save_registry()
                
                return True
                
            finally:
                # Clean up
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            logger.error(f"Error verifying archive {archive_id}: {e}")
            archive_info.status = "corrupted"
            self._save_registry()
            return False
            
    def cleanup_expired_archives(self) -> int:
        """
        Remove archives that have exceeded their retention period.
        
        Returns:
            Number of archives removed
        """
        if not self.enabled:
            return 0
            
        now = datetime.now()
        expired_archives = [
            archive_id for archive_id, info in self.registry.items()
            if info.retention_until < now and info.policy_name != "permanent"
        ]
        
        removed_count = 0
        for archive_id in expired_archives:
            if self.delete_archive(archive_id):
                removed_count += 1
                
        logger.info(f"Cleaned up {removed_count} expired archives")
        return removed_count
        
    def get_storage_statistics(self) -> Dict:
        """
        Get storage usage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        total_size = sum(info.size_bytes for info in self.registry.values())
        
        # Calculate size by policy
        by_policy = {}
        for archive_id, info in self.registry.items():
            if info.policy_name not in by_policy:
                by_policy[info.policy_name] = {"count": 0, "size": 0}
            by_policy[info.policy_name]["count"] += 1
            by_policy[info.policy_name]["size"] += info.size_bytes
            
        # Calculate size by status
        by_status = {}
        for info in self.registry.values():
            status = info.status
            if status not in by_status:
                by_status[status] = {"count": 0, "size": 0}
            by_status[status]["count"] += 1
            by_status[status]["size"] += info.size_bytes
            
        return {
            "total_archives": len(self.registry),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_size_gb": total_size / (1024 * 1024 * 1024),
            "by_policy": by_policy,
            "by_status": by_status,
            "archive_directory": str(self.archive_dir),
            "free_space_bytes": shutil.disk_usage(self.archive_dir).free
        }
        
    def create_policy(self, name: str, description: str, retention_days: int, **kwargs) -> ArchivePolicy:
        """
        Create a new archival policy.
        
        Args:
            name: Policy name
            description: Policy description
            retention_days: Retention period in days
            **kwargs: Additional policy parameters
            
        Returns:
            Created policy
        """
        if name in self.policies:
            raise ValueError(f"Policy already exists: {name}")
            
        policy = ArchivePolicy(
            name=name,
            description=description,
            retention_days=retention_days,
            **kwargs
        )
        
        self.policies[name] = policy
        logger.info(f"Created new archival policy: {name}")
        return policy
        
    def delete_policy(self, name: str) -> bool:
        """
        Delete an archival policy.
        
        Args:
            name: Policy name
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.policies:
            return False
            
        # Check if any archives use this policy
        archives_using_policy = [
            archive_id for archive_id, info in self.registry.items()
            if info.policy_name == name
        ]
        
        if archives_using_policy:
            logger.warning(f"Cannot delete policy {name}: used by {len(archives_using_policy)} archives")
            return False
            
        del self.policies[name]
        logger.info(f"Deleted archival policy: {name}")
        return True
        
    def get_policies(self) -> Dict[str, ArchivePolicy]:
        """
        Get all archival policies.
        
        Returns:
            Dictionary mapping policy names to policies
        """
        return self.policies.copy()
        
    def get_archival_report(self) -> Dict:
        """
        Create a comprehensive archival report.
        
        Returns:
            Dictionary with archival statistics and findings
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "enabled": self.enabled,
                "archive_directory": str(self.archive_dir)
            },
            "statistics": self.stats.copy(),
            "storage_statistics": self.get_storage_statistics(),
            "policies": {
                name: policy.to_dict()
                for name, policy in self.policies.items()
            },
            "archives": [
                info.to_dict()
                for info in self.registry.values()
            ],
            "recommendations": []
        }
        
        # Add recommendations based on findings
        storage_stats = report["storage_statistics"]
        
        if storage_stats["total_size_gb"] > 10:
            report["recommendations"].append(
                "Large archival storage usage. Consider reviewing retention policies."
            )
            
        expired_count = len([
            info for info in self.registry.values()
            if info.retention_until < datetime.now() and info.policy_name != "permanent"
        ])
        
        if expired_count > 0:
            report["recommendations"].append(
                f"{expired_count} expired archives found. Consider running cleanup."
            )
            
        corrupted_count = len([
            info for info in self.registry.values()
            if info.status == "corrupted"
        ])
        
        if corrupted_count > 0:
            report["recommendations"].append(
                f"{corrupted_count} corrupted archives found. Consider verification and restoration."
            )
            
        return report