from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ContextBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    access_level: str = Field(default="user", pattern="^(public|user|privileged|admin)$")
    context_metadata: Optional[Dict[str, Any]] = None

class ContextCreate(ContextBase):
    """Schema for creating a new context"""
    pass

class ContextUpdate(BaseModel):
    """Schema for updating an existing context"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    access_level: Optional[str] = Field(None, pattern="^(public|user|privileged|admin)$")
    context_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ContextResponse(ContextBase):
    """Schema for context response"""
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    memory_count: Optional[int] = 0
    relation_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class ContextSearch(BaseModel):
    """Schema for context search request"""
    query: Optional[str] = None
    owner_id: Optional[int] = None
    access_level: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class ContextStats(BaseModel):
    """Schema for context statistics"""
    context_id: int
    total_memories: int
    total_relations: int
    active_memories: int
    last_updated: datetime
    most_central_memories: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True