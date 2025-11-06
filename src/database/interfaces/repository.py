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
Repository interfaces for data access abstraction.
Following the Repository pattern to separate data access from business logic.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime

from ..models import Memory, Context, Relation, MemoryChunk


class MemoryRepository(ABC):
    """
    Abstract repository interface for Memory entities.
    Implements the Repository pattern for clean separation of data access.
    """
    
    @abstractmethod
    async def create(self, memory: Memory) -> Memory:
        """Create a new memory entity."""
        pass
    
    @abstractmethod
    async def find_by_id(self, memory_id: int) -> Optional[Memory]:
        """Find memory by ID."""
        pass
    
    @abstractmethod
    async def find_by_owner(self, owner_id: str, limit: int = 100) -> List[Memory]:
        """Find memories by owner."""
        pass
    
    @abstractmethod
    async def find_by_context(self, context_id: int, limit: int = 100) -> List[Memory]:
        """Find memories by context."""
        pass
    
    @abstractmethod
    async def search(self, query: str, filters: Dict[str, Any], limit: int = 100) -> List[Memory]:
        """Search memories with filters."""
        pass
    
    @abstractmethod
    async def update(self, memory_id: int, updates: Dict[str, Any]) -> Optional[Memory]:
        """Update memory entity."""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: int) -> bool:
        """Delete memory entity."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total memory count."""
        pass


class ContextRepository(ABC):
    """Abstract repository interface for Context entities."""
    
    @abstractmethod
    async def create(self, context: Context) -> Context:
        """Create a new context entity."""
        pass
    
    @abstractmethod
    async def find_by_id(self, context_id: int) -> Optional[Context]:
        """Find context by ID."""
        pass
    
    @abstractmethod
    async def find_by_owner(self, owner_id: str, limit: int = 100) -> List[Context]:
        """Find contexts by owner."""
        pass
    
    @abstractmethod
    async def update(self, context_id: int, updates: Dict[str, Any]) -> Optional[Context]:
        """Update context entity."""
        pass
    
    @abstractmethod
    async def delete(self, context_id: int) -> bool:
        """Delete context entity."""
        pass


class RelationRepository(ABC):
    """Abstract repository interface for Relation entities."""
    
    @abstractmethod
    async def create(self, relation: Relation) -> Relation:
        """Create a new relation entity."""
        pass
    
    @abstractmethod
    async def find_by_id(self, relation_id: int) -> Optional[Relation]:
        """Find relation by ID."""
        pass
    
    @abstractmethod
    async def find_by_memory(self, memory_id: int) -> List[Relation]:
        """Find relations for a memory."""
        pass
    
    @abstractmethod
    async def update(self, relation_id: int, updates: Dict[str, Any]) -> Optional[Relation]:
        """Update relation entity."""
        pass
    
    @abstractmethod
    async def delete(self, relation_id: int) -> bool:
        """Delete relation entity."""
        pass


class ChunkRepository(ABC):
    """Abstract repository interface for MemoryChunk entities."""
    
    @abstractmethod
    async def create(self, chunk: MemoryChunk) -> MemoryChunk:
        """Create a new chunk entity."""
        pass
    
    @abstractmethod
    async def find_by_memory(self, memory_id: int) -> List[MemoryChunk]:
        """Find chunks for a memory."""
        pass
    
    @abstractmethod
    async def update(self, chunk_id: int, updates: Dict[str, Any]) -> Optional[MemoryChunk]:
        """Update chunk entity."""
        pass
    
    @abstractmethod
    async def delete(self, chunk_id: int) -> bool:
        """Delete chunk entity."""
        pass
    
    @abstractmethod
    async def delete_by_memory(self, memory_id: int) -> bool:
        """Delete all chunks for a memory."""
        pass


class UnitOfWork(Protocol):
    """
    Unit of Work interface for managing transactions.
    Ensures consistency across repository operations.
    """
    
    def __enter__(self):
        pass
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass