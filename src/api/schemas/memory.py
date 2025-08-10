"""
Pydantic schemas for memory operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

class MemoryBase(BaseModel):
    """Base schema for memory operations."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    context_id: Optional[int] = Field(None)
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

class MemoryCreate(MemoryBase):
    """Schema for creating a new memory."""
    pass

class MemoryUpdate(BaseModel):
    """Schema for updating a memory."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
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

class MemoryResponse(MemoryBase):
    """Schema for memory response."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    version: int = 1

    class Config:
        from_attributes = True

class MemorySearch(BaseModel):
    """Schema for memory search."""
    query: str = Field(..., min_length=1)
    context_id: Optional[int] = Field(None)
    access_level: Optional[str] = Field(None, pattern="^(public|user|privileged|admin)$")
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.5, ge=0.0, le=1.0)

class MemoryStats(BaseModel):
    """Schema for memory statistics."""
    total_memories: int
    memories_by_context: Dict[str, int]
    memories_by_access_level: Dict[str, int]
    total_words: int
    average_words_per_memory: float
    oldest_memory: Optional[datetime]
    newest_memory: Optional[datetime]

class ExportResponse(BaseModel):
    """Schema for export response."""
    total_items: int
    format: str
    exported_at: datetime
    file_path: Optional[str] = None

class ImportResponse(BaseModel):
    """Schema for import response."""
    total_items: int
    imported_items: int
    skipped_items: int
    errors: List[str] = Field(default_factory=list)
    imported_at: datetime