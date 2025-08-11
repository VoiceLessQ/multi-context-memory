"""
ContextRepository for database operations on Context entities.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Context

logger = logging.getLogger(__name__)

class ContextRepository:
    """Repository for Context database operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, context: Context) -> Context:
        """Create a new context."""
        try:
            self.session.add(context)
            self.session.commit()
            self.session.refresh(context)
            return context
        except Exception as e:
            logger.error(f"Error creating context: {e}")
            self.session.rollback()
            raise
    
    async def find_by_id(self, context_id: int) -> Optional[Context]:
        """Find a context by ID."""
        try:
            result = await self.session.execute(
                select(Context).where(Context.id == context_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding context by ID {context_id}: {e}")
            return None
    
    async def find_by_name(self, name: str) -> Optional[Context]:
        """Find a context by name."""
        try:
            result = await self.session.execute(
                select(Context).where(Context.name == name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding context by name {name}: {e}")
            return None
    
    async def find_by_owner(self, owner_id: int) -> List[Context]:
        """Find all contexts for a specific owner."""
        try:
            result = await self.session.execute(
                select(Context).where(Context.owner_id == owner_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding contexts for owner {owner_id}: {e}")
            return []
    
    async def find_by_access_level(self, access_level: str) -> List[Context]:
        """Find all contexts with a specific access level."""
        try:
            result = await self.session.execute(
                select(Context).where(Context.access_level == access_level)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding contexts with access level {access_level}: {e}")
            return []
    
    async def find_active(self) -> List[Context]:
        """Find all active contexts."""
        try:
            result = await self.session.execute(
                select(Context).where(Context.is_active == True)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding active contexts: {e}")
            return []
    
    async def update(self, context: Context) -> Optional[Context]:
        """Update an existing context."""
        try:
            self.session.commit()
            self.session.refresh(context)
            return context
        except Exception as e:
            logger.error(f"Error updating context {context.id}: {e}")
            self.session.rollback()
            return None
    
    async def delete(self, context_id: int) -> bool:
        """Delete a context by ID."""
        try:
            context = await self.find_by_id(context_id)
            if not context:
                return False
            
            self.session.delete(context)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting context {context_id}: {e}")
            self.session.rollback()
            return False
    
    async def count(self) -> int:
        """Count total number of contexts."""
        try:
            result = await self.session.execute(select(Context))
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error counting contexts: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get context statistics."""
        try:
            # Total contexts
            total_contexts = await self.count()
            
            # Active contexts
            active_contexts = len(await self.find_active())
            
            # Access level distribution
            access_levels = {}
            for level in ["public", "user", "privileged", "admin"]:
                contexts = await self.find_by_access_level(level)
                access_levels[level] = len(contexts)
            
            # Owner distribution
            from sqlalchemy import func
            owner_counts = await self.session.execute(
                select(Context.owner_id, func.count(Context.id))
                .group_by(Context.owner_id)
            )
            owner_distribution = {row[0]: row[1] for row in owner_counts}
            
            return {
                "total_contexts": total_contexts,
                "active_contexts": active_contexts,
                "inactive_contexts": total_contexts - active_contexts,
                "access_level_distribution": access_levels,
                "owner_distribution": owner_distribution
            }
            
        except Exception as e:
            logger.error(f"Error getting context statistics: {e}")
            return {}