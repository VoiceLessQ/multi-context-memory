"""
Test script for testing the migration manager.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from src.database.enhanced_memory_db import EnhancedMemoryDB
from src.migration.migration_manager import MigrationManager
from tests.test_config import TestConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataGenerator:
    """Generate test data for the migration system."""
    
    def __init__(self):
        self.test_data = [
            {
                "title": "Legacy Memory 1",
                "content": "This is a legacy memory with small content.",
                "context_id": 1,
                "owner_id": "test_user_1"
            },
            {
                "title": "Legacy Memory 2",
                "content": "This is another legacy memory with slightly more content to test compression.",
                "context_id": 1,
                "owner_id": "test_user_1"
            },
            {
                "title": "Large Legacy Memory",
                "content": "This is a large legacy memory with a lot of content to test compression and lazy loading. " * 100,
                "context_id": 2,
                "owner_id": "test_user_2"
            },
            {
                "title": "Medium Legacy Memory",
                "content": "This is a medium legacy memory with some content. " * 50,
                "context_id": 2,
                "owner_id": "test_user_2"
            },
            {
                "title": "Very Large Legacy Memory",
                "content": "This is a very large legacy memory with an enormous amount of content to test compression and lazy loading. " * 500,
                "context_id": 3,
                "owner_id": "test_user_3"
            }
        ]
    
    def get_test_data(self) -> List[Dict[str, Any]]:
        """Get test data."""
        return self.test_data
    
    def get_large_test_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate large test data."""
        large_data = []
        for i in range(count):
            large_data.append({
                "title": f"Large Legacy Memory {i}",
                "content": f"This is a large legacy memory with content for testing. " * (i % 10 + 1),
                "context_id": (i % 5) + 1,
                "owner_id": f"test_user_{(i % 3) + 1}"
            })
        return large_data

async def create_legacy_memories(db: EnhancedMemoryDB, test_data: List[Dict[str, Any]]):
    """Create legacy memories without compression."""
    created_memories = []
    for data in test_data:
        # Create memory without compression
        memory = await db.create_memory(data, compress_content=False)
        created_memories.append(memory)
        logger.info(f"Created legacy memory {memory.id}")
    
    return created_memories

async def create_legacy_relations(db: EnhancedMemoryDB, memories: List[Any]):
    """Create legacy relations."""
    for i in range(len(memories)):
        for j in range(i + 1, len(memories)):
            await db.create_relation({
                "source_memory_id": memories[i].id,
                "target_memory_id": memories[j].id,
                "name": "related_to",
                "strength": 0.8
            })
            logger.info(f"Created relation between memory {memories[i].id} and {memories[j].id}")

async def test_migration_manager():
    """Test the migration manager."""
    logger.info("Testing migration manager...")
    
    # Ensure test directories exist
    TestConfig.ensure_test_directories()
    
    # Initialize database
    db = EnhancedMemoryDB(TestConfig.DATABASE_URL)
    
    try:
        # Initialize database
        await db.initialize()
        await db.create_tables()
        
        # Create test contexts
        for context in TestConfig.TEST_CONTEXTS:
            await db.create_context(context)
        
        # Create test data
        test_generator = TestDataGenerator()
        test_data = test_generator.get_test_data()
        large_test_data = test_generator.get_large_test_data(50)
        
        # Create legacy memories
        legacy_memories = await create_legacy_memories(db, test_data + large_test_data)
        
        # Create legacy relations
        await create_legacy_relations(db, legacy_memories)
        
        # Initialize migration manager
        migration_manager = MigrationManager(
            db_url=TestConfig.DATABASE_URL,
            batch_size=10,
            dry_run=True  # Start with dry run
        )
        
        # Test dry run
        logger.info("Testing dry run...")
        report = await migration_manager.run_migration()
        
        logger.info(f"Dry run report: {report}")
        
        # Test actual migration
        logger.info("Testing actual migration...")
        migration_manager = MigrationManager(
            db_url=TestConfig.DATABASE_URL,
            batch_size=10,
            dry_run=False
        )
        
        report = await migration_manager.run_migration()
        
        logger.info(f"Actual migration report: {report}")
        
        # Verify migration
        logger.info("Verifying migration...")
        
        # Check if memories are compressed
        for memory in legacy_memories:
            migrated_memory = await db.get_memory(memory.id)
            if migrated_memory:
                logger.info(f"Memory {memory.id}: Compressed = {migrated_memory.content_compressed}")
            else:
                logger.error(f"Memory {memory.id} not found after migration")
        
        # Check if relations are preserved
        for memory in legacy_memories:
            relations = await db.get_memory_relations(memory.id)
            logger.info(f"Memory {memory.id}: {len(relations)} relations")
        
        logger.info("Migration manager test completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration manager test failed: {e}")
        raise
    
    finally:
        # Clean up
        await cleanup_test_data(db)
        await db.close()

async def cleanup_test_data(db: EnhancedMemoryDB):
    """Clean up test data."""
    logger.info("Cleaning up test data...")
    
    # Get all test memories
    memories = await db.get_memories()
    
    # Delete test memories
    for memory in memories:
        if memory.title.startswith("Legacy Memory"):
            await db.delete_memory(memory.id)
            logger.info(f"Deleted memory {memory.id}")
    
    # Delete test contexts
    for context in TestConfig.TEST_CONTEXTS:
        await db.delete_context(context["id"])
        logger.info(f"Deleted context {context['id']}")
    
    logger.info("Test data cleaned up")

async def main():
    """Main test function."""
    logger.info("Starting migration manager test...")
    
    try:
        await test_migration_manager()
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())