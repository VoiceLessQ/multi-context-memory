from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import Memory

class DatabaseInterface(ABC):
    """Abstract interface for database operations required by DeduplicationManager."""

    @abstractmethod
    def get_memory(self, memory_id: int, **kwargs) -> Optional[Memory]:
        """
        Retrieve a single memory by its ID.
        
        Args:
            memory_id: The ID of the memory to retrieve.
            **kwargs: Additional arguments for getting memory (e.g., decompress, use_lazy_loading).
            
        Returns:
            Memory object if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_all_memories(self, limit: Optional[int] = None, **kwargs) -> List[Memory]:
        """
        Retrieve all memories from the database.
        
        Args:
            limit: Optional maximum number of memories to retrieve.
            **kwargs: Additional arguments for getting memories.
            
        Returns:
            List of Memory objects.
        """
        pass

    @abstractmethod
    def update_memory(self, memory_id: int, updates: Dict[str, Any], **kwargs) -> Optional[Memory]:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update.
            updates: A dictionary of fields to update.
            **kwargs: Additional arguments for updating memory.
            
        Returns:
            Updated Memory object if successful, None otherwise.
        """
        pass

    @abstractmethod
    def update_relations(self, old_memory_id: int, new_memory_id: int) -> bool:
        """
        Update all relations pointing from old_memory_id to new_memory_id.
        
        Args:
            old_memory_id: The ID of the memory to be replaced.
            new_memory_id: The ID of the memory to replace it with.
            
        Returns:
            True if update was successful, False otherwise.
        """
        pass

    @abstractmethod
    def delete_memory(self, memory_id: int, **kwargs) -> bool:
        """
        Delete a memory from the database.
        
        Args:
            memory_id: The ID of the memory to delete.
            **kwargs: Additional arguments for deleting memory.
            
        Returns:
            True if deletion was successful, False otherwise.
        """
        pass