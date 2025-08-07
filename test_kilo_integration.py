import asyncio
import json
import time
import requests
from mcp import ClientSession, StdioServerParameters
import mcp

async def test_mcp_server_connection():
    """Test basic MCP server connection"""
    print("Testing MCP server connection...")
    
    try:
        # Test the health endpoint first
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
        
        # Test MCP server connection
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcm-mcp", "python", "-m", "src.mcp_server"]
        )
        
        async with mcp.stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✓ MCP session initialized")
                
                # List resources
                resources = await session.list_resources()
                print(f"✓ Available resources: {len(resources.resources)}")
                
                # List tools
                tools = await session.list_tools()
                print(f"✓ Available tools: {len(tools.tools)}")
                
                return True
                
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False

async def test_memory_operations():
    """Test memory operations through MCP"""
    print("\nTesting memory operations...")
    
    try:
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcm-mcp", "python", "-m", "src.mcp_server"]
        )
        
        async with mcp.stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Create a memory
                print("Creating memory...")
                create_result = await session.call_tool("create_memory", {
                    "title": "Test Memory",
                    "content": "This is a test memory created by the integration test",
                    "access_level": "user",
                    "memory_metadata": {
                        "tags": ["test", "integration"],
                        "source": "test_script"
                    }
                })
                print(f"✓ Memory created: {create_result}")
                
                # Search for memories
                print("Searching memories...")
                search_result = await session.call_tool("search_memories", {
                    "query": "test memory",
                    "use_semantic": False,
                    "limit": 5
                })
                print(f"✓ Search results: {len(search_result.get('result', []))} memories found")
                
                # Verify our test memory is in the results
                if search_result.get("result"):
                    memories = search_result["result"]
                    test_memory = next((m for m in memories if "Test Memory" in m.get("title", "")), None)
                    if test_memory:
                        print(f"✓ Test memory found in search results: {test_memory['id']}")
                    else:
                        print("✗ Test memory not found in search results")
                
                return True
                
    except Exception as e:
        print(f"✗ Memory operations test failed: {e}")
        return False

async def test_context_operations():
    """Test context operations through MCP"""
    print("\nTesting context operations...")
    
    try:
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcm-mcp", "python", "-m", "src.mcp_server"]
        )
        
        async with mcp.stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Create a context
                print("Creating context...")
                context_result = await session.call_tool("create_context", {
                    "name": "Test Context",
                    "description": "A test context for integration testing",
                    "access_level": "user",
                    "context_metadata": {
                        "category": "test",
                        "purpose": "integration testing"
                    }
                })
                print(f"✓ Context created: {context_result}")
                
                return True
                
    except Exception as e:
        print(f"✗ Context operations test failed: {e}")
        return False

async def test_relation_operations():
    """Test relation operations through MCP"""
    print("\nTesting relation operations...")
    
    try:
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcm-mcp", "python", "-m", "src.mcp_server"]
        )
        
        async with mcp.stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Create two memories
                print("Creating memories for relation test...")
                memory1_result = await session.call_tool("create_memory", {
                    "title": "Memory 1",
                    "content": "First memory for relation testing",
                    "access_level": "user"
                })
                
                memory2_result = await session.call_tool("create_memory", {
                    "title": "Memory 2",
                    "content": "Second memory for relation testing",
                    "access_level": "user"
                })
                
                # Create a relation
                print("Creating relation...")
                relation_result = await session.call_tool("create_relation", {
                    "name": "related_to",
                    "source_memory_id": memory1_result["id"],
                    "target_memory_id": memory2_result["id"],
                    "strength": 0.8
                })
                print(f"✓ Relation created: {relation_result}")
                
                return True
                
    except Exception as e:
        print(f"✗ Relation operations test failed: {e}")
        return False

async def test_kilo_config():
    """Test the Kilo configuration"""
    print("\nTesting Kilo configuration...")
    
    try:
        with open("kilo_config.json", "r") as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ["mcpServers", "mcpClients", "settings"]
        for section in required_sections:
            if section in config:
                print(f"✓ {section} section found")
            else:
                print(f"✗ {section} section missing")
                return False
        
        # Check server configuration
        server_config = config["mcpServers"]["memory-system"]
        if "command" in server_config and "args" in server_config:
            print("✓ Server configuration valid")
        else:
            print("✗ Server configuration invalid")
            return False
        
        # Check client configuration
        client_config = config["mcpClients"]["memory-system"]
        if "server" in client_config and "capabilities" in client_config:
            print("✓ Client configuration valid")
        else:
            print("✗ Client configuration invalid")
            return False
        
        # Check settings
        settings = config["settings"]["memory-system"]
        if "autoConnect" in settings:
            print("✓ Settings valid")
        else:
            print("✗ Settings invalid")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting Kilo Code Integration Tests")
    print("=" * 50)
    
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(5)
    
    tests = [
        ("Configuration Test", test_kilo_config),
        ("MCP Server Connection", test_mcp_server_connection),
        ("Memory Operations", test_memory_operations),
        ("Context Operations", test_context_operations),
        ("Relation Operations", test_relation_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Kilo Code integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check the output above for details.")
    
    return passed == len(results)

if __name__ == "__main__":
    asyncio.run(main())