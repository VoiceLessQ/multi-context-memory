"""
User schemas for the enhanced MCP Multi-Context Memory System API.
Provides Pydantic models for user operations.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator

class UserBase(BaseModel):
    """Base schema for user operations."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    is_admin: bool = Field(False, description="Admin status")

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, description="Password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    is_admin: Optional[bool] = Field(None, description="Admin status")
    password: Optional[str] = Field(None, min_length=8, description="Password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
        return v

class UserResponse(UserBase):
    """Schema for user response."""
    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Active status")
    
    class Config:
        orm_mode = True

class UserLoginRequest(BaseModel):
    """Schema for user login request."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")

class UserLoginResponse(BaseModel):
    """Schema for user login response."""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")

class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    is_admin: bool = Field(False, description="Admin status")

class UserRegisterResponse(BaseModel):
    """Schema for user registration response."""
    message: str = Field(..., description="Registration message")
    user: UserResponse = Field(..., description="User information")

class UserPasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserPasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr = Field(..., description="Email address")

class UserPasswordResetConfirmRequest(BaseModel):
    """Schema for password reset confirmation request."""
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserStatsResponse(BaseModel):
    """Schema for user statistics response."""
    total_memories: int = Field(..., description="Total number of memories")
    total_contexts: int = Field(..., description="Total number of contexts")
    total_relations: int = Field(..., description="Total number of relations")
    active_memories: int = Field(..., description="Number of active memories")
    active_contexts: int = Field(..., description="Number of active contexts")
    recent_activity: list[Dict[str, Any]] = Field(..., description="Recent activity")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

class UserListResponse(BaseModel):
    """Schema for user list response."""
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")

class UserBatchRequest(BaseModel):
    """Schema for user batch operations."""
    operation: str = Field(..., regex="^(activate|deactivate|delete|make_admin|remove_admin)$", description="Batch operation")
    user_ids: list[int] = Field(..., description="List of user IDs")

class UserBatchResponse(BaseModel):
    """Schema for user batch response."""
    total: int = Field(..., description="Total number of users processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: list[str] = Field(default_factory=list, description="Operation errors")