#!/usr/bin/env python3
"""
Script to index existing memories from SQLite to ChromaDB vector store.
This enables semantic search functionality for memories created before vector indexing was active.
"""

import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.refactored_memory_db import RefactoredMemoryDB
from src.database.session import SessionLocal
from src.services import get_knowledge_retrieval_service
from src.database.strategies.compression_strategy import ZstdCompressionStrategy, AdaptiveCompressionStrategy


async def index_existing_memories():
    """Index all existing memories from SQLite to ChromaDB."""
    print("=" * 60)
    print("Indexing Existing Memories to Vector Store")
    print("=" * 60)
    print()

    try:
        # Initialize database
        print("1. Connecting to database...")
        db = RefactoredMemoryDB('sqlite:///./data/sqlite/memory.db', SessionLocal())

        # Get all memories
        print("2. Fetching all memories...")
        memories = await db.search_memories(query="", limit=10000)  # Get all
        print(f"   Found {len(memories)} memories in database")

        if not memories:
            print("\n⚠ No memories to index!")
            return 0

        # Initialize knowledge retrieval service
        print("\n3. Initializing vector store...")
        knowledge_service = get_knowledge_retrieval_service()
        vector_store = knowledge_service.vector_store
        current_count = vector_store._collection.count()
        print(f"   Vector store currently has {current_count} items")

        # Clear existing collection if it has compressed data
        if current_count > 0:
            print("   Clearing existing collection (contains compressed data)...")
            try:
                # Delete the collection and recreate
                vector_store._client.delete_collection(vector_store.collection_name)
                vector_store._collection = vector_store._client.get_or_create_collection(
                    name=vector_store.collection_name,
                    embedding_function=vector_store._embedding_function,
                    metadata={"description": "AI-driven knowledge retrieval system"}
                )
                print("   ✓ Collection cleared and recreated")
            except Exception as e:
                print(f"   Warning: Could not clear collection: {e}")

        # Prepare items for batch indexing
        print("\n4. Preparing memories for indexing...")
        items_to_index = []
        skipped = 0

        # Initialize decompression strategy
        compression_strategy = AdaptiveCompressionStrategy()

        for memory in memories:
            # Get the actual content - decompress if needed
            content = memory.content

            # Check if content is compressed (starts with compression markers)
            if content and (content.startswith('eJ') or content.startswith('eN') or content.startswith('KL')):
                # Content is compressed, need to decompress it
                try:
                    content = compression_strategy.decompress(content)
                except Exception as e:
                    print(f"   Warning: Could not decompress memory {memory.id}: {e}")
                    skipped += 1
                    continue

            # Skip if content is empty or too short
            if not content or len(content.strip()) < 10:
                skipped += 1
                continue

            items_to_index.append({
                "content": content,
                "metadata": {
                    "memory_id": str(memory.id),
                    "title": memory.title,
                    "context_id": str(memory.context_id) if memory.context_id else "none",
                    "access_level": memory.access_level or "public",
                    "created_at": memory.created_at.isoformat() if memory.created_at else "",
                    "category": getattr(memory, 'category', 'uncategorized')
                },
                "id": f"memory_{memory.id}"
            })

        print(f"   Prepared {len(items_to_index)} items")
        if skipped > 0:
            print(f"   Skipped {skipped} items (compressed/empty/too short)")

        # Batch index with progress
        print("\n5. Indexing to vector store (this may take a moment)...")
        batch_size = 32
        indexed_count = 0

        for i in range(0, len(items_to_index), batch_size):
            batch = items_to_index[i:i + batch_size]
            indexed_ids = knowledge_service.index_knowledge_batch(batch, batch_size=batch_size)
            indexed_count += len(indexed_ids)

            # Progress indicator
            progress = (indexed_count / len(items_to_index)) * 100
            print(f"   Progress: {indexed_count}/{len(items_to_index)} ({progress:.1f}%)")

        # Verify indexing
        print("\n6. Verifying indexing...")
        final_count = vector_store._collection.count()
        print(f"   Vector store now has {final_count} items")
        print(f"   Newly indexed: {final_count - current_count} memories")

        print("\n" + "=" * 60)
        print(f"✅ SUCCESS! Indexed {indexed_count} memories")
        print("=" * 60)
        print("\nSemantic search is now active!")
        print("Try these MCP tools:")
        print("  - search_semantic: AI-powered semantic search")
        print("  - find_similar_knowledge: Find similar content")
        print()

        return indexed_count

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return -1


if __name__ == "__main__":
    result = asyncio.run(index_existing_memories())
    sys.exit(0 if result >= 0 else 1)
