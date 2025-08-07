"""
Error handling utilities for the enhanced MCP Multi-Context Memory System.
"""
import logging
import traceback
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys

logger = logging.getLogger(__name__)

class MCPMemoryException(Exception):
    """
    Base exception for MCP Memory System.
    """
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(MCPMemoryException):
    """
    Authentication related errors.
    """
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")

class AuthorizationError(MCPMemoryException):
    """
    Authorization related errors.
    """
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(message, "AUTHZ_ERROR")

class ValidationError(MCPMemoryException):
    """
    Validation related errors.
    """
    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details)

class NotFoundError(MCPMemoryException):
    """
    Resource not found errors.
    """
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id is not None:
            message += f": {resource_id}"
        super().__init__(message, "NOT_FOUND_ERROR")

class ConflictError(MCPMemoryException):
    """
    Conflict errors (e.g., duplicate resource).
    """
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT_ERROR")

class DatabaseError(MCPMemoryException):
    """
    Database related errors.
    """
    def __init__(self, message: str, original_error: Exception = None):
        details = {"original_error": str(original_error)} if original_error else {}
        super().__init__(message, "DATABASE_ERROR", details)

class ConfigurationError(MCPMemoryException):
    """
    Configuration related errors.
    """
    def __init__(self, message: str):
        super().__init__(message, "CONFIG_ERROR")

class MigrationError(MCPMemoryException):
    """
    Migration related errors.
    """
    def __init__(self, message: str, step: str = None):
        details = {"step": step} if step else {}
        super().__init__(message, "MIGRATION_ERROR", details)

class APIError(MCPMemoryException):
    """
    API related errors.
    """
    def __init__(self, message: str, status_code: int = 500):
        self.status_code = status_code
        super().__init__(message, "API_ERROR")

def handle_errors(error: Exception, context: str = None) -> Dict[str, Any]:
    """
    Handle errors consistently across the application.
    
    Args:
        error: The exception that occurred
        context: Context where the error occurred
        
    Returns:
        Error details dictionary
    """
    error_details = {
        "timestamp": None,
        "context": context,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": None,
        "error_code": None,
        "details": {}
    }
    
    # Set timestamp
    from datetime import datetime
    error_details["timestamp"] = datetime.now().isoformat()
    
    # Get context information
    if context:
        error_details["context"] = context
    
    # Get error type and message
    error_details["error_type"] = type(error).__name__
    error_details["error_message"] = str(error)
    
    # Get traceback
    error_details["traceback"] = traceback.format_exc()
    
    # Get error code and details for custom exceptions
    if isinstance(error, MCPMemoryException):
        error_details["error_code"] = error.error_code
        error_details["details"] = error.details
    
    # Log the error
    log_error(error, context)
    
    return error_details

def log_error(error: Exception, context: str = None) -> None:
    """
    Log errors with appropriate severity.
    
    Args:
        error: The exception that occurred
        context: Context where the error occurred
    """
    log_message = f"Error in {context}" if context else "Error occurred"
    
    if isinstance(error, MCPMemoryException):
        if error.error_code in ["AUTH_ERROR", "AUTHZ_ERROR", "VALIDATION_ERROR"]:
            logger.warning(f"{log_message}: {error}")
        elif error.error_code in ["NOT_FOUND_ERROR", "CONFLICT_ERROR"]:
            logger.info(f"{log_message}: {error}")
        else:
            logger.error(f"{log_message}: {error}")
    else:
        logger.error(f"{log_message}: {error}", exc_info=True)

def create_error_response(
    error: Exception,
    context: str = None,
    include_traceback: bool = False
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error: The exception that occurred
        context: Context where the error occurred
        include_traceback: Whether to include traceback in response
        
    Returns:
        JSONResponse with error details
    """
    error_details = handle_errors(error, context)
    
    # Determine status code
    status_code = 500
    if isinstance(error, HTTPException):
        status_code = error.status_code
    elif isinstance(error, StarletteHTTPException):
        status_code = error.status_code
    elif isinstance(error, MCPMemoryException):
        if error.error_code == "AUTH_ERROR":
            status_code = 401
        elif error.error_code == "AUTHZ_ERROR":
            status_code = 403
        elif error.error_code == "NOT_FOUND_ERROR":
            status_code = 404
        elif error.error_code == "VALIDATION_ERROR":
            status_code = 422
        elif error.error_code == "CONFLICT_ERROR":
            status_code = 409
    
    # Prepare response data
    response_data = {
        "error": {
            "code": error_details["error_code"] or "INTERNAL_ERROR",
            "message": error_details["error_message"],
            "details": error_details["details"]
        }
    }
    
    # Add timestamp
    response_data["error"]["timestamp"] = error_details["timestamp"]
    
    # Add context if provided
    if error_details["context"]:
        response_data["error"]["context"] = error_details["context"]
    
    # Add traceback if requested and in development
    if include_traceback and error_details["traceback"]:
        response_data["error"]["traceback"] = error_details["traceback"]
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

def setup_exception_handlers(app) -> None:
    """
    Setup exception handlers for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    @app.exception_handler(MCPMemoryException)
    async def mcp_memory_exception_handler(request: Request, exc: MCPMemoryException):
        return create_error_response(exc, f"API endpoint: {request.url.path}")
    
    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(request: Request, exc: AuthenticationError):
        return create_error_response(exc, f"Authentication: {request.url.path}")
    
    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(request: Request, exc: AuthorizationError):
        return create_error_response(exc, f"Authorization: {request.url.path}")
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return create_error_response(exc, f"Validation: {request.url.path}")
    
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return create_error_response(exc, f"Resource not found: {request.url.path}")
    
    @app.exception_handler(ConflictError)
    async def conflict_exception_handler(request: Request, exc: ConflictError):
        return create_error_response(exc, f"Conflict: {request.url.path}")
    
    @app.exception_handler(DatabaseError)
    async def database_exception_handler(request: Request, exc: DatabaseError):
        return create_error_response(exc, f"Database operation: {request.url.path}")
    
    @app.exception_handler(ConfigurationError)
    async def configuration_exception_handler(request: Request, exc: ConfigurationError):
        return create_error_response(exc, f"Configuration: {request.url.path}")
    
    @app.exception_handler(MigrationError)
    async def migration_exception_handler(request: Request, exc: MigrationError):
        return create_error_response(exc, f"Migration: {request.url.path}")
    
    @app.exception_handler(APIError)
    async def api_exception_handler(request: Request, exc: APIError):
        return create_error_response(exc, f"API: {request.url.path}")
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return create_error_response(
            ValidationError(
                message="Validation failed",
                details={"errors": exc.errors()}
            ),
            f"Validation: {request.url.path}"
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return create_error_response(exc, f"HTTP: {request.url.path}")
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return create_error_response(
            exc,
            f"General error in {request.url.path}",
            include_traceback=True
        )

def handle_database_error(error: Exception, operation: str) -> DatabaseError:
    """
    Handle database errors consistently.
    
    Args:
        error: The database error that occurred
        operation: The database operation being performed
        
    Returns:
        DatabaseError with appropriate message
    """
    error_message = f"Database {operation} failed"
    
    # Add specific error details based on error type
    if "unique constraint" in str(error).lower():
        error_message += ": Duplicate entry"
    elif "foreign key" in str(error).lower():
        error_message += ": Foreign key constraint violation"
    elif "not null constraint" in str(error).lower():
        error_message += ": Not null constraint violation"
    elif "syntax error" in str(error).lower():
        error_message += ": SQL syntax error"
    
    return DatabaseError(error_message, original_error=error)

def handle_validation_error(field: str, value: Any, message: str = None) -> ValidationError:
    """
    Handle validation errors consistently.
    
    Args:
        field: The field that failed validation
        value: The invalid value
        message: Custom error message
        
    Returns:
        ValidationError with appropriate message
    """
    if message:
        error_message = message
    else:
        error_message = f"Invalid value for field '{field}': {value}"
    
    return ValidationError(error_message, field=field)

def handle_not_found(resource: str, resource_id: Any = None) -> NotFoundError:
    """
    Handle not found errors consistently.
    
    Args:
        resource: The type of resource that was not found
        resource_id: The ID of the resource that was not found
        
    Returns:
        NotFoundError with appropriate message
    """
    return NotFoundError(resource, resource_id)

def handle_conflict(message: str) -> ConflictError:
    """
    Handle conflict errors consistently.
    
    Args:
        message: Conflict error message
        
    Returns:
        ConflictError with the provided message
    """
    return ConflictError(message)

def handle_auth_error(message: str = "Authentication failed") -> AuthenticationError:
    """
    Handle authentication errors consistently.
    
    Args:
        message: Authentication error message
        
    Returns:
        AuthenticationError with the provided message
    """
    return AuthenticationError(message)

def handle_authz_error(message: str = "Authorization failed") -> AuthorizationError:
    """
    Handle authorization errors consistently.
    
    Args:
        message: Authorization error message
        
    Returns:
        AuthorizationError with the provided message
    """
    return AuthorizationError(message)

def handle_config_error(message: str) -> ConfigurationError:
    """
    Handle configuration errors consistently.
    
    Args:
        message: Configuration error message
        
    Returns:
        ConfigurationError with the provided message
    """
    return ConfigurationError(message)

def handle_migration_error(message: str, step: str = None) -> MigrationError:
    """
    Handle migration errors consistently.
    
    Args:
        message: Migration error message
        step: The migration step where the error occurred
        
    Returns:
        MigrationError with the provided message and step
    """
    return MigrationError(message, step=step)

def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is retryable, False otherwise
    """
    retryable_errors = [
        "ConnectionError",
        "TimeoutError",
        "OperationalError",
        "DatabaseError",
        "RetryError"
    ]
    
    return type(error).__name__ in retryable_errors

def get_error_code(error: Exception) -> str:
    """
    Get the error code for an exception.
    
    Args:
        error: The exception to get the code for
        
    Returns:
        Error code string
    """
    if isinstance(error, MCPMemoryException):
        return error.error_code
    
    # Default error codes for common exceptions
    error_codes = {
        "ValueError": "VALUE_ERROR",
        "TypeError": "TYPE_ERROR",
        "KeyError": "KEY_ERROR",
        "IndexError": "INDEX_ERROR",
        "AttributeError": "ATTRIBUTE_ERROR",
        "ImportError": "IMPORT_ERROR",
        "ModuleNotFoundError": "MODULE_NOT_FOUND_ERROR",
        "FileNotFoundError": "FILE_NOT_FOUND_ERROR",
        "PermissionError": "PERMISSION_ERROR",
        "TimeoutError": "TIMEOUT_ERROR",
        "ConnectionError": "CONNECTION_ERROR",
        "HTTPException": "HTTP_ERROR",
        "RequestValidationError": "VALIDATION_ERROR",
        "ValidationError": "VALIDATION_ERROR"
    }
    
    return error_codes.get(type(error).__name__, "INTERNAL_ERROR")