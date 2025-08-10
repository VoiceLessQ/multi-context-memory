"""
Error handling utilities for the MCP Multi-Context Memory System.
"""
import logging
import traceback
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

def log_error(error: Exception, context: str = "Operation") -> None:
    """
    Log an error with traceback.
    
    Args:
        error: The exception that occurred
        context: Context of the error (e.g., "User registration")
    """
    logger.error(f"Error in {context}: {type(error).__name__} - {str(error)}")
    logger.error(traceback.format_exc())

def handle_errors(error: Exception, context: str = "Operation") -> Dict[str, Any]:
    """
    Log an error and return a standardized error dictionary.
    
    Args:
        error: The exception that occurred
        context: Context of the error (e.g., "User registration")
        
    Returns:
        Dictionary with error details
    """
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "traceback": traceback.format_exc()
    }
    
    logger.error(f"Error in {context}: {error_details}")
    return error_details

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom handler for request validation errors.
    
    Args:
        request: The FastAPI request object
        exc: The RequestValidationError instance
        
    Returns:
        JSONResponse with formatted error details
    """
    error_details = handle_errors(exc, "Request validation")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors(), "internal": error_details},
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom handler for HTTP exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The HTTPException instance
        
    Returns:
        JSONResponse with formatted error details
    """
    error_details = handle_errors(exc, f"HTTP Error {exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "internal": error_details},
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Custom handler for general exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The generic Exception instance
        
    Returns:
        JSONResponse with formatted error details
    """
    error_details = handle_errors(exc, "Internal server error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "internal": error_details},
    )

def add_exception_handlers(app):
    """
    Add custom exception handlers to a FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler) # StarletteHTTPException is the base for FastAPI's HTTPException
    app.add_exception_handler(Exception, general_exception_handler)