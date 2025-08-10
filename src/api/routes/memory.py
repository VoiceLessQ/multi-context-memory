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
from ...api.dependencies import get_enhanced_db
from ...utils.auth import get_current_user, get_optional_user
from ...utils.error_handling import handle_errors
from ...utils.text_processing import extract_keywords, generate_summary
from ...schemas.config import ChunkedStorageConfig, HybridStorageConfig
from ...storage.hybrid_storage import HybridStorage

router = APIRouter()

# Temporary stub for AI summarization - TODO: Implement actual AI summarization
async def ai_summarize_memory(content: str) -> str:
    """
    Temporary stub for AI-powered memory summarization.
    
    Args:
        content: Memory content to summarize
        
    Returns:
        Generated summary (currently falls back to basic text processing)
    """
    # For now, fall back to the basic summarization function
    return generate_summary(content)

@router.post("/", response_model=MemoryResponse, status_code=201)
async def create_memory(
    memory_data: MemoryCreate,
    use_compression: bool = True,
    use_chunked_storage: bool = False,
    use_hybrid_storage: bool = False,
    use_distributed_storage: bool = False,
    use_deduplication: bool = False,
    use_archival: bool = False,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new memory with optional storage optimizations.
    
    Args:
        memory_data: Memory data to create
        use_compression: Whether to compress the content
        use_chunked_storage: Whether to use chunked storage
        use_hybrid_storage: Whether to use hybrid storage
        use_distributed_storage: Whether to use distributed storage
        use_deduplication: Whether to use deduplication
        use_archival: Whether to use archival
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
            use_compression=use_compression,
            use_chunked_storage=use_chunked_storage,
            use_hybrid_storage=use_hybrid_storage,
            use_distributed_storage=use_distributed_storage,
            use_deduplication=use_deduplication,
            use_archival=use_archival,
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
    access_level: Optional[str] = Query(None, pattern="^(public|user|privileged|admin)$"),
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
    use_compression: bool = True,
    use_chunked_storage: bool = False,
    use_hybrid_storage: bool = False,
    use_distributed_storage: bool = False,
    use_deduplication: bool = False,
    use_archival: bool = False,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple memories in batch with optional storage optimizations.
    
    Args:
        memories_data: List of memory data to create
        use_compression: Whether to compress the content
        use_chunked_storage: Whether to use chunked storage
        use_hybrid_storage: Whether to use hybrid storage
        use_distributed_storage: Whether to use distributed storage
        use_deduplication: Whether to use deduplication
        use_archival: Whether to use archival
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
                use_compression=use_compression,
                use_chunked_storage=use_chunked_storage,
                use_hybrid_storage=use_hybrid_storage,
                use_distributed_storage=use_distributed_storage,
                use_deduplication=use_deduplication,
                use_archival=use_archival,
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
    format: str = Path(..., pattern="^(json|csv|xml|pdf)$"),
    context_id: Optional[int] = Query(None),
    access_level: Optional[str] = Query(None, pattern="^(public|user|privileged|admin)$"),
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

# Chunked Storage Management Endpoints

@router.get("/storage/chunked/status")
async def get_chunked_storage_status(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get the current status of chunked storage.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Chunked storage status
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        # Get chunked storage status
        status = db.get_chunked_storage_status()
        
        return status
        
    except Exception as e:
        handle_errors(e, "Failed to get chunked storage status")
        raise HTTPException(status_code=500, detail="Failed to get chunked storage status")

@router.post("/storage/chunked/enable")
async def enable_chunked_storage(
    config: ChunkedStorageConfig,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable chunked storage with configuration.
    
    Args:
        config: Chunked storage configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If enabling fails
    """
    try:
        # Set chunked storage configuration
        db.set_chunked_storage_enabled(True)
        db.set_chunk_size(config.chunk_size)
        db.set_max_chunks(config.max_chunks)
        
        return {"message": "Chunked storage enabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to enable chunked storage")
        raise HTTPException(status_code=500, detail="Failed to enable chunked storage")

@router.post("/storage/chunked/disable")
async def disable_chunked_storage(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable chunked storage.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If disabling fails
    """
    try:
        # Disable chunked storage
        db.set_chunked_storage_enabled(False)
        
        return {"message": "Chunked storage disabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to disable chunked storage")
        raise HTTPException(status_code=500, detail="Failed to disable chunked storage")

@router.put("/storage/chunked/config")
async def update_chunked_storage_config(
    config: ChunkedStorageConfig,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update chunked storage configuration.
    
    Args:
        config: Updated chunked storage configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Update chunked storage configuration
        db.set_chunk_size(config.chunk_size)
        db.set_max_chunks(config.max_chunks)
        
        return {"message": "Chunked storage configuration updated successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to update chunked storage configuration")
        raise HTTPException(status_code=500, detail="Failed to update chunked storage configuration")

@router.post("/storage/chunked/migrate/{memory_id}")
async def migrate_memory_to_chunks(
    memory_id: int = Path(..., gt=0),
    compress: bool = Query(True),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Migrate an existing memory to chunked storage.
    
    Args:
        memory_id: Memory ID to migrate
        compress: Whether to compress the content
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If migration fails
    """
    try:
        # Check if memory exists and user has permission
        memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Get full content
        if not hasattr(memory, '_content_loaded') or not memory._content_loaded:
            await db.load_full_content(memory)
        
        # Update memory with chunked storage
        success = await db.update_memory(
            memory_id=memory_id,
            content=memory.content,
            use_chunked_storage=True,
            compress_content=compress
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to migrate memory to chunks")
        
        return {"message": "Memory migrated to chunked storage successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to migrate memory to chunks")
        raise HTTPException(status_code=500, detail="Failed to migrate memory to chunks")

@router.get("/storage/chunked/info/{memory_id}")
async def get_chunked_memory_info(
    memory_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get information about a memory stored in chunks.
    
    Args:
        memory_id: Memory ID to get info for
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Chunked memory information
        
    Raises:
        HTTPException: If info retrieval fails
    """
    try:
        # Check if memory exists and user has permission
        memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id if current_user else None
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Get chunked storage info
        info = {
            "memory_id": memory_id,
            "title": memory.title,
            "content_size": memory.content_size,
            "content_compressed": memory.content_compressed,
            "chunked_storage_enabled": db.chunked_storage_enabled,
            "chunk_count": 0
        }
        
        # Get chunk count if using chunked storage
        if db.chunked_storage and db.chunked_storage_enabled:
            info["chunk_count"] = len(db.chunked_storage.get_memory_chunks(memory_id))
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to get chunked memory info")
        raise HTTPException(status_code=500, detail="Failed to get chunked memory info")

# Hybrid Storage Management Endpoints

@router.get("/storage/hybrid/status")
async def get_hybrid_storage_status(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get the current status of hybrid storage.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Hybrid storage status
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        # Get hybrid storage status
        status = db.get_hybrid_storage_status()
        
        return status
        
    except Exception as e:
        handle_errors(e, "Failed to get hybrid storage status")
        raise HTTPException(status_code=500, detail="Failed to get hybrid storage status")

@router.post("/storage/hybrid/enable")
async def enable_hybrid_storage(
    config: HybridStorageConfig,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable hybrid storage with configuration.
    
    Args:
        config: Hybrid storage configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If enabling fails
    """
    try:
        # Initialize hybrid storage
        hybrid_storage = HybridStorage(
            backends=config.backends,
            cache_size=config.cache_size,
            compression=config.compression,
            encryption=config.encryption
        )
        
        # Set hybrid storage in database
        db.set_hybrid_storage(hybrid_storage)
        
        return {"message": "Hybrid storage enabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to enable hybrid storage")
        raise HTTPException(status_code=500, detail="Failed to enable hybrid storage")

@router.post("/storage/hybrid/disable")
async def disable_hybrid_storage(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable hybrid storage.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If disabling fails
    """
    try:
        # Disable hybrid storage
        db.set_hybrid_storage(None)
        
        return {"message": "Hybrid storage disabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to disable hybrid storage")
        raise HTTPException(status_code=500, detail="Failed to disable hybrid storage")

@router.put("/storage/hybrid/config")
async def update_hybrid_storage_config(
    config: HybridStorageConfig,
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update hybrid storage configuration.
    
    Args:
        config: Updated hybrid storage configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If update fails
    """
    try:
        # Update hybrid storage configuration
        if db.hybrid_storage:
            db.hybrid_storage.update_config(
                backends=config.backends,
                cache_size=config.cache_size,
                compression=config.compression,
                encryption=config.encryption
            )
        
        return {"message": "Hybrid storage configuration updated successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to update hybrid storage configuration")
        raise HTTPException(status_code=500, detail="Failed to update hybrid storage configuration")

@router.post("/storage/hybrid/migrate/{memory_id}")
async def migrate_memory_to_hybrid(
    memory_id: int = Path(..., gt=0),
    backend: Optional[str] = Query(None),
    compress: bool = Query(True),
    encrypt: bool = Query(False),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Migrate an existing memory to hybrid storage.
    
    Args:
        memory_id: Memory ID to migrate
        backend: Specific backend to use (optional)
        compress: Whether to compress the content
        encrypt: Whether to encrypt the content
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If migration fails
    """
    try:
        # Check if memory exists and user has permission
        memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Get full content
        if not hasattr(memory, '_content_loaded') or not memory._content_loaded:
            await db.load_full_content(memory)
        
        # Update memory with hybrid storage
        success = await db.update_memory(
            memory_id=memory_id,
            content=memory.content,
            use_hybrid_storage=True,
            hybrid_backend=backend,
            compress_content=compress,
            encrypt_content=encrypt
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to migrate memory to hybrid storage")
        
        return {"message": "Memory migrated to hybrid storage successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to migrate memory to hybrid storage")
        raise HTTPException(status_code=500, detail="Failed to migrate memory to hybrid storage")

@router.get("/storage/hybrid/info/{memory_id}")
async def get_hybrid_memory_info(
    memory_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get information about a memory stored in hybrid storage.
    
    Args:
        memory_id: Memory ID to get info for
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Hybrid memory information
        
    Raises:
        HTTPException: If info retrieval fails
    """
    try:
        # Check if memory exists and user has permission
        memory = await db.get_memory(
            memory_id=memory_id,
            user_id=current_user.id if current_user else None
        )
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        # Get hybrid storage info
        info = {
            "memory_id": memory_id,
            "title": memory.title,
            "content_size": memory.content_size,
            "content_compressed": memory.content_compressed,
            "hybrid_storage_enabled": db.hybrid_storage is not None,
            "backend": memory.hybrid_backend,
            "encrypted": memory.content_encrypted
        }
        
        # Get backend info if using hybrid storage
        if db.hybrid_storage:
            backend_info = db.hybrid_storage.get_backend_info(memory.hybrid_backend)
            info.update(backend_info)
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to get hybrid memory info")
        raise HTTPException(status_code=500, detail="Failed to get hybrid memory info")

@router.get("/storage/hybrid/backends")
async def get_hybrid_storage_backends(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get information about available hybrid storage backends.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of available backends
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get available backends
        backends = db.hybrid_storage.get_backends() if db.hybrid_storage else {}
        
        return backends
        
    except Exception as e:
        handle_errors(e, "Failed to get hybrid storage backends")
        raise HTTPException(status_code=500, detail="Failed to get hybrid storage backends")

@router.post("/storage/hybrid/health-check")
async def run_hybrid_storage_health_check(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run a health check on hybrid storage backends.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Health check results
        
    Raises:
        HTTPException: If health check fails
    """
    try:
        # Run health check
        if not db.hybrid_storage:
            raise HTTPException(status_code=400, detail="Hybrid storage is not enabled")
        
        results = await db.hybrid_storage.health_check()
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to run hybrid storage health check")
        raise HTTPException(status_code=500, detail="Failed to run hybrid storage health check")

# Deduplication Management Endpoints

@router.get("/deduplication/status")
async def get_deduplication_status(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get the current status of deduplication.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Deduplication status
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        # Get deduplication status
        status = db.get_deduplication_status()
        
        return status
        
    except Exception as e:
        handle_errors(e, "Failed to get deduplication status")
        raise HTTPException(status_code=500, detail="Failed to get deduplication status")

@router.post("/deduplication/enable")
async def enable_deduplication(
    config: Optional[Dict[str, Any]] = Body(None),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable deduplication with configuration.
    
    Args:
        config: Deduplication configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If enabling fails
    """
    try:
        # Enable deduplication
        db.set_deduplication_enabled(True)
        if config:
            db.set_deduplication_config(config)
        
        return {"message": "Deduplication enabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to enable deduplication")
        raise HTTPException(status_code=500, detail="Failed to enable deduplication")

@router.post("/deduplication/disable")
async def disable_deduplication(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable deduplication.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If disabling fails
    """
    try:
        # Disable deduplication
        db.set_deduplication_enabled(False)
        
        return {"message": "Deduplication disabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to disable deduplication")
        raise HTTPException(status_code=500, detail="Failed to disable deduplication")

@router.get("/deduplication/stats")
async def get_deduplication_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get deduplication statistics.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Deduplication statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get deduplication statistics
        stats = db.get_deduplication_stats()
        
        return stats
        
    except Exception as e:
        handle_errors(e, "Failed to get deduplication statistics")
        raise HTTPException(status_code=500, detail="Failed to get deduplication statistics")

@router.post("/deduplication/find-duplicates")
async def find_duplicate_memories(
    threshold: float = Query(0.9, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Find duplicate memories.
    
    Args:
        threshold: Similarity threshold for duplicates
        limit: Maximum number of duplicates to return
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of duplicate memory groups
        
    Raises:
        HTTPException: If duplicate search fails
    """
    try:
        # Find duplicates
        duplicates = await db.find_duplicate_memories(
            threshold=threshold,
            limit=limit,
            user_id=current_user.id if current_user else None
        )
        
        return {"duplicates": duplicates}
        
    except Exception as e:
        handle_errors(e, "Failed to find duplicate memories")
        raise HTTPException(status_code=500, detail="Failed to find duplicate memories")

@router.post("/deduplication/merge/{memory_id}")
async def merge_duplicate_memories(
    memory_id: int = Path(..., gt=0),
    duplicate_ids: List[int] = Body(...),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Merge duplicate memories.
    
    Args:
        memory_id: Primary memory ID to merge into
        duplicate_ids: List of duplicate memory IDs to merge
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If merge fails
    """
    try:
        # Merge duplicates
        success = await db.merge_duplicate_memories(
            primary_id=memory_id,
            duplicate_ids=duplicate_ids,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to merge duplicate memories")
        
        return {"message": "Duplicate memories merged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to merge duplicate memories")
        raise HTTPException(status_code=500, detail="Failed to merge duplicate memories")

# Archival Management Endpoints

@router.get("/archival/status")
async def get_archival_status(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get the current status of archival.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Archival status
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        # Get archival status
        status = db.get_archival_status()
        
        return status
        
    except Exception as e:
        handle_errors(e, "Failed to get archival status")
        raise HTTPException(status_code=500, detail="Failed to get archival status")

@router.post("/archival/enable")
async def enable_archival(
    config: Optional[Dict[str, Any]] = Body(None),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable archival with configuration.
    
    Args:
        config: Archival configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If enabling fails
    """
    try:
        # Enable archival
        db.set_archival_enabled(True)
        if config:
            db.set_archival_config(config)
        
        return {"message": "Archival enabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to enable archival")
        raise HTTPException(status_code=500, detail="Failed to enable archival")

@router.post("/archival/disable")
async def disable_archival(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable archival.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If disabling fails
    """
    try:
        # Disable archival
        db.set_archival_enabled(False)
        
        return {"message": "Archival disabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to disable archival")
        raise HTTPException(status_code=500, detail="Failed to disable archival")

@router.get("/archival/stats")
async def get_archival_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get archival statistics.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Archival statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get archival statistics
        stats = db.get_archival_stats()
        
        return stats
        
    except Exception as e:
        handle_errors(e, "Failed to get archival statistics")
        raise HTTPException(status_code=500, detail="Failed to get archival statistics")

@router.post("/archival/archive/{memory_id}")
async def archive_memory(
    memory_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Archive a memory.
    
    Args:
        memory_id: Memory ID to archive
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If archival fails
    """
    try:
        # Archive memory
        success = await db.archive_memory(
            memory_id=memory_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to archive memory")
        
        return {"message": "Memory archived successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to archive memory")
        raise HTTPException(status_code=500, detail="Failed to archive memory")

@router.post("/archival/restore/{memory_id}")
async def restore_memory(
    memory_id: int = Path(..., gt=0),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a memory from archival.
    
    Args:
        memory_id: Memory ID to restore
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If restoration fails
    """
    try:
        # Restore memory
        success = await db.restore_memory(
            memory_id=memory_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to restore memory")
        
        return {"message": "Memory restored successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to restore memory")
        raise HTTPException(status_code=500, detail="Failed to restore memory")

@router.get("/archived-memories")
async def get_archived_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get archived memories.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of archived memories
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get archived memories
        memories = await db.get_archived_memories(
            skip=skip,
            limit=limit,
            user_id=current_user.id if current_user else None
        )
        
        return memories
        
    except Exception as e:
        handle_errors(e, "Failed to get archived memories")
        raise HTTPException(status_code=500, detail="Failed to get archived memories")

# Distributed Storage Management Endpoints

@router.get("/distributed-storage/status")
async def get_distributed_storage_status(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get the current status of distributed storage.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Distributed storage status
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        # Get distributed storage status
        status = db.get_distributed_storage_status()
        
        return status
        
    except Exception as e:
        handle_errors(e, "Failed to get distributed storage status")
        raise HTTPException(status_code=500, detail="Failed to get distributed storage status")

@router.post("/distributed-storage/enable")
async def enable_distributed_storage(
    config: Optional[Dict[str, Any]] = Body(None),
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable distributed storage with configuration.
    
    Args:
        config: Distributed storage configuration
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If enabling fails
    """
    try:
        # Enable distributed storage
        db.set_distributed_storage_enabled(True)
        if config:
            db.set_distributed_storage_config(config)
        
        return {"message": "Distributed storage enabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to enable distributed storage")
        raise HTTPException(status_code=500, detail="Failed to enable distributed storage")

@router.post("/distributed-storage/disable")
async def disable_distributed_storage(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable distributed storage.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If disabling fails
    """
    try:
        # Disable distributed storage
        db.set_distributed_storage_enabled(False)
        
        return {"message": "Distributed storage disabled successfully"}
        
    except Exception as e:
        handle_errors(e, "Failed to disable distributed storage")
        raise HTTPException(status_code=500, detail="Failed to disable distributed storage")

@router.get("/distributed-storage/stats")
async def get_distributed_storage_stats(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get distributed storage statistics.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        Distributed storage statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get distributed storage statistics
        stats = db.get_distributed_storage_stats()
        
        return stats
        
    except Exception as e:
        handle_errors(e, "Failed to get distributed storage statistics")
        raise HTTPException(status_code=500, detail="Failed to get distributed storage statistics")

@router.get("/distributed-storage/nodes")
async def get_distributed_storage_nodes(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get distributed storage nodes.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user (optional)
        
    Returns:
        List of distributed storage nodes
        
    Raises:
        HTTPException: If node retrieval fails
    """
    try:
        # Get distributed storage nodes
        nodes = db.get_distributed_storage_nodes()
        
        return nodes
        
    except Exception as e:
        handle_errors(e, "Failed to get distributed storage nodes")
        raise HTTPException(status_code=500, detail="Failed to get distributed storage nodes")

@router.post("/distributed-storage/health-check")
async def run_distributed_storage_health_check(
    db: EnhancedMemoryDB = Depends(get_enhanced_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run a health check on distributed storage nodes.
    
    Args:
        db: Database dependency
        current_user: Current authenticated user
        
    Returns:
        Health check results
        
    Raises:
        HTTPException: If health check fails
    """
    try:
        # Run health check
        if not db.distributed_storage:
            raise HTTPException(status_code=400, detail="Distributed storage is not enabled")
        
        results = await db.distributed_storage.health_check()
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        handle_errors(e, "Failed to run distributed storage health check")
        raise HTTPException(status_code=500, detail="Failed to run distributed storage health check")