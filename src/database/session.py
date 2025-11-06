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
Session management for the enhanced MCP Multi-Context Memory System.
Provides SQLAlchemy session management and dependency injection.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# from .models import Base
# Models import removed due to relative import issues
# from ..config.settings import get_settings
# Settings import removed due to relative import issues

# Get settings
# settings = get_settings()
settings = type('Settings', (), {
    'database_url': 'sqlite:///./memory.db',
    'debug': False,
    'max_connections': 10,
    'query_timeout': 30
})()

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.max_connections,
    pool_timeout=settings.query_timeout
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create database tables."""
    # Base.metadata.create_all(bind=engine) - Disabled due to import issues
    pass

def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Session: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Get database session with context manager.
    
    Yields:
        Session: SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database with tables."""
    create_tables()

# Global session counter for monitoring
_session_count = 0

def get_session_count() -> int:
    """Get current session count for monitoring."""
    global _session_count
    return _session_count

def increment_session_count():
    """Increment session count."""
    global _session_count
    _session_count += 1

def decrement_session_count():
    """Decrement session count."""
    global _session_count
    _session_count -= 1