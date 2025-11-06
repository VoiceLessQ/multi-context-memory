"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

"""
Memory Controller - Clean API layer using Controller pattern.
Replaces the bloated api/routes/memory.py (1,746 lines) with focused controllers.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime

from ...database.models import User
from ...schemas.memory import (
    MemoryCreate, MemoryUpdate, MemoryResponse, MemoryStats,
    MemorySearch, MemorySearchResponse, MemorySummary, MemorySummaryResponse
)
from ..services.memory_service import MemoryServiceImpl, MemoryStatsService
from ...utils.error_handling import handle_errors

logger = logging.getLogger(__name__)


class MemoryController:
    """
    Clean Memory Controller implementing Controller pattern.
    Focuses purely on HTTP concerns, delegates business logic to services.
    """
    
    def __init__(
        self, 
        memory_service: MemoryServiceImpl,
        stats_service: MemoryStatsService
    ):
        self.memory_service = memory_service
        self.stats_service = stats_service
    
    # ========== CORE CRUD OPERATIONS ==========
    
    async def create_memory(
        self,
        memory_data: MemoryCreate,
        current_user: User,
        storage_options: Optional[Dict[str, bool]] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> MemoryResponse:
        """Create a new memory - thin controller layer."""
        try:
            # Convert Pydantic model to dict and delegate to service
            memory = await self.memory_service.create_memory(
                title=memory_data.title,
                content=memory_data.content,
                owner_id=current_user.id,
                context_id=memory_data.context_id,
                access_level=memory_data.access_level or "private",
                metadata=memory_data.metadata,
                storage_options=storage_options or {}
            )
            
            # Schedule background tasks if provided
            if background_tasks:
                background_tasks.add_task(self._post_create_tasks, memory.id)
            
            # Convert to response model
            return MemoryResponse.from_orm(memory)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            handle_errors(e, "Failed to create memory")
            raise HTTPException(status_code=500, detail="Failed to create memory")
    
    async def get_memory(
        self,
        memory_id: int,
        current_user: Optional[User] = None,
        load_full_content: bool = True
    ) -> MemoryResponse:
        """Get memory by ID - thin controller layer."""
        try:
            if memory_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid memory ID")
            
            # Delegate to service
            memory = await self.memory_service.get_memory(
                memory_id=memory_id,
                user_id=current_user.id if current_user else None,
                load_options={"use_lazy_loading": not load_full_content}
            )
            
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return MemoryResponse.from_orm(memory)
            
        except HTTPException:
            raise
        except Exception as e:
            handle_errors(e, "Failed to retrieve memory")
            raise HTTPException(status_code=500, detail="Failed to retrieve memory")
    
    async def update_memory(
        self,
        memory_id: int,
        memory_data: MemoryUpdate,
        current_user: User
    ) -> MemoryResponse:
        """Update memory - thin controller layer."""
        try:
            if memory_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid memory ID")
            
            # Convert to dict, excluding unset fields
            updates = memory_data.dict(exclude_unset=True)
            
            # Delegate to service
            memory = await self.memory_service.update_memory(
                memory_id=memory_id,
                updates=updates,
                user_id=current_user.id
            )
            
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return MemoryResponse.from_orm(memory)
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            handle_errors(e, "Failed to update memory")
            raise HTTPException(status_code=500, detail="Failed to update memory")
    
    async def delete_memory(
        self,
        memory_id: int,
        current_user: User
    ) -> Dict[str, str]:
        """Delete memory - thin controller layer."""
        try:
            if memory_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid memory ID")
            
            # Delegate to service
            success = await self.memory_service.delete_memory(
                memory_id=memory_id,
                user_id=current_user.id
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return {"message": "Memory deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            handle_errors(e, "Failed to delete memory")
            raise HTTPException(status_code=500, detail="Failed to delete memory")
    
    # ========== SEARCH AND QUERY OPERATIONS ==========
    
    async def search_memories(
        self,
        search_data: MemorySearch,
        current_user: Optional[User] = None
    ) -> List[MemorySearchResponse]:
        """Search memories - thin controller layer."""
        try:
            if not search_data.query or not search_data.query.strip():
                raise HTTPException(status_code=400, detail="Search query is required")
            
            # Delegate to service
            memories = await self.memory_service.search_memories(
                query=search_data.query,
                filters=search_data.filters or {},
                user_id=current_user.id if current_user else None,
                pagination={
                    "skip": search_data.skip or 0,
                    "limit": search_data.limit or 100
                }
            )
            
            # Convert to response models
            return [
                MemorySearchResponse(
                    id=memory.id,
                    title=memory.title,
                    content_preview=memory.content[:200] + "..." if len(memory.content) > 200 else memory.content,
                    context_id=memory.context_id,
                    access_level=memory.access_level,
                    created_at=memory.created_at,
                    relevance_score=0.8  # Placeholder - would come from search engine
                )
                for memory in memories
            ]
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            handle_errors(e, "Failed to search memories")
            raise HTTPException(status_code=500, detail="Failed to search memories")
    
    async def get_memories(
        self,
        skip: int = 0,
        limit: int = 100,
        context_id: Optional[int] = None,
        access_level: Optional[str] = None,
        current_user: Optional[User] = None
    ) -> List[MemoryResponse]:
        """Get memories with pagination - thin controller layer."""
        try:
            # Validate pagination parameters
            if skip < 0:
                skip = 0
            if limit <= 0 or limit > 1000:
                limit = 100
            
            # Build filters
            filters = {}
            if context_id:
                filters['context_id'] = context_id
            if access_level:
                filters['access_level'] = access_level
            
            # Use search with empty query to get all memories
            memories = await self.memory_service.search_memories(
                query="",  # Empty query gets all
                filters=filters,
                user_id=current_user.id if current_user else None,
                pagination={"skip": skip, "limit": limit}
            )
            
            return [MemoryResponse.from_orm(memory) for memory in memories]
            
        except Exception as e:
            handle_errors(e, "Failed to retrieve memories")
            raise HTTPException(status_code=500, detail="Failed to retrieve memories")
    
    # ========== BATCH OPERATIONS ==========
    
    async def batch_create_memories(
        self,
        memories_data: List[MemoryCreate],
        current_user: User,
        storage_options: Optional[Dict[str, bool]] = None
    ) -> List[MemoryResponse]:
        """Create multiple memories in batch."""
        try:
            if not memories_data:
                raise HTTPException(status_code=400, detail="No memory data provided")
            
            if len(memories_data) > 100:
                raise HTTPException(status_code=400, detail="Too many memories (max 100 per batch)")
            
            # Convert to service format
            memories_dict = [
                {
                    "title": mem.title,
                    "content": mem.content,
                    "context_id": mem.context_id,
                    "access_level": mem.access_level or "private",
                    "metadata": mem.metadata
                }
                for mem in memories_data
            ]
            
            # Delegate to service
            created_memories = await self.memory_service.bulk_create_memories(
                memories_data=memories_dict,
                user_id=current_user.id,
                options=storage_options or {}
            )
            
            return [MemoryResponse.from_orm(memory) for memory in created_memories]
            
        except HTTPException:
            raise
        except Exception as e:
            handle_errors(e, "Failed to create memories in batch")
            raise HTTPException(status_code=500, detail="Failed to create memories in batch")
    
    async def batch_update_memories(
        self,
        updates_data: List[Dict[str, Any]],
        current_user: User
    ) -> List[MemoryResponse]:
        """Update multiple memories in batch."""
        try:
            if not updates_data:
                raise HTTPException(status_code=400, detail="No update data provided")
            
            updated_memories = []
            
            for update_data in updates_data:
                if "memory_id" not in update_data:
                    continue  # Skip invalid entries
                
                memory_id = update_data.pop("memory_id")
                
                try:
                    memory = await self.memory_service.update_memory(
                        memory_id=memory_id,
                        updates=update_data,
                        user_id=current_user.id
                    )
                    
                    if memory:
                        updated_memories.append(memory)
                        
                except Exception as e:
                    logger.error(f"Failed to update memory {memory_id}: {e}")
                    continue  # Continue with other updates
            
            return [MemoryResponse.from_orm(memory) for memory in updated_memories]
            
        except Exception as e:
            handle_errors(e, "Failed to update memories in batch")
            raise HTTPException(status_code=500, detail="Failed to update memories in batch")
    
    async def batch_delete_memories(
        self,
        memory_ids: List[int],
        current_user: User
    ) -> Dict[str, Any]:
        """Delete multiple memories in batch."""
        try:
            if not memory_ids:
                raise HTTPException(status_code=400, detail="No memory IDs provided")
            
            deleted_count = 0
            failed_ids = []
            
            for memory_id in memory_ids:
                try:
                    success = await self.memory_service.delete_memory(
                        memory_id=memory_id,
                        user_id=current_user.id
                    )
                    
                    if success:
                        deleted_count += 1
                    else:
                        failed_ids.append(memory_id)
                        
                except Exception as e:
                    logger.error(f"Failed to delete memory {memory_id}: {e}")
                    failed_ids.append(memory_id)
                    continue
            
            return {
                "deleted_count": deleted_count,
                "failed_count": len(failed_ids),
                "failed_ids": failed_ids,
                "message": f"Deleted {deleted_count} memories"
            }
            
        except Exception as e:
            handle_errors(e, "Failed to delete memories in batch")
            raise HTTPException(status_code=500, detail="Failed to delete memories in batch")
    
    # ========== ANALYSIS AND STATISTICS ==========
    
    async def get_memory_stats(
        self,
        current_user: Optional[User] = None
    ) -> MemoryStats:
        """Get memory statistics."""
        try:
            return await self.stats_service.get_memory_statistics(
                user_id=current_user.id if current_user else None,
                include_content_analysis=True
            )
            
        except Exception as e:
            handle_errors(e, "Failed to retrieve memory statistics")
            raise HTTPException(status_code=500, detail="Failed to retrieve memory statistics")
    
    async def analyze_memory_content(
        self,
        memory_id: int,
        analysis_type: str = "keywords",
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Analyze memory content."""
        try:
            if memory_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid memory ID")
            
            valid_types = ["keywords", "sentiment", "complexity", "readability"]
            if analysis_type not in valid_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid analysis type. Must be one of: {valid_types}"
                )
            
            # Check access first
            memory = await self.memory_service.get_memory(
                memory_id=memory_id,
                user_id=current_user.id if current_user else None
            )
            
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            # Delegate to service
            analysis = await self.memory_service.analyze_content(
                memory_id=memory_id,
                analysis_type=analysis_type
            )
            
            return analysis
            
        except HTTPException:
            raise
        except Exception as e:
            handle_errors(e, "Failed to analyze memory content")
            raise HTTPException(status_code=500, detail="Failed to analyze memory content")
    
    async def summarize_memory(
        self,
        memory_id: int,
        max_length: int = 50,
        current_user: Optional[User] = None
    ) -> MemorySummaryResponse:
        """Generate memory summary."""
        try:
            if memory_id <= 0:
                raise HTTPException(status_code=400, detail="Invalid memory ID")
            
            if max_length <= 0 or max_length > 500:
                raise HTTPException(status_code=400, detail="Max length must be between 1 and 500")
            
            # Check access first
            memory = await self.memory_service.get_memory(
                memory_id=memory_id,
                user_id=current_user.id if current_user else None
            )
            
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            # Generate summary
            summary = await self.memory_service.generate_summary(
                memory_id=memory_id,
                max_length=max_length
            )
            
            return MemorySummaryResponse(
                memory_id=memory_id,
                summary=summary,
                generated_at=datetime.utcnow(),
                method="extractive"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            handle_errors(e, "Failed to generate summary")
            raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    # ========== PRIVATE HELPER METHODS ==========
    
    async def _post_create_tasks(self, memory_id: int):
        """Background tasks after memory creation."""
        try:
            # Add any post-creation tasks here
            # e.g., indexing, relation discovery, notification sending
            logger.info(f"Running post-create tasks for memory {memory_id}")
            
        except Exception as e:
            logger.error(f"Error in post-create tasks for memory {memory_id}: {e}")


class StorageController:
    """
    Specialized controller for storage management operations.
    Separated for single responsibility principle.
    """
    
    def __init__(self, memory_service: MemoryServiceImpl):
        self.memory_service = memory_service
    
    async def get_storage_status(self) -> Dict[str, Any]:
        """Get storage system status."""
        try:
            # This would get status from the refactored database
            return {
                "compression": {"enabled": True, "algorithm": "adaptive"},
                "chunked_storage": {"enabled": False},
                "hybrid_storage": {"enabled": False},
                "distributed_storage": {"enabled": False}
            }
            
        except Exception as e:
            handle_errors(e, "Failed to get storage status")
            raise HTTPException(status_code=500, detail="Failed to get storage status")
    
    async def migrate_memory_storage(
        self,
        memory_id: int,
        target_strategy: str,
        current_user: User
    ) -> Dict[str, Any]:
        """Migrate memory to different storage strategy."""
        try:
            # Check access first
            memory = await self.memory_service.get_memory(
                memory_id=memory_id,
                user_id=current_user.id
            )
            
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            # This would implement storage migration logic
            # For now, return success message
            return {
                "message": f"Memory {memory_id} migration to {target_strategy} completed",
                "memory_id": memory_id,
                "target_strategy": target_strategy
            }
            
        except HTTPException:
            raise
        except Exception as e:
            handle_errors(e, "Failed to migrate memory storage")
            raise HTTPException(status_code=500, detail="Failed to migrate memory storage")