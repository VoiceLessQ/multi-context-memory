"""
Pydantic schemas for authentication operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator

class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None

class UserBase(BaseModel):
    """Base schema for user operations."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    role: str = Field("user", regex="^(user|privileged|admin)$")

    @validator('username')
    def validate_username(cls, v):
        """Validate username."""
        if not v or not isinstance(v, str):
            raise ValueError("Username must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        return v

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        """Validate password."""
        if not v or not isinstance(v, str):
            raise ValueError("Password must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Password cannot be empty")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None)
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, regex="^(user|privileged|admin)$")

    @validator('username')
    def validate_username(cls, v):
        """Validate username."""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Username must be a string")
            v = v.strip()
            if not v:
                raise ValueError("Username cannot be empty")
        return v

class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

    @validator('username')
    def validate_username(cls, v):
        """Validate username."""
        if not v or not isinstance(v, str):
            raise ValueError("Username must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        return v

class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('current_password')
    def validate_current_password(cls, v):
        """Validate current password."""
        if not v or not isinstance(v, str):
            raise ValueError("Current password must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Current password cannot be empty")
        return v

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password."""
        if not v or not isinstance(v, str):
            raise ValueError("New password must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("New password cannot be empty")
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v

class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator('token')
    def validate_token(cls, v):
        """Validate reset token."""
        if not v or not isinstance(v, str):
            raise ValueError("Reset token must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Reset token cannot be empty")
        return v

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password."""
        if not v or not isinstance(v, str):
            raise ValueError("New password must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("New password cannot be empty")
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return v

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., min_length=1)

    @validator('refresh_token')
    def validate_refresh_token(cls, v):
        """Validate refresh token."""
        if not v or not isinstance(v, str):
            raise ValueError("Refresh token must be a non-empty string")
        v = v.strip()
        if not v:
            raise ValueError("Refresh token cannot be empty")
        return v

class UserStats(BaseModel):
    """Schema for user statistics."""
    total_memories: int
    total_contexts: int
    total_relations: int
    memories_created_last_7_days: int
    memories_created_last_30_days: int
    last_login: Optional[datetime]
    account_age_days: int
    most_used_context: Optional[str]
    most_used_access_level: str
    average_words_per_memory: float