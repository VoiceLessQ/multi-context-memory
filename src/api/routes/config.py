"""
API routes for configuration management in the MCP Multi-Context Memory System.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from ...database.refactored_memory_db import RefactoredMemoryDB
from ...schemas.config import SystemConfig, ChunkedStorageConfig, CompressionConfig, LazyLoadingConfig
from ...api.dependencies import get_enhanced_db, get_current_user
from ...utils.error_handling import handle_errors
from ...config.manager import ConfigManager

router = APIRouter()
config_manager = ConfigManager()

@router.get("/system", response_model=SystemConfig)
async def get_system_config(
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Get the current system configuration.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        System configuration
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get configuration
        config = config_manager.get_config()
        
        return config
        
    except Exception as e:
        handle_errors(e, "Failed to get system configuration")
        raise HTTPException(status_code=500, detail="Failed to get system configuration")

@router.put("/system", response_model=SystemConfig)
async def update_system_config(
    config: SystemConfig,
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Update the system configuration.
    
    Args:
        config: Updated system configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated system configuration
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Update configuration
        success = config_manager.save_config(config)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save system configuration")
        
        # Get updated configuration
        updated_config = config_manager.get_config()
        
        return updated_config
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update system configuration")
        raise HTTPException(status_code=500, detail="Failed to update system configuration")

@router.post("/system/reset")
async def reset_system_config(
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Reset the system configuration to default values.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If reset fails
    """
    try:
        # Reset configuration
        success = config_manager.reset_config()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset system configuration")
        
        return {"message": "System configuration reset to default values"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to reset system configuration")
        raise HTTPException(status_code=500, detail="Failed to reset system configuration")

@router.get("/system/validate")
async def validate_system_config(
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Validate the current system configuration.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Validation results
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Validate configuration
        validation_result = config_manager.validate_config()
        
        return validation_result
        
    except Exception as e:
        handle_errors(e, "Failed to validate system configuration")
        raise HTTPException(status_code=500, detail="Failed to validate system configuration")

@router.get("/system/export/{format}")
async def export_system_config(
    format: str = Path(..., pattern="^(json|yaml|yml)$"),
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Export the system configuration.
    
    Args:
        format: Export format (json, yaml, yml)
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Exported configuration
        
    Raises:
        HTTPException: If export fails
    """
    try:
        # Export configuration
        exported_config = config_manager.export_config(format=format)
        
        if not exported_config:
            raise HTTPException(status_code=500, detail="Failed to export system configuration")
        
        return {"config": exported_config, "format": format}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to export system configuration")
        raise HTTPException(status_code=500, detail="Failed to export system configuration")

@router.post("/system/import")
async def import_system_config(
    config_data: str,
    format: str = Query(..., pattern="^(json|yaml|yml)$"),
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Import a system configuration.
    
    Args:
        config_data: Configuration data to import
        format: Import format (json, yaml, yml)
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If import fails
    """
    try:
        # Import configuration
        success = config_manager.import_config(config_data, format=format)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to import system configuration")
        
        return {"message": "System configuration imported successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to import system configuration")
        raise HTTPException(status_code=500, detail="Failed to import system configuration")

# Chunked Storage Configuration Endpoints

@router.get("/storage/chunked", response_model=ChunkedStorageConfig)
async def get_chunked_storage_config(
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Get the chunked storage configuration.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Chunked storage configuration
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get configuration
        config = config_manager.get_chunked_storage_config()
        
        return ChunkedStorageConfig(**config)
        
    except Exception as e:
        handle_errors(e, "Failed to get chunked storage configuration")
        raise HTTPException(status_code=500, detail="Failed to get chunked storage configuration")

@router.put("/storage/chunked", response_model=ChunkedStorageConfig)
async def update_chunked_storage_config(
    config: ChunkedStorageConfig,
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Update the chunked storage configuration.
    
    Args:
        config: Updated chunked storage configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated chunked storage configuration
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Update configuration
        success = config_manager.update_chunked_storage_config(config.dict())
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update chunked storage configuration")
        
        # Get updated configuration
        updated_config = config_manager.get_chunked_storage_config()
        
        return ChunkedStorageConfig(**updated_config)
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update chunked storage configuration")
        raise HTTPException(status_code=500, detail="Failed to update chunked storage configuration")

# Compression Configuration Endpoints

@router.get("/compression", response_model=CompressionConfig)
async def get_compression_config(
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Get the compression configuration.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Compression configuration
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get configuration
        config = config_manager.get_compression_config()
        
        return CompressionConfig(**config)
        
    except Exception as e:
        handle_errors(e, "Failed to get compression configuration")
        raise HTTPException(status_code=500, detail="Failed to get compression configuration")

@router.put("/compression", response_model=CompressionConfig)
async def update_compression_config(
    config: CompressionConfig,
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Update the compression configuration.
    
    Args:
        config: Updated compression configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated compression configuration
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Update configuration
        success = config_manager.update_compression_config(config.dict())
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update compression configuration")
        
        # Get updated configuration
        updated_config = config_manager.get_compression_config()
        
        return CompressionConfig(**updated_config)
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update compression configuration")
        raise HTTPException(status_code=500, detail="Failed to update compression configuration")

# Lazy Loading Configuration Endpoints

@router.get("/lazy-loading", response_model=LazyLoadingConfig)
async def get_lazy_loading_config(
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Get the lazy loading configuration.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Lazy loading configuration
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get configuration
        config = config_manager.get_lazy_loading_config()
        
        return LazyLoadingConfig(**config)
        
    except Exception as e:
        handle_errors(e, "Failed to get lazy loading configuration")
        raise HTTPException(status_code=500, detail="Failed to get lazy loading configuration")

@router.put("/lazy-loading", response_model=LazyLoadingConfig)
async def update_lazy_loading_config(
    config: LazyLoadingConfig,
    db: RefactoredMemoryDB = Depends(get_enhanced_db),
    current_user = Depends(get_current_user)
):
    """
    Update the lazy loading configuration.
    
    Args:
        config: Updated lazy loading configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated lazy loading configuration
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Update configuration
        success = config_manager.update_lazy_loading_config(config.dict())
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update lazy loading configuration")
        
        # Get updated configuration
        updated_config = config_manager.get_lazy_loading_config()
        
        return LazyLoadingConfig(**updated_config)
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update lazy loading configuration")
        raise HTTPException(status_code=500, detail="Failed to update lazy loading configuration")