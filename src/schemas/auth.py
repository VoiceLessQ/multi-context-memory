"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(User):
    """Schema for user response - alias for User"""
    pass

class UserStats(BaseModel):
    """Schema for user statistics"""
    total_users: int = 0
    active_users: int = 0
    admin_users: int = 0
    recent_registrations: int = 0

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: list = []

class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class UserActivationRequest(BaseModel):
    token: str

class UserDeactivationRequest(BaseModel):
    user_id: int
    reason: Optional[str] = None

class AuthStats(BaseModel):
    """Schema for authentication statistics"""
    total_logins: int = 0
    failed_logins: int = 0
    active_sessions: int = 0