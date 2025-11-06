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
Deduplication system for the MCP Multi-Context Memory System.
"""
import hashlib
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import mmh3  # MurmurHash3 for fast hashing
import xxhash  # Even faster hashing
import numpy as np
import spacy
from collections import defaultdict
import time
import pickle
import os

# Handle sklearn import gracefully
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    logging.warning("sklearn not available. Some features will be disabled.")
    TfidfVectorizer = None
    cosine_similarity = None
    SKLEARN_AVAILABLE = False

from ..database.models import Memory, Context, Relation
from ..database.db_interface import DatabaseInterface
from ..utils.compression import CompressionManager

logger = logging.getLogger(__name__)

class DeduplicationManager:
    """Manage memory deduplication with multiple strategies."""
    
    def __init__(self, db: DatabaseInterface, config: Dict = None):
        """
        Initialize the deduplication manager.
        
        Args:
            db: Enhanced memory database instance
            config: Configuration dictionary
        """
        self.db = db
        self.config = config or {}
        
        # Configuration settings
        self.enabled = self.config.get("deduplication_enabled", True)
        self.strategy = self.config.get("deduplication_strategy", "content_hash")  # content_hash, fuzzy, semantic
        self.threshold = self.config.get("deduplication_threshold", 0.95)  # Similarity threshold
        self.batch_size = self.config.get("deduplication_batch_size", 1000)
        self.max_similarity_checks = self.config.get("max_similarity_checks", 100)
        
        # Initialize models and tools
        self._initialize_models()
        
        # Cache for hashes and similarities
        self.hash_cache = {}
        self.similarity_cache = {}
        
        # Statistics
        self.stats = {
            "total_memories": 0,
            "duplicate_groups": 0,
            "duplicates_found": 0,
            "space_saved": 0,
            "processing_time": 0
        }
        
    def _initialize_models(self):
        """Initialize NLP models and tools for semantic deduplication."""
        try:
            # Try to load spaCy model for advanced text processing
            try:
                self.nlp = spacy.load("en_core_web_md")
            except OSError:
                logger.warning("spaCy model 'en_core_web_md' not found. Using basic text processing.")
                self.nlp = None
            
            # Initialize TF-IDF vectorizer for fuzzy matching only if sklearn is available
            if SKLEARN_AVAILABLE:
                self.vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=2
                )
                logger.info("TF-IDF vectorizer initialized")
            else:
                self.vectorizer = None
                logger.warning("TF-IDF vectorizer disabled due to missing sklearn")
            
            # Initialize hashers
            self.murmur_hasher = mmh3
            self.xx_hasher = xxhash.xxh64()
            
            logger.info("Deduplication models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing deduplication models: {e}")
            self.nlp = None
            self.vectorizer = None
            
    def calculate_content_hash(self, content: str, method: str = "xxhash") -> str:
        """
        Calculate a hash for the given content.
        
        Args:
            content: Text content to hash
            method: Hashing method ('md5', 'sha256', 'murmur', 'xxhash')
            
        Returns:
            Hexadecimal hash string
        """
        if not content:
            return ""
            
        # Normalize content
        normalized = content.lower().strip()
        
        if method == "md5":
            return hashlib.md5(normalized.encode()).hexdigest()
        elif method == "sha256":
            return hashlib.sha256(normalized.encode()).hexdigest()
        elif method == "murmur":
            return str(self.murmur_hasher.hash(normalized))
        elif method == "xxhash":
            return str(self.xx_hasher.intdigest(normalized))
        else:
            raise ValueError(f"Unknown hashing method: {method}")
            
    def extract_features(self, content: str) -> Dict:
        """
        Extract features from content for fuzzy matching.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            "length": len(content),
            "word_count": len(content.split()),
            "char_count": len(content.replace(" ", "")),
            "avg_word_length": sum(len(word) for word in content.split()) / len(content.split()) if content.split() else 0,
            "punctuation_count": sum(1 for char in content if char in ".,!?;:\"'()[]{}"),
            "digit_count": sum(1 for char in content if char.isdigit()),
            "uppercase_count": sum(1 for char in content if char.isupper()),
        }
        
        # Add spaCy features if available
        if self.nlp and content:
            try:
                doc = self.nlp(content[:1000])  # Process first 1000 chars for performance
                features.update({
                    "noun_count": sum(1 for token in doc if token.pos_ == "NOUN"),
                    "verb_count": sum(1 for token in doc if token.pos_ == "VERB"),
                    "adj_count": sum(1 for token in doc if token.pos_ == "ADJ"),
                    "entity_count": len(doc.ents),
                    "sentence_count": len(list(doc.sents)),
                })
            except Exception as e:
                logger.warning(f"Error extracting spaCy features: {e}")
                
        return features
        
    def calculate_similarity(self, content1: str, content2: str, method: str = "cosine") -> float:
        """
        Calculate similarity between two pieces of content.
        
        Args:
            content1: First content
            content2: Second content
            method: Similarity calculation method ('cosine', 'jaccard', 'levenshtein')
            
        Returns:
            Similarity score between 0 and 1
        """
        if not content1 or not content2:
            return 0.0
            
        # Check cache first
        cache_key = f"{hash(content1)}_{hash(content2)}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
            
        if method == "cosine":
            # Use TF-IDF for cosine similarity
            if not SKLEARN_AVAILABLE or not self.vectorizer or not cosine_similarity:
                logger.warning("sklearn not available, falling back to Jaccard similarity")
                method = "jaccard"
            else:
                try:
                    corpus = [content1, content2]
                    tfidf = self.vectorizer.fit_transform(corpus)
                    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
                    self.similarity_cache[cache_key] = similarity
                    return similarity
                except Exception as e:
                    logger.warning(f"Error calculating cosine similarity: {e}")
                    return 0.0
                
        elif method == "jaccard":
            # Calculate Jaccard similarity
            set1 = set(content1.lower().split())
            set2 = set(content2.lower().split())
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            similarity = len(intersection) / len(union) if union else 0.0
            self.similarity_cache[cache_key] = similarity
            return similarity
            
        elif method == "levenshtein":
            # Calculate normalized Levenshtein distance
            try:
                from Levenshtein import ratio
                similarity = ratio(content1, content2) / 100.0
                self.similarity_cache[cache_key] = similarity
                return similarity
            except ImportError:
                logger.warning("python-Levenshtein not available, falling back to Jaccard similarity")
                method = "jaccard"
                # Fall through to Jaccard calculation
            except Exception as e:
                logger.warning(f"Error calculating Levenshtein similarity: {e}")
                return 0.0
            
        else:
            raise ValueError(f"Unknown similarity method: {method}")
            
    def find_exact_duplicates(self, memories: List[Memory]) -> Dict[str, List[Memory]]:
        """
        Find exact duplicates based on content hash.
        
        Args:
            memories: List of memory objects
            
        Returns:
            Dictionary mapping hash to list of duplicate memories
        """
        duplicates = defaultdict(list)
        
        for memory in memories:
            if not memory.content:
                continue
                
            # Calculate hash using configured method
            hash_method = self.config.get("hash_method", "xxhash")
            content_hash = self.calculate_content_hash(memory.content, hash_method)
            
            # Store in duplicates dictionary
            duplicates[content_hash].append(memory)
            
        # Filter out non-duplicates
        duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}
        
        return duplicates
        
    def find_fuzzy_duplicates(self, memories: List[Memory]) -> Dict[str, List[Memory]]:
        """
        Find fuzzy duplicates based on content similarity.
        
        Args:
            memories: List of memory objects
            
        Returns:
            Dictionary mapping memory ID to list of similar memories
        """
        if not SKLEARN_AVAILABLE or not self.vectorizer:
            logger.warning("sklearn not available, skipping fuzzy deduplication")
            return {}
            
        duplicates = defaultdict(list)
        processed = 0
        
        # Convert memories to list of tuples for easier processing
        memory_list = [(mem.id, mem.content) for mem in memories if mem.content]
        
        # Calculate TF-IDF matrix for all memories
        try:
            corpus = [content for _, content in memory_list]
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except Exception as e:
            logger.warning(f"Error creating TF-IDF matrix: {e}")
            return duplicates
            
        # Calculate pairwise similarities
        for i in range(len(memory_list)):
            mem_id1, content1 = memory_list[i]
            
            # Compare with next max_similarity_checks memories
            end_idx = min(i + self.max_similarity_checks, len(memory_list))
            
            for j in range(i + 1, end_idx):
                mem_id2, content2 = memory_list[j]
                
                # Calculate similarity
                similarity = self.calculate_similarity(content1, content2)
                
                # Check if above threshold
                if similarity >= self.threshold:
                    duplicates[mem_id1].append(mem_id2)
                    duplicates[mem_id2].append(mem_id1)
                    
                processed += 1
                if processed % 1000 == 0:
                    logger.info(f"Processed {processed} similarity checks")
                    
        return duplicates
        
    def find_semantic_duplicates(self, memories: List[Memory]) -> Dict[str, List[Memory]]:
        """
        Find semantic duplicates based on meaning.
        
        Args:
            memories: List of memory objects
            
        Returns:
            Dictionary mapping memory ID to list of semantically similar memories
        """
        duplicates = defaultdict(list)
        
        if not self.nlp:
            logger.warning("spaCy model not available for semantic deduplication")
            return self.find_fuzzy_duplicates(memories)
            
        if not SKLEARN_AVAILABLE or not cosine_similarity:
            logger.warning("sklearn not available, skipping semantic similarity calculation")
            return self.find_fuzzy_duplicates(memories)
            
        # Process memories in batches
        for i in range(0, len(memories), self.batch_size):
            batch = memories[i:i + self.batch_size]
            logger.info(f"Processing semantic batch {i//self.batch_size + 1}")
            
            # Extract embeddings for batch
            embeddings = []
            valid_memories = []
            
            for memory in batch:
                if not memory.content:
                    continue
                    
                try:
                    # Process with spaCy
                    doc = self.nlp(memory.content[:1000])  # Limit length for performance
                    if doc.vector_norm > 0:
                        embeddings.append(doc.vector)
                        valid_memories.append(memory)
                except Exception as e:
                    logger.warning(f"Error processing memory {memory.id}: {e}")
                    continue
                    
            if not embeddings:
                continue
                
            # Convert to numpy array
            embeddings = np.array(embeddings)
            
            # Calculate cosine similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Find duplicates
            for idx1, mem1 in enumerate(valid_memories):
                for idx2, mem2 in enumerate(valid_memories[idx1 + 1:], idx1 + 1):
                    if similarity_matrix[idx1][idx2] >= self.threshold:
                        duplicates[mem1.id].append(mem2.id)
                        duplicates[mem2.id].append(mem1.id)
                        
        return duplicates
        
    def find_duplicates(self, memories: List[Memory] = None) -> Dict[str, List[Memory]]:
        """
        Find all duplicates using the configured strategy.
        
        Args:
            memories: Optional list of memories to check. If None, checks all memories.
            
        Returns:
            Dictionary mapping memory ID to list of duplicate memory IDs
        """
        if not self.enabled:
            logger.info("Deduplication is disabled")
            return {}
            
        start_time = time.time()
        
        # Get memories to check
        if memories is None:
            memories = self.db.get_all_memories()
            
        self.stats["total_memories"] = len(memories)
        
        # Find duplicates based on strategy
        if self.strategy == "content_hash":
            duplicates = self.find_exact_duplicates(memories)
        elif self.strategy == "fuzzy":
            duplicates = self.find_fuzzy_duplicates(memories)
        elif self.strategy == "semantic":
            duplicates = self.find_semantic_duplicates(memories)
        else:
            logger.warning(f"Unknown deduplication strategy: {self.strategy}")
            return {}
            
        # Convert to consistent format
        formatted_duplicates = defaultdict(list)
        for hash_val, mem_list in duplicates.items():
            for i, mem1 in enumerate(mem_list):
                for mem2 in mem_list[i + 1:]:
                    formatted_duplicates[mem1.id].append(mem2.id)
                    formatted_duplicates[mem2.id].append(mem1.id)
                    
        # Update statistics
        self.stats["duplicate_groups"] = len(duplicates)
        self.stats["duplicates_found"] = sum(len(v) for v in formatted_duplicates.values()) // 2
        self.stats["processing_time"] = time.time() - start_time
        
        logger.info(f"Found {self.stats['duplicates_found']} duplicates in {self.stats['processing_time']:.2f}s")
        
        return dict(formatted_duplicates)
        
    def merge_duplicates(self, duplicates: Dict[str, List[str]], strategy: str = "keep_first") -> List[str]:
        """
        Merge duplicate memories.
        
        Args:
            duplicates: Dictionary mapping memory ID to list of duplicate IDs
            strategy: Merge strategy ('keep_first', 'keep_latest', 'keep_longest', 'merge_all')
            
        Returns:
            List of memory IDs that were merged/removed
        """
        if not duplicates:
            return []
            
        merged_ids = []
        processed = set()
        
        for mem_id, dup_ids in duplicates.items():
            if mem_id in processed:
                continue
                
            # Get all related memories
            all_ids = [mem_id] + dup_ids
            
            # Skip if already processed
            if any(id in processed for id in all_ids):
                continue
                
            # Get memory objects
            memories = [self.db.get_memory(id) for id in all_ids if self.db.get_memory(id)]
            
            if not memories:
                continue
                
            # Select memory to keep based on strategy
            if strategy == "keep_first":
                kept_memory = memories[0]
            elif strategy == "keep_latest":
                kept_memory = max(memories, key=lambda m: m.created_at)
            elif strategy == "keep_longest":
                kept_memory = max(memories, key=lambda m: len(m.content or ""))
            elif strategy == "merge_all":
                # Merge all contents
                merged_content = "\n\n".join([m.content or "" for m in memories])
                kept_memory = memories[0]
                kept_memory.content = merged_content
                self.db.update_memory(kept_memory.id, content=merged_content)
            else:
                logger.warning(f"Unknown merge strategy: {strategy}")
                kept_memory = memories[0]
                
            # Mark other memories as merged
            for memory in memories:
                if memory.id != kept_memory.id:
                    # Update relations to point to kept memory
                    self.db.update_relations(memory.id, kept_memory.id)
                    
                    # Mark as merged (you might need a new field in the model)
                    # For now, we'll just delete it
                    try:
                        self.db.delete_memory(memory.id)
                        merged_ids.append(memory.id)
                    except Exception as e:
                        logger.error(f"Error deleting memory {memory.id}: {e}")
                        
            processed.update(all_ids)
            
        logger.info(f"Merged {len(merged_ids)} duplicate memories")
        return merged_ids
        
    def create_deduplication_report(self) -> Dict:
        """
        Create a comprehensive deduplication report.
        
        Returns:
            Dictionary with deduplication statistics and findings
        """
        report = {
            "timestamp": time.time(),
            "configuration": {
                "enabled": self.enabled,
                "strategy": self.strategy,
                "threshold": self.threshold,
                "batch_size": self.batch_size
            },
            "statistics": self.stats.copy(),
            "findings": {
                "total_memories_analyzed": self.stats["total_memories"],
                "duplicate_groups_found": self.stats["duplicate_groups"],
                "total_duplicates_found": self.stats["duplicates_found"],
                "processing_time_seconds": self.stats["processing_time"]
            },
            "recommendations": []
        }
        
        # Add recommendations based on findings
        if self.stats["total_memories"] > 0:
            duplicate_ratio = self.stats["duplicates_found"] / self.stats["total_memories"]
            report["findings"]["duplicate_ratio"] = duplicate_ratio
            
            if duplicate_ratio > 0.1:
                report["recommendations"].append(
                    "High duplicate ratio detected. Consider implementing regular deduplication."
                )
                
            if self.stats["processing_time"] > 60:
                report["recommendations"].append(
                    "Deduplication processing is slow. Consider optimizing the strategy or using batch processing."
                )
                
        return report
        
    def save_deduplication_state(self, file_path: str):
        """
        Save the current deduplication state to a file.
        
        Args:
            file_path: Path to save the state
        """
        state = {
            "hash_cache": self.hash_cache,
            "similarity_cache": self.similarity_cache,
            "stats": self.stats,
            "timestamp": time.time()
        }
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(state, f)
            logger.info(f"Deduplication state saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving deduplication state: {e}")
            
    def load_deduplication_state(self, file_path: str):
        """
        Load deduplication state from a file.
        
        Args:
            file_path: Path to load the state from
        """
        if not os.path.exists(file_path):
            logger.warning(f"Deduplication state file not found: {file_path}")
            return
            
        try:
            with open(file_path, 'rb') as f:
                state = pickle.load(f)
                
            self.hash_cache = state.get("hash_cache", {})
            self.similarity_cache = state.get("similarity_cache", {})
            self.stats = state.get("stats", self.stats)
            
            logger.info(f"Deduplication state loaded from {file_path}")
        except Exception as e:
            logger.error(f"Error loading deduplication state: {e}")
            
    def clear_cache(self):
        """Clear all cached data."""
        self.hash_cache.clear()
        self.similarity_cache.clear()
        logger.info("Deduplication cache cleared")
        
    def get_optimal_threshold(self, sample_memories: List[Memory], target_precision: float = 0.95) -> float:
        """
        Find the optimal similarity threshold for deduplication.
        
        Args:
            sample_memories: Sample of memories to analyze
            target_precision: Target precision for the threshold
            
        Returns:
            Optimal threshold value
        """
        if not sample_memories:
            return self.threshold
            
        if not SKLEARN_AVAILABLE or not self.vectorizer:
            logger.warning("sklearn not available, cannot calculate optimal threshold")
            return self.threshold
            
        # Test different thresholds
        thresholds = np.arange(0.7, 1.0, 0.05)
        results = []
        
        for threshold in thresholds:
            self.threshold = threshold
            
            # Find duplicates with this threshold
            duplicates = self.find_fuzzy_duplicates(sample_memories)
            
            # Calculate metrics
            total_pairs = len(sample_memories) * (len(sample_memories) - 1) / 2
            found_pairs = sum(len(v) for v in duplicates.values()) // 2
            
            if total_pairs > 0:
                precision = found_pairs / total_pairs if found_pairs > 0 else 0
                recall = found_pairs / (found_pairs + 1)  # Simplified recall calculation
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            else:
                precision = recall = f1 = 0
                
            results.append({
                "threshold": threshold,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "duplicates_found": found_pairs
            })
            
        # Find threshold that meets target precision
        optimal_threshold = self.threshold
        for result in results:
            if result["precision"] >= target_precision:
                optimal_threshold = result["threshold"]
                break
                
        logger.info(f"Optimal threshold: {optimal_threshold} (target precision: {target_precision})")
        return optimal_threshold