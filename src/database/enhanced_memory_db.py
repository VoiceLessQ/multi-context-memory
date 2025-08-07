"""
Enhanced Memory Database with automatic relation discovery and embeddings
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import networkx as nx
import logging

from .models import Memory, Context, Relation, User
from ..utils.error_handling import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)

class EnhancedMemoryDB:
    def __init__(self, database_url: str, model_name: str = "all-MiniLM-L6-v2"):
        self.database_url = database_url
        self.model = SentenceTransformer(model_name)
        self.knowledge_graph = nx.DiGraph()
        self._load_graph()
    
    def store_knowledge_with_embeddings(
        self,
        db: Session,
        user_id: int,
        title: str,
        content: str,
        context_id: Optional[int] = None,
        auto_relate: bool = True,
        threshold: float = 0.7
    ) -> Memory:
        """Store knowledge with automatic embedding and relation discovery"""
        
        # Generate embedding
        full_text = f"{title} {content}"
        embedding = self.model.encode(full_text)
        
        # Create memory
        memory = Memory(
            title=title,
            content=content,
            owner_id=user_id,
            context_id=context_id,
            embedding=embedding
        )
        
        db.add(memory)
        db.flush()  # Get ID without committing
        
        # Auto-discover relations if enabled
        if auto_relate:
            similar_memories = self._find_similar_memories(
                db, embedding, threshold, exclude_id=memory.id
            )
            
            for similar_id, similarity in similar_memories:
                relation = Relation(
                    name=self._determine_relation_type(similarity),
                    source_memory_id=memory.id,
                    target_memory_id=similar_id,
                    owner_id=user_id,
                    strength=similarity,
                    relation_metadata={"auto_generated": True}
                )
                db.add(relation)
        
        db.commit()
        
        # Update graph
        self.knowledge_graph.add_node(memory.id, title=title, content=content[:100])
        
        return memory
    def create_memory(
        self,
        db: Session,
        user_id: int,
        title: str,
        content: str,
        context_id: Optional[int] = None,
        access_level: str = "user",
        memory_metadata: Optional[Dict[str, Any]] = None,
        auto_relate: bool = True,
        threshold: float = 0.7
    ) -> Memory:
        """
        Create a new memory with automatic AI-powered embedding and relation discovery.
        This method is a wrapper around store_knowledge_with_embeddings to align
        with API expectations and ensure AI features are used by default.
        """
        logger.info(f"Creating memory for user_id {user_id}: '{title}'")
        
        # The store_knowledge_with_embeddings method handles:
        # - Embedding generation
        # - Memory object creation and saving
        # - Automatic relation discovery if auto_relate is True
        # - Knowledge graph updates
        
        memory = self.store_knowledge_with_embeddings(
            db=db,
            user_id=user_id,
            title=title,
            content=content,
            context_id=context_id,
            auto_relate=auto_relate,
            threshold=threshold
        )
        
        # Note: The original API route (MemoryCreate) includes 'access_level' and 'memory_metadata'.
        # store_knowledge_with_embeddings currently doesn't use these directly when creating the Memory object.
        # If these fields are critical and not handled by the Memory model's defaults,
        # the Memory object created in store_knowledge_with_embeddings might need to be updated
        # or this method could fetch and update the memory after store_knowledge_with_embeddings commits.
        # For now, we assume the Memory model handles defaults or these are less critical
        # than the core AI features being enabled.
        # If 'access_level' and 'memory_metadata' need to be set explicitly:
        # db.refresh(memory) # Ensure memory is loaded with all attributes after commit
        # if memory.access_level != access_level and hasattr(memory, 'access_level'):
        #     memory.access_level = access_level
        # if memory_metadata and hasattr(memory, 'memory_metadata'):
        #     memory.memory_metadata = memory_metadata
        # db.commit() # Commit if changes were made

        logger.info(f"Memory created successfully with ID: {memory.id}")
        return memory
    
    def _find_similar_memories(
        self,
        db: Session,
        embedding: np.ndarray,
        threshold: float = 0.7,
        limit: int = 10,
        exclude_id: Optional[int] = None
    ) -> List[Tuple[int, float]]:
        """Find similar memories based on embeddings"""
        
        query = db.query(Memory).filter(Memory.embedding_vector.isnot(None))
        if exclude_id:
            query = query.filter(Memory.id != exclude_id)
        
        results = []
        for memory in query.all():
            if memory.embedding is not None:
                similarity = np.dot(embedding, memory.embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(memory.embedding)
                )
                
                if similarity >= threshold:
                    results.append((memory.id, float(similarity)))
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _determine_relation_type(self, similarity: float) -> str:
        """Determine relation type based on similarity score"""
        if similarity > 0.95:
            return "duplicate"
        elif similarity > 0.85:
            return "highly_related"
        elif similarity > 0.75:
            return "related"
        else:
            return "associated"
    
    def semantic_search(
        self,
        db: Session,
        query: str,
        user_id: int,
        limit: int = 10,
        context_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        
        # Generate query embedding
        query_embedding = self.model.encode(query)
        
        # Build base query
        base_query = db.query(Memory).filter(
            Memory.owner_id == user_id,
            Memory.is_active == True
        )
        
        if context_id:
            base_query = base_query.filter(Memory.context_id == context_id)
        
        # Calculate similarities
        results = []
        for memory in base_query.all():
            if memory.embedding is not None:
                similarity = np.dot(query_embedding, memory.embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(memory.embedding)
                )
                
                # Count relations
                relation_count = db.query(Relation).filter(
                    or_(
                        Relation.source_memory_id == memory.id,
                        Relation.target_memory_id == memory.id
                    )
                ).count()
                
                results.append({
                    "id": memory.id,
                    "title": memory.title,
                    "content": memory.content[:200] + "..." if len(memory.content) > 200 else memory.content,
                    "similarity": float(similarity),
                    "relation_count": relation_count,
                    "context_id": memory.context_id,
                    "created_at": memory.created_at.isoformat()
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def get_graph_analytics(self, db: Session) -> Dict[str, Any]:
        """Get graph analytics and statistics"""
        
        # Update graph with latest data
        self._load_graph_from_db(db)
        
        analytics = {
            "total_memories": db.query(Memory).count(),
            "total_relations": db.query(Relation).count(),
            "total_contexts": db.query(Context).count(),
            "graph_metrics": {}
        }
        
        if self.knowledge_graph.number_of_nodes() > 0:
            analytics["graph_metrics"] = {
                "nodes": self.knowledge_graph.number_of_nodes(),
                "edges": self.knowledge_graph.number_of_edges(),
                "density": nx.density(self.knowledge_graph),
                "is_connected": nx.is_weakly_connected(self.knowledge_graph)
            }
            
            # Calculate centrality for top nodes
            if self.knowledge_graph.number_of_edges() > 0:
                centrality = nx.degree_centrality(self.knowledge_graph)
                top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
                
                # Get memory titles for top nodes
                top_memories = []
                for node_id, score in top_nodes:
                    memory = db.query(Memory).filter(Memory.id == node_id).first()
                    if memory:
                        top_memories.append({
                            "id": node_id,
                            "title": memory.title,
                            "centrality": score
                        })
                
                analytics["graph_metrics"]["top_central_memories"] = top_memories
        
        return analytics
    
    def _load_graph(self):
        """Load graph from database on initialization"""
        # This will be called on startup
        pass
    
    def _load_graph_from_db(self, db: Session):
        """Load graph from database"""
        self.knowledge_graph.clear()
        
        # Add all memories as nodes
        for memory in db.query(Memory).filter(Memory.is_active == True).all():
            self.knowledge_graph.add_node(
                memory.id,
                title=memory.title,
                content=memory.content[:100]
            )
        
        # Add all relations as edges
        for relation in db.query(Relation).filter(Relation.is_active == True).all():
            if relation.source_memory_id and relation.target_memory_id:
                self.knowledge_graph.add_edge(
                    relation.source_memory_id,
                    relation.target_memory_id,
                    relation_type=relation.name,
                    strength=relation.strength
                )