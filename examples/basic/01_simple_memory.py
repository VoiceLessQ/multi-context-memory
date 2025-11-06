"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

Example 01: Simple Memory Creation and Retrieval
This example demonstrates the basic CRUD operations for memories.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configuration
API_BASE_URL = "http://localhost:8002"


async def main():
    """Main example function demonstrating simple memory operations."""

    print("=" * 60)
    print("Example 01: Simple Memory Creation and Retrieval")
    print("=" * 60)
    print()

    async with aiohttp.ClientSession() as session:

        # Step 1: Create a simple memory
        print("📝 Step 1: Creating a new memory...")
        memory_data = {
            "title": "Python Best Practices",
            "content": "Always use virtual environments to isolate project dependencies. "
                      "This prevents conflicts between different projects and keeps your "
                      "system Python clean.",
            "access_level": "user",
            "memory_metadata": {
                "tags": ["python", "best-practices", "development"],
                "category": "programming",
                "importance": 8
            }
        }

        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/memories/",
                json=memory_data
            ) as response:
                if response.status == 200:
                    created_memory = await response.json()
                    memory_id = created_memory.get("id")
                    print(f"✅ Memory created successfully!")
                    print(f"   ID: {memory_id}")
                    print(f"   Title: {created_memory.get('title')}")
                    print()
                else:
                    print(f"❌ Failed to create memory: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Error creating memory: {e}")
            return

        # Step 2: Retrieve the created memory
        print("🔍 Step 2: Retrieving the memory...")
        try:
            async with session.get(
                f"{API_BASE_URL}/api/v1/memories/{memory_id}"
            ) as response:
                if response.status == 200:
                    retrieved_memory = await response.json()
                    print(f"✅ Memory retrieved successfully!")
                    print(f"   Title: {retrieved_memory.get('title')}")
                    print(f"   Content: {retrieved_memory.get('content')[:100]}...")
                    print(f"   Tags: {retrieved_memory.get('memory_metadata', {}).get('tags')}")
                    print()
                else:
                    print(f"❌ Failed to retrieve memory: {response.status}")
        except Exception as e:
            print(f"❌ Error retrieving memory: {e}")

        # Step 3: Update the memory
        print("✏️  Step 3: Updating the memory...")
        update_data = {
            "content": retrieved_memory.get('content') +
                      " Additionally, use requirements.txt to track dependencies.",
            "memory_metadata": {
                "tags": ["python", "best-practices", "development", "dependencies"],
                "category": "programming",
                "importance": 9,
                "updated": True
            }
        }

        try:
            async with session.put(
                f"{API_BASE_URL}/api/v1/memories/{memory_id}",
                json=update_data
            ) as response:
                if response.status == 200:
                    updated_memory = await response.json()
                    print(f"✅ Memory updated successfully!")
                    print(f"   New tags: {updated_memory.get('memory_metadata', {}).get('tags')}")
                    print()
                else:
                    print(f"❌ Failed to update memory: {response.status}")
        except Exception as e:
            print(f"❌ Error updating memory: {e}")

        # Step 4: List all memories
        print("📋 Step 4: Listing all memories...")
        try:
            async with session.get(
                f"{API_BASE_URL}/api/v1/memories/"
            ) as response:
                if response.status == 200:
                    memories = await response.json()
                    print(f"✅ Found {len(memories)} memories:")
                    for mem in memories[:5]:  # Show first 5
                        print(f"   - {mem.get('id')}: {mem.get('title')}")
                    print()
                else:
                    print(f"❌ Failed to list memories: {response.status}")
        except Exception as e:
            print(f"❌ Error listing memories: {e}")

        # Step 5: Delete the memory (optional - uncomment to test)
        print("🗑️  Step 5: Cleaning up...")
        print("   (Keeping the memory for other examples)")
        print("   To delete, uncomment the deletion code in the script")
        print()

        # Uncomment to delete:
        # async with session.delete(
        #     f"{API_BASE_URL}/api/v1/memories/{memory_id}"
        # ) as response:
        #     if response.status == 200:
        #         print(f"✅ Memory deleted successfully!")

    print("=" * 60)
    print("✅ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🚀 Starting Example 01: Simple Memory Operations\n")
    print("Prerequisites:")
    print("  - MCP server running on http://localhost:8002")
    print("  - You can start it with: docker-compose up -d")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Example interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
