"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

Example 02: Search Memories
This example demonstrates text search and semantic search capabilities.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

API_BASE_URL = "http://localhost:8002"


async def create_sample_memories(session):
    """Create sample memories for searching."""
    print("📝 Creating sample memories...\n")

    memories = [
        {
            "title": "Python Programming Basics",
            "content": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "memory_metadata": {"tags": ["python", "programming", "basics"], "category": "tutorial"}
        },
        {
            "title": "Machine Learning Introduction",
            "content": "Machine learning is a subset of AI that enables systems to learn from data without explicit programming.",
            "memory_metadata": {"tags": ["ml", "ai", "data-science"], "category": "tutorial"}
        },
        {
            "title": "Docker Container Guide",
            "content": "Docker is a platform for developing, shipping, and running applications in containers.",
            "memory_metadata": {"tags": ["docker", "containers", "devops"], "category": "tutorial"}
        },
        {
            "title": "REST API Design",
            "content": "REST APIs use HTTP methods to perform CRUD operations on resources in a stateless manner.",
            "memory_metadata": {"tags": ["api", "rest", "web"], "category": "tutorial"}
        }
    ]

    created_ids = []
    for memory in memories:
        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/memories/",
                json=memory
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    created_ids.append(result["id"])
                    print(f"  ✅ Created: {memory['title']}")
        except Exception as e:
            print(f"  ❌ Error creating {memory['title']}: {e}")

    print(f"\n✅ Created {len(created_ids)} sample memories\n")
    return created_ids


async def text_search(session, query):
    """Perform a text-based search."""
    print(f"🔍 Text Search: '{query}'")
    print("-" * 60)

    try:
        async with session.get(
            f"{API_BASE_URL}/api/v1/memories/search",
            params={"query": query, "limit": 10}
        ) as response:
            if response.status == 200:
                results = await response.json()
                print(f"Found {len(results)} results:\n")
                for idx, result in enumerate(results, 1):
                    print(f"{idx}. {result.get('title')}")
                    print(f"   Content: {result.get('content')[:80]}...")
                    print(f"   Tags: {result.get('memory_metadata', {}).get('tags')}")
                    print()
            else:
                print(f"❌ Search failed: {response.status}")
    except Exception as e:
        print(f"❌ Search error: {e}")


async def semantic_search(session, query):
    """Perform a semantic (AI-powered) search."""
    print(f"🧠 Semantic Search: '{query}'")
    print("-" * 60)

    search_data = {
        "query": query,
        "limit": 5,
        "similarity_threshold": 0.5,
        "use_cache": True
    }

    try:
        async with session.post(
            f"{API_BASE_URL}/api/v1/search/semantic",
            json=search_data
        ) as response:
            if response.status == 200:
                results = await response.json()
                print(f"Found {len(results.get('results', []))} results:\n")

                for idx, result in enumerate(results.get('results', []), 1):
                    similarity = result.get('similarity_score', 0)
                    print(f"{idx}. {result.get('title')} (similarity: {similarity:.2f})")
                    print(f"   Content: {result.get('content')[:80]}...")
                    print(f"   Tags: {result.get('memory_metadata', {}).get('tags')}")
                    print()

                if 'search_time' in results:
                    print(f"⚡ Search completed in {results['search_time']:.2f}ms")
            else:
                print(f"❌ Semantic search failed: {response.status}")
    except Exception as e:
        print(f"❌ Semantic search error: {e}")


async def search_by_tags(session, tags):
    """Search memories by tags."""
    print(f"🏷️  Tag Search: {tags}")
    print("-" * 60)

    try:
        params = {"tags": ",".join(tags), "limit": 10}
        async with session.get(
            f"{API_BASE_URL}/api/v1/memories/search",
            params=params
        ) as response:
            if response.status == 200:
                results = await response.json()
                print(f"Found {len(results)} memories with tags {tags}:\n")
                for idx, result in enumerate(results, 1):
                    print(f"{idx}. {result.get('title')}")
                    print(f"   Tags: {result.get('memory_metadata', {}).get('tags')}")
                    print()
            else:
                print(f"❌ Tag search failed: {response.status}")
    except Exception as e:
        print(f"❌ Tag search error: {e}")


async def main():
    """Main example function."""
    print("=" * 60)
    print("Example 02: Search Memories")
    print("=" * 60)
    print()

    async with aiohttp.ClientSession() as session:

        # Create sample data
        memory_ids = await create_sample_memories(session)

        # Example 1: Text search
        await text_search(session, "programming")
        print()

        # Example 2: Semantic search
        await semantic_search(session, "learning from data")
        print()

        # Example 3: Tag-based search
        await search_by_tags(session, ["python", "programming"])
        print()

        # Example 4: Another semantic search
        await semantic_search(session, "software containers")
        print()

    print("=" * 60)
    print("✅ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🚀 Starting Example 02: Search Memories\n")
    print("Prerequisites:")
    print("  - MCP server running on http://localhost:8002")
    print("  - Vector search enabled (CHROMA_ENABLED=true)")
    print("  - Redis enabled for caching (REDIS_ENABLED=true)")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Example interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
