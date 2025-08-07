"""
Data migration tools for converting between JSONL and SQLite formats.
"""
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import aiofiles
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from ...database.models import Base, User, Context, Memory, Relation
from ...database.enhanced_memory_db import EnhancedMemoryDB
from ...utils.error_handling import MigrationError, handle_migration_error
from ...utils.crypto import decrypt_data, encrypt_data

logger = logging.getLogger(__name__)

class JSONLToSQLiteMigrator:
    """
    Migrator for converting JSONL data to SQLite format.
    """
    
    def __init__(self, 
                 jsonl_data_path: str = "./data/jsonl/",
                 sqlite_data_path: str = "./data/sqlite/",
                 batch_size: int = 1000,
                 validate_data: bool = True):
        """
        Initialize the migrator.
        
        Args:
            jsonl_data_path: Path to JSONL data files
            sqlite_data_path: Path to SQLite database
            batch_size: Batch size for migration
            validate_data: Whether to validate data during migration
        """
        self.jsonl_data_path = Path(jsonl_data_path)
        self.sqlite_data_path = Path(sqlite_data_path)
        self.batch_size = batch_size
        self.validate_data = validate_data
        self.db = None
        
        # Create SQLite directory if it doesn't exist
        self.sqlite_data_path.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """
        Initialize the migrator.
        """
        # Initialize database
        database_url = f"sqlite+aiosqlite:///{self.sqlite_data_path}/memory.db"
        self.db = EnhancedMemoryDB(database_url=database_url)
        await self.db.initialize()
        
        # Create tables
        await self.db.create_tables()
        
    async def close(self):
        """
        Close the migrator.
        """
        if self.db:
            await self.db.close()
            
    async def migrate_all(self) -> Dict[str, Any]:
        """
        Migrate all data from JSONL to SQLite.
        
        Returns:
            Migration results
        """
        results = {
            "users": {"migrated": 0, "errors": 0, "skipped": 0},
            "contexts": {"migrated": 0, "errors": 0, "skipped": 0},
            "memories": {"migrated": 0, "errors": 0, "skipped": 0},
            "relations": {"migrated": 0, "errors": 0, "skipped": 0},
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration": None
        }
        
        try:
            start_time = datetime.now()
            
            # Migrate users
            await self.migrate_users(results)
            
            # Migrate contexts
            await self.migrate_contexts(results)
            
            # Migrate memories
            await self.migrate_memories(results)
            
            # Migrate relations
            await self.migrate_relations(results)
            
            # Update results
            end_time = datetime.now()
            results["end_time"] = end_time.isoformat()
            results["total_duration"] = str(end_time - start_time)
            
            logger.info(f"Migration completed: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise MigrationError(f"Migration failed: {e}", step="migrate_all")
            
    async def migrate_users(self, results: Dict[str, Any]) -> None:
        """
        Migrate users from JSONL to SQLite.
        
        Args:
            results: Migration results to update
        """
        try:
            jsonl_file = self.jsonl_data_path / "users.jsonl"
            
            if not jsonl_file.exists():
                logger.warning(f"Users JSONL file not found: {jsonl_file}")
                return
                
            # Read JSONL file
            async with aiofiles.open(jsonl_file, 'r') as f:
                lines = await f.readlines()
                
            # Process in batches
            batch = []
            for line in lines:
                try:
                    user_data = json.loads(line.strip())
                    
                    # Validate data
                    if self.validate_data:
                        self._validate_user_data(user_data)
                        
                    batch.append(user_data)
                    
                    # Process batch
                    if len(batch) >= self.batch_size:
                        await self._process_user_batch(batch, results)
                        batch = []
                        
                except Exception as e:
                    logger.error(f"Error processing user line: {e}")
                    results["users"]["errors"] += 1
                    
            # Process remaining batch
            if batch:
                await self._process_user_batch(batch, results)
                
        except Exception as e:
            logger.error(f"Error migrating users: {e}")
            raise MigrationError(f"User migration failed: {e}", step="migrate_users")
            
    async def _process_user_batch(self, batch: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """
        Process a batch of users.
        
        Args:
            batch: Batch of user data
            results: Migration results to update
        """
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(batch)
            
            # Handle password encryption
            if 'password' in df.columns:
                df['password_hash'] = df['password'].apply(self._hash_password)
                df = df.drop('password', axis=1)
                
            # Convert to records
            records = df.to_dict('records')
            
            # Insert into database
            await self.db.db.execute(insert(User).values(records))
            
            # Update results
            results["users"]["migrated"] += len(records)
            
            logger.info(f"Migrated {len(records)} users")
            
        except Exception as e:
            logger.error(f"Error processing user batch: {e}")
            results["users"]["errors"] += len(batch)
            raise
            
    async def migrate_contexts(self, results: Dict[str, Any]) -> None:
        """
        Migrate contexts from JSONL to SQLite.
        
        Args:
            results: Migration results to update
        """
        try:
            jsonl_file = self.jsonl_data_path / "contexts.jsonl"
            
            if not jsonl_file.exists():
                logger.warning(f"Contexts JSONL file not found: {jsonl_file}")
                return
                
            # Read JSONL file
            async with aiofiles.open(jsonl_file, 'r') as f:
                lines = await f.readlines()
                
            # Process in batches
            batch = []
            for line in lines:
                try:
                    context_data = json.loads(line.strip())
                    
                    # Validate data
                    if self.validate_data:
                        self._validate_context_data(context_data)
                        
                    batch.append(context_data)
                    
                    # Process batch
                    if len(batch) >= self.batch_size:
                        await self._process_context_batch(batch, results)
                        batch = []
                        
                except Exception as e:
                    logger.error(f"Error processing context line: {e}")
                    results["contexts"]["errors"] += 1
                    
            # Process remaining batch
            if batch:
                await self._process_context_batch(batch, results)
                
        except Exception as e:
            logger.error(f"Error migrating contexts: {e}")
            raise MigrationError(f"Context migration failed: {e}", step="migrate_contexts")
            
    async def _process_context_batch(self, batch: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """
        Process a batch of contexts.
        
        Args:
            batch: Batch of context data
            results: Migration results to update
        """
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(batch)
            
            # Handle metadata
            if 'metadata' in df.columns:
                df['metadata'] = df['metadata'].apply(json.dumps)
                
            # Convert to records
            records = df.to_dict('records')
            
            # Insert into database
            await self.db.db.execute(insert(Context).values(records))
            
            # Update results
            results["contexts"]["migrated"] += len(records)
            
            logger.info(f"Migrated {len(records)} contexts")
            
        except Exception as e:
            logger.error(f"Error processing context batch: {e}")
            results["contexts"]["errors"] += len(batch)
            raise
            
    async def migrate_memories(self, results: Dict[str, Any]) -> None:
        """
        Migrate memories from JSONL to SQLite.
        
        Args:
            results: Migration results to update
        """
        try:
            jsonl_file = self.jsonl_data_path / "memories.jsonl"
            
            if not jsonl_file.exists():
                logger.warning(f"Memories JSONL file not found: {jsonl_file}")
                return
                
            # Read JSONL file
            async with aiofiles.open(jsonl_file, 'r') as f:
                lines = await f.readlines()
                
            # Process in batches
            batch = []
            for line in lines:
                try:
                    memory_data = json.loads(line.strip())
                    
                    # Validate data
                    if self.validate_data:
                        self._validate_memory_data(memory_data)
                        
                    batch.append(memory_data)
                    
                    # Process batch
                    if len(batch) >= self.batch_size:
                        await self._process_memory_batch(batch, results)
                        batch = []
                        
                except Exception as e:
                    logger.error(f"Error processing memory line: {e}")
                    results["memories"]["errors"] += 1
                    
            # Process remaining batch
            if batch:
                await self._process_memory_batch(batch, results)
                
        except Exception as e:
            logger.error(f"Error migrating memories: {e}")
            raise MigrationError(f"Memory migration failed: {e}", step="migrate_memories")
            
    async def _process_memory_batch(self, batch: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """
        Process a batch of memories.
        
        Args:
            batch: Batch of memory data
            results: Migration results to update
        """
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(batch)
            
            # Handle metadata
            if 'metadata' in df.columns:
                df['metadata'] = df['metadata'].apply(json.dumps)
                
            # Handle tags
            if 'tags' in df.columns:
                df['tags'] = df['tags'].apply(json.dumps)
                
            # Convert to records
            records = df.to_dict('records')
            
            # Insert into database
            await self.db.db.execute(insert(Memory).values(records))
            
            # Update results
            results["memories"]["migrated"] += len(records)
            
            logger.info(f"Migrated {len(records)} memories")
            
        except Exception as e:
            logger.error(f"Error processing memory batch: {e}")
            results["memories"]["errors"] += len(batch)
            raise
            
    async def migrate_relations(self, results: Dict[str, Any]) -> None:
        """
        Migrate relations from JSONL to SQLite.
        
        Args:
            results: Migration results to update
        """
        try:
            jsonl_file = self.jsonl_data_path / "relations.jsonl"
            
            if not jsonl_file.exists():
                logger.warning(f"Relations JSONL file not found: {jsonl_file}")
                return
                
            # Read JSONL file
            async with aiofiles.open(jsonl_file, 'r') as f:
                lines = await f.readlines()
                
            # Process in batches
            batch = []
            for line in lines:
                try:
                    relation_data = json.loads(line.strip())
                    
                    # Validate data
                    if self.validate_data:
                        self._validate_relation_data(relation_data)
                        
                    batch.append(relation_data)
                    
                    # Process batch
                    if len(batch) >= self.batch_size:
                        await self._process_relation_batch(batch, results)
                        batch = []
                        
                except Exception as e:
                    logger.error(f"Error processing relation line: {e}")
                    results["relations"]["errors"] += 1
                    
            # Process remaining batch
            if batch:
                await self._process_relation_batch(batch, results)
                
        except Exception as e:
            logger.error(f"Error migrating relations: {e}")
            raise MigrationError(f"Relation migration failed: {e}", step="migrate_relations")
            
    async def _process_relation_batch(self, batch: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """
        Process a batch of relations.
        
        Args:
            batch: Batch of relation data
            results: Migration results to update
        """
        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(batch)
            
            # Handle metadata
            if 'metadata' in df.columns:
                df['metadata'] = df['metadata'].apply(json.dumps)
                
            # Convert to records
            records = df.to_dict('records')
            
            # Insert into database
            await self.db.db.execute(insert(Relation).values(records))
            
            # Update results
            results["relations"]["migrated"] += len(records)
            
            logger.info(f"Migrated {len(records)} relations")
            
        except Exception as e:
            logger.error(f"Error processing relation batch: {e}")
            results["relations"]["errors"] += len(batch)
            raise
            
    def _validate_user_data(self, user_data: Dict[str, Any]) -> None:
        """
        Validate user data.
        
        Args:
            user_data: User data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        required_fields = ["username", "email", "password"]
        
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate email format
        if "@" not in user_data["email"]:
            raise ValueError(f"Invalid email format: {user_data['email']}")
            
        # Validate password length
        if len(user_data["password"]) < 8:
            raise ValueError(f"Password too short: {user_data['password']}")
            
    def _validate_context_data(self, context_data: Dict[str, Any]) -> None:
        """
        Validate context data.
        
        Args:
            context_data: Context data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        required_fields = ["name", "user_id"]
        
        for field in required_fields:
            if field not in context_data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate name length
        if len(context_data["name"]) > 255:
            raise ValueError(f"Context name too long: {context_data['name']}")
            
    def _validate_memory_data(self, memory_data: Dict[str, Any]) -> None:
        """
        Validate memory data.
        
        Args:
            memory_data: Memory data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        required_fields = ["title", "content", "user_id"]
        
        for field in required_fields:
            if field not in memory_data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate title length
        if len(memory_data["title"]) > 255:
            raise ValueError(f"Memory title too long: {memory_data['title']}")
            
        # Validate content length
        if len(memory_data["content"]) > 1000000:  # 1MB
            raise ValueError(f"Memory content too long: {memory_data['content']}")
            
    def _validate_relation_data(self, relation_data: Dict[str, Any]) -> None:
        """
        Validate relation data.
        
        Args:
            relation_data: Relation data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        required_fields = ["source_type", "source_id", "target_type", "target_id", "relation_type"]
        
        for field in required_fields:
            if field not in relation_data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate relation type
        valid_types = ["belongs_to", "related_to", "contains", "references", "similar_to"]
        if relation_data["relation_type"] not in valid_types:
            raise ValueError(f"Invalid relation type: {relation_data['relation_type']}")
            
    def _hash_password(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        from ...utils.auth import get_password_hash
        return get_password_hash(password)
        
    async def export_to_jsonl(self, output_path: str = "./data/exported_jsonl/") -> Dict[str, Any]:
        """
        Export data from SQLite to JSONL format.
        
        Args:
            output_path: Path to export JSONL files
            
        Returns:
            Export results
        """
        results = {
            "users": {"exported": 0, "errors": 0},
            "contexts": {"exported": 0, "errors": 0},
            "memories": {"exported": 0, "errors": 0},
            "relations": {"exported": 0, "errors": 0},
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration": None
        }
        
        try:
            start_time = datetime.now()
            
            # Create output directory
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Export users
            await self._export_users_to_jsonl(output_path, results)
            
            # Export contexts
            await self._export_contexts_to_jsonl(output_path, results)
            
            # Export memories
            await self._export_memories_to_jsonl(output_path, results)
            
            # Export relations
            await self._export_relations_to_jsonl(output_path, results)
            
            # Update results
            end_time = datetime.now()
            results["end_time"] = end_time.isoformat()
            results["total_duration"] = str(end_time - start_time)
            
            logger.info(f"Export completed: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise MigrationError(f"Export failed: {e}", step="export_to_jsonl")
            
    async def _export_users_to_jsonl(self, output_path: Path, results: Dict[str, Any]) -> None:
        """
        Export users to JSONL format.
        
        Args:
            output_path: Output path
            results: Export results to update
        """
        try:
            # Query users
            result = await self.db.db.execute(select(User))
            users = result.scalars().all()
            
            # Write to JSONL file
            output_file = output_path / "users.jsonl"
            async with aiofiles.open(output_file, 'w') as f:
                for user in users:
                    user_data = {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat()
                    }
                    await f.write(json.dumps(user_data) + "\n")
                    
            results["users"]["exported"] = len(users)
            logger.info(f"Exported {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error exporting users: {e}")
            results["users"]["errors"] = 1
            raise
            
    async def _export_contexts_to_jsonl(self, output_path: Path, results: Dict[str, Any]) -> None:
        """
        Export contexts to JSONL format.
        
        Args:
            output_path: Output path
            results: Export results to update
        """
        try:
            # Query contexts
            result = await self.db.db.execute(select(Context))
            contexts = result.scalars().all()
            
            # Write to JSONL file
            output_file = output_path / "contexts.jsonl"
            async with aiofiles.open(output_file, 'w') as f:
                for context in contexts:
                    context_data = {
                        "id": context.id,
                        "user_id": context.user_id,
                        "name": context.name,
                        "description": context.description,
                        "context_type": context.context_type,
                        "metadata": context.metadata,
                        "access_level": context.access_level,
                        "created_at": context.created_at.isoformat(),
                        "updated_at": context.updated_at.isoformat()
                    }
                    await f.write(json.dumps(context_data) + "\n")
                    
            results["contexts"]["exported"] = len(contexts)
            logger.info(f"Exported {len(contexts)} contexts")
            
        except Exception as e:
            logger.error(f"Error exporting contexts: {e}")
            results["contexts"]["errors"] = 1
            raise
            
    async def _export_memories_to_jsonl(self, output_path: Path, results: Dict[str, Any]) -> None:
        """
        Export memories to JSONL format.
        
        Args:
            output_path: Output path
            results: Export results to update
        """
        try:
            # Query memories
            result = await self.db.db.execute(select(Memory))
            memories = result.scalars().all()
            
            # Write to JSONL file
            output_file = output_path / "memories.jsonl"
            async with aiofiles.open(output_file, 'w') as f:
                for memory in memories:
                    memory_data = {
                        "id": memory.id,
                        "user_id": memory.user_id,
                        "context_id": memory.context_id,
                        "title": memory.title,
                        "content": memory.content,
                        "memory_type": memory.memory_type,
                        "metadata": memory.metadata,
                        "access_level": memory.access_level,
                        "tags": memory.tags,
                        "created_at": memory.created_at.isoformat(),
                        "updated_at": memory.updated_at.isoformat()
                    }
                    await f.write(json.dumps(memory_data) + "\n")
                    
            results["memories"]["exported"] = len(memories)
            logger.info(f"Exported {len(memories)} memories")
            
        except Exception as e:
            logger.error(f"Error exporting memories: {e}")
            results["memories"]["errors"] = 1
            raise
            
    async def _export_relations_to_jsonl(self, output_path: Path, results: Dict[str, Any]) -> None:
        """
        Export relations to JSONL format.
        
        Args:
            output_path: Output path
            results: Export results to update
        """
        try:
            # Query relations
            result = await self.db.db.execute(select(Relation))
            relations = result.scalars().all()
            
            # Write to JSONL file
            output_file = output_path / "relations.jsonl"
            async with aiofiles.open(output_file, 'w') as f:
                for relation in relations:
                    relation_data = {
                        "id": relation.id,
                        "user_id": relation.user_id,
                        "source_type": relation.source_type,
                        "source_id": relation.source_id,
                        "target_type": relation.target_type,
                        "target_id": relation.target_id,
                        "relation_type": relation.relation_type,
                        "metadata": relation.metadata,
                        "access_level": relation.access_level,
                        "created_at": relation.created_at.isoformat(),
                        "updated_at": relation.updated_at.isoformat()
                    }
                    await f.write(json.dumps(relation_data) + "\n")
                    
            results["relations"]["exported"] = len(relations)
            logger.info(f"Exported {len(relations)} relations")
            
        except Exception as e:
            logger.error(f"Error exporting relations: {e}")
            results["relations"]["errors"] = 1
            raise
            
    async def validate_migration(self) -> Dict[str, Any]:
        """
        Validate the migration results.
        
        Returns:
            Validation results
        """
        validation_results = {
            "users": {"valid": 0, "invalid": 0, "errors": []},
            "contexts": {"valid": 0, "invalid": 0, "errors": []},
            "memories": {"valid": 0, "invalid": 0, "errors": []},
            "relations": {"valid": 0, "invalid": 0, "errors": []},
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "total_duration": None
        }
        
        try:
            start_time = datetime.now()
            
            # Validate users
            await self._validate_users(validation_results)
            
            # Validate contexts
            await self._validate_contexts(validation_results)
            
            # Validate memories
            await self._validate_memories(validation_results)
            
            # Validate relations
            await self._validate_relations(validation_results)
            
            # Update results
            end_time = datetime.now()
            validation_results["end_time"] = end_time.isoformat()
            validation_results["total_duration"] = str(end_time - start_time)
            
            logger.info(f"Validation completed: {validation_results}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise MigrationError(f"Validation failed: {e}", step="validate_migration")
            
    async def _validate_users(self, validation_results: Dict[str, Any]) -> None:
        """
        Validate users.
        
        Args:
            validation_results: Validation results to update
        """
        try:
            # Query users
            result = await self.db.db.execute(select(User))
            users = result.scalars().all()
            
            for user in users:
                try:
                    # Validate user data
                    if not user.username:
                        validation_results["users"]["invalid"] += 1
                        validation_results["users"]["errors"].append(f"User {user.id} has empty username")
                        continue
                        
                    if not user.email:
                        validation_results["users"]["invalid"] += 1
                        validation_results["users"]["errors"].append(f"User {user.id} has empty email")
                        continue
                        
                    if "@" not in user.email:
                        validation_results["users"]["invalid"] += 1
                        validation_results["users"]["errors"].append(f"User {user.id} has invalid email: {user.email}")
                        continue
                        
                    validation_results["users"]["valid"] += 1
                    
                except Exception as e:
                    validation_results["users"]["invalid"] += 1
                    validation_results["users"]["errors"].append(f"Error validating user {user.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error validating users: {e}")
            raise
            
    async def _validate_contexts(self, validation_results: Dict[str, Any]) -> None:
        """
        Validate contexts.
        
        Args:
            validation_results: Validation results to update
        """
        try:
            # Query contexts
            result = await self.db.db.execute(select(Context))
            contexts = result.scalars().all()
            
            for context in contexts:
                try:
                    # Validate context data
                    if not context.name:
                        validation_results["contexts"]["invalid"] += 1
                        validation_results["contexts"]["errors"].append(f"Context {context.id} has empty name")
                        continue
                        
                    if len(context.name) > 255:
                        validation_results["contexts"]["invalid"] += 1
                        validation_results["contexts"]["errors"].append(f"Context {context.id} has name too long: {context.name}")
                        continue
                        
                    validation_results["contexts"]["valid"] += 1
                    
                except Exception as e:
                    validation_results["contexts"]["invalid"] += 1
                    validation_results["contexts"]["errors"].append(f"Error validating context {context.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error validating contexts: {e}")
            raise
            
    async def _validate_memories(self, validation_results: Dict[str, Any]) -> None:
        """
        Validate memories.
        
        Args:
            validation_results: Validation results to update
        """
        try:
            # Query memories
            result = await self.db.db.execute(select(Memory))
            memories = result.scalars().all()
            
            for memory in memories:
                try:
                    # Validate memory data
                    if not memory.title:
                        validation_results["memories"]["invalid"] += 1
                        validation_results["memories"]["errors"].append(f"Memory {memory.id} has empty title")
                        continue
                        
                    if len(memory.title) > 255:
                        validation_results["memories"]["invalid"] += 1
                        validation_results["memories"]["errors"].append(f"Memory {memory.id} has title too long: {memory.title}")
                        continue
                        
                    if not memory.content:
                        validation_results["memories"]["invalid"] += 1
                        validation_results["memories"]["errors"].append(f"Memory {memory.id} has empty content")
                        continue
                        
                    if len(memory.content) > 1000000:  # 1MB
                        validation_results["memories"]["invalid"] += 1
                        validation_results["memories"]["errors"].append(f"Memory {memory.id} has content too long: {len(memory.content)} characters")
                        continue
                        
                    validation_results["memories"]["valid"] += 1
                    
                except Exception as e:
                    validation_results["memories"]["invalid"] += 1
                    validation_results["memories"]["errors"].append(f"Error validating memory {memory.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error validating memories: {e}")
            raise
            
    async def _validate_relations(self, validation_results: Dict[str, Any]) -> None:
        """
        Validate relations.
        
        Args:
            validation_results: Validation results to update
        """
        try:
            # Query relations
            result = await self.db.db.execute(select(Relation))
            relations = result.scalars().all()
            
            valid_types = ["belongs_to", "related_to", "contains", "references", "similar_to"]
            
            for relation in relations:
                try:
                    # Validate relation data
                    if not relation.source_type:
                        validation_results["relations"]["invalid"] += 1
                        validation_results["relations"]["errors"].append(f"Relation {relation.id} has empty source type")
                        continue
                        
                    if not relation.target_type:
                        validation_results["relations"]["invalid"] += 1
                        validation_results["relations"]["errors"].append(f"Relation {relation.id} has empty target type")
                        continue
                        
                    if not relation.relation_type:
                        validation_results["relations"]["invalid"] += 1
                        validation_results["relations"]["errors"].append(f"Relation {relation.id} has empty relation type")
                        continue
                        
                    if relation.relation_type not in valid_types:
                        validation_results["relations"]["invalid"] += 1
                        validation_results["relations"]["errors"].append(f"Relation {relation.id} has invalid relation type: {relation.relation_type}")
                        continue
                        
                    validation_results["relations"]["valid"] += 1
                    
                except Exception as e:
                    validation_results["relations"]["invalid"] += 1
                    validation_results["relations"]["errors"].append(f"Error validating relation {relation.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error validating relations: {e}")
            raise