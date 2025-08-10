"""
Admin schemas for the enhanced MCP Multi-Context Memory System.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class AdminUserBase(BaseModel):
    """Base schema for admin user operations."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: str = Field(default="user", pattern="^(user|privileged|admin)$")
    is_active: bool = True

class AdminUserCreate(AdminUserBase):
    """Schema for creating a new user by admin."""
    password: str = Field(..., min_length=8, max_length=100)

class AdminUserUpdate(BaseModel):
    """Schema for updating a user by admin."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(user|privileged|admin)$")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)

class AdminUserResponse(AdminUserBase):
    """Schema for user response to admin."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
        
    class Config:
        from_attributes = True

class SystemStats(BaseModel):
    """Schema for system statistics."""
    total_users: int = 0
    total_memories: int = 0
    total_contexts: int = 0
    total_relations: int = 0
    storage_used_mb: float = 0.0
    active_sessions: int = 0

class SystemLog(BaseModel):
    """Schema for system log."""
    timestamp: datetime
    level: str
    message: str
    module: str
    user_id: Optional[int] = None

class SystemLogResponse(SystemLog):
    """Schema for system log response."""
    id: int
        
    class Config:
        from_attributes = True

class SystemLogFilter(BaseModel):
    """Schema for system log filtering."""
    level: Optional[str] = None
    module: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)

class BackupRequest(BaseModel):
    """Schema for backup request."""
    include_data: bool = True
    include_config: bool = True
    compression: bool = True
    description: Optional[str] = None

class BackupResponse(BaseModel):
    """Schema for backup response."""
    backup_id: str
    file_path: str
    size_bytes: int
    created_at: datetime
    description: Optional[str] = None

class RestoreRequest(BaseModel):
    """Schema for restore request."""
    backup_id: str
    restore_data: bool = True
    restore_config: bool = True

class RestoreResponse(BaseModel):
    """Schema for restore response."""
    success: bool
    message: str
    restored_at: datetime

class SystemHealth(BaseModel):
    """Schema for system health check."""
    status: str = "healthy"
    database_status: str = "connected"
    storage_status: str = "available"
    memory_usage_percent: float = 0.0
    disk_usage_percent: float = 0.0
    uptime_seconds: int = 0

class SystemConfig(BaseModel):
    """Schema for system configuration."""
    debug_mode: bool = False
    log_level: str = "INFO"
    max_upload_size_mb: int = 100
    session_timeout_minutes: int = 30
    backup_retention_days: int = 30