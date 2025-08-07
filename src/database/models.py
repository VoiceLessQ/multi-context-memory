"""
SQLAlchemy models for the enhanced MCP Multi-Context Memory System.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as JSONColumn

Base = declarative_base()

class User(Base):
    """User model for authentication and access control."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contexts = relationship("Context", back_populates="owner")
    memories = relationship("Memory", back_populates="owner")
    relations = relationship("Relation", back_populates="owner")

class Context(Base):
    """Context model for organizing memories."""
    __tablename__ = "contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    access_level = Column(String(20), default="user")  # public, user, privileged, admin
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    context_metadata = Column(JSONColumn, nullable=True)  # Additional context metadata
    
    # Relationships
    owner = relationship("User", back_populates="contexts")
    memories = relationship("Memory", back_populates="context")
    relations = relationship("Relation", back_populates="source_context")

class Memory(Base):
    """Memory model for storing knowledge entities."""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    access_level = Column(String(20), default="user")  # public, user, privileged, admin
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    context_id = Column(Integer, ForeignKey("contexts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    memory_metadata = Column(JSONColumn, nullable=True)  # Additional memory metadata
    embedding_vector = Column(LargeBinary, nullable=True)  # For storing numpy arrays
    
    # Relationships
    owner = relationship("User", back_populates="memories")
    context = relationship("Context", back_populates="memories")
    relations = relationship("Relation", back_populates="target_memory")
    
    @property
    def embedding(self):
        """Get embedding as numpy array"""
        if self.embedding_vector:
            import numpy as np
            return np.frombuffer(self.embedding_vector, dtype=np.float32)
        return None
    
    @embedding.setter
    def embedding(self, value):
        """Set embedding from numpy array"""
        if value is not None:
            import numpy as np
            self.embedding_vector = np.array(value, dtype=np.float32).tobytes()
        else:
            self.embedding_vector = None

class Relation(Base):
    """Relation model for defining relationships between memories and contexts."""
    __tablename__ = "relations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "contains", "related_to", "parent_of"
    source_context_id = Column(Integer, ForeignKey("contexts.id"), nullable=True)
    target_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True)
    source_memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True)
    target_context_id = Column(Integer, ForeignKey("contexts.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strength = Column(Float, default=1.0)  # Relationship strength (0.0 to 1.0)
    relation_metadata = Column(JSONColumn, nullable=True)  # Additional relation metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User", back_populates="relations")
    source_context = relationship("Context", foreign_keys=[source_context_id], back_populates="relations")
    target_memory = relationship("Memory", foreign_keys=[target_memory_id], back_populates="relations")
    source_memory = relationship("Memory", foreign_keys=[source_memory_id])
    target_context = relationship("Context", foreign_keys=[target_context_id])

class MemoryVersion(Base):
    """MemoryVersion model for tracking memory changes."""
    __tablename__ = "memory_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_description = Column(Text, nullable=True)
    version_metadata = Column(JSONColumn, nullable=True)
    
    # Relationships
    memory = relationship("Memory")
    creator = relationship("User")

class SearchHistory(Base):
    """SearchHistory model for tracking search queries."""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    search_metadata = Column(JSONColumn, nullable=True)  # Additional search metadata
    
    # Relationships
    user = relationship("User")

class SystemConfig(Base):
    """SystemConfig model for system-wide configuration."""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    updater = relationship("User")

class AuditLog(Base):
    """AuditLog model for tracking system changes."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., "create", "update", "delete"
    resource_type = Column(String(50), nullable=False)  # e.g., "memory", "context", "user"
    resource_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audit_details = Column(JSONColumn, nullable=True)  # Additional details about the action
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")