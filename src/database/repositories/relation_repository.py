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
RelationRepository for database operations on Relation entities.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from ..models import Relation

logger = logging.getLogger(__name__)

class RelationRepository:
    """Repository for Relation database operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, relation: Relation) -> Relation:
        """Create a new relation."""
        try:
            self.session.add(relation)
            self.session.commit()
            self.session.refresh(relation)
            return relation
        except Exception as e:
            logger.error(f"Error creating relation: {e}")
            self.session.rollback()
            raise
    
    def find_by_id(self, relation_id: int) -> Optional[Relation]:
        """Find a relation by ID."""
        try:
            result = self.session.execute(
                select(Relation).where(Relation.id == relation_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding relation by ID {relation_id}: {e}")
            return None
    
    def find_by_memory_id(self, memory_id: int) -> List[Relation]:
        """Find all relations for a specific memory (as source or target)."""
        try:
            result = self.session.execute(
                select(Relation).where(
                    or_(
                        Relation.source_memory_id == memory_id,
                        Relation.target_memory_id == memory_id
                    )
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding relations for memory {memory_id}: {e}")
            return []
    
    def find_by_source_memory(self, source_memory_id: int) -> List[Relation]:
        """Find all relations where the memory is the source."""
        try:
            result = self.session.execute(
                select(Relation).where(Relation.source_memory_id == source_memory_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding relations for source memory {source_memory_id}: {e}")
            return []
    
    def find_by_target_memory(self, target_memory_id: int) -> List[Relation]:
        """Find all relations where the memory is the target."""
        try:
            result = self.session.execute(
                select(Relation).where(Relation.target_memory_id == target_memory_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding relations for target memory {target_memory_id}: {e}")
            return []

    def find_by_name(self, name: str) -> List[Relation]:
        """Find all relations with a specific name."""
        try:
            result = self.session.execute(
                select(Relation).where(Relation.name == name)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding relations with name {name}: {e}")
            return []

    def find_all(self) -> List[Relation]:
        """Find all relations."""
        try:
            result = self.session.execute(select(Relation))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding all relations: {e}")
            return []
    
    def find_by_strength_range(self, min_strength: float, max_strength: float) -> List[Relation]:
        """Find all relations with strength in the specified range."""
        try:
            result = self.session.execute(
                select(Relation).where(
                    and_(
                        Relation.strength >= min_strength,
                        Relation.strength <= max_strength
                    )
                )
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding relations with strength range {min_strength}-{max_strength}: {e}")
            return []

    def update(self, relation: Relation) -> Optional[Relation]:
        """Update an existing relation."""
        try:
            self.session.commit()
            self.session.refresh(relation)
            return relation
        except Exception as e:
            logger.error(f"Error updating relation {relation.id}: {e}")
            self.session.rollback()
            return None

    def delete(self, relation_id: int) -> bool:
        """Delete a relation by ID."""
        try:
            relation = self.find_by_id(relation_id)
            if not relation:
                return False

            self.session.delete(relation)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting relation {relation_id}: {e}")
            self.session.rollback()
            return False

    def count(self) -> int:
        """Count total number of relations."""
        try:
            result = self.session.execute(select(Relation))
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error counting relations: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get relation statistics."""
        try:
            # Total relations
            total_relations = self.count()

            # Relation type distribution
            relation_types = {}
            all_relations = self.session.execute(select(Relation))
            for relation in all_relations.scalars().all():
                rel_name = relation.name or "unknown"
                relation_types[rel_name] = relation_types.get(rel_name, 0) + 1

            # Strength distribution
            strength_ranges = {
                "weak": 0,      # 0.0 - 0.3
                "medium": 0,    # 0.3 - 0.7
                "strong": 0     # 0.7 - 1.0
            }

            all_relations = self.session.execute(select(Relation))
            for relation in all_relations.scalars().all():
                strength = relation.strength or 0.0
                if strength < 0.3:
                    strength_ranges["weak"] += 1
                elif strength < 0.7:
                    strength_ranges["medium"] += 1
                else:
                    strength_ranges["strong"] += 1

            # Memory participation (how many memories have relations)
            from sqlalchemy import func
            memory_counts = self.session.execute(
                select(
                    func.count(func.distinct(Relation.source_memory_id)).label("source_memories"),
                    func.count(func.distinct(Relation.target_memory_id)).label("target_memories")
                )
            )
            row = memory_counts.fetchone()
            source_memories = row[0] if row else 0
            target_memories = row[1] if row else 0

            return {
                "total_relations": total_relations,
                "relation_type_distribution": relation_types,
                "strength_distribution": strength_ranges,
                "memories_with_relations": max(source_memories, target_memories),
                "average_relations_per_memory": total_relations / max(source_memories, 1)
            }

        except Exception as e:
            logger.error(f"Error getting relation statistics: {e}")
            return {}