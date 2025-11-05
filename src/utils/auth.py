"""
Authentication utilities for the MCP Multi-Context Memory System.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..database.models import User
from ..database.refactored_memory_db import RefactoredMemoryDB

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# JWT Configuration - MUST be set via environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY environment variable must be set. "
        "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create an access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Create a refresh token.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh token lasts longer
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: RefactoredMemoryDB = Depends(lambda: RefactoredMemoryDB()) # Simplified for now
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token
        db: Database dependency
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If user is not found or token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # This is a simplified user retrieval. In a real app, you'd have a proper DB dependency.
    # For now, let's assume a method exists or we need to adjust this.
    # user = await db.get_user_by_username(username=username)
    # if user is None:
    #     raise credentials_exception
    # return user
    
    # Placeholder until DB integration is fully sorted
    raise HTTPException(status_code=501, detail="User retrieval not fully implemented")

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: RefactoredMemoryDB = Depends(lambda: RefactoredMemoryDB()) # Simplified for now
) -> Optional[User]:
    """
    Get the current user if a valid token is provided, otherwise return None.
    
    Args:
        token: Optional JWT token
        db: Database dependency
        
    Returns:
        Current user if authenticated, None otherwise
    """
    if token is None:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None

# Dependency to get RefactoredMemoryDB instance
# This is a placeholder and might need to be connected to your actual DB setup
def get_enhanced_db() -> RefactoredMemoryDB:
    """
    Dependency to get an RefactoredMemoryDB instance.
    This is a simplified version.
    """
    # In a real application, you would initialize this with proper session/connection
    # For now, returning a new instance. This might need adjustment based on your FastAPI app setup.
    return RefactoredMemoryDB()