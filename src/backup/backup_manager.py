"""
Backup management system for the MCP Multi-Context Memory System.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import shutil
import json
import sqlite3
from sqlalchemy.orm import Session
import logging
import zipfile
import os

from ..database.models import Memory, Context, Relation

logger = logging.getLogger(__name__)

class BackupManager:
    """Manage database backups with versioning and verification."""
    
    def __init__(self, backup_dir: str = "./data/backups/"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 10  # Keep last 10 backups
    
    def create_backup(self, db_url: str, backup_name: Optional[str] = None) -> str:
        """Create a complete database backup."""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = self.backup_dir / backup_name
            
            # Copy database file
            source_path = Path(db_url.replace("sqlite:///", ""))
            if source_path.exists():
                shutil.copy2(source_path, backup_path)
                logger.info(f"Database copied to {backup_path}")
            else:
                logger.warning(f"Source database not found: {source_path}")
            
            # Create backup metadata
            metadata = self._create_backup_metadata(db_url, backup_name, backup_path)
            
            # Create backup archive
            archive_path = self._create_backup_archive(backup_path, metadata)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created: {archive_path}")
            return str(archive_path)
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def _create_backup_metadata(self, db_url: str, backup_name: str, backup_path: Path) -> Dict[str, Any]:
        """Create backup metadata."""
        try:
            # Connect to database to get schema info
            db_path = Path(db_url.replace("sqlite:///", ""))
            
            metadata = {
                "timestamp": datetime.utcnow().isoformat(),
                "backup_name": backup_name,
                "source_database": str(db_path),
                "backup_size": backup_path.stat().st_size if backup_path.exists() else 0,
                "version": "1.0",
                "database_info": self._get_database_info(db_path)
            }
            
            # Save metadata
            metadata_file = backup_path.with_suffix(".json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error creating backup metadata: {e}")
            return {}
    
    def _get_database_info(self, db_path: Path) -> Dict[str, Any]:
        """Get database information."""
        try:
            if not db_path.exists():
                return {}
            
            info = {}
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table counts
            tables = ["memories", "contexts", "relations"]
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    info[f"{table}_count"] = count
                except Exception as e:
                    logger.warning(f"Error counting table {table}: {e}")
                    info[f"{tables}_count"] = 0
            
            # Get database size
            info["database_size_bytes"] = db_path.stat().st_size
            
            # Get schema info
            try:
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
                tables_info = cursor.fetchall()
                info["tables"] = {name: sql for name, sql in tables_info}
            except Exception as e:
                logger.warning(f"Error getting schema info: {e}")
                info["tables"] = {}
            
            conn.close()
            return info
        
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}
    
    def _create_backup_archive(self, backup_path: Path, metadata: Dict[str, Any]) -> Path:
        """Create a zip archive of the backup."""
        try:
            archive_path = self.backup_dir / f"{backup_path.stem}.zip"
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                if backup_path.exists():
                    zipf.write(backup_path, backup_path.name)
                
                # Add metadata file
                metadata_file = backup_path.with_suffix(".json")
                if metadata_file.exists():
                    zipf.write(metadata_file, metadata_file.name)
            
            # Remove original files
            if backup_path.exists():
                backup_path.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            return archive_path
        
        except Exception as e:
            logger.error(f"Error creating backup archive: {e}")
            raise
    
    def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup integrity."""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return {"verified": False, "error": "Backup file not found"}
            
            verification_result = {
                "verified": False,
                "backup_path": str(backup_path),
                "checks": {}
            }
            
            # Check if it's a zip file
            if backup_file.suffix.lower() != '.zip':
                verification_result["checks"]["file_type"] = {"passed": False, "message": "Not a zip file"}
                return verification_result
            
            # Extract and verify
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # List files in archive
                files = zipf.namelist()
                verification_result["checks"]["files_present"] = {
                    "passed": len(files) > 0,
                    "files": files
                }
                
                # Check for database file
                db_files = [f for f in files if f.endswith('.db')]
                verification_result["checks"]["database_file"] = {
                    "passed": len(db_files) > 0,
                    "files": db_files
                }
                
                # Check for metadata file
                metadata_files = [f for f in files if f.endswith('.json')]
                verification_result["checks"]["metadata_file"] = {
                    "passed": len(metadata_files) > 0,
                    "files": metadata_files
                }
                
                # Extract and verify database
                if db_files:
                    try:
                        # Extract to temporary location
                        temp_dir = self.backup_dir / "temp_verify"
                        temp_dir.mkdir(exist_ok=True)
                        
                        zipf.extract(db_files[0], temp_dir)
                        temp_db_path = temp_dir / db_files[0]
                        
                        # Test database connection
                        conn = sqlite3.connect(temp_db_path)
                        cursor = conn.cursor()
                        
                        # Try to query schema
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        
                        verification_result["checks"]["database_integrity"] = {
                            "passed": True,
                            "tables": [table[0] for table in tables]
                        }
                        
                        conn.close()
                        
                        # Clean up
                        temp_db_path.unlink()
                        temp_dir.rmdir()
                        
                    except Exception as e:
                        verification_result["checks"]["database_integrity"] = {
                            "passed": False,
                            "error": str(e)
                        }
                
                # Verify metadata
                if metadata_files:
                    try:
                        with zipf.open(metadata_files[0]) as f:
                            metadata = json.load(f)
                        
                        required_fields = ["timestamp", "backup_name", "source_database"]
                        missing_fields = [field for field in required_fields if field not in metadata]
                        
                        verification_result["checks"]["metadata_integrity"] = {
                            "passed": len(missing_fields) == 0,
                            "missing_fields": missing_fields,
                            "metadata": metadata
                        }
                        
                    except Exception as e:
                        verification_result["checks"]["metadata_integrity"] = {
                            "passed": False,
                            "error": str(e)
                        }
            
            # Overall verification
            all_checks_passed = all(
                check.get("passed", False) 
                for check in verification_result["checks"].values()
            )
            
            verification_result["verified"] = all_checks_passed
            
            return verification_result
        
        except Exception as e:
            logger.error(f"Error verifying backup: {e}")
            return {"verified": False, "error": str(e)}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("*.zip"):
                metadata = self._get_backup_metadata(backup_file)
                
                verification_result = self.verify_backup(str(backup_file))
                
                backups.append({
                    "name": backup_file.stem,
                    "path": str(backup_file),
                    "timestamp": metadata.get("timestamp"),
                    "size": backup_file.stat().st_size,
                    "verified": verification_result.get("verified", False),
                    "database_size": metadata.get("database_info", {}).get("database_size_bytes", 0),
                    "memory_count": metadata.get("database_info", {}).get("memories_count", 0),
                    "context_count": metadata.get("database_info", {}).get("contexts_count", 0),
                    "relation_count": metadata.get("database_info", {}).get("relations_count", 0)
                })
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return backups
        
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def _get_backup_metadata(self, backup_file: Path) -> Dict[str, Any]:
        """Get metadata from backup file."""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Find metadata file
                metadata_files = [f for f in zipf.namelist() if f.endswith('.json')]
                
                if metadata_files:
                    with zipf.open(metadata_files[0]) as f:
                        return json.load(f)
                
                return {}
        
        except Exception as e:
            logger.error(f"Error getting backup metadata: {e}")
            return {}
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """Restore database from backup."""
        try:
            backup_file = Path(backup_path)
            target_file = Path(target_path)
            
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create backup of current database
            if target_file.exists():
                current_backup = self.create_backup(str(target_file), f"pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
                logger.info(f"Current database backed up to: {current_backup}")
            
            # Extract backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Find database file
                db_files = [f for f in zipf.namelist() if f.endswith('.db')]
                
                if not db_files:
                    logger.error("No database file found in backup")
                    return False
                
                # Extract database file
                zipf.extract(db_files[0], target_file.parent)
                
                # Move extracted file to target location
                extracted_path = target_file.parent / db_files[0]
                extracted_path.rename(target_file)
            
            logger.info(f"Database restored from {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Clean up old backups, keeping only the most recent ones."""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.max_backups:
                # Remove oldest backups
                backups_to_remove = backups[self.max_backups:]
                
                for backup in backups_to_remove:
                    backup_path = Path(backup["path"])
                    if backup_path.exists():
                        backup_path.unlink()
                        logger.info(f"Removed old backup: {backup_path}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def create_incremental_backup(self, db_url: str, last_backup_time: datetime) -> str:
        """Create incremental backup of changes since last backup."""
        try:
            # This is a simplified version - in production, you'd want
            # to implement proper incremental backup with transaction logs
            
            backup_name = f"incremental_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_name
            
            # For now, create a full backup
            # In production, you'd only backup changed records
            return self.create_backup(db_url, backup_name)
        
        except Exception as e:
            logger.error(f"Error creating incremental backup: {e}")
            raise
    
    def backup_configuration(self) -> str:
        """Backup system configuration files."""
        try:
            config_backup_name = f"config_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            config_backup_path = self.backup_dir / config_backup_name
            
            # Create zip of config files
            config_files = [
                ".env",
                "kilo_config.json",
                "docker-compose.yml",
                "Dockerfile"
            ]
            
            with zipfile.ZipFile(config_backup_path.with_suffix('.zip'), 'w', zipfile.ZIP_DEFLATED) as zipf:
                for config_file in config_files:
                    file_path = Path(config_file)
                    if file_path.exists():
                        zipf.write(file_path, file_path.name)
            
            logger.info(f"Configuration backup created: {config_backup_path.with_suffix('.zip')}")
            return str(config_backup_path.with_suffix('.zip'))
        
        except Exception as e:
            logger.error(f"Error backing up configuration: {e}")
            raise