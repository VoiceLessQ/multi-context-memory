"""
Memory service implementation with business logic.
Extracts business logic from the bloated api/routes/memory.py (1,746 lines).
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...database.interfaces.service import MemoryService
from ...database.interfaces.repository import MemoryRepository, ContextRepository, RelationRepository
from ...database.refactored_memory_db import RefactoredMemoryDB
from ...database.models import Memory, Context, User
from ...schemas.memory import MemoryCreate, MemoryUpdate, MemoryResponse, MemoryStats
from ...utils.text_processing import extract_keywords, generate_summary
from ...utils.error_handling import handle_errors

logger = logging.getLogger(__name__)


class MemoryServiceImpl(MemoryService):
    """
    Concrete implementation of MemoryService.
    Handles all memory-related business logic cleanly separated from API concerns.
    """
    
    def __init__(
        self,
        memory_db: RefactoredMemoryDB,
        memory_repository: MemoryRepository,
        context_repository: Optional[ContextRepository] = None
    ):
        self.memory_db = memory_db
        self.memory_repository = memory_repository
        self.context_repository = context_repository
    
    async def create_memory(
        self,
        title: str,
        content: str,
        owner_id: str,
        context_id: Optional[int] = None,
        access_level: str = "private",
        metadata: Optional[Dict[str, Any]] = None,
        storage_options: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """Create memory with business logic validation."""
        try:
            # Validate inputs
            if not title or not title.strip():
                raise ValueError("Memory title cannot be empty")
            
            if not content or not content.strip():
                raise ValueError("Memory content cannot be empty")
            
            if len(title) > 500:
                raise ValueError("Memory title too long (max 500 characters)")
            
            if len(content) > 10_000_000:  # 10MB limit
                raise ValueError("Memory content too large (max 10MB)")
            
            # Validate context exists if provided
            if context_id and self.context_repository:
                context = await self.context_repository.find_by_id(context_id)
                if not context:
                    raise ValueError(f"Context {context_id} not found")
            
            # Validate access level
            valid_access_levels = ["public", "user", "privileged", "admin", "private"]
            if access_level not in valid_access_levels:
                raise ValueError(f"Invalid access level. Must be one of: {valid_access_levels}")
            
            # Extract storage options
            storage_opts = storage_options or {}
            use_compression = storage_opts.get('use_compression', True)
            use_chunked_storage = storage_opts.get('use_chunked_storage', False)
            use_hybrid_storage = storage_opts.get('use_hybrid_storage', False)
            use_distributed_storage = storage_opts.get('use_distributed_storage', False)
            use_deduplication = storage_opts.get('use_deduplication', False)
            use_archival = storage_opts.get('use_archival', False)
            
            # Create memory using the refactored database
            memory = await self.memory_db.create_memory(
                title=title.strip(),
                content=content.strip(),
                owner_id=owner_id,
                context_id=context_id,
                access_level=access_level,
                memory_metadata=metadata or {},
                compress_content=use_compression,
                use_chunked_storage=use_chunked_storage,
                use_hybrid_storage=use_hybrid_storage,
                use_distributed_storage=use_distributed_storage,
                use_deduplication=use_deduplication,
                use_archival=use_archival
            )
            
            logger.info(f"Memory created successfully: {memory.id} - {memory.title}")
            return memory
            
        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            handle_errors(e, "Failed to create memory")
            raise
    
    async def get_memory(
        self,
        memory_id: int,
        user_id: Optional[str] = None,
        load_options: Optional[Dict[str, Any]] = None
    ) -> Optional[Memory]:
        """Get memory with access control and loading options."""
        try:
            if memory_id <= 0:
                raise ValueError("Invalid memory ID")
            
            # Get memory from database
            load_opts = load_options or {}
            decompress = load_opts.get('decompress', True)
            use_lazy_loading = load_opts.get('use_lazy_loading', None)
            
            memory = await self.memory_db.get_memory(
                memory_id=memory_id,
                decompress=decompress,
                use_lazy_loading=use_lazy_loading
            )
            
            if not memory:
                return None
            
            # Apply access control
            if user_id and not self._check_access(memory, user_id):
                logger.warning(f"User {user_id} denied access to memory {memory_id}")
                return None
            
            return memory
            
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            handle_errors(e, "Failed to get memory")
            return None
    
    async def update_memory(
        self,
        memory_id: int,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[Memory]:
        """Update memory with validation and access control."""
        try:
            if memory_id <= 0:
                raise ValueError("Invalid memory ID")
            
            # Check if memory exists and user has access
            existing_memory = await self.get_memory(memory_id, user_id)
            if not existing_memory:
                return None
            
            # Validate updates
            validated_updates = self._validate_updates(updates)
            
            # Apply updates using refactored database
            updated_memory = await self.memory_db.update_memory(
                memory_id=memory_id,
                **validated_updates
            )
            
            if updated_memory:
                logger.info(f"Memory updated successfully: {updated_memory.id}")
            
            return updated_memory
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            handle_errors(e, "Failed to update memory")
            return None
    
    async def delete_memory(
        self,
        memory_id: int,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete memory with access control."""
        try:
            if memory_id <= 0:
                raise ValueError("Invalid memory ID")
            
            # Check if memory exists and user has access
            existing_memory = await self.get_memory(memory_id, user_id)
            if not existing_memory:
                return False
            
            # Delete using refactored database
            success = await self.memory_db.delete_memory(memory_id)
            
            if success:
                logger.info(f"Memory deleted successfully: {memory_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            handle_errors(e, "Failed to delete memory")
            return False
    
    async def search_memories(
        self,
        query: str,
        filters: Dict[str, Any],
        user_id: Optional[str] = None,
        pagination: Optional[Dict[str, Any]] = None
    ) -> List[Memory]:
        """Search memories with business logic filtering."""
        try:
            # Validate query
            if not query or not query.strip():
                raise ValueError("Search query cannot be empty")
            
            if len(query) > 1000:
                raise ValueError("Search query too long (max 1000 characters)")
            
            # Apply pagination
            paginate = pagination or {}
            skip = paginate.get('skip', 0)
            limit = paginate.get('limit', 100)
            
            if skip < 0:
                skip = 0
            if limit <= 0 or limit > 1000:
                limit = 100
            
            # Apply user-based filtering
            search_filters = dict(filters)
            if user_id:
                search_filters['owner_id'] = user_id
            
            # Search using refactored database
            memories = await self.memory_db.search_memories(
                query=query.strip(),
                limit=limit,
                **search_filters
            )
            
            # Apply access control filtering
            accessible_memories = [
                memory for memory in memories
                if self._check_access(memory, user_id)
            ]
            
            logger.info(f"Found {len(accessible_memories)} accessible memories for query: {query}")
            return accessible_memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            handle_errors(e, "Failed to search memories")
            return []
    
    async def bulk_create_memories(
        self,
        memories_data: List[Dict[str, Any]],
        user_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Memory]:
        """Create multiple memories with transaction support."""
        try:
            if not memories_data:
                raise ValueError("No memories data provided")
            
            if len(memories_data) > 100:
                raise ValueError("Too many memories (max 100 per batch)")
            
            created_memories = []
            options = options or {}
            
            # Process each memory
            for i, memory_data in enumerate(memories_data):
                try:
                    # Validate required fields
                    if 'title' not in memory_data or 'content' not in memory_data:
                        raise ValueError(f"Memory {i}: title and content are required")
                    
                    # Create memory
                    memory = await self.create_memory(
                        title=memory_data['title'],
                        content=memory_data['content'],
                        owner_id=user_id,
                        context_id=memory_data.get('context_id'),
                        access_level=memory_data.get('access_level', 'private'),
                        metadata=memory_data.get('metadata'),
                        storage_options=options
                    )
                    
                    created_memories.append(memory)
                    
                except Exception as e:
                    logger.error(f"Error creating memory {i}: {e}")
                    # Continue with other memories rather than failing entire batch
                    continue
            
            logger.info(f"Bulk created {len(created_memories)} out of {len(memories_data)} memories")
            return created_memories
            
        except Exception as e:
            logger.error(f"Error in bulk create memories: {e}")
            handle_errors(e, "Failed to bulk create memories")
            return []
    
    async def analyze_content(
        self,
        memory_id: int,
        analysis_type: str = "keywords"
    ) -> Dict[str, Any]:
        """Analyze memory content for insights."""
        try:
            memory = await self.memory_repository.find_by_id(memory_id)
            if not memory:
                raise ValueError(f"Memory {memory_id} not found")
            
            # Load full content if needed
            if not hasattr(memory, '_content_loaded') or not memory._content_loaded:
                await self.memory_db._load_full_content(memory)
            
            content = memory.content
            
            if analysis_type == "keywords":
                keywords = extract_keywords(content)
                return {
                    "memory_id": memory_id,
                    "analysis_type": "keywords",
                    "keywords": keywords,
                    "keyword_count": len(keywords)
                }
            
            elif analysis_type == "sentiment":
                # Basic sentiment analysis (placeholder)
                positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
                negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing', 'frustrating']
                
                words = content.lower().split()
                positive_count = sum(1 for word in words if word in positive_words)
                negative_count = sum(1 for word in words if word in negative_words)
                
                sentiment_score = (positive_count - negative_count) / max(len(words), 1)
                
                return {
                    "memory_id": memory_id,
                    "analysis_type": "sentiment",
                    "sentiment_score": sentiment_score,
                    "positive_indicators": positive_count,
                    "negative_indicators": negative_count
                }
            
            elif analysis_type == "complexity":
                # Text complexity analysis
                sentences = content.split('.')
                words = content.split()
                characters = len(content)
                
                avg_words_per_sentence = len(words) / max(len(sentences), 1)
                avg_chars_per_word = characters / max(len(words), 1)
                
                complexity_score = (avg_words_per_sentence * 0.3) + (avg_chars_per_word * 0.7)
                
                return {
                    "memory_id": memory_id,
                    "analysis_type": "complexity",
                    "complexity_score": complexity_score,
                    "sentence_count": len(sentences),
                    "word_count": len(words),
                    "character_count": characters,
                    "avg_words_per_sentence": avg_words_per_sentence,
                    "avg_chars_per_word": avg_chars_per_word
                }
            
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
        except Exception as e:
            logger.error(f"Error analyzing content for memory {memory_id}: {e}")
            handle_errors(e, "Failed to analyze content")
            return {}
    
    async def generate_summary(
        self,
        memory_id: int,
        max_length: int = 50
    ) -> str:
        """Generate memory summary."""
        try:
            memory = await self.memory_repository.find_by_id(memory_id)
            if not memory:
                raise ValueError(f"Memory {memory_id} not found")
            
            # Load full content if needed
            if not hasattr(memory, '_content_loaded') or not memory._content_loaded:
                await self.memory_db._load_full_content(memory)
            
            # Generate summary using text processing utility
            summary = generate_summary(memory.content, max_length)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for memory {memory_id}: {e}")
            handle_errors(e, "Failed to generate summary")
            return ""
    
    def _check_access(self, memory: Memory, user_id: Optional[str]) -> bool:
        """Check if user has access to memory based on access level."""
        if not user_id:
            return memory.access_level == "public"
        
        # Owner always has access
        if memory.owner_id == user_id:
            return True
        
        # Check access level
        if memory.access_level == "public":
            return True
        elif memory.access_level == "user":
            return True  # Any authenticated user
        elif memory.access_level in ["privileged", "admin"]:
            # In a real system, you'd check user roles here
            return False  # For now, restrict access
        else:  # private
            return False
    
    def _validate_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate update data."""
        validated = {}
        
        if 'title' in updates:
            title = updates['title']
            if not title or not title.strip():
                raise ValueError("Title cannot be empty")
            if len(title) > 500:
                raise ValueError("Title too long (max 500 characters)")
            validated['title'] = title.strip()
        
        if 'content' in updates:
            content = updates['content']
            if not content or not content.strip():
                raise ValueError("Content cannot be empty")
            if len(content) > 10_000_000:  # 10MB limit
                raise ValueError("Content too large (max 10MB)")
            validated['content'] = content.strip()
        
        if 'access_level' in updates:
            access_level = updates['access_level']
            valid_levels = ["public", "user", "privileged", "admin", "private"]
            if access_level not in valid_levels:
                raise ValueError(f"Invalid access level. Must be one of: {valid_levels}")
            validated['access_level'] = access_level
        
        if 'memory_metadata' in updates:
            metadata = updates['memory_metadata']
            if not isinstance(metadata, dict):
                raise ValueError("Metadata must be a dictionary")
            validated['memory_metadata'] = metadata
        
        return validated


class MemoryStatsService:
    """
    Specialized service for memory statistics and analytics.
    Separated for single responsibility principle.
    """
    
    def __init__(self, memory_db: RefactoredMemoryDB):
        self.memory_db = memory_db
    
    async def get_memory_statistics(
        self,
        user_id: Optional[str] = None,
        include_content_analysis: bool = True
    ) -> MemoryStats:
        """Get comprehensive memory statistics."""
        try:
            # Get basic statistics from database
            basic_stats = await self.memory_db.get_statistics()
            
            # Add user-specific filtering if needed
            user_stats = {}
            if user_id:
                user_memories = await self.memory_db.search_memories(
                    query="", 
                    owner_id=user_id,
                    limit=10000
                )
                user_stats = {
                    "user_memory_count": len(user_memories),
                    "user_total_size": sum(m.content_size for m in user_memories),
                    "user_compressed_count": sum(1 for m in user_memories if m.content_compressed)
                }
            
            # Combine stats
            stats_data = {**basic_stats, **user_stats}
            
            # Create MemoryStats object
            return MemoryStats(**stats_data)
            
        except Exception as e:
            logger.error(f"Error getting memory statistics: {e}")
            handle_errors(e, "Failed to get memory statistics")
            # Return empty stats on error
            return MemoryStats()
    
    async def get_usage_patterns(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze usage patterns."""
        try:
            # This would integrate with the performance monitor
            # For now, return basic patterns
            
            patterns = {
                "daily_activity": {},
                "popular_contexts": [],
                "frequent_searches": [],
                "access_patterns": {}
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {e}")
            return {}