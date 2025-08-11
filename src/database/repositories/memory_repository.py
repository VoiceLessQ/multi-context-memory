"""
SQLAlchemy-based Memory Repository implementation.
Extracts data access logic from the monolithic enhanced_memory_db.py.
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from ..interfaces.repository import MemoryRepository
from ..models import Memory

logger = logging.getLogger(__name__)


class SQLAlchemyMemoryRepository(MemoryRepository):
    """
    SQLAlchemy implementation of MemoryRepository.
    Focused solely on data access operations.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    async def create(self, memory: Memory) -> Memory:
        """Create a new memory entity."""
        try:
            self.session.add(memory)
            self.session.commit()
            self.session.refresh(memory)
            logger.info(f"Created memory: {memory.id} - {memory.title}")
            return memory
        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            self.session.rollback()
            raise
    
    async def find_by_id(self, memory_id: int) -> Optional[Memory]:
        """Find memory by ID."""
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            return memory
        except Exception as e:
            logger.error(f"Error finding memory {memory_id}: {e}")
            return None
    
    async def find_by_owner(self, owner_id: str, limit: int = 100) -> List[Memory]:
        """Find memories by owner."""
        try:
            memories = (
                self.session.query(Memory)
                .filter(Memory.owner_id == owner_id)
                .limit(limit)
                .all()
            )
            logger.info(f"Found {len(memories)} memories for owner: {owner_id}")
            return memories
        except Exception as e:
            logger.error(f"Error finding memories by owner {owner_id}: {e}")
            return []
    
    async def find_by_context(self, context_id: int, limit: int = 100) -> List[Memory]:
        """Find memories by context."""
        try:
            memories = (
                self.session.query(Memory)
                .filter(Memory.context_id == context_id)
                .limit(limit)
                .all()
            )
            logger.info(f"Found {len(memories)} memories in context: {context_id}")
            return memories
        except Exception as e:
            logger.error(f"Error finding memories by context {context_id}: {e}")
            return []
    
    async def search(self, query: str, filters: Dict[str, Any], limit: int = 100) -> List[Memory]:
        """Search memories with filters."""
        try:
            # Build base query
            db_query = self.session.query(Memory)
            
            # Apply search query
            if query:
                search_filter = or_(
                    Memory.title.contains(query),
                    Memory.content.contains(query)
                )
                db_query = db_query.filter(search_filter)
            
            # Apply filters
            if "owner_id" in filters:
                db_query = db_query.filter(Memory.owner_id == filters["owner_id"])
            
            if "context_id" in filters:
                db_query = db_query.filter(Memory.context_id == filters["context_id"])
            
            if "access_level" in filters:
                db_query = db_query.filter(Memory.access_level == filters["access_level"])
            
            if "created_after" in filters:
                db_query = db_query.filter(Memory.created_at >= filters["created_after"])
            
            if "created_before" in filters:
                db_query = db_query.filter(Memory.created_at <= filters["created_before"])
            
            # Apply limit and execute
            memories = db_query.limit(limit).all()
            
            logger.info(f"Found {len(memories)} memories matching query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def update(self, memory_id: int, updates: Dict[str, Any]) -> Optional[Memory]:
        """Update memory entity."""
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            
            if not memory:
                logger.warning(f"Memory not found for update: {memory_id}")
                return None
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(memory, field):
                    setattr(memory, field, value)
                else:
                    logger.warning(f"Field {field} not found in Memory model")
            
            memory.updated_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"Updated memory: {memory.id}")
            return memory
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            self.session.rollback()
            return None
    
    async def delete(self, memory_id: int) -> bool:
        """Delete memory entity."""
        try:
            memory = self.session.query(Memory).filter(Memory.id == memory_id).first()
            
            if not memory:
                logger.warning(f"Memory not found for deletion: {memory_id}")
                return False
            
            self.session.delete(memory)
            self.session.commit()
            
            logger.info(f"Deleted memory: {memory_id} - {memory.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            self.session.rollback()
            return False
    
    async def count(self) -> int:
        """Get total memory count."""
        try:
            count = self.session.query(Memory).count()
            return count
        except Exception as e:
            logger.error(f"Error counting memories: {e}")
            return 0
    
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Memory]:
        """Find memories by multiple criteria."""
        try:
            query = self.session.query(Memory)
            
            conditions = []
            
            # Build conditions dynamically
            for field, value in criteria.items():
                if hasattr(Memory, field):
                    if isinstance(value, list):
                        conditions.append(getattr(Memory, field).in_(value))
                    elif isinstance(value, dict) and "operator" in value:
                        # Handle complex conditions
                        column = getattr(Memory, field)
                        operator = value["operator"]
                        operand = value["value"]
                        
                        if operator == "gt":
                            conditions.append(column > operand)
                        elif operator == "lt":
                            conditions.append(column < operand)
                        elif operator == "gte":
                            conditions.append(column >= operand)
                        elif operator == "lte":
                            conditions.append(column <= operand)
                        elif operator == "like":
                            conditions.append(column.like(f"%{operand}%"))
                        elif operator == "ilike":
                            conditions.append(column.ilike(f"%{operand}%"))
                    else:
                        conditions.append(getattr(Memory, field) == value)
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            memories = query.all()
            logger.info(f"Found {len(memories)} memories matching criteria")
            return memories
            
        except Exception as e:
            logger.error(f"Error finding memories by criteria: {e}")
            return []
    
    async def get_compressed_memories(self) -> List[Memory]:
        """Get all compressed memories."""
        try:
            memories = (
                self.session.query(Memory)
                .filter(Memory.content_compressed == True)
                .all()
            )
            return memories
        except Exception as e:
            logger.error(f"Error getting compressed memories: {e}")
            return []
    
    async def get_large_memories(self, size_threshold: int = 10000) -> List[Memory]:
        """Get memories above size threshold."""
        try:
            memories = (
                self.session.query(Memory)
                .filter(Memory.content_size > size_threshold)
                .all()
            )
            return memories
        except Exception as e:
            logger.error(f"Error getting large memories: {e}")
            return []
    
    async def get_memories_by_access_pattern(self, pattern: str) -> List[Memory]:
        """Get memories by access pattern (frequent, rare, recent, old)."""
        try:
            query = self.session.query(Memory)
            
            if pattern == "frequent":
                query = query.filter(Memory.access_count > 10).order_by(Memory.access_count.desc())
            elif pattern == "rare":
                query = query.filter(Memory.access_count <= 3).order_by(Memory.access_count.asc())
            elif pattern == "recent":
                cutoff = datetime.utcnow().replace(day=datetime.utcnow().day - 7)  # Last week
                query = query.filter(Memory.last_accessed >= cutoff).order_by(Memory.last_accessed.desc())
            elif pattern == "old":
                cutoff = datetime.utcnow().replace(month=datetime.utcnow().month - 3)  # 3 months ago
                query = query.filter(Memory.last_accessed <= cutoff).order_by(Memory.last_accessed.asc())
            else:
                logger.warning(f"Unknown access pattern: {pattern}")
                return []
            
            memories = query.limit(100).all()
            return memories
            
        except Exception as e:
            logger.error(f"Error getting memories by access pattern {pattern}: {e}")
            return []
    
    async def bulk_update(self, memory_ids: List[int], updates: Dict[str, Any]) -> int:
        """Bulk update multiple memories."""
        try:
            updated_count = (
                self.session.query(Memory)
                .filter(Memory.id.in_(memory_ids))
                .update(updates, synchronize_session=False)
            )
            self.session.commit()
            
            logger.info(f"Bulk updated {updated_count} memories")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error bulk updating memories: {e}")
            self.session.rollback()
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get repository-level statistics."""
        try:
            total_memories = await self.count()
            compressed_count = len(await self.get_compressed_memories())
            
            # Size statistics
            size_stats = (
                self.session.query(
                    self.session.query(Memory.content_size).func.avg().label('avg_size'),
                    self.session.query(Memory.content_size).func.max().label('max_size'),
                    self.session.query(Memory.content_size).func.min().label('min_size')
                ).first()
            )
            
            # Access pattern statistics
            access_stats = (
                self.session.query(
                    self.session.query(Memory.access_count).func.sum().label('total_accesses'),
                    self.session.query(Memory.access_count).func.avg().label('avg_accesses')
                ).first()
            )
            
            return {
                "total_memories": total_memories,
                "compressed_memories": compressed_count,
                "compression_ratio": compressed_count / max(total_memories, 1),
                "average_size": size_stats.avg_size or 0,
                "max_size": size_stats.max_size or 0,
                "min_size": size_stats.min_size or 0,
                "total_accesses": access_stats.total_accesses or 0,
                "average_accesses": access_stats.avg_accesses or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}