"""
Test configuration for the enhanced memory system.
"""
import os
from pathlib import Path

class TestConfig:
    """Test configuration settings."""
    
    # Database settings
    DATABASE_URL = "sqlite:///./data/test_memory.db"
    
    # Test data directory
    TEST_DATA_DIR = Path("./data/test_data/")
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Backup directory for tests
    TEST_BACKUP_DIR = Path("./data/test_backups/")
    TEST_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Log directory for tests
    TEST_LOG_DIR = Path("./logs/test/")
    TEST_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Test user settings
    TEST_USERS = [
        {"id": "test_user_1", "name": "Test User 1"},
        {"id": "test_user_2", "name": "Test User 2"},
        {"id": "test_user_3", "name": "Test User 3"}
    ]
    
    # Test context settings
    TEST_CONTEXTS = [
        {"id": 1, "name": "Test Context 1", "description": "First test context"},
        {"id": 2, "name": "Test Context 2", "description": "Second test context"},
        {"id": 3, "name": "Test Context 3", "description": "Third test context"},
        {"id": 4, "name": "Test Context 4", "description": "Fourth test context"},
        {"id": 5, "name": "Test Context 5", "description": "Fifth test context"}
    ]
    
    # Compression settings for tests
    COMPRESSION_ENABLED = True
    COMPRESSION_THRESHOLD = 1024  # 1KB
    COMPRESSION_ALGORITHM = "zlib"  # zlib, gzip, bz2, lzma
    
    # Lazy loading settings for tests
    LAZY_LOADING_ENABLED = True
    LAZY_LOADING_THRESHOLD = 2048  # 2KB
    
    # Performance monitoring settings for tests
    PERFORMANCE_MONITORING_ENABLED = True
    PERFORMANCE_THRESHOLD = 100  # 100ms
    
    # Test settings
    TEST_CLEANUP = True  # Clean up test data after tests
    TEST_VERBOSE = True  # Enable verbose logging
    
    # Large test data settings
    LARGE_TEST_DATA_COUNT = 100  # Number of large test memories to create
    LARGE_TEST_DATA_SIZE = 1024 * 1024  # 1MB per memory (average)
    
    # Performance test settings
    PERFORMANCE_TEST_ITERATIONS = 10  # Number of iterations for performance tests
    
    @classmethod
    def get_test_db_path(cls) -> str:
        """Get test database path."""
        return cls.DATABASE_URL.replace("sqlite:///", "")
    
    @classmethod
    def ensure_test_directories(cls):
        """Ensure test directories exist."""
        cls.TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEST_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEST_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def cleanup_test_data(cls):
        """Clean up test data."""
        if cls.TEST_CLEANUP:
            # Remove test database
            test_db_path = cls.get_test_db_path()
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
                print(f"Removed test database: {test_db_path}")
            
            # Remove test data directory
            if os.path.exists(cls.TEST_DATA_DIR):
                import shutil
                shutil.rmtree(cls.TEST_DATA_DIR)
                print(f"Removed test data directory: {cls.TEST_DATA_DIR}")
            
            # Remove test backup directory
            if os.path.exists(cls.TEST_BACKUP_DIR):
                import shutil
                shutil.rmtree(cls.TEST_BACKUP_DIR)
                print(f"Removed test backup directory: {cls.TEST_BACKUP_DIR}")
            
            # Remove test log directory
            if os.path.exists(cls.TEST_LOG_DIR):
                import shutil
                shutil.rmtree(cls.TEST_LOG_DIR)
                print(f"Removed test log directory: {cls.TEST_LOG_DIR}")
    
    @classmethod
    def get_test_user_id(cls, index: int) -> str:
        """Get test user ID by index."""
        if 0 <= index < len(cls.TEST_USERS):
            return cls.TEST_USERS[index]["id"]
        return cls.TEST_USERS[0]["id"]
    
    @classmethod
    def get_test_context_id(cls, index: int) -> int:
        """Get test context ID by index."""
        if 0 <= index < len(cls.TEST_CONTEXTS):
            return cls.TEST_CONTEXTS[index]["id"]
        return cls.TEST_CONTEXTS[0]["id"]