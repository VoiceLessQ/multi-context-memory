from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class RelationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    source_context_id: Optional[int] = None
    target_memory_id: Optional[int] = None
    source_memory_id: Optional[int] = None
    target_context_id: Optional[int] = None
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    relation_metadata: Optional[Dict[str, Any]] = None

class RelationCreate(RelationBase):
    """Schema for creating a new relation"""
    pass

class RelationUpdate(BaseModel):
    """Schema for updating an existing relation"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    relation_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class RelationResponse(RelationBase):
    """Schema for relation response"""
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    auto_generated: Optional[bool] = False
    
    class Config:
        from_attributes = True

class RelationSearch(BaseModel):
    """Schema for relation search request"""
    source_id: Optional[int] = None
    target_id: Optional[int] = None
    relation_type: Optional[str] = None
    min_strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    auto_generated: Optional[bool] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filters: Optional[Dict[str, Any]] = None

class RelationSearchResponse(BaseModel):
    """Schema for relation search response"""
    id: int
    name: str
    source_memory_id: Optional[int] = None
    target_memory_id: Optional[int] = None
    strength: float
    similarity: Optional[float] = None
    created_at: datetime
        
    class Config:
        from_attributes = True

class RelationStats(BaseModel):
    """Schema for relation statistics"""
    total_relations: int = 0
    relation_types: Dict[str, int] = {}
    average_strength: float = 0.0
    most_connected_memories: List[Dict[str, Any]] = []

class RelationGraph(BaseModel):
    """Schema for relation graph"""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    center_node_id: int
    max_depth: int
        
    class Config:
        from_attributes = True

class RelationBulkCreate(BaseModel):
    """Schema for bulk relation creation"""
    relations: List[RelationCreate]
    skip_duplicates: bool = True

class GraphQuery(BaseModel):
    """Schema for graph-based queries"""
    start_node_id: int
    max_depth: int = Field(default=3, ge=1, le=10)
    relation_types: Optional[List[str]] = None
    min_strength: float = Field(default=0.5, ge=0.0, le=1.0)
    include_metadata: bool = False

class GraphAnalytics(BaseModel):
    """Schema for graph analytics response"""
    total_nodes: int
    total_edges: int
    density: float
    is_connected: bool
    components: int
    average_degree: float
    top_central_nodes: List[Dict[str, Any]]
    clustering_coefficient: Optional[float] = None
    
    class Config:
        from_attributes = True