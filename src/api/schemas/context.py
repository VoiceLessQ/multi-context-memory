"""
Pydantic schemas for context operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

class ContextBase(BaseModel):
    """Base schema for context operations."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    access_level: str = Field("user", pattern="^(public|user|privileged|admin)$")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata dictionary."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v

class ContextCreate(ContextBase):
    """Schema for creating a new context."""
    pass

class ContextUpdate(BaseModel):
    """Schema for updating a context."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    access_level: Optional[str] = Field(None, pattern="^(public|user|privileged|admin)$")
    metadata: Optional[Dict[str, Any]] = Field(None)

    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata dictionary."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v

class ContextResponse(ContextBase):
    """Schema for context response."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    version: int = 1

    class Config:
        from_attributes = True

class ContextStats(BaseModel):
    """Schema for context statistics."""
    total_contexts: int
    total_memories: int
    memories_by_context: Dict[str, int]
    contexts_by_access_level: Dict[str, int]
    oldest_context: Optional[datetime]
    newest_context: Optional[datetime]
    most_active_context: Optional[str]
    average_memories_per_context: float