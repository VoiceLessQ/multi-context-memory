"""
Logging configuration for the enhanced MCP Multi-Context Memory System.
Provides centralized logging setup with file and console handlers.
"""
import logging
import logging.handlers
import os
from typing import Optional, Dict, Any
from pathlib import Path

from .settings import get_settings

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Log message format
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    log_format = log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set up specific loggers
    setup_loggers()

def setup_loggers() -> None:
    """Setup specific loggers for different modules."""
    settings = get_settings()
    
    # Database logger
    db_logger = logging.getLogger("database")
    db_logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)
    
    # API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)
    
    # MCP logger
    mcp_logger = logging.getLogger("mcp")
    mcp_logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)
    
    # Extension logger
    extension_logger = logging.getLogger("extension")
    extension_logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)
    
    # Migration logger
    migration_logger = logging.getLogger("migration")
    migration_logger.setLevel(logging.INFO if not settings.debug else logging.DEBUG)
    
    # Security logger
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.WARNING)
    
    # Performance logger
    performance_logger = logging.getLogger("performance")
    performance_logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)

def log_performance(logger: logging.Logger, operation: str, duration: float, **kwargs) -> None:
    """
    Log performance metrics.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration: Duration in seconds
        **kwargs: Additional metrics
    """
    metrics = {
        "operation": operation,
        "duration": duration,
        **kwargs
    }
    logger.info(f"Performance: {metrics}")

def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log error with context.
    
    Args:
        logger: Logger instance
        error: Exception instance
        context: Additional context information
    """
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }
    logger.error(f"Error occurred: {error_info}")

def log_security(logger: logging.Logger, event: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log security events.
    
    Args:
        logger: Logger instance
        event: Security event type
        details: Additional event details
    """
    security_info = {
        "event": event,
        "details": details or {},
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
        ))
    }
    logger.warning(f"Security Event: {security_info}")

def log_audit(logger: logging.Logger, action: str, resource_type: str, 
             resource_id: int, user_id: Optional[int] = None, 
             details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log audit events.
    
    Args:
        logger: Logger instance
        action: Action performed
        resource_type: Type of resource
        resource_id: ID of resource
        user_id: User ID (if applicable)
        details: Additional audit details
    """
    audit_info = {
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "user_id": user_id,
        "details": details or {},
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
        ))
    }
    logger.info(f"Audit: {audit_info}")

# Initialize logging when module is imported
setup_logging()