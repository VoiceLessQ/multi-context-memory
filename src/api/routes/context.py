"""
API routes for context operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from pydantic import UUID4

from ...database.models import Context, User, Memory
from ...database.enhanced_memory_db import EnhancedMemoryDB
from ...schemas.context import (
    ContextCreate, ContextUpdate, ContextResponse, ContextStats,
    ContextSearch, ContextSearchResponse, ContextHierarchy
)
from ...schemas.auth import TokenData
from ...utils.auth import get_current_user, get_optional_user
from ...utils.error_handling import handle_errors

router = APIRouter()

@router.post("/", response_model=ContextResponse, status_code=201)
async def create_context(
    context_data: ContextCreate,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new context.
    
    Args:
        context_data: Context data to create
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Created context
        
    Raises:
        HTTPException: If context creation fails
    """
    try:
        # Create context
        context = await db.create_context(
            user_id=current_user.id,
            **context_data.dict()
        )
        
        return context
        
    except Exception as e:
        handle_errors(e, "Failed to create context")
        raise HTTPException(status_code=500, detail="Failed to create context")

@router.get("/", response_model=List[ContextResponse])
async def get_contexts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    parent_id: Optional[int] = Query(None),
    access_level: Optional[str] = Query(None, regex="^(public|user|privileged|admin)$"),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get contexts with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        parent_id: Filter by parent context ID
        access_level: Filter by access level
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of contexts
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get contexts
        contexts = await db.get_contexts(
            skip=skip,
            limit=limit,
            parent_id=parent_id,
            access_level=access_level,
            user_id=current_user.id if current_user else None
        )
        
        return contexts
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve contexts")
        raise HTTPException(status_code=500, detail="Failed to retrieve contexts")

@router.get("/{context_id}", response_model=ContextResponse)
async def get_context(
    context_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a specific context by ID.
    
    Args:
        context_id: Context ID to retrieve
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Context details
        
    Raises:
        HTTPException: If context not found or retrieval fails
    """
    try:
        # Get context
        context = await db.get_context(
            context_id=context_id,
            user_id=current_user.id if current_user else None
        )
        
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve context")
        raise HTTPException(status_code=500, detail="Failed to retrieve context")

@router.put("/{context_id}", response_model=ContextResponse)
async def update_context(
    context_id: int = Path(..., gt=0),
    context_data: ContextUpdate = Body(...),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing context.
    
    Args:
        context_id: Context ID to update
        context_data: Updated context data
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated context
        
    Raises:
        HTTPException: If context not found or update fails
    """
    try:
        # Check if context exists and user has permission
        existing_context = await db.get_context(
            context_id=context_id,
            user_id=current_user.id
        )
        
        if not existing_context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        # Update context
        context = await db.update_context(
            context_id=context_id,
            user_id=current_user.id,
            **context_data.dict(exclude_unset=True)
        )
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update context")
        raise HTTPException(status_code=500, detail="Failed to update context")

@router.delete("/{context_id}", status_code=204)
async def delete_context(
    context_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a context.
    
    Args:
        context_id: Context ID to delete
        db: Database dependency
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If context not found or deletion fails
    """
    try:
        # Check if context exists and user has permission
        existing_context = await db.get_context(
            context_id=context_id,
            user_id=current_user.id
        )
        
        if not existing_context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        # Delete context
        await db.delete_context(
            context_id=context_id,
            user_id=current_user.id
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to delete context")
        raise HTTPException(status_code=500, detail="Failed to delete context")

@router.get("/stats/summary", response_model=ContextStats)
async def get_context_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get context statistics.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Context statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get statistics
        stats = await db.get_context_stats(
            user_id=current_user.id if current_user else None
        )
        
        return stats
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve context statistics")
        raise HTTPException(status_code=500, detail="Failed to retrieve context statistics")

@router.post("/search", response_model=List[ContextSearchResponse])
async def search_contexts(
    search_data: ContextSearch,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Search contexts using various criteria.
    
    Args:
        search_data: Search parameters
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of matching contexts
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Search contexts
        contexts = await db.search_contexts(
            query=search_data.query,
            filters=search_data.filters,
            user_id=current_user.id if current_user else None
        )
        
        return contexts
        
    except Exception as e:
        handle_errors(e, "Failed to search contexts")
        raise HTTPException(status_code=500, detail="Failed to search contexts")

@router.get("/hierarchy/tree", response_model=List[ContextHierarchy])
async def get_context_hierarchy(
    root_id: Optional[int] = Query(None),
    max_depth: int = Query(5, ge=1, le=10),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get context hierarchy as a tree structure.
    
    Args:
        root_id: Root context ID (optional, defaults to user's root contexts)
        max_depth: Maximum depth of hierarchy to retrieve
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of context hierarchy nodes
        
    Raises:
        HTTPException: If hierarchy retrieval fails
    """
    try:
        # Get hierarchy
        hierarchy = await db.get_context_hierarchy(
            root_id=root_id,
            max_depth=max_depth,
            user_id=current_user.id if current_user else None
        )
        
        return hierarchy
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve context hierarchy")
        raise HTTPException(status_code=500, detail="Failed to retrieve context hierarchy")

@router.get("/{context_id}/children", response_model=List[ContextResponse])
async def get_context_children(
    context_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get child contexts of a specific context.
    
    Args:
        context_id: Parent context ID
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of child contexts
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get child contexts
        children = await db.get_context_children(
            context_id=context_id,
            user_id=current_user.id if current_user else None
        )
        
        return children
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve child contexts")
        raise HTTPException(status_code=500, detail="Failed to retrieve child contexts")

@router.get("/{context_id}/memories", response_model=List[Dict[str, Any]])
async def get_context_memories(
    context_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get memories associated with a specific context.
    
    Args:
        context_id: Context ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of memories in the context
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get context memories
        memories = await db.get_context_memories(
            context_id=context_id,
            skip=skip,
            limit=limit,
            user_id=current_user.id if current_user else None
        )
        
        return memories
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve context memories")
        raise HTTPException(status_code=500, detail="Failed to retrieve context memories")

@router.post("/{context_id}/move", response_model=ContextResponse)
async def move_context(
    context_id: int = Path(..., gt=0),
    new_parent_id: Optional[int] = Body(None),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Move a context to a new parent.
    
    Args:
        context_id: Context ID to move
        new_parent_id: New parent context ID (optional for root)
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated context
        
    Raises:
        HTTPException: If move fails
    """
    try:
        # Check if context exists and user has permission
        existing_context = await db.get_context(
            context_id=context_id,
            user_id=current_user.id
        )
        
        if not existing_context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        # Move context
        context = await db.move_context(
            context_id=context_id,
            new_parent_id=new_parent_id,
            user_id=current_user.id
        )
        
        return context
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to move context")
        raise HTTPException(status_code=500, detail="Failed to move context")

@router.post("/batch-create", response_model=List[ContextResponse], status_code=201)
async def batch_create_contexts(
    contexts_data: List[ContextCreate],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple contexts in batch.
    
    Args:
        contexts_data: List of context data to create
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        List of created contexts
        
    Raises:
        HTTPException: If batch creation fails
    """
    try:
        # Create contexts
        contexts = []
        for context_data in contexts_data:
            context = await db.create_context(
                user_id=current_user.id,
                **context_data.dict()
            )
            contexts.append(context)
        
        return contexts
        
    except Exception as e:
        handle_errors(e, "Failed to create contexts in batch")
        raise HTTPException(status_code=500, detail="Failed to create contexts in batch")

@router.post("/batch-update", response_model=List[ContextResponse])
async def batch_update_contexts(
    updates_data: List[Dict[str, Any]],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update multiple contexts in batch.
    
    Args:
        updates_data: List of update data with context_id and fields to update
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        List of updated contexts
        
    Raises:
        HTTPException: If batch update fails
    """
    try:
        # Update contexts
        contexts = []
        for update_data in updates_data:
            context_id = update_data.pop("context_id")
            context = await db.update_context(
                context_id=context_id,
                user_id=current_user.id,
                **update_data
            )
            contexts.append(context)
        
        return contexts
        
    except Exception as e:
        handle_errors(e, "Failed to update contexts in batch")
        raise HTTPException(status_code=500, detail="Failed to update contexts in batch")

@router.post("/batch-delete", status_code=204)
async def batch_delete_contexts(
    context_ids: List[int],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete multiple contexts in batch.
    
    Args:
        context_ids: List of context IDs to delete
        db: Database dependency
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If batch deletion fails
    """
    try:
        # Delete contexts
        for context_id in context_ids:
            await db.delete_context(
                context_id=context_id,
                user_id=current_user.id
            )
        
        return None
        
    except Exception as e:
        handle_errors(e, "Failed to delete contexts in batch")
        raise HTTPException(status_code=500, detail="Failed to delete contexts in batch")

@router.get("/export/{format}")
async def export_contexts(
    format: str = Path(..., regex="^(json|csv|xml|pdf)$"),
    parent_id: Optional[int] = Query(None),
    access_level: Optional[str] = Query(None, regex="^(public|user|privileged|admin)$"),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Export contexts in various formats.
    
    Args:
        format: Export format (json, csv, xml, pdf)
        parent_id: Filter by parent context ID
        access_level: Filter by access level
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Exported data
        
    Raises:
        HTTPException: If export fails
    """
    try:
        # Get contexts
        contexts = await db.get_contexts(
            parent_id=parent_id,
            access_level=access_level,
            user_id=current_user.id if current_user else None
        )
        
        # Export based on format
        if format == "json":
            return {"contexts": [context.dict() for context in contexts]}
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
        handle_errors(e, "Failed to export contexts")
        raise HTTPException(status_code=500, detail="Failed to export contexts")