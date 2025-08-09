"""
API routes for authentication operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from ...database.models import User
from ...database.enhanced_memory_db import EnhancedMemoryDB
from ...schemas.auth import (
    Token, TokenData, UserCreate, UserResponse, UserUpdate,
    UserStats, LoginRequest, RefreshTokenRequest, PasswordResetRequest,
    PasswordResetConfirm, PasswordChangeRequest, UserActivationRequest
)
from ...utils.auth import (
    create_access_token, create_refresh_token, verify_password,
    get_password_hash, get_current_user, get_optional_user,
    verify_token, oauth2_scheme
)
from ...utils.error_handling import handle_errors
from ...utils.email import send_verification_email, send_password_reset_email

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User data to register
        db: Database dependency
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If registration fails
    """
    try:
        # Check if user already exists
        existing_user = await db.get_user_by_username(username=user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        existing_user = await db.get_user_by_email(email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create user
        user = await db.create_user(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=user_data.is_active
        )
        
        # Send verification email if needed
        if not user.is_active:
            await send_verification_email(user.email, user.id)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to register user")
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Login user with username and password.
    
    Args:
        form_data: Login form data
        db: Database dependency
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If login fails
    """
    try:
        # Get user
        user = await db.get_user_by_username(username=form_data.username)
        
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not activated"
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        # Update last login
        await db.update_user_last_login(user_id=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to login user")
        raise HTTPException(status_code=500, detail="Failed to login user")

@router.post("/login-with-token", response_model=Token)
async def login_with_token(
    login_data: LoginRequest,
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Login user with email and password.
    
    Args:
        login_data: Login data with email and password
        db: Database dependency
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If login fails
    """
    try:
        # Get user
        user = await db.get_user_by_email(email=login_data.email)
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not activated"
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        # Update last login
        await db.update_user_last_login(user_id=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to login user")
        raise HTTPException(status_code=500, detail="Failed to login user")

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Refresh access token.
    
    Args:
        refresh_data: Refresh token data
        db: Database dependency
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh fails
    """
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token)
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user = await db.get_user_by_username(username=username)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not activated"
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to refresh token")
        raise HTTPException(status_code=500, detail="Failed to refresh token")

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Logout user.
    
    Args:
        current_user: Current authenticated user
        db: Database dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If logout fails
    """
    try:
        # Add token to blacklist (if implemented)
        # await db.add_token_to_blacklist(token=access_token, expires_at=...)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        handle_errors(e, "Failed to logout user")
        raise HTTPException(status_code=500, detail="Failed to logout user")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        return current_user
        
    except Exception as e:
        handle_errors(e, "Failed to get current user")
        raise HTTPException(status_code=500, detail="Failed to get current user")

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Update current user information.
    
    Args:
        user_data: Updated user data
        current_user: Current authenticated user
        db: Database dependency
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Update user
        user = await db.update_user(
            user_id=current_user.id,
            **user_data.dict(exclude_unset=True)
        )
        
        return user
        
    except Exception as e:
        handle_errors(e, "Failed to update current user")
        raise HTTPException(status_code=500, detail="Failed to update current user")

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password change fails
    """
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        # Update password
        await db.update_user_password(
            user_id=current_user.id,
            new_password_hash=get_password_hash(password_data.new_password)
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to change password")
        raise HTTPException(status_code=500, detail="Failed to change password")

@router.post("/reset-password-request")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Request password reset.
    
    Args:
        reset_data: Password reset request data
        db: Database dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If request fails
    """
    try:
        # Get user
        user = await db.get_user_by_email(email=reset_data.email)
        
        if user:
            # Send password reset email
            await send_password_reset_email(user.email, user.id)
        
        return {"message": "Password reset email sent"}
        
    except Exception as e:
        handle_errors(e, "Failed to request password reset")
        raise HTTPException(status_code=500, detail="Failed to request password reset")

@router.post("/reset-password-confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Confirm password reset.
    
    Args:
        reset_data: Password reset confirmation data
        db: Database dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If confirmation fails
    """
    try:
        # Verify reset token
        payload = verify_token(reset_data.reset_token)
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Get user
        user = await db.get_user_by_id(user_id=user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Update password
        await db.update_user_password(
            user_id=user_id,
            new_password_hash=get_password_hash(reset_data.new_password)
        )
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to reset password")
        raise HTTPException(status_code=500, detail="Failed to reset password")

@router.post("/activate")
async def activate_user(
    activation_data: UserActivationRequest,
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Activate user account.
    
    Args:
        activation_data: User activation data
        db: Database dependency
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If activation fails
    """
    try:
        # Verify activation token
        payload = verify_token(activation_data.activation_token)
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activation token"
            )
        
        # Get user
        user = await db.get_user_by_id(user_id=user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Activate user
        await db.update_user(
            user_id=user_id,
            is_active=True
        )
        
        return {"message": "Account activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to activate account")
        raise HTTPException(status_code=500, detail="Failed to activate account")

@router.get("/stats/summary", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Get user statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database dependency
        
    Returns:
        User statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get statistics
        stats = await db.get_user_stats(user_id=current_user.id)
        
        return stats
        
    except Exception as e:
        handle_errors(e, "Failed to get user statistics")
        raise HTTPException(status_code=500, detail="Failed to get user statistics")

@router.post("/verify-email")
async def verify_email_address(
    email: str = Body(..., regex=r'^[^@]+@[^@]+\.[^@]+$'),
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Verify email address format.
    
    Args:
        email: Email address to verify
        db: Database dependency
        
    Returns:
        Verification result
        
    Raises:
        HTTPException: If verification fails
    """
    try:
        # Check if email is already registered
        existing_user = await db.get_user_by_email(email=email)
        
        if existing_user:
            return {
                "valid": True,
                "message": "Email is valid but already registered",
                "registered": True
            }
        else:
            return {
                "valid": True,
                "message": "Email is valid and available",
                "registered": False
            }
        
    except Exception as e:
        handle_errors(e, "Failed to verify email")
        raise HTTPException(status_code=500, detail="Failed to verify email")

@router.post("/check-username")
async def check_username_availability(
    username: str = Body(..., min_length=3, max_length=50),
    db: EnhancedMemoryDB = Depends(get_enhanced_db)
):
    """
    Check username availability.
    
    Args:
        username: Username to check
        db: Database dependency
        
    Returns:
        Availability result
        
    Raises:
        HTTPException: If check fails
    """
    try:
        # Check if username is already registered
        existing_user = await db.get_user_by_username(username=username)
        
        if existing_user:
            return {
                "available": False,
                "message": "Username is already taken"
            }
        else:
            return {
                "available": True,
                "message": "Username is available"
            }
        
    except Exception as e:
        handle_errors(e, "Failed to check username")
        raise HTTPException(status_code=500, detail="Failed to check username")