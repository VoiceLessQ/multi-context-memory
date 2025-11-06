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
Refactored Enhanced Memory Database using Repository and Strategy patterns.
This replaces the monolithic enhanced_memory_db.py with a clean, maintainable architecture.

Key improvements:
- Separation of concerns using Repository pattern
- Flexible storage strategies using Strategy pattern
- Dependency injection for better testability
- SOLID principles compliance
- Reduced from 1,737 lines to manageable, focused components
"""
import logging
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from datetime import datetime

from .repositories.context_repository import ContextRepository
from .repositories.relation_repository import RelationRepository
from .repositories.memory_repository import SQLAlchemyMemoryRepository
from .interfaces.storage_strategy import (
    StorageStrategy, CompressionStrategy, ChunkedStorageStrategy,
    HybridStorageStrategy, DistributedStorageStrategy, CachingStrategy,
    IndexingStrategy, EncryptionStrategy, StorageStrategyFactory
)
from .interfaces.service import (
    MemoryService, ContextService, RelationService, 
    DeduplicationService, ArchivalService, AnalyticsService,
    ConfigurationService
)
from .strategies.compression_strategy import ZstdCompressionStrategy, AdaptiveCompressionStrategy
from .strategies.chunked_storage_strategy import SQLAlchemyChunkedStorageStrategy
from .models import Memory, Context, Relation, MemoryChunk

logger = logging.getLogger(__name__)


class RefactoredMemoryDB:
    """
    Refactored Memory Database using modern architecture patterns.
    
    This class acts as a facade that orchestrates Repository and Strategy patterns
    instead of the original monolithic approach. It's highly configurable and testable.
    """
    
    def __init__(
        self,
        db_url: str,
        session: Optional[Session] = None,
        repositories: Optional[Dict[str, Any]] = None,
        strategies: Optional[Dict[str, Any]] = None,
        services: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize with dependency injection support.
        
        Args:
            db_url: Database connection URL
            session: SQLAlchemy session (optional)
            repositories: Injected repository implementations
            strategies: Injected strategy implementations
            services: Injected service implementations
            config: Configuration dictionary
        """
        self.db_url = db_url
        self.session = session
        self.config = config or {}
        
        # Configuration flags (extracted from original class) - Initialize FIRST
        self.lazy_loading_enabled = self.config.get('lazy_loading_enabled', True)
        self.compression_enabled = self.config.get('compression_enabled', True)
        self.chunked_storage_enabled = self.config.get('chunked_storage_enabled', False)
        self.chunk_size = self.config.get('chunk_size', 10000)
        self.max_chunks = self.config.get('max_chunks', 100)
        
        # Initialize performance monitoring
        self.performance_monitor = None
        # Performance monitor removed due to import issues
        
        # Initialize repositories (with dependency injection support)
        self._init_repositories(repositories or {})
        
        # Initialize strategies (with dependency injection support)
        self._init_strategies(strategies or {})
        
        # Initialize services (with dependency injection support)
        self._init_services(services or {})
        
        logger.info("RefactoredMemoryDB initialized with modern architecture patterns")
    
    def _init_repositories(self, injected_repos: Dict[str, Any]):
        """Initialize repositories with optional dependency injection."""
        self.memory_repository = injected_repos.get(
            'memory',
            SQLAlchemyMemoryRepository(self.session) if self.session else None
        )
        
        # Initialize context repository
        self.context_repository = injected_repos.get(
            'context',
            ContextRepository(self.session) if self.session else None
        )
        
        # Initialize relation repository
        self.relation_repository = injected_repos.get(
            'relation',
            RelationRepository(self.session) if self.session else None
        )
        
        # Initialize chunk repository (placeholder)
        self.chunk_repository = injected_repos.get('chunk', None)
    
    def _init_strategies(self, injected_strategies: Dict[str, Any]):
        """Initialize storage strategies with optional dependency injection."""
        # Compression strategy
        compression_algo = self.config.get('compression_algorithm', 'adaptive')
        if compression_algo == 'adaptive':
            self.compression_strategy = injected_strategies.get(
                'compression',
                AdaptiveCompressionStrategy()
            )
        else:
            self.compression_strategy = injected_strategies.get(
                'compression',
                ZstdCompressionStrategy()
            )
        
        # Chunked storage strategy
        if self.chunked_storage_enabled:
            self.chunked_storage_strategy = injected_strategies.get(
                'chunked_storage',
                SQLAlchemyChunkedStorageStrategy(
                    self.chunk_repository,
                    self.session,
                    self.chunk_size,
                    self.max_chunks,
                    self.compression_strategy
                ) if self.chunk_repository and self.session else None
            )
        else:
            self.chunked_storage_strategy = None
        
        # Other strategies (placeholders for full implementation)
        self.hybrid_storage_strategy = injected_strategies.get('hybrid_storage', None)
        self.distributed_storage_strategy = injected_strategies.get('distributed_storage', None)
        self.caching_strategy = injected_strategies.get('caching', None)
        self.indexing_strategy = injected_strategies.get('indexing', None)
        self.encryption_strategy = injected_strategies.get('encryption', None)
    
    def _init_services(self, injected_services: Dict[str, Any]):
        """Initialize service layer with optional dependency injection."""
        # Services will be implemented as the refactoring continues
        self.memory_service = injected_services.get('memory', None)
        self.context_service = injected_services.get('context', None)
        self.relation_service = injected_services.get('relation', None)
        self.deduplication_service = injected_services.get('deduplication', None)
        self.archival_service = injected_services.get('archival', None)
        self.analytics_service = injected_services.get('analytics', None)
        self.configuration_service = injected_services.get('configuration', None)
    
    # ========== HIGH-LEVEL FACADE METHODS ==========
    # These replace the original monolithic methods with clean orchestration
    
    async def create_memory(
        self,
        title: str,
        content: str,
        owner_id: str,
        context_id: Optional[int] = None,
        access_level: str = "private",
        memory_metadata: Optional[Dict[str, Any]] = None,
        compress_content: Optional[bool] = None,
        use_chunked_storage: Optional[bool] = None,
        use_hybrid_storage: Optional[bool] = None,
        use_distributed_storage: Optional[bool] = None,
        use_deduplication: Optional[bool] = None,
        use_archival: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Create memory using Repository and Strategy patterns.
        Much cleaner than the original 80-line method.
        """
        try:
            # Determine storage strategy
            should_compress = compress_content if compress_content is not None else self.compression_enabled
            use_chunks = use_chunked_storage if use_chunked_storage is not None else self.chunked_storage_enabled
            
            # Create memory entity
            memory = Memory(
                title=title,
                content="",  # Will be set by storage strategy
                owner_id=owner_id,
                context_id=context_id,
                access_level=access_level,
                memory_metadata=memory_metadata or {},
                content_compressed=False,
                content_size=len(content)
            )
            
            # Create memory record first
            created_memory = await self.memory_repository.create(memory)
            
            # Apply storage strategy
            if use_chunks and self.chunked_storage_strategy:
                success = await self.chunked_storage_strategy.store(created_memory, content, compress=should_compress)
                if success:
                    created_memory.content_compressed = True
                else:
                    raise Exception("Failed to store memory using chunked storage")
            else:
                # Store with compression if enabled
                if should_compress and self.compression_strategy:
                    compressed_content, was_compressed = self.compression_strategy.compress(content)
                    created_memory.content = compressed_content
                    created_memory.content_compressed = was_compressed
                else:
                    created_memory.content = content
            
            # Commit changes
            self.session.commit()
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("create")
                self.performance_monitor.record_query_time(0.1)
            
            logger.info(f"Created memory using modern patterns: {created_memory.id} - {created_memory.title}")
            return created_memory
            
        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            self.session.rollback()
            raise
    
    async def create_context(
        self,
        name: str,
        description: str,
        owner_id: int = 1,
        access_level: str = "user"
    ) -> Optional[Context]:
        """
        Create a new context.
        
        Args:
            name: Name of the context
            description: Description of the context
            owner_id: ID of the owner user
            access_level: Access level for the context
            
        Returns:
            Created Context object or None if creation failed
        """
        try:
            if not self.context_repository:
                logger.error("Context repository not initialized")
                return None
                
            # Create context entity
            from .models import Context
            from datetime import datetime
            
            context = Context(
                name=name,
                description=description,
                owner_id=owner_id,
                access_level=access_level,
                context_metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            # Use repository pattern
            return await self.context_repository.create(context)
                
        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return None
    
    async def get_memory(
        self,
        memory_id: int,
        decompress: bool = True,
        use_lazy_loading: Optional[bool] = None,
        owner_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Memory]:
        """
        Get memory using Repository pattern with strategy-based content loading.
        Much simpler than the original 200-line method.
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return None
                
            use_lazy = use_lazy_loading if use_lazy_loading is not None else self.lazy_loading_enabled
            
            # Get memory from repository
            memory = await self.memory_repository.find_by_id(memory_id)
            if not memory:
                return None
            
            # Check ownership if owner_id is provided
            if owner_id and memory.owner_id != owner_id:
                logger.warning(f"Memory {memory_id} does not belong to owner {owner_id}")
                return None
            
            # Load content based on strategy
            if use_lazy:
                # Lazy loading - only load preview
                if hasattr(memory, 'content_preview') and memory.content_preview:
                    memory.content = memory.content_preview
                else:
                    # Use first 100 characters as preview
                    memory.content = memory.content[:100] if memory.content else ""
                memory._content_loaded = False
            else:
                # Eager loading - load full content
                await self._load_full_content(memory, decompress)
            
            return memory
            
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            if self.performance_monitor:
                self.performance_monitor.record_error()
            return None
    
    async def _load_full_content(self, memory: Memory, decompress: bool = True):
        """
        Load full content for a memory, handling decompression if needed.
        """
        try:
            if memory.content_compressed and decompress and self.compression_strategy:
                # Decompress content
                decompressed_content = self.compression_strategy.decompress(memory.content)
                memory.content = decompressed_content
            elif memory.content_compressed and not decompress:
                # Keep compressed content but mark as not loaded
                memory._content_loaded = False
                return
            else:
                # Content is already in plaintext
                memory._content_loaded = True
                return
            
            memory._content_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading full content for memory {memory.id}: {e}")
            # Keep original content on error
            memory._content_loaded = False
    
    async def search_memories(
        self,
        query: str,
        owner_id: Optional[str] = None,
        context_id: Optional[int] = None,
        access_level: Optional[str] = None,
        limit: int = 100,
        **kwargs
    ) -> List[Memory]:
        """
        Search memories using Repository pattern.
        Replaces the original complex search method with clean delegation.
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return []
                
            # Build filters
            filters = {}
            if owner_id:
                filters["owner_id"] = owner_id
            if context_id:
                filters["context_id"] = context_id
            if access_level:
                filters["access_level"] = access_level
            
            # Delegate to repository
            memories = await self.memory_repository.search(query, filters, limit)
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_search()
                self.performance_monitor.record_query_time(0.2)
            
            logger.info(f"Found {len(memories)} memories using repository pattern")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def update_memory(
        self,
        memory_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        access_level: Optional[str] = None,
        memory_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Memory]:
        """
        Update memory using Repository and Strategy patterns.
        Much cleaner than the original complex update method.
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return None
                
            # Prepare updates
            updates = {}
            if title is not None:
                updates["title"] = title
            if access_level is not None:
                updates["access_level"] = access_level
            if memory_metadata is not None:
                updates["memory_metadata"] = memory_metadata
            
            # Handle content updates with strategy
            if content is not None:
                memory = await self.memory_repository.find_by_id(memory_id)
                if not memory:
                    return None
                
                # Apply storage strategy for content
                if self.chunked_storage_strategy and self.chunked_storage_enabled:
                    success = await self.chunked_storage_strategy.update(memory_id, content)
                    if success:
                        updates["content_compressed"] = True
                        updates["content_size"] = len(content)
                    else:
                        raise Exception("Failed to update memory using chunked storage")
                else:
                    # Direct content update with compression
                    if self.compression_enabled and self.compression_strategy:
                        compressed_content, was_compressed = self.compression_strategy.compress(content)
                        updates["content"] = compressed_content
                        updates["content_compressed"] = was_compressed
                    else:
                        updates["content"] = content
                        updates["content_compressed"] = False
                    
                    updates["content_size"] = len(content)
            
            # Apply updates via repository
            updated_memory = await self.memory_repository.update(memory_id, updates)
            
            # Commit the session if the repository didn't commit
            if updated_memory and not getattr(self.memory_repository, '_committed', False):
                self.session.commit()
                self.memory_repository._committed = True
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("update")
                self.performance_monitor.record_query_time(0.1)
            
            if updated_memory:
                logger.info(f"Updated memory using modern patterns: {updated_memory.id}")
            return updated_memory
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            if self.session:
                self.session.rollback()
            return None
    
    async def delete_memory(self, memory_id: int, **kwargs) -> bool:
        """
        Delete memory using Repository and Strategy patterns.
        Much simpler than the original method with complex cleanup.
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return False
                
            # Clean up chunked storage if used
            if self.chunked_storage_strategy:
                await self.chunked_storage_strategy.delete(memory_id)
            
            # Delete via repository
            success = await self.memory_repository.delete(memory_id)
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("delete")
                self.performance_monitor.record_query_time(0.05)
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False
    
    async def bulk_create_memories(self, memories_data: List[Dict[str, Any]], **kwargs) -> List[Memory]:
        """
        Create multiple memories at once.
        
        Args:
            memories_data: List of memory data dictionaries
            
        Returns:
            List of created Memory objects
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return []
                
            created_memories = []
            
            for memory_data in memories_data:
                try:
                    # Extract required fields
                    title = memory_data.get("title")
                    content = memory_data.get("content")
                    owner_id = memory_data.get("owner_id", "1")
                    
                    if not title or not content:
                        logger.warning(f"Skipping memory with missing title or content: {memory_data}")
                        continue
                    
                    # Create memory
                    memory = await self.create_memory(
                        title=title,
                        content=content,
                        owner_id=owner_id,
                        context_id=memory_data.get("context_id"),
                        access_level=memory_data.get("access_level", "private"),
                        memory_metadata=memory_data.get("memory_metadata"),
                        compress_content=memory_data.get("compress_content"),
                        use_chunked_storage=memory_data.get("use_chunked_storage"),
                        use_hybrid_storage=memory_data.get("use_hybrid_storage"),
                        use_distributed_storage=memory_data.get("use_distributed_storage"),
                        use_deduplication=memory_data.get("use_deduplication"),
                        use_archival=memory_data.get("use_archival")
                    )
                    
                    if memory:
                        created_memories.append(memory)
                        
                except Exception as e:
                    logger.error(f"Error creating memory in bulk operation: {e}")
                    continue
            
            return created_memories
            
        except Exception as e:
            logger.error(f"Error in bulk create memories: {e}")
            return []
    
    async def create_large_memory(
        self,
        title: str,
        content: str,
        owner_id: str,
        context_id: Optional[int] = None,
        access_level: str = "private",
        compress_content: bool = True,
        **kwargs
    ) -> Memory:
        """
        Create a large memory without splitting into chunks.
        
        Args:
            title: Title of the memory
            content: Content of the memory
            owner_id: Owner ID
            context_id: Context ID (optional)
            access_level: Access level
            compress_content: Whether to compress content
            
        Returns:
            Created Memory object
        """
        try:
            # For large memories, always use compression
            should_compress = compress_content
            
            # Create memory entity
            memory = Memory(
                title=title,
                content="",  # Will be set by storage strategy
                owner_id=owner_id,
                context_id=context_id,
                access_level=access_level,
                memory_metadata={"is_large": True},
                content_compressed=False,
                content_size=len(content)
            )
            
            # Create memory record first
            created_memory = await self.memory_repository.create(memory)
            
            # Apply compression if enabled
            if should_compress and self.compression_strategy:
                compressed_content, was_compressed = self.compression_strategy.compress(content)
                created_memory.content = compressed_content
                created_memory.content_compressed = was_compressed
            else:
                created_memory.content = content
                created_memory.content_compressed = False
            
            # Commit changes
            self.session.commit()
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("create_large")
                self.performance_monitor.record_query_time(0.2)
            
            logger.info(f"Created large memory: {created_memory.id} - {created_memory.title}")
            return created_memory
            
        except Exception as e:
            logger.error(f"Error creating large memory: {e}")
            self.session.rollback()
            raise
    
    async def categorize_memories(
        self,
        context_id: Optional[int] = None,
        auto_generate_tags: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Automatically categorize and tag memories based on content analysis.
        
        Args:
            context_id: Filter by context ID (optional)
            auto_generate_tags: Whether to auto-generate tags from content
            
        Returns:
            Dictionary containing categorization results
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return {"error": "Memory repository not initialized"}
            
            # Get all memories
            filters = {}
            if context_id:
                filters["context_id"] = context_id
                
            memories = await self.memory_repository.find_by_criteria(filters)
            
            categorized_count = 0
            tagged_count = 0
            errors = []
            
            for memory in memories:
                try:
                    # Generate category based on content length
                    content_length = len(memory.content) if memory.content else 0
                    
                    if content_length < 500:
                        category = "short"
                    elif content_length < 5000:
                        category = "medium"
                    else:
                        category = "long"
                    
                    # Update memory category
                    if memory.memory_metadata is None:
                        memory.memory_metadata = {}
                        
                    old_category = memory.memory_metadata.get("category")
                    memory.memory_metadata["category"] = category
                    
                    # Generate tags if enabled
                    if auto_generate_tags:
                        # Simple keyword extraction (placeholder)
                        tags = []
                        if memory.content:
                            words = memory.content.lower().split()
                            # Get most common words (excluding very common ones)
                            common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
                            word_counts = {}
                            
                            for word in words:
                                if len(word) > 3 and word not in common_words:
                                    word_counts[word] = word_counts.get(word, 0) + 1
                            
                            # Get top 3 words as tags
                            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
                            tags = [word for word, count in sorted_words[:3]]
                        
                        old_tags = memory.memory_metadata.get("tags", [])
                        memory.memory_metadata["tags"] = tags
                        tagged_count += 1 if tags else 0
                    
                    # Update memory in repository
                    await self.memory_repository.update(memory.id, {"memory_metadata": memory.memory_metadata})
                    
                    # Check if category changed
                    if old_category != category:
                        categorized_count += 1
                        
                except Exception as e:
                    logger.error(f"Error categorizing memory {memory.id}: {e}")
                    errors.append(f"Memory {memory.id}: {str(e)}")
            
            # Commit changes
            self.session.commit()
            
            return {
                "total_memories": len(memories),
                "categorized_memories": categorized_count,
                "tagged_memories": tagged_count,
                "errors": errors,
                "categorization_complete": True,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error categorizing memories: {e}")
            return {
                "error": str(e),
                "categorization_complete": False,
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def analyze_content(
        self,
        memory_id: Optional[int] = None,
        analysis_type: str = "keywords",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform advanced content analysis on memories.
        
        Args:
            memory_id: Specific memory to analyze (optional)
            analysis_type: Type of analysis ('keywords', 'sentiment', 'complexity', 'readability')
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return {"error": "Memory repository not initialized"}
            
            # Get memories to analyze
            if memory_id:
                memory = await self.memory_repository.find_by_id(memory_id)
                if not memory:
                    return {"error": f"Memory with ID {memory_id} not found"}
                memories = [memory]
            else:
                # Analyze all memories
                memories = await self.memory_repository.find_by_criteria({})
            
            results = {}
            
            for memory in memories:
                try:
                    content = memory.content or ""
                    analysis_result = {}
                    
                    if analysis_type == "keywords":
                        # Simple keyword extraction
                        words = content.lower().split()
                        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
                        word_counts = {}
                        
                        for word in words:
                            if len(word) > 3 and word not in common_words:
                                word_counts[word] = word_counts.get(word, 0) + 1
                        
                        # Get top 10 keywords
                        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
                        analysis_result["keywords"] = sorted_words[:10]
                        analysis_result["total_words"] = len(words)
                        analysis_result["unique_words"] = len(word_counts)
                    
                    elif analysis_type == "sentiment":
                        # Simple sentiment analysis (placeholder)
                        positive_words = {"good", "great", "excellent", "positive", "happy", "love", "like", "wonderful", "amazing"}
                        negative_words = {"bad", "terrible", "awful", "negative", "sad", "hate", "dislike", "horrible", "worst"}
                        
                        content_lower = content.lower()
                        positive_count = sum(1 for word in positive_words if word in content_lower)
                        negative_count = sum(1 for word in negative_words if word in content_lower)
                        
                        analysis_result["positive_score"] = positive_count
                        analysis_result["negative_score"] = negative_count
                        analysis_result["sentiment"] = "positive" if positive_count > negative_count else "negative" if negative_count > positive_count else "neutral"
                    
                    elif analysis_type == "complexity":
                        # Simple complexity metrics
                        sentences = content.split('.')
                        words = content.split()
                        
                        avg_words_per_sentence = len(words) / max(len(sentences), 1)
                        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
                        
                        analysis_result["sentence_count"] = len(sentences)
                        analysis_result["word_count"] = len(words)
                        analysis_result["avg_words_per_sentence"] = round(avg_words_per_sentence, 2)
                        analysis_result["avg_word_length"] = round(avg_word_length, 2)
                        analysis_result["complexity_score"] = min(10, round(avg_words_per_sentence + avg_word_length / 5, 1))
                    
                    elif analysis_type == "readability":
                        # Simple readability score (placeholder)
                        words = content.split()
                        sentences = content.split('.')
                        
                        avg_words_per_sentence = len(words) / max(len(sentences), 1)
                        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
                        
                        # Flesch Reading Ease formula (simplified)
                        readability_score = max(0, min(100, 206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_word_length / 100))
                        
                        analysis_result["readability_score"] = round(readability_score, 1)
                        analysis_result["readability_level"] = (
                            "Easy" if readability_score > 80 else
                            "Medium" if readability_score > 50 else
                            "Hard"
                        )
                    
                    else:
                        analysis_result["error"] = f"Unknown analysis type: {analysis_type}"
                    
                    results[memory.id] = {
                        "title": memory.title,
                        "analysis": analysis_result,
                        "analyzed_at": datetime.utcnow().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Error analyzing memory {memory.id}: {e}")
                    results[memory.id] = {
                        "error": str(e),
                        "analyzed_at": datetime.utcnow().isoformat()
                    }
            
            return {
                "analysis_type": analysis_type,
                "results": results,
                "total_analyzed": len(memories),
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
    
    async def summarize_memory(
        self,
        memory_id: int,
        max_length: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate or update summary for a memory.
        
        Args:
            memory_id: Memory ID to summarize
            max_length: Maximum summary length in words
            
        Returns:
            Dictionary containing summary result
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return {"error": "Memory repository not initialized"}
            
            # Get memory
            memory = await self.memory_repository.find_by_id(memory_id)
            if not memory:
                return {"error": f"Memory with ID {memory_id} not found"}
            
            content = memory.content or ""
            
            # Generate summary (simple approach)
            if content:
                # Split into sentences and take first few
                sentences = content.split('.')
                summary_sentences = [s.strip() for s in sentences[:2] if s.strip()]
                summary = '. '.join(summary_sentences)
                
                # Truncate to max_length words
                words = summary.split()
                if len(words) > max_length:
                    summary = ' '.join(words[:max_length]) + '...'
            else:
                summary = ""
            
            # Update memory with summary
            if memory.memory_metadata is None:
                memory.memory_metadata = {}
                
            memory.memory_metadata["summary"] = summary
            memory.memory_metadata["summary_length"] = len(summary.split())
            memory.memory_metadata["summary_generated_at"] = datetime.utcnow().isoformat()
            
            # Update memory in repository
            await self.memory_repository.update(memory_id, {"memory_metadata": memory.memory_metadata})
            
            # Commit changes
            self.session.commit()
            
            return {
                "memory_id": memory_id,
                "title": memory.title,
                "summary": summary,
                "summary_length": len(summary.split()),
                "max_length": max_length,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error summarizing memory {memory_id}: {e}")
            return {
                "error": str(e),
                "memory_id": memory_id,
                "generated_at": datetime.utcnow().isoformat()
            }
    
    
    
    
    
    async def search_semantic(
        self,
        query: str,
        limit: int = 10,
        context_id: Optional[int] = None,
        similarity_threshold: float = 0.3,
        **kwargs
    ) -> List[Memory]:
        """
        Perform AI-powered semantic search across memories.
        
        Args:
            query: Search query
            limit: Maximum results
            context_id: Filter by context ID (optional)
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of Memory objects
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return []
            
            # Get all memories
            filters = {}
            if context_id:
                filters["context_id"] = context_id
                
            memories = await self.memory_repository.find_by_criteria(filters)
            
            # Simple semantic search (placeholder)
            # In a real implementation, this would use embeddings and vector similarity
            scored_memories = []
            
            for memory in memories:
                # Simple keyword matching as a placeholder for semantic search
                score = 0.0
                query_lower = query.lower()
                
                # Check if query is in title
                if memory.title and query_lower in memory.title.lower():
                    score += 0.5
                
                # Check if query is in content
                if memory.content and query_lower in memory.content.lower():
                    score += 0.3
                
                # Check if query is in tags
                if memory.memory_metadata and memory.memory_metadata.get("tags"):
                    tags = memory.memory_metadata.get("tags", [])
                    for tag in tags:
                        if query_lower in tag.lower():
                            score += 0.2
                            break
                
                # Check if score meets threshold
                if score >= similarity_threshold:
                    scored_memories.append((memory, score))
            
            # Sort by score (descending) and limit results
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            results = [memory for memory, score in scored_memories[:limit]]
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("semantic_search")
                self.performance_monitor.record_query_time(0.2)
            
            logger.info(f"Semantic search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def analyze_knowledge_graph(
        self,
        analysis_type: str = "overview",
        memory_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze the knowledge graph and provide insights.
        
        Args:
            analysis_type: Type of analysis ('overview', 'centrality', 'connections')
            memory_id: Specific memory ID for focused analysis (optional)
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            if not self.memory_repository or not self.relation_repository:
                logger.error("Repositories not initialized")
                return {"error": "Repositories not initialized"}
            
            # Get memories and relations
            if memory_id:
                # Get specific memory and its relations
                memory = await self.memory_repository.find_by_id(memory_id)
                if not memory:
                    return {"error": f"Memory with ID {memory_id} not found"}
                    
                memories = [memory]
                relations = await self.relation_repository.find_by_memory_id(memory_id)
            else:
                # Get all memories and relations
                memories = await self.memory_repository.find_by_criteria({})
                relations = await self.relation_repository.find_all()
            
            analysis_result = {}
            
            if analysis_type == "overview":
                # Basic overview statistics
                analysis_result = {
                    "total_memories": len(memories),
                    "total_relations": len(relations),
                    "average_relations_per_memory": len(relations) / max(len(memories), 1),
                    "memories_with_relations": len(set(
                        rel.source_memory_id for rel in relations
                    ).union(
                        rel.target_memory_id for rel in relations
                    )),
                    "analysis_completed_at": datetime.utcnow().isoformat()
                }
                
                # Add memory categories if available
                categories = {}
                for memory in memories:
                    if memory.memory_metadata and memory.memory_metadata.get("category"):
                        category = memory.memory_metadata.get("category")
                        categories[category] = categories.get(category, 0) + 1
                
                if categories:
                    analysis_result["memory_categories"] = categories
            
            elif analysis_type == "centrality":
                # Simple centrality analysis (placeholder)
                # In a real implementation, this would calculate degree, betweenness, closeness centrality
                centrality_scores = {}
                
                # Calculate degree centrality (number of connections)
                memory_connections = {}
                for relation in relations:
                    memory_connections[relation.source_memory_id] = memory_connections.get(relation.source_memory_id, 0) + 1
                    memory_connections[relation.target_memory_id] = memory_connections.get(relation.target_memory_id, 0) + 1
                
                # Find most connected memories
                sorted_connections = sorted(memory_connections.items(), key=lambda x: x[1], reverse=True)
                
                analysis_result = {
                    "most_connected_memories": [
                        {"memory_id": mem_id, "connections": count}
                        for mem_id, count in sorted_connections[:5]
                    ],
                    "average_connections": sum(memory_connections.values()) / max(len(memories), 1),
                    "analysis_completed_at": datetime.utcnow().isoformat()
                }
            
            elif analysis_type == "connections":
                # Analyze connection patterns
                connection_types = {}
                memory_groups = {}  # Find clusters of related memories
                
                for relation in relations:
                    # Count relation types
                    relation_type = relation.name
                    connection_types[relation_type] = connection_types.get(relation_type, 0) + 1
                    
                    # Track connected memories (simplified clustering)
                    if relation.source_memory_id not in memory_groups:
                        memory_groups[relation.source_memory_id] = set()
                    if relation.target_memory_id not in memory_groups:
                        memory_groups[relation.target_memory_id] = set()
                    
                    memory_groups[relation.source_memory_id].add(relation.target_memory_id)
                    memory_groups[relation.target_memory_id].add(relation.source_memory_id)
                
                # Find clusters (simplified)
                clusters = []
                processed_memories = set()
                
                for memory_id in memory_groups:
                    if memory_id not in processed_memories:
                        cluster = set()
                        stack = [memory_id]
                        
                        while stack:
                            current_id = stack.pop()
                            if current_id not in processed_memories:
                                processed_memories.add(current_id)
                                cluster.add(current_id)
                                # Add connected memories
                                for connected_id in memory_groups.get(current_id, set()):
                                    if connected_id not in processed_memories:
                                        stack.append(connected_id)
                        
                        if len(cluster) > 1:  # Only include clusters with more than one memory
                            clusters.append(list(cluster))
                
                analysis_result = {
                    "connection_types": connection_types,
                    "number_of_clusters": len(clusters),
                    "cluster_sizes": [len(cluster) for cluster in clusters],
                    "largest_cluster_size": max([len(cluster) for cluster in clusters], default=0),
                    "analysis_completed_at": datetime.utcnow().isoformat()
                }
                
                if clusters:
                    analysis_result["example_clusters"] = clusters[:3]  # Show first 3 clusters
            
            else:
                analysis_result["error"] = f"Unknown analysis type: {analysis_type}"
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("knowledge_graph_analysis")
                self.performance_monitor.record_query_time(0.3)
            
            logger.info(f"Knowledge graph analysis ({analysis_type}) completed")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing knowledge graph: {e}")
            return {
                "error": str(e),
                "analysis_completed_at": datetime.utcnow().isoformat()
            }
    
    async def ingest_book(
        self,
        book_path: str,
        owner_id: str = "system",
        context_id: int = 1,
        enable_chunking: bool = True,
        chunk_size: int = 10000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ingest a book file, parse it into chapters, and store in the database.
        
        Args:
            book_path: Path to the book file
            owner_id: Owner ID for the book
            context_id: Context ID for the book
            enable_chunking: Enable chunked storage for large chapters
            chunk_size: Maximum size of chunks in characters
            
        Returns:
            Dictionary containing ingestion results
        """
        try:
            if not self.memory_repository:
                logger.error("Memory repository not initialized")
                return {"error": "Memory repository not initialized"}
            
            # Read book file (placeholder - in real implementation, use proper file reading)
            try:
                with open(book_path, 'r', encoding='utf-8') as file:
                    book_content = file.read()
            except Exception as e:
                logger.error(f"Error reading book file: {e}")
                return {"error": f"Error reading book file: {str(e)}"}
            
            # Simple chapter parsing (split by common chapter markers)
            import re
            chapters = re.split(r'\n\s*\n\s*(?:Chapter|第|chapter)\s+\d+', book_content)
            
            if len(chapters) < 2:
                # If no clear chapter markers, split by paragraphs
                chapters = [p.strip() for p in book_content.split('\n\n') if p.strip()]
            
            # Create memories for each chapter
            created_memories = []
            errors = []
            
            for i, chapter_content in enumerate(chapters, 1):
                try:
                    if not chapter_content.strip():
                        continue
                    
                    # Truncate very long chapters if chunking is enabled
                    content = chapter_content.strip()
                    if enable_chunking and len(content) > chunk_size:
                        # Split into chunks
                        chunks = [content[j:j+chunk_size] for j in range(0, len(content), chunk_size)]
                        
                        for chunk_idx, chunk in enumerate(chunks, 1):
                            title = f"Chapter {i}, Part {chunk_idx}"
                            
                            # Create memory for chunk
                            memory = await self.create_memory(
                                title=title,
                                content=chunk,
                                owner_id=owner_id,
                                context_id=context_id,
                                memory_metadata={
                                    "book_path": book_path,
                                    "chapter": i,
                                    "chunk": chunk_idx,
                                    "total_chunks": len(chunks),
                                    "is_book_chunk": True
                                }
                            )
                            
                            if memory:
                                created_memories.append(memory)
                    else:
                        # Create single memory for chapter
                        title = f"Chapter {i}"
                        
                        memory = await self.create_memory(
                            title=title,
                            content=content,
                            owner_id=owner_id,
                            context_id=context_id,
                            memory_metadata={
                                "book_path": book_path,
                                "chapter": i,
                                "is_book_chunk": False
                            }
                        )
                        
                        if memory:
                            created_memories.append(memory)
                            
                except Exception as e:
                    logger.error(f"Error processing chapter {i}: {e}")
                    errors.append(f"Chapter {i}: {str(e)}")
            
            # Create a summary memory for the book
            if created_memories:
                summary_content = f"Book ingested from {book_path}\n\n"
                summary_content += f"Total chapters: {len(chapters)}\n"
                summary_content += f"Created memories: {len(created_memories)}\n"
                summary_content += f"Owner: {owner_id}\n"
                summary_content += f"Context: {context_id}\n"
                
                summary_memory = await self.create_memory(
                    title=f"Summary: {book_path}",
                    content=summary_content,
                    owner_id=owner_id,
                    context_id=context_id,
                    memory_metadata={
                        "book_path": book_path,
                        "is_book_summary": True,
                        "total_chapters": len(chapters),
                        "total_memories": len(created_memories)
                    }
                )
                
                if summary_memory:
                    created_memories.append(summary_memory)
            
            # Record performance metrics
            if self.performance_monitor:
                self.performance_monitor.record_memory_operation("ingest_book")
                self.performance_monitor.record_query_time(0.5)
            
            return {
                "book_path": book_path,
                "total_chapters": len(chapters),
                "created_memories": len(created_memories),
                "errors": errors,
                "ingestion_complete": True,
                "ingested_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error ingesting book: {e}")
            return {
                "error": str(e),
                "ingestion_complete": False,
                "ingested_at": datetime.utcnow().isoformat()
            }
    
    # ========== HELPER METHODS ==========
    
    
    # ========== CONFIGURATION METHODS ==========
    # These replace the original configuration methods with cleaner implementations
    
    def set_compression_enabled(self, enabled: bool):
        """Enable or disable compression."""
        self.compression_enabled = enabled
        logger.info(f"Compression {'enabled' if enabled else 'disabled'}")
    
    def set_compression_algorithm(self, algorithm: str):
        """Set compression algorithm."""
        self.config['compression_algorithm'] = algorithm
        logger.info(f"Compression algorithm set to: {algorithm}")
        
    def set_compression_level(self, level: int):
        """Set compression level."""
        if level < 0 or level > 22:
            raise ValueError("Compression level must be between 0 and 22")
        self.config['compression_level'] = level
        logger.info(f"Compression level set to: {level}")
        
    def set_compression_threshold(self, threshold: int):
        """Set compression threshold."""
        if threshold < 0:
            raise ValueError("Compression threshold must be non-negative")
        self.config['compression_threshold'] = threshold
        logger.info(f"Compression threshold set to: {threshold}")
    
    def set_lazy_loading_enabled(self, enabled: bool):
        """Enable or disable lazy loading."""
        self.lazy_loading_enabled = enabled
        logger.info(f"Lazy loading {'enabled' if enabled else 'disabled'}")
        
    def set_preview_length(self, length: int):
        """Set preview length for lazy loading."""
        if length < 0:
            raise ValueError("Preview length must be non-negative")
        self.config['preview_length'] = length
        logger.info(f"Preview length set to: {length}")
        
    def set_eager_load_threshold(self, threshold: int):
        """Set eager load threshold."""
        if threshold < 0:
            raise ValueError("Eager load threshold must be non-negative")
        self.config['eager_load_threshold'] = threshold
        logger.info(f"Eager load threshold set to: {threshold}")
    
    def set_chunked_storage_enabled(self, enabled: bool):
        """Enable or disable chunked storage."""
        self.chunked_storage_enabled = enabled
        logger.info(f"Chunked storage {'enabled' if enabled else 'disabled'}")
    
    def set_chunk_size(self, size: int):
        """Configure chunk size."""
        if size <= 0:
            raise ValueError("Chunk size must be positive")
        self.chunk_size = size
        if self.chunked_storage_strategy:
            self.chunked_storage_strategy.configure_chunk_size(size)
        logger.info(f"Chunk size set to: {size}")
    
    def set_max_chunks(self, max_chunks: int):
        """Configure maximum chunks."""
        if max_chunks <= 0:
            raise ValueError("Max chunks must be positive")
        self.max_chunks = max_chunks
        if self.chunked_storage_strategy:
            self.chunked_storage_strategy.configure_max_chunks(max_chunks)
        logger.info(f"Max chunks set to: {max_chunks}")
    
    # ========== STATISTICS AND MONITORING ==========
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics using Repository pattern."""
        try:
            stats = {}
            
            # Repository statistics
            if self.memory_repository:
                repo_stats = await self.memory_repository.get_statistics()
                stats.update(repo_stats)
            else:
                logger.warning("Memory repository not initialized, skipping statistics")
            
            # Strategy statistics
            strategy_stats = {}
            
            if self.compression_strategy:
                # This would need to be implemented in compression strategies
                strategy_stats["compression"] = {"enabled": True, "algorithm": type(self.compression_strategy).__name__}
            
            if self.chunked_storage_strategy:
                chunked_stats = await self.chunked_storage_strategy.get_stats()
                strategy_stats["chunked_storage"] = chunked_stats
            
            stats["strategies"] = strategy_stats
            
            # Performance statistics
            if self.performance_monitor:
                perf_stats = self.performance_monitor.get_metrics_summary(hours=1)
                stats["performance"] = perf_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if self.performance_monitor:
            return self.performance_monitor.get_metrics_summary(hours=1)
        return {}
    
    # ========== CONTEXT METHODS ==========
    
    async def search_contexts(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs
    ) -> List[Context]:
        """Search contexts."""
        try:
            # For now, return empty list - context repository not fully implemented
            logger.warning("Context search not fully implemented yet")
            return []
        except Exception as e:
            logger.error(f"Error searching contexts: {e}")
            return []
    
    
    async def update_context(
        self,
        context_id: int,
        context_data: Dict[str, Any],
        **kwargs
    ) -> Optional[Context]:
        """Update context."""
        try:
            # For now, return None - context repository not fully implemented
            logger.warning("Context update not fully implemented yet")
            return None
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            return None
    
    async def delete_context(self, context_id: int, **kwargs) -> bool:
        """Delete context."""
        try:
            # For now, return False - context repository not fully implemented
            logger.warning("Context deletion not fully implemented yet")
            return False
        except Exception as e:
            logger.error(f"Error deleting context: {e}")
            return False
    
    # ========== RELATION METHODS ==========
    
    async def create_relation(
        self,
        name: str,
        source_memory_id: int,
        target_memory_id: int,
        strength: float = 1.0,
        relation_metadata: Optional[Dict[str, Any]] = None,
        owner_id: int = 1
    ) -> Optional[Relation]:
        """
        Create a new relation between memories.
        
        Args:
            name: Name/type of the relation
            source_memory_id: Source memory ID
            target_memory_id: Target memory ID
            strength: Relation strength (0-1)
            relation_metadata: Additional metadata
            owner_id: ID of the owner user
            
        Returns:
            Created Relation object or None if creation failed
        """
        try:
            if not self.relation_repository:
                logger.error("Relation repository not initialized")
                return None
                
            # Create relation entity
            from .models import Relation
            from datetime import datetime
            
            relation = Relation(
                name=name,
                source_memory_id=source_memory_id,
                target_memory_id=target_memory_id,
                strength=strength,
                relation_metadata=relation_metadata or {},
                owner_id=owner_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_active=True
            )
            
            # Use repository pattern
            return await self.relation_repository.create(relation)
                
        except Exception as e:
            logger.error(f"Error creating relation: {e}")
            return None
    
    async def get_memory_relations(self, memory_id: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get all relations for a specific memory.
        
        Args:
            memory_id: Memory ID to get relations for
            
        Returns:
            List of relation dictionaries
        """
        try:
            if not self.relation_repository:
                logger.error("Relation repository not initialized")
                return []
                
            relations = await self.relation_repository.find_by_memory_id(memory_id)
            
            # Convert to dictionaries for JSON serialization
            result = []
            for relation in relations:
                result.append({
                    "id": relation.id,
                    "name": relation.name,
                    "source_memory_id": relation.source_memory_id,
                    "target_memory_id": relation.target_memory_id,
                    "strength": relation.strength,
                    "relation_metadata": relation.relation_metadata or {},
                    "created_at": relation.created_at.isoformat() if relation.created_at else None
                })
            
            return result
                
        except Exception as e:
            logger.error(f"Error getting memory relations: {e}")
            return []
    
    async def bulk_create_relations(self, relations_data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Create multiple relations at once.
        
        Args:
            relations_data: List of relation data dictionaries
            
        Returns:
            List of created relation dictionaries
        """
        try:
            if not self.relation_repository:
                logger.error("Relation repository not initialized")
                return []
                
            created_relations = []
            
            for relation_data in relations_data:
                try:
                    relation = await self.create_relation(
                        name=relation_data.get("name"),
                        source_memory_id=relation_data.get("source_memory_id"),
                        target_memory_id=relation_data.get("target_memory_id"),
                        strength=relation_data.get("strength", 1.0),
                        relation_metadata=relation_data.get("relation_metadata"),
                        owner_id=relation_data.get("owner_id", 1)
                    )
                    
                    if relation:
                        created_relations.append({
                            "id": relation.id,
                            "name": relation.name,
                            "source_memory_id": relation.source_memory_id,
                            "target_memory_id": relation.target_memory_id,
                            "strength": relation.strength,
                            "relation_metadata": relation.relation_metadata or {}
                        })
                        
                except Exception as e:
                    logger.error(f"Error creating relation in bulk operation: {e}")
                    continue
            
            return created_relations
            
        except Exception as e:
            logger.error(f"Error in bulk create relations: {e}")
            return []
    
    async def search_relations(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs
    ) -> List[Relation]:
        """Search relations."""
        try:
            # For now, return empty list - relation repository not fully implemented
            logger.warning("Relation search not fully implemented yet")
            return []
        except Exception as e:
            logger.error(f"Error searching relations: {e}")
            return []
    
    
    async def update_relation(
        self,
        relation_id: int,
        relation_data: Dict[str, Any],
        **kwargs
    ) -> Optional[Relation]:
        """Update relation."""
        try:
            # For now, return None - relation repository not fully implemented
            logger.warning("Relation update not fully implemented yet")
            return None
        except Exception as e:
            logger.error(f"Error updating relation: {e}")
            return None
    
    async def delete_relation(self, relation_id: int, **kwargs) -> bool:
        """Delete relation."""
        try:
            # For now, return False - relation repository not fully implemented
            logger.warning("Relation deletion not fully implemented yet")
            return False
        except Exception as e:
            logger.error(f"Error deleting relation: {e}")
            return False

    # ========== LEGACY COMPATIBILITY METHODS ==========
    # These provide compatibility with the old interface while using new patterns
    
    async def get_memory_by_id(self, memory_id: int, **kwargs) -> Optional[Memory]:
        """Legacy compatibility method."""
        return await self.get_memory(memory_id, **kwargs)
    
    async def get_all_memories(self, limit: Optional[int] = None, **kwargs) -> List[Memory]:
        """Legacy compatibility method."""
        if self.memory_repository:
            return await self.memory_repository.find_by_criteria({})
        return []
    
    async def get_memory_count(self) -> int:
        """Legacy compatibility method."""
        if self.memory_repository:
            return await self.memory_repository.count()
        return 0
    
    async def get_memory_statistics(self, include_content_analysis: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive memory statistics.
        
        Args:
            include_content_analysis: Whether to include detailed content analysis
            
        Returns:
            Dictionary containing memory statistics
        """
        try:
            if not self.memory_repository:
                return {}
            
            # Get basic statistics from repository
            stats = await self.memory_repository.get_statistics()
            
            # Add additional statistics
            total_memories = stats.get("total_memories", 0)
            compressed_count = stats.get("compressed_memories", 0)
            
            # Get category breakdown
            categories = {}
            if include_content_analysis:
                # This would typically involve more complex analysis
                # For now, we'll get a simple breakdown by access level
                try:
                    all_memories = await self.memory_repository.find_by_criteria({})
                    for memory in all_memories:
                        if memory.access_level:
                            categories[memory.access_level] = categories.get(memory.access_level, 0) + 1
                        else:
                            categories["uncategorized"] = categories.get("uncategorized", 0) + 1
                except Exception as e:
                    logger.warning(f"Could not analyze categories: {e}")
            
            # Get date range
            oldest_date = None
            newest_date = None
            try:
                all_memories = await self.memory_repository.find_by_criteria({})
                if all_memories:
                    dates = [m.created_at for m in all_memories if m.created_at]
                    if dates:
                        oldest_date = min(dates).isoformat()
                        newest_date = max(dates).isoformat()
            except Exception as e:
                logger.warning(f"Could not determine date range: {e}")
            
            # Compile final statistics
            result = {
                "total_memories": total_memories,
                "compressed_memories": compressed_count,
                "compression_ratio": compressed_count / max(total_memories, 1),
                "categories": categories,
                "oldest_memory_date": oldest_date,
                "newest_memory_date": newest_date,
                "include_content_analysis": include_content_analysis
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting memory statistics: {e}")
            return {}
    
    
    
    
    
    # ========== INITIALIZATION AND CLEANUP ==========
    
    async def initialize(self):
        """Initialize the database with all components."""
        try:
            logger.info("Initializing RefactoredMemoryDB...")
            
            # Initialize database connection if needed
            if not self.session:
                from .session import SessionLocal
                self.session = SessionLocal()
            
            # Initialize repositories if not already done
            self._init_repositories({})
            self._init_strategies({})
            self._init_services({})
            
            logger.info("RefactoredMemoryDB initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RefactoredMemoryDB: {e}")
            raise
    
    async def initialize_hybrid_storage(self):
        """Initialize hybrid storage system."""
        try:
            # Initialize hybrid storage if strategy is available
            if self.hybrid_storage_strategy:
                await self.hybrid_storage_strategy.initialize()
            logger.info("Hybrid storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize hybrid storage: {e}")
            # Don't raise - this is optional functionality
    
    async def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            from .models import Base
            from sqlalchemy import create_engine
            
            engine = create_engine(self.db_url)
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def load_initial_data(self):
        """Load any initial data required by the system."""
        try:
            # This could load default users, contexts, etc.
            # For now, it's a placeholder that can be extended
            logger.info("Initial data loading completed")
            
        except Exception as e:
            logger.error(f"Failed to load initial data: {e}")
            # Don't raise - this is optional functionality
    
    async def check_connection(self):
        """Check database connection health."""
        try:
            if self.session:
                # Simple query to check connection
                self.session.execute("SELECT 1")
                return True
            else:
                raise Exception("No database session available")
            
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        try:
            if self.session:
                self.session.close()
            logger.info("RefactoredMemoryDB closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing RefactoredMemoryDB: {e}")


# ========== FACTORY FOR CREATING REFACTORED DB ==========

class RefactoredMemoryDBFactory:
    """
    Factory for creating RefactoredMemoryDB instances with different configurations.
    Implements the Factory pattern for flexible object creation.
    """
    
    @staticmethod
    def create_default(db_url: str, session: Optional[Session] = None) -> RefactoredMemoryDB:
        """Create a RefactoredMemoryDB with default configuration."""
        config = {
            'lazy_loading_enabled': True,
            'compression_enabled': True,
            'chunked_storage_enabled': False,
            'chunk_size': 10000,
            'max_chunks': 100,
            'compression_algorithm': 'adaptive'
        }
        
        return RefactoredMemoryDB(
            db_url=db_url,
            session=session,
            config=config
        )
    
    @staticmethod
    def create_high_performance(db_url: str, session: Optional[Session] = None) -> RefactoredMemoryDB:
        """Create a RefactoredMemoryDB optimized for high performance."""
        config = {
            'lazy_loading_enabled': False,  # Eager loading for performance
            'compression_enabled': True,
            'chunked_storage_enabled': True,  # Better for large content
            'chunk_size': 8192,  # Optimized chunk size
            'max_chunks': 200,
            'compression_algorithm': 'zstd'  # Fast compression
        }
        
        return RefactoredMemoryDB(
            db_url=db_url,
            session=session,
            config=config
        )
    
    @staticmethod
    def create_memory_optimized(db_url: str, session: Optional[Session] = None) -> RefactoredMemoryDB:
        """Create a RefactoredMemoryDB optimized for memory usage."""
        config = {
            'lazy_loading_enabled': True,  # Save memory
            'compression_enabled': True,
            'chunked_storage_enabled': True,
            'chunk_size': 4096,  # Smaller chunks
            'max_chunks': 50,
            'compression_algorithm': 'adaptive'  # Best compression
        }
        
        return RefactoredMemoryDB(
            db_url=db_url,
            session=session,
            config=config
        )