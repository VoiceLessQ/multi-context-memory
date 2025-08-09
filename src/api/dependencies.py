"""
Dependencies module for the enhanced MCP Multi-Context Memory System API.
Provides dependency injection for authentication, authorization, and database access.
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

# Optional JWT support
try:
    from jose import jwt
    JWT_AVAILABLE = True
except ImportError:
    logging.warning("JWT features not available - install python-jose")
    JWT_AVAILABLE = False
    # Create dummy jwt module
    class jwt:
        class ExpiredSignatureError(Exception):
            pass
        class JWTError(Exception):
            pass
        @staticmethod
        def decode(*args, **kwargs):
            raise Exception("JWT not available")
        @staticmethod
        def encode(*args, **kwargs):
            return "dummy-token"

from ..database.enhanced_memory_db import EnhancedMemoryDB

# Optional settings and logging
try:
    from ..config.settings import get_settings
    from ..config.logging import get_logger
    logger = get_logger(__name__)
    settings = get_settings()
except ImportError:
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    # Create dummy settings
    class DummySettings:
        def __init__(self):
            self.database_url = "sqlite:///memory.db"
            self.secret_key = "dummy-secret"
            self.algorithm = "HS256"
    settings = DummySettings()

security = HTTPBearer()

def get_db() -> EnhancedMemoryDB:
    """Get database instance."""
    # This would typically be implemented with a database session manager
    # For now, we'll create a new instance each time
    return EnhancedMemoryDB(database_url=settings.database_url)

def get_enhanced_db() -> EnhancedMemoryDB:
    """Get enhanced database instance."""
    return get_db()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: EnhancedMemoryDB = Depends(get_db)
) -> Dict[str, Any]:
    """Get current authenticated user."""
    if not JWT_AVAILABLE:
        # Return dummy user when JWT is not available
        logger.warning("JWT not available, using dummy user")
        return {
            "id": 1,
            "username": "default_user",
            "email": "user@example.com",
            "is_admin": False
        }
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.get_user_by_username(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: EnhancedMemoryDB = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """Get current authenticated user (optional - returns None if not authenticated)."""
    if not JWT_AVAILABLE:
        # Return dummy user when JWT is not available
        return {
            "id": 1,
            "username": "default_user",
            "email": "user@example.com",
            "is_admin": False
        }
    
    if credentials is None:
        return None
        
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        user = db.get_user_by_username(user_id)
        if user is None or not user.is_active:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    except (jwt.ExpiredSignatureError, jwt.JWTError):
        return None
    except Exception as e:
        logger.warning(f"Optional authentication error: {str(e)}")
        return None

def get_current_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current admin user."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def check_resource_permission(
    resource_owner_id: int,
    current_user: Dict[str, Any],
    resource_type: str = "resource"
) -> bool:
    """Check if user has permission to access a resource."""
    if resource_owner_id == current_user["id"]:
        return True
    
    if current_user.get("is_admin"):
        return True
    
    # Add additional permission checks here if needed
    # For example, check if user has specific role or permission
    
    return False

def rate_limit_check(
    user_id: int,
    db: EnhancedMemoryDB,
    window_minutes: int = 60,
    max_requests: int = 100
) -> bool:
    """Check if user has exceeded rate limit."""
    # This would typically be implemented with Redis or similar
    # For now, we'll always return True
    return True

def validate_access_level(
    access_level: str,
    current_user: Dict[str, Any]
) -> bool:
    """Validate user's access level against required level."""
    access_levels = ["public", "user", "privileged", "admin"]
    
    if access_level not in access_levels:
        return False
    
    user_level = "public"
    if current_user.get("is_admin"):
        user_level = "admin"
    elif current_user.get("is_privileged"):
        user_level = "privileged"
    else:
        user_level = "user"
    
    return access_levels.index(user_level) >= access_levels.index(access_level)

def get_pagination_params(
    page: int = 1,
    per_page: int = 10,
    max_per_page: int = 100
) -> tuple[int, int]:
    """Get pagination parameters."""
    page = max(1, page)
    per_page = min(max_per_page, max(1, per_page))
    offset = (page - 1) * per_page
    return offset, per_page

def validate_search_query(query: str) -> bool:
    """Validate search query."""
    if not query or len(query.strip()) == 0:
        return False
    
    # Add additional validation if needed
    # For example, check for SQL injection attempts
    
    return True

def sanitize_input(input_data: str) -> str:
    """Sanitize input data."""
    # Basic sanitization
    input_data = input_data.strip()
    
    # Add additional sanitization if needed
    # For example, escape HTML characters, remove special characters, etc.
    
    return input_data

def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """Validate metadata."""
    if not isinstance(metadata, dict):
        return False
    
    # Add additional validation if needed
    # For example, check for sensitive information, validate keys/values, etc.
    
    return True

def log_api_call(
    endpoint: str,
    method: str,
    user_id: Optional[int],
    status_code: int,
    execution_time: float,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """Log API call."""
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "user_id": user_id,
        "status_code": status_code,
        "execution_time": execution_time,
        **(additional_info or {})
    }
    
    logger.info(f"API Call: {log_data}")