"""
API routes for admin operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from ...database.models import User, Context, Memory, Relation
from ...database.enhanced_memory_db import EnhancedMemoryDB
from ...schemas.admin import (
    AdminUserBase, AdminUserCreate, AdminUserUpdate, AdminUserResponse,
    SystemStats, SystemLog, SystemLogResponse, SystemLogFilter,
    BackupRequest, BackupResponse, RestoreRequest, RestoreResponse,
    SystemHealth, SystemConfig
)
from ...schemas.auth import TokenData
from ...api.dependencies import get_enhanced_db
from ...utils.auth import get_current_user, get_optional_user
from ...utils.error_handling import handle_errors
from ...utils.admin import (
    create_admin_user, update_admin_user, delete_admin_user,
    get_system_stats, get_system_logs, backup_system, restore_system,
    get_system_health, update_system_config
)

router = APIRouter()

# User Management
@router.post("/users", response_model=AdminUserResponse, status_code=201)
async def create_admin_user_route(
    user_data: AdminUserCreate,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user (admin only).
    
    Args:
        user_data: User data to create
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Created user
        
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
        
        # Create user
        user = await create_admin_user(
            db=db,
            user_data=user_data
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to create user")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("/users", response_model=List[AdminUserResponse])
async def get_admin_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None, pattern="^(user|privileged|admin)$"),
    is_active: Optional[bool] = Query(None),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get users with optional filtering (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        role: Filter by role
        is_active: Filter by active status
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        List of users
        
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
        
        # Get users
        users = await db.get_users(
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active
        )
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve users")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")

@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_admin_user(
    user_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific user by ID (admin only).
    
    Args:
        user_id: User ID to retrieve
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        User details
        
    Raises:
        HTTPException: If user not found or retrieval fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get user
        user = await db.get_user_by_id(user_id=user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve user")
        raise HTTPException(status_code=500, detail="Failed to retrieve user")

@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user_route(
    user_id: int = Path(..., gt=0),
    user_data: AdminUserUpdate = Body(...),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing user (admin only).
    
    Args:
        user_id: User ID to update
        user_data: Updated user data
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or update fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Update user
        user = await update_admin_user(
            db=db,
            user_id=user_id,
            user_data=user_data
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update user")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/users/{user_id}", status_code=204)
async def delete_admin_user_route(
    user_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user (admin only).
    
    Args:
        user_id: User ID to delete
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Raises:
        HTTPException: If user not found or deletion fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Delete user
        await delete_admin_user(
            db=db,
            user_id=user_id
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to delete user")
        raise HTTPException(status_code=500, detail="Failed to delete user")

# System Management
@router.get("/stats/summary", response_model=SystemStats)
async def get_admin_system_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get system statistics (admin only).
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        System statistics
        
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
        
        # Get system statistics
        stats = await get_system_stats(db=db)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve system statistics")
        raise HTTPException(status_code=500, detail="Failed to retrieve system statistics")

@router.get("/logs", response_model=List[SystemLogResponse])
async def get_admin_system_logs(
    filter_data: SystemLogFilter = Depends(),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get system logs with optional filtering (admin only).
    
    Args:
        filter_data: Log filter parameters
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        List of system logs
        
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
        
        # Get system logs
        logs = await get_system_logs(
            db=db,
            filter_data=filter_data
        )
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve system logs")
        raise HTTPException(status_code=500, detail="Failed to retrieve system logs")

@router.post("/backup", response_model=BackupResponse)
async def create_admin_backup(
    backup_data: BackupRequest,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a system backup (admin only).
    
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
        
        # Create backup
        backup = await backup_system(
            db=db,
            backup_data=backup_data
        )
        
        return backup
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to create backup")
        raise HTTPException(status_code=500, detail="Failed to create backup")

@router.post("/restore", response_model=RestoreResponse)
async def create_admin_restore(
    restore_data: RestoreRequest,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore system from backup (admin only).
    
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
        
        # Restore system
        restore = await restore_system(
            db=db,
            restore_data=restore_data
        )
        
        return restore
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to restore system")
        raise HTTPException(status_code=500, detail="Failed to restore system")

@router.get("/health", response_model=SystemHealth)
async def get_admin_system_health(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get system health status (admin only).
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        System health status
        
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
        
        # Get system health
        health = await get_system_health(db=db)
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve system health")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")

@router.put("/config", response_model=SystemConfig)
async def update_admin_system_config(
    config_data: SystemConfig,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update system configuration (admin only).
    
    Args:
        config_data: Updated system configuration
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Updated system configuration
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Update system configuration
        config = await update_system_config(
            db=db,
            config_data=config_data
        )
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update system configuration")
        raise HTTPException(status_code=500, detail="Failed to update system configuration")

# Data Management
@router.get("/data/export/{format}")
async def export_admin_data(
    format: str = Path(..., pattern="^(json|csv|xml|pdf)$"),
    data_type: str = Query(..., pattern="^(all|users|memories|contexts|relations)$"),
    include_sensitive: bool = Query(False),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export system data in various formats (admin only).
    
    Args:
        format: Export format (json, csv, xml, pdf)
        data_type: Type of data to export
        include_sensitive: Whether to include sensitive data
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Exported data
        
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
        
        # Export data based on type
        if data_type == "all":
            # Export all data
            pass
        elif data_type == "users":
            # Export users data
            pass
        elif data_type == "memories":
            # Export memories data
            pass
        elif data_type == "contexts":
            # Export contexts data
            pass
        elif data_type == "relations":
            # Export relations data
            pass
        
        # TODO: Implement actual export logic
        
        raise HTTPException(status_code=400, detail="Export not implemented yet")
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to export data")
        raise HTTPException(status_code=500, detail="Failed to export data")

@router.post("/data/cleanup")
async def cleanup_admin_data(
    dry_run: bool = Query(True),
    data_type: Optional[str] = Query(None, pattern="^(all|memories|contexts|relations)$"),
    older_than_days: Optional[int] = Query(None, ge=1),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up system data (admin only).
    
    Args:
        dry_run: Whether to perform a dry run
        data_type: Type of data to clean up
        older_than_days: Clean up data older than this many days
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Cleanup results
        
    Raises:
        HTTPException: If cleanup fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # TODO: Implement actual cleanup logic
        
        return {
            "message": "Cleanup not implemented yet",
            "dry_run": dry_run,
            "data_type": data_type,
            "older_than_days": older_than_days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to cleanup data")
        raise HTTPException(status_code=500, detail="Failed to cleanup data")

# Maintenance Operations
@router.post("/maintenance/reindex")
async def reindex_admin_data(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reindex system data (admin only).
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Reindex results
        
    Raises:
        HTTPException: If reindex fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # TODO: Implement actual reindex logic
        
        return {"message": "Reindex not implemented yet"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to reindex data")
        raise HTTPException(status_code=500, detail="Failed to reindex data")

@router.post("/maintenance/analyze")
async def analyze_admin_data(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze system data (admin only).
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # TODO: Implement actual analysis logic
        
        return {"message": "Analysis not implemented yet"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to analyze data")
        raise HTTPException(status_code=500, detail="Failed to analyze data")

@router.post("/maintenance/upgrade")
async def upgrade_admin_system(
    version: str = Body(..., min_length=1),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upgrade system to a new version (admin only).
    
    Args:
        version: Target version to upgrade to
        db: Database dependency
        current_user: Current authenticated user (must be admin)
        
    Returns:
        Upgrade results
        
    Raises:
        HTTPException: If upgrade fails
    """
    try:
        # Check if current user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # TODO: Implement actual upgrade logic
        
        return {"message": "Upgrade not implemented yet", "version": version}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to upgrade system")
        raise HTTPException(status_code=500, detail="Failed to upgrade system")