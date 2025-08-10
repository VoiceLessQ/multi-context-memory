"""
Test runner for testing the enhanced memory system with new data.
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_new_data import main as run_tests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/test_new_data.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main test runner function."""
    logger.info("Starting test runner for new data...")
    
    try:
        # Run tests
        await run_tests()
        logger.info("Test runner completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)