"""
Test script for testing the enhanced memory system with new data.
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from src.database.enhanced_memory_db import EnhancedMemoryDB
from src.monitoring.memory_monitor import MemoryMonitor
from src.monitoring.dashboard import MonitoringDashboard
from tests.test_config import TestConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataGenerator:
    """Generate test data for the memory system."""
    
    def __init__(self):
        self.test_data = [
            {
                "title": "Test Memory 1",
                "content": "This is a test memory with small content.",
                "context_id": 1,
                "owner_id": "test_user_1"
            },
            {
                "title": "Test Memory 2",
                "content": "This is another test memory with slightly more content to test compression.",
                "context_id": 1,
                "owner_id": "test_user_1"
            },
            {
                "title": "Large Test Memory",
                "content": "This is a large test memory with a lot of content to test compression and lazy loading. " * 100,
                "context_id": 2,
                "owner_id": "test_user_2"
            },
            {
                "title": "Medium Test Memory",
                "content": "This is a medium test memory with some content. " * 50,
                "context_id": 2,
                "owner_id": "test_user_2"
            },
            {
                "title": "Very Large Test Memory",
                "content": "This is a very large test memory with an enormous amount of content to test compression and lazy loading. " * 500,
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
                "title": f"Large Test Memory {i}",
                "content": f"This is a large test memory with content for testing. " * (i % 10 + 1),
                "context_id": (i % 5) + 1,
                "owner_id": f"test_user_{(i % 3) + 1}"
            })
        return large_data

async def test_memory_creation(db: EnhancedMemoryDB):
    """Test memory creation with compression."""
    logger.info("Testing memory creation with compression...")
    
    test_generator = TestDataGenerator()
    test_data = test_generator.get_test_data()
    
    created_memories = []
    for data in test_data:
        start_time = time.time()
        
        memory = await db.create_memory(data)
        created_memories.append(memory)
        
        end_time = time.time()
        logger.info(f"Created memory {memory.id} in {end_time - start_time:.4f} seconds")
        logger.info(f"Memory size: {len(memory.content)} bytes")
        logger.info(f"Compressed: {memory.content_compressed}")
    
    return created_memories

async def test_memory_search(db: EnhancedMemoryDB, use_lazy: bool = True):
    """Test memory search with lazy loading."""
    logger.info(f"Testing memory search with lazy loading: {use_lazy}...")
    
    # Test search with lazy loading
    start_time = time.time()
    memories = await db.search_memories("test", use_lazy=use_lazy)
    end_time = time.time()
    
    logger.info(f"Found {len(memories)} memories in {end_time - start_time:.4f} seconds")
    
    # Check if lazy loading is working
    for memory in memories:
        if hasattr(memory, '_content_loaded'):
            logger.info(f"Memory {memory.id}: Content loaded = {memory._content_loaded}")
        else:
            logger.info(f"Memory {memory.id}: No lazy loading info")
    
    return memories

async def test_memory_retrieval(db: EnhancedMemoryDB, use_lazy: bool = True):
    """Test memory retrieval with lazy loading."""
    logger.info(f"Testing memory retrieval with lazy loading: {use_lazy}...")
    
    # Get all memories
    all_memories = await db.get_memories(use_lazy=use_lazy)
    
    logger.info(f"Retrieved {len(all_memories)} memories")
    
    # Check if lazy loading is working
    for memory in all_memories:
        if hasattr(memory, '_content_loaded'):
            logger.info(f"Memory {memory.id}: Content loaded = {memory._content_loaded}")
        else:
            logger.info(f"Memory {memory.id}: No lazy loading info")
    
    return all_memories

async def test_memory_monitoring():
    """Test memory monitoring."""
    logger.info("Testing memory monitoring...")
    
    # Initialize memory monitor
    memory_monitor = MemoryMonitor(TestConfig.DATABASE_URL)
    
    # Get memory usage stats
    memory_stats = memory_monitor.get_memory_usage_stats()
    logger.info(f"Memory usage stats: {memory_stats}")
    
    # Get compression stats
    compression_stats = memory_monitor.get_compression_stats()
    logger.info(f"Compression stats: {compression_stats}")
    
    # Get lazy loading stats
    lazy_loading_stats = memory_monitor.get_lazy_loading_stats()
    logger.info(f"Lazy loading stats: {lazy_loading_stats}")
    
    # Get performance stats
    performance_stats = memory_monitor.get_performance_stats()
    logger.info(f"Performance stats: {performance_stats}")
    
    # Get alerts
    alerts = memory_monitor.get_alerts()
    logger.info(f"Alerts: {alerts}")
    
    # Generate report
    report = memory_monitor.generate_report()
    logger.info(f"Report generated: {len(report)} sections")
    
    return report

async def test_dashboard():
    """Test dashboard generation."""
    logger.info("Testing dashboard generation...")
    
    # Initialize dashboard
    dashboard = MonitoringDashboard(TestConfig.DATABASE_URL)
    
    # Get dashboard data
    dashboard_data = dashboard.get_dashboard_data()
    logger.info(f"Dashboard data: {len(dashboard_data)} sections")
    
    # Generate HTML dashboard
    html_dashboard = dashboard.generate_html_dashboard()
    logger.info(f"HTML dashboard generated: {len(html_dashboard)} characters")
    
    # Save dashboard
    dashboard_saved = dashboard.save_dashboard("test_dashboard.html")
    logger.info(f"Dashboard saved: {dashboard_saved}")
    
    return dashboard_data

async def test_performance(db: EnhancedMemoryDB):
    """Test system performance."""
    logger.info("Testing system performance...")
    
    test_generator = TestDataGenerator()
    large_data = test_generator.get_large_test_data(TestConfig.LARGE_TEST_DATA_COUNT)
    
    # Test batch memory creation
    start_time = time.time()
    created_memories = []
    for data in large_data:
        memory = await db.create_memory(data)
        created_memories.append(memory)
    end_time = time.time()
    
    logger.info(f"Created {len(created_memories)} memories in {end_time - start_time:.4f} seconds")
    logger.info(f"Average creation time: {(end_time - start_time) / len(created_memories):.4f} seconds per memory")
    
    # Test search performance
    start_time = time.time()
    for i in range(TestConfig.PERFORMANCE_TEST_ITERATIONS):
        memories = await db.search_memories("test")
    end_time = time.time()
    
    logger.info(f"Performed {TestConfig.PERFORMANCE_TEST_ITERATIONS} searches in {end_time - start_time:.4f} seconds")
    logger.info(f"Average search time: {(end_time - start_time) / TestConfig.PERFORMANCE_TEST_ITERATIONS:.4f} seconds per search")
    
    return created_memories

async def cleanup_test_data(db: EnhancedMemoryDB):
    """Clean up test data."""
    logger.info("Cleaning up test data...")
    
    # Get all test memories
    memories = await db.get_memories()
    
    # Delete test memories
    for memory in memories:
        if memory.title.startswith("Test Memory"):
            await db.delete_memory(memory.id)
            logger.info(f"Deleted memory {memory.id}")
    
    # Delete test contexts
    for context in TestConfig.TEST_CONTEXTS:
        await db.delete_context(context["id"])
        logger.info(f"Deleted context {context['id']}")
    
    logger.info("Test data cleaned up")

async def main():
    """Main test function."""
    logger.info("Starting test with new data...")
    
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
        
        # Test 1: Memory creation with compression
        created_memories = await test_memory_creation(db)
        
        # Test 2: Memory search with lazy loading
        await test_memory_search(db, use_lazy=True)
        await test_memory_search(db, use_lazy=False)
        
        # Test 3: Memory retrieval with lazy loading
        await test_memory_retrieval(db, use_lazy=True)
        await test_memory_retrieval(db, use_lazy=False)
        
        # Test 4: Memory monitoring
        await test_memory_monitoring()
        
        # Test 5: Dashboard generation
        await test_dashboard()
        
        # Test 6: Performance testing
        await test_performance(db)
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    
    finally:
        # Clean up
        await cleanup_test_data(db)
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())