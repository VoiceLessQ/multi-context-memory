"""
Migration script to add access_count and last_accessed columns to the memories table.
"""
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

def run_migration(db_path: str = "data/sqlite/memory.db"):
    # Convert to absolute path
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
        
    print(f"Using database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    print(f"Database size: {os.path.getsize(db_path)} bytes")
    
    # Check if we should use the other database file
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        alt_path = os.path.join(os.path.dirname(db_path), "memory.db" if os.path.basename(db_path) == "memories.db" else "memories.db")
        if os.path.exists(alt_path) and os.path.getsize(alt_path) > 0:
            print(f"Switching to alternative database: {alt_path}")
            db_path = alt_path
    """
    Run the migration to add access_count and last_accessed columns.
    
    Args:
        db_path: Path to the SQLite database file
    """
    try:
        # Convert to absolute path
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
            
        print(f"Using database path: {db_path}")
        print(f"Database exists: {os.path.exists(db_path)}")
        print(f"Database size: {os.path.getsize(db_path)} bytes")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'")
        table_exists = cursor.fetchone()
        print(f"Memories table exists: {bool(table_exists)}")
        
        if not table_exists:
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Available tables: {tables}")
            return
            
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(memories)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        if "access_count" not in columns:
            # Add access_count column
            cursor.execute("ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0")
            logger.info("Added access_count column to memories table")
        else:
            logger.info("access_count column already exists")
        
        if "last_accessed" not in columns:
            # Add last_accessed column
            cursor.execute("ALTER TABLE memories ADD COLUMN last_accessed DATETIME")
            logger.info("Added last_accessed column to memories table")
        else:
            logger.info("last_accessed column already exists")
        
        # Commit changes
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Get the database path from environment or use default
    import os
    db_path = os.getenv("DATABASE_URL", "data/sqlite/memories.db")
    
    # Run the migration
    run_migration(db_path)