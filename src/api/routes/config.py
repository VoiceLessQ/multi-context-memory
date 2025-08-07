"""
API routes for configuration operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from ...database.models import User, Config
from ...database.enhanced_memory_db import EnhancedMemoryDB
from ...schemas.config import (
    ConfigBase, ConfigCreate, ConfigUpdate, ConfigResponse, ConfigStats,
    ConfigSearch, ConfigSearchResponse, ConfigBackup, ConfigBackupResponse,
    ConfigRestore, ConfigRestoreResponse, ConfigHealth, ConfigAuditLog,
    ConfigAuditLogResponse, ConfigAuditLogFilter
)
from ...schemas.auth import TokenData
from ...utils.auth import get_current_user, get_optional_user
from ...utils.error_handling import handle_errors
from ...utils.config import (
    create_config, update_config, delete_config, get_config_stats,
    search_configs, backup_configs, restore_configs, get_config_health,
    get_config_audit_logs
)

router = APIRouter()

# Configuration Management
@router.post("/", response_model=ConfigResponse, status_code=201)
async def create_admin_config(
    config_data: ConfigCreate,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new configuration (admin only).
    
    Args:
        config_data: Configuration data to create
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created configuration
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Create configuration
        config = await create_config(
            db=db,
            config_data=config_data,
            user_id=current_user.id
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to create configuration")
        raise HTTPException(status_code=500, detail="Failed to create configuration")

@router.get("/", response_model=List[ConfigResponse])
async def get_admin_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    is_sensitive: Optional[bool] = Query(None),
    is_system: Optional[bool] = Query(None),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get configurations with optional filtering (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        category: Filter by category
        is_sensitive: Filter by sensitive status
        is_system: Filter by system status
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        List of configurations
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get configurations
        configs = await db.get_configs(
            skip=skip,
            limit=limit,
            category=category,
            is_sensitive=is_sensitive,
            is_system=is_system
        )
        
        return configs
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve configurations")
        raise HTTPException(status_code=500, detail="Failed to retrieve configurations")

@router.get("/{config_id}", response_model=ConfigResponse)
async def get_admin_config(
    config_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific configuration by ID (admin only).
    
    Args:
        config_id: Configuration ID to retrieve
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Configuration details
        
    Raises:
        HTTPException: If configuration not found or retrieval fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get configuration
        config = await db.get_config(config_id=config_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve configuration")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")

@router.put("/{config_id}", response_model=ConfigResponse)
async def update_admin_config(
    config_id: int = Path(..., gt=0),
    config_data: ConfigUpdate = Body(...),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing configuration (admin only).
    
    Args:
        config_id: Configuration ID to update
        config_data: Updated configuration data
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated configuration
        
    Raises:
        HTTPException: If configuration not found or update fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Update configuration
        config = await update_config(
            db=db,
            config_id=config_id,
            config_data=config_data,
            user_id=current_user.id
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update configuration")
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@router.delete("/{config_id}", status_code=204)
async def delete_admin_config(
    config_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a configuration (admin only).
    
    Args:
        config_id: Configuration ID to delete
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Raises:
        HTTPException: If configuration not found or deletion fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Delete configuration
        await delete_config(
            db=db,
            config_id=config_id,
            user_id=current_user.id
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to delete configuration")
        raise HTTPException(status_code=500, detail="Failed to delete configuration")

# Configuration Statistics
@router.get("/stats/summary", response_model=ConfigStats)
async def get_admin_config_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get configuration statistics (admin only).
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Configuration statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get configuration statistics
        stats = await get_config_stats(db=db)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve configuration statistics")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration statistics")

# Configuration Search
@router.post("/search", response_model=List[ConfigSearchResponse])
async def search_admin_configs(
    search_data: ConfigSearch,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search configurations using various criteria (admin only).
    
    Args:
        search_data: Search parameters
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        List of matching configurations
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Search configurations
        configs = await search_configs(
            db=db,
            search_data=search_data
        )
        
        return configs
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to search configurations")
        raise HTTPException(status_code=500, detail="Failed to search configurations")

# Configuration Backup
@router.post("/backup", response_model=ConfigBackupResponse)
async def create_admin_config_backup(
    backup_data: ConfigBackup,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a configuration backup (admin only).
    
    Args:
        backup_data: Backup request data
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Backup response
        
    Raises:
        HTTPException: If backup creation fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Create configuration backup
        backup = await backup_configs(
            db=db,
            backup_data=backup_data,
            user_id=current_user.id
        )
        
        return backup
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to create configuration backup")
        raise HTTPException(status_code=500, detail="Failed to create configuration backup")

# Configuration Restore
@router.post("/restore", response_model=ConfigRestoreResponse)
async def create_admin_config_restore(
    restore_data: ConfigRestore,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore configurations from backup (admin only).
    
    Args:
        restore_data: Restore request data
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Restore response
        
    Raises:
        HTTPException: If restore fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Restore configurations
        restore = await restore_configs(
            db=db,
            restore_data=restore_data,
            user_id=current_user.id
        )
        
        return restore
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to restore configurations")
        raise HTTPException(status_code=500, detail="Failed to restore configurations")

# Configuration Health
@router.get("/health", response_model=ConfigHealth)
async def get_admin_config_health(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get configuration health status (admin only).
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Configuration health status
        
    Raises:
        HTTPException: If health check fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get configuration health
        health = await get_config_health(db=db)
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve configuration health")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration health")

# Configuration Audit Logs
@router.get("/audit-logs", response_model=ConfigAuditLogResponse)
async def get_admin_config_audit_logs(
    filter_data: ConfigAuditLogFilter = Depends(),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get configuration audit logs with optional filtering (admin only).
    
    Args:
        filter_data: Audit log filter parameters
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        List of configuration audit logs
        
    Raises:
        HTTPException: If log retrieval fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get configuration audit logs
        logs = await get_config_audit_logs(
            db=db,
            filter_data=filter_data
        )
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve configuration audit logs")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration audit logs")

# Configuration Import/Export
@router.get("/export/{format}")
async def export_admin_configs(
    format: str = Path(..., regex="^(json|yaml|csv|xml)$"),
    category: Optional[str] = Query(None),
    include_sensitive: bool = Query(False),
    include_system: bool = Query(False),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export configurations in various formats (admin only).
    
    Args:
        format: Export format (json, yaml, csv, xml)
        category: Filter by category
        include_sensitive: Whether to include sensitive configurations
        include_system: Whether to include system configurations
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Exported configurations
        
    Raises:
        HTTPException: If export fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get configurations
        configs = await db.get_configs(
            category=category,
            is_sensitive=include_sensitive,
            is_system=include_system
        )
        
        # Export based on format
        if format == "json":
            return {"configs": [config.dict() for config in configs]}
        elif format == "yaml":
            # TODO: Implement YAML export
            pass
        elif format == "csv":
            # TODO: Implement CSV export
            pass
        elif format == "xml":
            # TODO: Implement XML export
            pass
        
        raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to export configurations")
        raise HTTPException(status_code=500, detail="Failed to export configurations")

@router.post("/import")
async def import_admin_configs(
    configs_data: List[Dict[str, Any]],
    merge_strategy: str = Body(..., regex="^(overwrite|skip|merge)$"),
    validate_only: bool = Body(False),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import configurations from external data (admin only).
    
    Args:
        configs_data: List of configuration data to import
        merge_strategy: How to handle conflicts
        validate_only: Whether to only validate without importing
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Import results
        
    Raises:
        HTTPException: If import fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # TODO: Implement actual import logic
        
        return {
            "message": "Import not implemented yet",
            "merge_strategy": merge_strategy,
            "validate_only": validate_only,
            "configs_count": len(configs_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to import configurations")
        raise HTTPException(status_code=500, detail="Failed to import configurations")

# Configuration Validation
@router.post("/validate")
async def validate_admin_configs(
    configs_data: List[Dict[str, Any]],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate configuration data (admin only).
    
    Args:
        configs_data: List of configuration data to validate
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Validation results
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # TODO: Implement actual validation logic
        
        return {
            "message": "Validation not implemented yet",
            "configs_count": len(configs_data),
            "valid": True,
            "errors": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to validate configurations")
        raise HTTPException(status_code=500, detail="Failed to validate configurations")

# Configuration Templates
@router.get("/templates")
async def get_admin_config_templates(
    category: Optional[str] = Query(None),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get configuration templates (admin only).
    
    Args:
        category: Filter by category
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        List of configuration templates
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # TODO: Implement actual template retrieval logic
        
        return {
            "message": "Templates not implemented yet",
            "category": category,
            "templates": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve configuration templates")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration templates")