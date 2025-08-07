"""
Pydantic schemas for relation operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

class RelationBase(BaseModel):
    """Base schema for relation operations."""
    source_memory_id: int = Field(..., gt=0)
    target_memory_id: int = Field(..., gt=0)
    relation_type: str = Field(..., min_length=1, max_length=50)
    strength: float = Field(0.5, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('source_memory_id')
    def validate_source_memory_id(cls, v):
        """Validate source memory ID."""
        if v <= 0:
            raise ValueError("Source memory ID must be greater than 0")
        return v

    @validator('target_memory_id')
    def validate_target_memory_id(cls, v):
        """Validate target memory ID."""
        if v <= 0:
            raise ValueError("Target memory ID must be greater than 0")
        return v

    @validator('relation_type')
    def validate_relation_type(cls, v):
        """Validate relation type."""
        if not v or not isinstance(v, str):
            raise ValueError("Relation type must be a non-empty string")
        return v.strip()

    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata dictionary."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v

class RelationCreate(RelationBase):
    """Schema for creating a new relation."""
    pass

class RelationUpdate(BaseModel):
    """Schema for updating a relation."""
    relation_type: Optional[str] = Field(None, min_length=1, max_length=50)
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None)

    @validator('relation_type')
    def validate_relation_type(cls, v):
        """Validate relation type."""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Relation type must be a string")
            v = v.strip()
            if not v:
                raise ValueError("Relation type cannot be empty")
        return v

    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata dictionary."""
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v

class RelationResponse(RelationBase):
    """Schema for relation response."""
    id: int
    created_at: datetime
    updated_at: datetime
    version: int = 1

    class Config:
        from_attributes = True

class RelationStats(BaseModel):
    """Schema for relation statistics."""
    total_relations: int
    relations_by_type: Dict[str, int]
    relations_by_strength: Dict[str, int]
    average_strength: float
    strongest_relation: Optional[str]
    weakest_relation: Optional[str]
    most_connected_memory: Optional[int]
    total_connections: int

class RelationDiscovery(BaseModel):
    """Schema for relation discovery."""
    source_memory_id: int
    target_memory_id: int
    relation_type: str
    strength: float
    similarity_score: float
    context_overlap: float
    keywords: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None

class RelationDiscoveryRequest(BaseModel):
    """Schema for relation discovery request."""
    query: str = Field(..., min_length=1)
    threshold: float = Field(0.5, ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=100)
    context_id: Optional[int] = Field(None)
    relation_types: Optional[List[str]] = Field(None)
    exclude_existing: bool = Field(True)