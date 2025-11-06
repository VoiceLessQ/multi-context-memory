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
Rollback management system for the MCP Multi-Context Memory System.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import json
from datetime import datetime
import shutil

from ..database.models import Memory, Context, Relation
from ..utils.compression import ContentCompressor

logger = logging.getLogger(__name__)

class RollbackManager:
    """Manage rollback procedures for each optimization phase."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rollback_scripts = {
            "compression": self._rollback_compression,
            "chunking": self._rollback_chunking,
            "lazy_loading": self._rollback_lazy_loading,
            "hybrid_storage": self._rollback_hybrid_storage,
            "deduplication": self._rollback_deduplication,
            "archiving": self._rollback_archiving
        }
        self.rollback_points_dir = Path("./data/rollback_points")
        self.rollback_points_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_rollback(self, phase: str) -> Dict[str, Any]:
        """Execute rollback for a specific phase."""
        try:
            if phase not in self.rollback_scripts:
                return {
                    "success": False,
                    "error": f"No rollback script available for phase: {phase}"
                }
            
            logger.info(f"Starting rollback for phase: {phase}")
            
            # Get rollback point
            rollback_point = self._get_rollback_point(phase)
            if not rollback_point:
                return {
                    "success": False,
                    "error": f"No rollback point found for phase: {phase}"
                }
            
            # Execute rollback
            rollback_func = self.rollback_scripts[phase]
            rollback_result = rollback_func()
            
            if rollback_result.get("success", False):
                logger.info(f"Rollback completed successfully for phase: {phase}")
                
                # Clean up rollback point
                self._cleanup_rollback_point(phase)
                
                return {
                    "success": True,
                    "phase": phase,
                    "message": "Rollback completed successfully",
                    "backup_restored": rollback_point.get("backup_path")
                }
            else:
                error_msg = rollback_result.get("error", "Unknown error")
                logger.error(f"Rollback failed for phase {phase}: {error_msg}")
                return {
                    "success": False,
                    "phase": phase,
                    "error": error_msg
                }
        
        except Exception as e:
            logger.error(f"Error during rollback of phase {phase}: {e}")
            return {
                "success": False,
                "phase": phase,
                "error": str(e)
            }
    
    def create_rollback_point(self, phase: str) -> Dict[str, Any]:
        """Create a rollback point before implementing a phase."""
        try:
            from ..backup.backup_manager import BackupManager
            
            backup_manager = BackupManager()
            backup_name = f"pre_{phase}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup
            backup_path = backup_manager.create_backup(str(self.db.bind.url), backup_name)
            
            # Verify backup
            verification = backup_manager.verify_backup(backup_path)
            if not verification.get("verified", False):
                logger.error(f"Backup verification failed for rollback point: {backup_path}")
                return {
                    "success": False,
                    "error": "Backup verification failed"
                }
            
            # Store rollback point reference
            rollback_point = {
                "phase": phase,
                "backup_path": backup_path,
                "timestamp": datetime.utcnow().isoformat(),
                "backup_name": backup_name,
                "verified": True
            }
            
            rollback_file = self.rollback_points_dir / f"{phase}_rollback.json"
            with open(rollback_file, 'w') as f:
                json.dump(rollback_point, f, indent=2)
            
            logger.info(f"Rollback point created for phase {phase}: {backup_path}")
            
            return {
                "success": True,
                "phase": phase,
                "backup_path": backup_path,
                "rollback_file": str(rollback_file)
            }
        
        except Exception as e:
            logger.error(f"Failed to create rollback point for phase {phase}: {e}")
            return {
                "success": False,
                "phase": phase,
                "error": str(e)
            }
    
    def _get_rollback_point(self, phase: str) -> Optional[Dict[str, Any]]:
        """Get rollback point for a phase."""
        try:
            rollback_file = self.rollback_points_dir / f"{phase}_rollback.json"
            
            if not rollback_file.exists():
                return None
            
            with open(rollback_file, 'r') as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"Error getting rollback point for phase {phase}: {e}")
            return None
    
    def _cleanup_rollback_point(self, phase: str):
        """Clean up rollback point files."""
        try:
            rollback_file = self.rollback_points_dir / f"{phase}_rollback.json"
            if rollback_file.exists():
                rollback_file.unlink()
            
            # Also remove backup file if it exists
            rollback_point = self._get_rollback_point(phase)
            if rollback_point and rollback_point.get("backup_path"):
                backup_path = Path(rollback_point["backup_path"])
                if backup_path.exists():
                    backup_path.unlink()
        
        except Exception as e:
            logger.error(f"Error cleaning up rollback point for phase {phase}: {e}")
    
    def _rollback_compression(self) -> Dict[str, Any]:
        """Rollback compression changes."""
        try:
            logger.info("Starting compression rollback...")
            
            # Get all compressed memories
            compressed_memories = self.db.query(Memory).filter(
                Memory.content_compressed == True
            ).all()
            
            if not compressed_memories:
                logger.info("No compressed memories found to rollback")
                return {"success": True, "message": "No compressed memories found"}
            
            logger.info(f"Found {len(compressed_memories)} compressed memories to rollback")
            
            # Decompress all content
            decompressed_count = 0
            error_count = 0
            
            for memory in compressed_memories:
                try:
                    # Decompress content
                    decompressed_content = ContentCompressor.decompress(memory.content)
                    
                    # Update memory
                    memory.content = decompressed_content
                    memory.content_compressed = False
                    
                    decompressed_count += 1
                    
                    # Log progress
                    if decompressed_count % 100 == 0:
                        logger.info(f"Decompressed {decompressed_count}/{len(compressed_memories)} memories")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to decompress memory {memory.id}: {e}")
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Compression rollback completed: {decompressed_count} memories decompressed, {error_count} errors")
            
            return {
                "success": True,
                "message": f"Decompressed {decompressed_count} memories, {error_count} errors"
            }
        
        except Exception as e:
            logger.error(f"Error during compression rollback: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _rollback_chunking(self) -> Dict[str, Any]:
        """Rollback chunked storage changes."""
        try:
            logger.info("Starting chunking rollback...")
            
            # Check if chunk table exists
            try:
                self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_chunks'")
                chunk_table_exists = self.db.fetchone() is not None
            except Exception:
                chunk_table_exists = False
            
            if not chunk_table_exists:
                logger.info("No chunk table found to rollback")
                return {"success": True, "message": "No chunk table found"}
            
            # Get all chunked memories
            try:
                chunked_memories = self.db.execute("""
                    SELECT DISTINCT mc.memory_id
                    FROM memory_chunks mc
                    JOIN memories m ON mc.memory_id = m.id
                    WHERE m.content_compressed = 1 OR m.content LIKE 'file://%'
                """).fetchall()
                
                memory_ids = [row[0] for row in chunked_memories]
                
                if not memory_ids:
                    logger.info("No chunked memories found to rollback")
                    return {"success": True, "message": "No chunked memories found"}
                
                logger.info(f"Found {len(memory_ids)} chunked memories to rollback")
                
                # Reconstruct content from chunks
                reconstructed_count = 0
                error_count = 0
                
                for memory_id in memory_ids:
                    try:
                        # Get chunks for this memory
                        chunks = self.db.execute("""
                            SELECT chunk_index, content
                            FROM memory_chunks
                            WHERE memory_id = ?
                            ORDER BY chunk_index
                        """, (memory_id,)).fetchall()
                        
                        if chunks:
                            # Reconstruct content
                            reconstructed_content = ''.join(chunk.content for chunk in chunks)
                            
                            # Update original memory
                            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
                            
                            if memory:
                                memory.content = reconstructed_content
                                memory.content_compressed = False
                                reconstructed_count += 1
                                
                                # Log progress
                                if reconstructed_count % 100 == 0:
                                    logger.info(f"Reconstructed {reconstructed_count}/{len(memory_ids)} memories")
                    
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Failed to reconstruct memory {memory_id}: {e}")
                
                # Drop chunk tables
                try:
                    self.db.execute("DROP TABLE IF EXISTS memory_chunks")
                    self.db.execute("DROP TABLE IF EXISTS memory_chunk_metadata")
                except Exception as e:
                    logger.warning(f"Error dropping chunk tables: {e}")
                
                # Commit changes
                self.db.commit()
                
                logger.info(f"Chunking rollback completed: {reconstructed_count} memories reconstructed, {error_count} errors")
                
                return {
                    "success": True,
                    "message": f"Reconstructed {reconstructed_count} memories, {error_count} errors"
                }
            
            except Exception as e:
                logger.error(f"Error during chunking rollback: {e}")
                self.db.rollback()
                return {"success": False, "error": str(e)}
        
        except Exception as e:
            logger.error(f"Error during chunking rollback: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _rollback_lazy_loading(self) -> Dict[str, Any]:
        """Rollback lazy loading changes."""
        try:
            logger.info("Starting lazy loading rollback...")
            
            # Lazy loading is typically a behavior change, not a schema change
            # No specific rollback needed, just restart service
            
            # Clear any lazy loading caches
            try:
                # Clear any cached data
                self.db.execute("DELETE FROM memory_cache")
                self.db.execute("DELETE FROM search_cache")
            except Exception as e:
                logger.warning(f"Error clearing caches: {e}")
            
            self.db.commit()
            
            logger.info("Lazy loading rollback completed")
            
            return {
                "success": True,
                "message": "Lazy loading rollback completed (service restart recommended)"
            }
        
        except Exception as e:
            logger.error(f"Error during lazy loading rollback: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _rollback_hybrid_storage(self) -> Dict[str, Any]:
        """Rollback hybrid storage changes."""
        try:
            logger.info("Starting hybrid storage rollback...")
            
            # Get all memories with file storage references
            file_stored_memories = self.db.query(Memory).filter(
                Memory.content.like("file://%")
            ).all()
            
            if not file_stored_memories:
                logger.info("No file-stored memories found to rollback")
                return {"success": True, "message": "No file-stored memories found"}
            
            logger.info(f"Found {len(file_stored_memories)} file-stored memories to rollback")
            
            # Read content from files and store in database
            restored_count = 0
            error_count = 0
            
            for memory in file_stored_memories:
                try:
                    file_path = Path(memory.content[7:])  # Remove "file://" prefix
                    
                    if file_path.exists():
                        # Read content from file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        
                        # Update memory
                        memory.content = file_content
                        memory.content_compressed = False
                        
                        # Remove file
                        file_path.unlink()
                        
                        restored_count += 1
                        
                        # Log progress
                        if restored_count % 100 == 0:
                            logger.info(f"Restored {restored_count}/{len(file_stored_memories)} memories")
                    else:
                        logger.warning(f"File not found for memory {memory.id}: {file_path}")
                        error_count += 1
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to restore content from file for memory {memory.id}: {e}")
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Hybrid storage rollback completed: {restored_count} memories restored, {error_count} errors")
            
            return {
                "success": True,
                "message": f"Restored {restored_count} memories, {error_count} errors"
            }
        
        except Exception as e:
            logger.error(f"Error during hybrid storage rollback: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _rollback_deduplication(self) -> Dict[str, Any]:
        """Rollback deduplication changes."""
        try:
            logger.info("Starting deduplication rollback...")
            
            # Check if deduplication table exists
            try:
                self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deduplication_hashes'")
                dedup_table_exists = self.db.fetchone() is not None
            except Exception:
                dedup_table_exists = False
            
            if not dedup_table_exists:
                logger.info("No deduplication table found to rollback")
                return {"success": True, "message": "No deduplication table found"}
            
            # Drop deduplication tables
            try:
                self.db.execute("DROP TABLE IF EXISTS deduplication_hashes")
                self.db.execute("DROP TABLE IF EXISTS deduplication_groups")
            except Exception as e:
                logger.warning(f"Error dropping deduplication tables: {e}")
            
            self.db.commit()
            
            logger.info("Deduplication rollback completed")
            
            return {
                "success": True,
                "message": "Deduplication rollback completed"
            }
        
        except Exception as e:
            logger.error(f"Error during deduplication rollback: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def _rollback_archiving(self) -> Dict[str, Any]:
        """Rollback archiving changes."""
        try:
            logger.info("Starting archiving rollback...")
            
            # Check if archive table exists
            try:
                self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='archived_memories'")
                archive_table_exists = self.db.fetchone() is not None
            except Exception:
                archive_table_exists = False
            
            if not archive_table_exists:
                logger.info("No archive table found to rollback")
                return {"success": True, "message": "No archive table found"}
            
            # Restore archived memories
            try:
                # Get archived memories
                archived_memories = self.db.execute("""
                    SELECT id, title, content, owner_id, context_id, access_level, 
                           memory_metadata, created_at, updated_at
                    FROM archived_memories
                    WHERE is_active = 1
                """).fetchall()
                
                if not archived_memories:
                    logger.info("No archived memories found to restore")
                else:
                    logger.info(f"Found {len(archived_memories)} archived memories to restore")
                    
                    # Restore to main memories table
                    restored_count = 0
                    
                    for memory_data in archived_memories:
                        try:
                            # Create new memory
                            memory = Memory(
                                id=memory_data.id,  # Use original ID
                                title=memory_data.title,
                                content=memory_data.content,
                                owner_id=memory_data.owner_id,
                                context_id=memory_data.context_id,
                                access_level=memory_data.access_level,
                                memory_metadata=memory_data.memory_metadata,
                                created_at=memory_data.created_at,
                                updated_at=memory_data.updated_at,
                                is_active=True
                            )
                            
                            self.db.add(memory)
                            restored_count += 1
                            
                            # Log progress
                            if restored_count % 100 == 0:
                                logger.info(f"Restored {restored_count}/{len(archived_memories)} archived memories")
                        
                        except Exception as e:
                            logger.error(f"Failed to restore archived memory {memory_data.id}: {e}")
                    
                    # Mark as restored in archive
                    self.db.execute("""
                        UPDATE archived_memories 
                        SET is_active = 0, archived_at = ? 
                        WHERE is_active = 1
                    """, (datetime.utcnow(),))
                
                # Drop archive tables
                self.db.execute("DROP TABLE IF EXISTS archived_memories")
                self.db.execute("DROP TABLE IF EXISTS archive_metadata")
                
                self.db.commit()
                
                logger.info(f"Archiving rollback completed: {restored_count} memories restored")
                
                return {
                    "success": True,
                    "message": f"Restored {restored_count} archived memories"
                }
            
            except Exception as e:
                logger.error(f"Error during archiving rollback: {e}")
                self.db.rollback()
                return {"success": False, "error": str(e)}
        
        except Exception as e:
            logger.error(f"Error during archiving rollback: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def list_rollback_points(self) -> List[Dict[str, Any]]:
        """List all available rollback points."""
        try:
            rollback_points = []
            
            for rollback_file in self.rollback_points_dir.glob("*_rollback.json"):
                try:
                    with open(rollback_file, 'r') as f:
                        rollback_point = json.load(f)
                    
                    rollback_points.append({
                        "phase": rollback_point.get("phase"),
                        "backup_path": rollback_point.get("backup_path"),
                        "timestamp": rollback_point.get("timestamp"),
                        "backup_name": rollback_point.get("backup_name"),
                        "verified": rollback_point.get("verified", False),
                        "rollback_file": str(rollback_file)
                    })
                
                except Exception as e:
                    logger.error(f"Error reading rollback file {rollback_file}: {e}")
            
            # Sort by timestamp (newest first)
            rollback_points.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return rollback_points
        
        except Exception as e:
            logger.error(f"Error listing rollback points: {e}")
            return []
    
    def cleanup_all_rollback_points(self):
        """Clean up all rollback points."""
        try:
            rollback_points = self.list_rollback_points()
            
            for rollback_point in rollback_points:
                phase = rollback_point.get("phase")
                self._cleanup_rollback_point(phase)
            
            logger.info("Cleaned up all rollback points")
        
        except Exception as e:
            logger.error(f"Error cleaning up rollback points: {e}")