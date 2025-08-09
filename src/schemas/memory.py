from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class MemoryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    context_id: Optional[int] = None
    access_level: str = Field(default="user", pattern="^(public|user|privileged|admin)$")
    memory_metadata: Optional[Dict[str, Any]] = None

class MemoryCreate(MemoryBase):
    """Schema for creating a new memory"""
    auto_relate: bool = True
    relation_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class MemoryUpdate(BaseModel):
    """Schema for updating an existing memory"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    context_id: Optional[int] = None
    access_level: Optional[str] = Field(None, pattern="^(public|user|privileged|admin)$")
    memory_metadata: Optional[Dict[str, Any]] = None

class MemoryResponse(MemoryBase):
    """Schema for memory response"""
    id: int
    owner_id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    relation_count: Optional[int] = 0
    similarity_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class MemorySearch(BaseModel):
    """Schema for memory search request"""
    query: str = Field(..., min_length=1)
    context_id: Optional[int] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    use_semantic: bool = True
    filters: Optional[Dict[str, Any]] = None

class MemoryBulkCreate(BaseModel):
    """Schema for bulk memory creation"""
    memories: List[MemoryCreate]
    auto_relate: bool = True
    batch_size: int = Field(default=100, ge=1, le=1000)

class MemoryVersion(BaseModel):
    """Schema for memory version history"""
    id: int
    memory_id: int
    version: int
    title: str
    content: str
    created_at: datetime
    created_by: int
    change_description: Optional[str] = None
    version_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class MemoryStats(BaseModel):
    """Schema for memory statistics"""
    total_memories: int = 0
    total_relations: int = 0
    total_contexts: int = 0
    memory_by_access_level: Dict[str, int] = {}
    recent_memories: int = 0
    top_contexts: List[Dict[str, Any]] = []

class MemorySearchResponse(BaseModel):
    """Schema for memory search response"""
    id: int
    title: str
    content: str
    similarity: float
    relation_count: int
    context_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MemorySummary(BaseModel):
    """Schema for memory summary request"""
    max_length: int = Field(default=50, ge=10, le=500)
    use_ai: bool = False

class MemorySummaryResponse(BaseModel):
    """Schema for memory summary response"""
    memory_id: int
    summary: str
    generated_at: datetime
    method: str  # "ai" or "extractive"
    
    class Config:
        from_attributes = True