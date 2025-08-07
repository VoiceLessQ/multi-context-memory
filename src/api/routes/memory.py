"""
API routes for memory operations in the enhanced MCP Multi-Context Memory System.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import UUID4

from ...database.models import Memory, Context, User
from ...database.enhanced_memory_db import EnhancedMemoryDB
from ...schemas.memory import (
    MemoryCreate, MemoryUpdate, MemoryResponse, MemoryStats,
    MemorySearch, MemorySearchResponse, MemorySummary, MemorySummaryResponse
)
from ...schemas.auth import TokenData
from ...utils.auth import get_current_user, get_optional_user
from ...utils.error_handling import handle_errors
from ...utils.text_processing import extract_keywords, generate_summary
from ...utils.ai import ai_summarize_memory

router = APIRouter()

@router.post("/", response_model=MemoryResponse, status_code=201)
async def create_memory(
    memory_data: MemoryCreate,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new memory.
    
    Args:
        memory_data: Memory data to create
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Created memory
        
    Raises:
        HTTPException: If memory creation fails
    """
    try:
        # Create memory
        memory = await db.create_memory(
            user_id=current_user.id,
            **memory_data.dict()
        )
        
        # Trigger background tasks
        # TODO: Add background tasks for relation discovery, summarization, etc.
        
        return memory
        
    except Exception as e:
        handle_errors(e, "Failed to create memory")
        raise HTTPException(status_code=500, detail="Failed to create memory")

@router.get("/", response_model=List[MemoryResponse])
async def get_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    context_id: Optional[int] = Query(None),
    access_level: Optional[str] = Query(None, regex="^(public|user|privileged|admin)$"),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get memories with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        context_id: Filter by context ID
        access_level: Filter by access level
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of memories
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get memories
        memories = await db.get_memories(
            skip=skip,
            limit=limit,
            context_id=context_id,
            access_level=access_level,
            user_id=current_user.id if current_user else None
        )
        
        return memories
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve memories")
        raise HTTPException(status_code=500, detail="Failed to retrieve memories")

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a specific memory by ID.
    
    Args:
        memory_id: Memory ID to retrieve
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Memory details
        
    Raises:
        HTTPException: If memory not found or retrieval fails
    """
    try:
        # Get memory
        memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id if current_user else None
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return memory
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to retrieve memory")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory")

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int = Path(..., gt=0),
    memory_data: MemoryUpdate = Body(...),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing memory.
    
    Args:
        memory_id: Memory ID to update
        memory_data: Updated memory data
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Updated memory
        
    Raises:
        HTTPException: If memory not found or update fails
    """
    try:
        # Check if memory exists and user has permission
        existing_memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id
        )
        
        if not existing_memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Update memory
        memory = await db.update_memory(
            memory_id=memory_id,
            user_id=current_user.id,
            **memory_data.dict(exclude_unset=True)
        )
        
        return memory
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to update memory")
        raise HTTPException(status_code=500, detail="Failed to update memory")

@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a memory.
    
    Args:
        memory_id: Memory ID to delete
        db: Database dependency
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If memory not found or deletion fails
    """
    try:
        # Check if memory exists and user has permission
        existing_memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id
        )
        
        if not existing_memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Delete memory
        await db.delete_memory(
            memory_id=memory_id,
            user_id=current_user.id
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to delete memory")
        raise HTTPException(status_code=500, detail="Failed to delete memory")

@router.get("/stats/summary", response_model=MemoryStats)
async def get_memory_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get memory statistics.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Memory statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get statistics
        stats = await db.get_memory_stats(
            user_id=current_user.id if current_user else None
        )
        
        return stats
        
    except Exception as e:
        handle_errors(e, "Failed to retrieve memory statistics")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory statistics")

@router.post("/search", response_model=List[MemorySearchResponse])
async def search_memories(
    search_data: MemorySearch,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Search memories using various criteria.
    
    Args:
        search_data: Search parameters
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of matching memories
        
    Raises:
        HTTPException: If search fails
    """
    try:
        # Search memories
        memories = await db.search_memories(
            query=search_data.query,
            filters=search_data.filters,
            user_id=current_user.id if current_user else None
        )
        
        return memories
        
    except Exception as e:
        handle_errors(e, "Failed to search memories")
        raise HTTPException(status_code=500, detail="Failed to search memories")

@router.post("/summarize/{memory_id}", response_model=MemorySummaryResponse)
async def summarize_memory(
    memory_id: int = Path(..., gt=0),
    use_ai: bool = Query(False),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Generate a summary for a memory.
    
    Args:
        memory_id: Memory ID to summarize
        use_ai: Whether to use AI for summarization
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Memory summary
        
    Raises:
        HTTPException: If memory not found or summarization fails
    """
    try:
        # Check if memory exists and user has permission
        memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id if current_user else None
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Generate summary
        if use_ai:
            summary = await ai_summarize_memory(memory.content)
        else:
            summary = generate_summary(memory.content)
        
        # Update memory with summary
        updated_memory = await db.update_memory(
            memory_id=memory_id,
            user_id=current_user.id if current_user else None,
            summary=summary
        )
        
        return MemorySummaryResponse(
            memory_id=memory_id,
            summary=summary,
            generated_at=updated_memory.updated_at,
            method="ai" if use_ai else "extractive"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to summarize memory")
        raise HTTPException(status_code=500, detail="Failed to summarize memory")

@router.post("/extract-keywords/{memory_id}")
async def extract_memory_keywords(
    memory_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Extract keywords from a memory.
    
    Args:
        memory_id: Memory ID to extract keywords from
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of keywords
        
    Raises:
        HTTPException: If memory not found or keyword extraction fails
    """
    try:
        # Check if memory exists and user has permission
        memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id if current_user else None
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Extract keywords
        keywords = extract_keywords(memory.content)
        
        # Update memory with keywords
        await db.update_memory(
            memory_id=memory_id,
            user_id=current_user.id if current_user else None,
            keywords=keywords
        )
        
        return {"memory_id": memory_id, "keywords": keywords}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to extract keywords")
        raise HTTPException(status_code=500, detail="Failed to extract keywords")

@router.post("/batch-create", response_model=List[MemoryResponse], status_code=201)
async def batch_create_memories(
    memories_data: List[MemoryCreate],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple memories in batch.
    
    Args:
        memories_data: List of memory data to create
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        List of created memories
        
    Raises:
        HTTPException: If batch creation fails
    """
    try:
        # Create memories
        memories = []
        for memory_data in memories_data:
            memory = await db.create_memory(
                user_id=current_user.id,
                **memory_data.dict()
            )
            memories.append(memory)
        
        # Trigger background tasks
        # TODO: Add background tasks for relation discovery, summarization, etc.
        
        return memories
        
    except Exception as e:
        handle_errors(e, "Failed to create memories in batch")
        raise HTTPException(status_code=500, detail="Failed to create memories in batch")

@router.post("/batch-update", response_model=List[MemoryResponse])
async def batch_update_memories(
    updates_data: List[Dict[str, Any]],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update multiple memories in batch.
    
    Args:
        updates_data: List of update data with memory_id and fields to update
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        List of updated memories
        
    Raises:
        HTTPException: If batch update fails
    """
    try:
        # Update memories
        memories = []
        for update_data in updates_data:
            memory_id = update_data.pop("memory_id")
            memory = await db.update_memory(
                memory_id=memory_id,
                user_id=current_user.id,
                **update_data
            )
            memories.append(memory)
        
        return memories
        
    except Exception as e:
        handle_errors(e, "Failed to update memories in batch")
        raise HTTPException(status_code=500, detail="Failed to update memories in batch")

@router.post("/batch-delete", status_code=204)
async def batch_delete_memories(
    memory_ids: List[int],
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete multiple memories in batch.
    
    Args:
        memory_ids: List of memory IDs to delete
        db: Database dependency
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If batch deletion fails
    """
    try:
        # Delete memories
        for memory_id in memory_ids:
            await db.delete_memory(
                memory_id=memory_id,
                user_id=current_user.id
            )
        
        return None
        
    except Exception as e:
        handle_errors(e, "Failed to delete memories in batch")
        raise HTTPException(status_code=500, detail="Failed to delete memories in batch")

@router.get("/export/{format}")
async def export_memories(
    format: str = Path(..., regex="^(json|csv|xml|pdf)$"),
    context_id: Optional[int] = Query(None),
    access_level: Optional[str] = Query(None, regex="^(public|user|privileged|admin)$"),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Export memories in various formats.
    
    Args:
        format: Export format (json, csv, xml, pdf)
        context_id: Filter by context ID
        access_level: Filter by access level
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Exported data
        
    Raises:
        HTTPException: If export fails
    """
    try:
        # Get memories
        memories = await db.get_memories(
            context_id=context_id,
            access_level=access_level,
            user_id=current_user.id if current_user else None
        )
        
        # Export based on format
        if format == "json":
            return {"memories": [memory.dict() for memory in memories]}
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
        handle_errors(e, "Failed to export memories")
        raise HTTPException(status_code=500, detail="Failed to export memories")