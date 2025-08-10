"""
Session management for the enhanced MCP Multi-Context Memory System.
Provides SQLAlchemy session management and dependency injection.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from .models import Base
from ..config.settings import get_settings

# Get settings
settings = get_settings()

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
    Base.metadata.create_all(bind=engine)

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