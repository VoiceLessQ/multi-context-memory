"""
API routes for relation operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from pydantic import UUID4

from ...database.models import Relation, User, Memory, Context
from ...database.enhanced_memory_db import EnhancedMemoryDB
from ...schemas.relation import (
    RelationCreate, RelationUpdate, RelationResponse, RelationStats,
    RelationSearch, RelationSearchResponse, RelationGraph
)
from ...schemas.auth import TokenData
from ...utils.auth import get_current_user, get_optional_user
from ...utils.error_handling import handle_errors

router = APIRouter()

@router.post("/", response_model=RelationResponse, status_code=201)
async def create_relation(
    relation_data: RelationCreate,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new relation.
    
    Args:
        relation_data: Relation data to create
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Created relation
        
    Raises:
        HTTPException: If relation creation fails
    """
    try:
        # Create relation
        relation = await db.create_relation(
            user_id=current_user.id,
            **relation_data.dict()
        )
        
        return relation
        
    except Exception as e:
        handle_errors(e, "Failed to create relation")
        raise HTTPException(status_code=500, detail="Failed to create relation")

@router.get("/", response_model=List[RelationResponse])
async def get_relations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    memory_id: Optional[int] = Query(None),
    context_id: Optional[int] = Query(None),
    relation_type: Optional[str] = Query(None),
    access_level: Optional[str] = Query(None, regex="^(public|user|privileged|admin)$"),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get relations with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        memory_id: Filter by memory ID
        context_id: Filter by context ID
        relation_type: Filter by relation type
        access_level: Filter by access level
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of relations
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get relations
        relations = await db.get_relations(
            skip=skip,
            limit=limit,
            memory_id=memory_id,
            context_id=context_id,
            relation_type=relation_type,
            access_level=access_level,
            user_id=current_user.id if current_user else None
        )
        
        return relations
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve relations")
        raise HTTPException(status_code=500, detail="Failed to retrieve relations")

@router.get("/{relation_id}", response_model=RelationResponse)
async def get_relation(
    relation_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a specific relation by ID.
    
    Args:
        relation_id: Relation ID to retrieve
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Relation details
        
    Raises:
        HTTPException: If relation not found or retrieval fails
    """
    try:
        # Get relation
        relation = await db.get_relation(
            relation_id=relation_id,
            user_id=current_user.id if current_user else None
        )
        
        if not relation:
            raise HTTPException(status_code=404, detail="Relation not found")
        
        return relation
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve relation")
        raise HTTPException(status_code=500, detail="Failed to retrieve relation")

@router.put("/{relation_id}", response_model=RelationResponse)
async def update_relation(
    relation_id: int = Path(..., gt=0),
    relation_data: RelationUpdate = Body(...),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing relation.
    
    Args:
        relation_id: Relation ID to update
        relation_data: Updated relation data
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated relation
        
    Raises:
        HTTPException: If relation not found or update fails
    """
    try:
        # Check if relation exists and user has permission
        existing_relation = await db.get_relation(
            relation_id=relation_id,
            user_id=current_user.id
        )
        
        if not existing_relation:
            raise HTTPException(status_code=404, detail="Relation not found")
        
        # Update relation
        relation = await db.update_relation(
            relation_id=relation_id,
            user_id=current_user.id,
            **relation_data.dict(exclude_unset=True)
        )
        
        return relation
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update relation")
        raise HTTPException(status_code=500, detail="Failed to update relation")

@router.delete("/{relation_id}", status_code=204)
async def delete_relation(
    relation_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a relation.
    
    Args:
        relation_id: Relation ID to delete
        db: Database dependency
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If relation not found or deletion fails
    """
    try:
        # Check if relation exists and user has permission
        existing_relation = await db.get_relation(
            relation_id=relation_id,
            user_id=current_user.id
        )
        
        if not existing_relation:
            raise HTTPException(status_code=404, detail="Relation not found")
        
        # Delete relation
        await db.delete_relation(
            relation_id=relation_id,
            user_id=current_user.id
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to delete relation")
        raise HTTPException(status_code=500, detail="Failed to delete relation")

@router.get("/stats/summary", response_model=RelationStats)
async def get_relation_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get relation statistics.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Relation statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get statistics
        stats = await db.get_relation_stats(
            user_id=current_user.id if current_user else None
        )
        
        return stats
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve relation statistics")
        raise HTTPException(status_code=500, detail="Failed to retrieve relation statistics")

@router.post("/search", response_model=List[RelationSearchResponse])
async def search_relations(
    search_data: RelationSearch,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Search relations using various criteria.
    
    Args:
        search_data: Search parameters
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of matching relations
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Search relations
        relations = await db.search_relations(
            query=search_data.query,
            filters=search_data.filters,
            user_id=current_user.id if current_user else None
        )
        
        return relations
        
    except Exception as e:
        handle_errors(e, "Failed to search relations")
        raise HTTPException(status_code=500, detail="Failed to search relations")

@router.get("/graph/{memory_id}", response_model=RelationGraph)
async def get_memory_relations_graph(
    memory_id: int = Path(..., gt=0),
    max_depth: int = Query(3, ge=1, le=5),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get relations graph for a specific memory.
    
    Args:
        memory_id: Memory ID to get relations for
        max_depth: Maximum depth of relations to retrieve
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Relations graph
        
    Raises:
        HTTPException: If graph retrieval fails
    """
    try:
        # Get relations graph
        graph = await db.get_memory_relations_graph(
            memory_id=memory_id,
            max_depth=max_depth,
            user_id=current_user.id if current_user else None
        )
        
        return graph
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve relations graph")
        raise HTTPException(status_code=500, detail="Failed to retrieve relations graph")

@router.get("/discover/{memory_id}")
async def discover_relations(
    memory_id: int = Path(..., gt=0),
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    max_results: int = Query(10, ge=1, le=100),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Discover potential relations for a memory.
    
    Args:
        memory_id: Memory ID to discover relations for
        threshold: Similarity threshold for relation discovery
        max_results: Maximum number of results to return
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of discovered relations
        
    Raises:
        HTTPException: If relation discovery fails
    """
    try:
        # Discover relations
        relations = await db.discover_relations(
            memory_id=memory_id,
            threshold=threshold,
            max_results=max_results,
            user_id=current_user.id if current_user else None
        )
        
        return {"memory_id": memory_id, "discovered_relations": relations}
        
    except Exception as e:
        handle_errors(e, "Failed to discover relations")
        raise HTTPException(status_code=500, detail="Failed to discover relations")

@router.post("/batch-create", response_model=List[RelationResponse], status_code=201)
async def batch_create_relations(
    relations_data: List[RelationCreate],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple relations in batch.
    
    Args:
        relations_data: List of relation data to create
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        List of created relations
        
    Raises:
        HTTPException: If batch creation fails
    """
    try:
        # Create relations
        relations = []
        for relation_data in relations_data:
            relation = await db.create_relation(
                user_id=current_user.id,
                **relation_data.dict()
            )
            relations.append(relation)
        
        return relations
        
    except Exception as e:
        handle_errors(e, "Failed to create relations in batch")
        raise HTTPException(status_code=500, detail="Failed to create relations in batch")

@router.post("/batch-update", response_model=List[RelationResponse])
async def batch_update_relations(
    updates_data: List[Dict[str, Any]],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update multiple relations in batch.
    
    Args:
        updates_data: List of update data with relation_id and fields to update
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        List of updated relations
        
    Raises:
        HTTPException: If batch update fails
    """
    try:
        # Update relations
        relations = []
        for update_data in updates_data:
            relation_id = update_data.pop("relation_id")
            relation = await db.update_relation(
                relation_id=relation_id,
                user_id=current_user.id,
                **update_data
            )
            relations.append(relation)
        
        return relations
        
    except Exception as e:
        handle_errors(e, "Failed to update relations in batch")
        raise HTTPException(status_code=500, detail="Failed to update relations in batch")

@router.post("/batch-delete", status_code=204)
async def batch_delete_relations(
    relation_ids: List[int],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete multiple relations in batch.
    
    Args:
        relation_ids: List of relation IDs to delete
        db: Database dependency
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If batch deletion fails
    """
    try:
        # Delete relations
        for relation_id in relation_ids:
            await db.delete_relation(
                relation_id=relation_id,
                user_id=current_user.id
            )
        
        return None
        
    except Exception as e:
        handle_errors(e, "Failed to delete relations in batch")
        raise HTTPException(status_code=500, detail="Failed to delete relations in batch")

@router.get("/export/{format}")
async def export_relations(
    format: str = Path(..., regex="^(json|csv|xml|pdf)$"),
    memory_id: Optional[int] = Query(None),
    context_id: Optional[int] = Query(None),
    relation_type: Optional[str] = Query(None),
    access_level: Optional[str] = Query(None, regex="^(public|user|privileged|admin)$"),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Export relations in various formats.
    
    Args:
        format: Export format (json, csv, xml, pdf)
        memory_id: Filter by memory ID
        context_id: Filter by context ID
        relation_type: Filter by relation type
        access_level: Filter by access level
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Exported data
        
    Raises:
        HTTPException: If export fails
    """
    try:
        # Get relations
        relations = await db.get_relations(
            memory_id=memory_id,
            context_id=context_id,
            relation_type=relation_type,
            access_level=access_level,
            user_id=current_user.id if current_user else None
        )
        
        # Export based on format
        if format == "json":
            return {"relations": [relation.dict() for relation in relations]}
        elif format == "csv":
            # TODO: Implement CSV export
            pass
        elif format == "xml":
            # TODO: Implement XML export
            pass
        elif format == "pdf":
            # TODO: Implement PDF export
            pass
        
        raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except Exception as e:
        handle_errors(e, "Failed to export relations")
        raise HTTPException(status_code=500, detail="Failed to export relations")