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
Script to run the migration process for existing data.
"""
import asyncio
import logging
import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.migration.migration_manager import MigrationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/migration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate existing data to new format")
    parser.add_argument("--db-url", default="sqlite:///./data/memory.db", help="Database URL")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for migration")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no actual migration)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting migration process...")
    
    try:
        # Initialize migration manager
        migration_manager = MigrationManager(
            db_url=args.db_url,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
        
        # Run migration
        report = await migration_manager.run_migration()
        
        # Print report
        print("\nMigration Report:")
        print(f"Total memories: {report['total_memories']}")
        print(f"Migrated memories: {report['migrated_memories']}")
        print(f"Failed memories: {report['failed_memories']}")
        print(f"Success rate: {report['success_rate']:.2f}%")
        print(f"Compression ratio: {report['compression_ratio']:.2f}%")
        print(f"Lazy loading ratio: {report['lazy_loading_ratio']:.2f}%")
        print(f"Average time per memory: {report['average_time_per_memory']:.4f} seconds")
        print(f"Total time: {report['elapsed_time']:.2f} seconds")
        
        logger.info("Migration process completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)