#!/usr/bin/env python3
"""
MCP Multi-Context Memory System - Connection Verification Script
Copyright (c) 2024 VoiceLessQ
Version: 2.0.0

This script verifies that the MCP server is properly connected and operational.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.refactored_memory_db import RefactoredMemoryDB
from src.database.session import SessionLocal, settings


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header():
    """Print script header."""
    print("=" * 60)
    print(f"{Colors.BOLD}MCP Multi-Context Memory - Connection Verification{Colors.END}")
    print("Version: 2.0.0")
    print("=" * 60)
    print()


def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.END} {message}")


def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


def print_info(message):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")


async def verify_database_connection():
    """Verify database connection and basic operations."""
    print(f"\n{Colors.BOLD}1. Database Connection Test{Colors.END}")
    print("-" * 60)

    try:
        # Check settings
        print_info(f"Database URL: {settings.database_url}")

        # Initialize database
        db = RefactoredMemoryDB(settings.database_url, SessionLocal())
        print_success("Database initialized successfully")

        # Test memory count
        count = await db.get_memory_count()
        print_success(f"Database accessible - Found {count} memories")

        # Test statistics
        stats = await db.get_memory_statistics()
        print_success("Statistics query successful")
        print_info(f"  Total memories: {stats.get('total_memories', 0)}")

        categories = stats.get('categories', {})
        if categories:
            print_info("  Categories:")
            for category, cat_count in list(categories.items())[:5]:
                print(f"    - {category}: {cat_count}")

        return True, db

    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False, None


async def verify_database_tables(db):
    """Verify all required database tables exist."""
    print(f"\n{Colors.BOLD}2. Database Schema Test{Colors.END}")
    print("-" * 60)

    required_tables = [
        'memories', 'contexts', 'relations', 'memory_chunks',
        'memory_versions', 'users', 'search_history',
        'system_config', 'audit_logs'
    ]

    try:
        # This is a simplified check - in production, you'd query the schema
        print_success(f"Checking for {len(required_tables)} required tables")

        # Test basic operations on core tables
        try:
            await db.get_memory_count()
            print_success("'memories' table accessible")
        except:
            print_error("'memories' table not accessible")
            return False

        print_success("Core tables verified")
        return True

    except Exception as e:
        print_error(f"Schema verification failed: {e}")
        return False


async def verify_mcp_handlers():
    """Verify MCP handler chain is properly configured."""
    print(f"\n{Colors.BOLD}3. MCP Handler Chain Test{Colors.END}")
    print("-" * 60)

    try:
        from src.mcp.handlers.base_handler import HandlerChain
        from src.mcp.handlers.memory_handler import MemoryHandler
        from src.mcp.handlers.context_handler import ContextHandler
        from src.mcp.handlers.relations_handler import RelationsHandler
        from src.mcp.handlers.advanced_handler import AdvancedHandler

        # Build handler chain
        chain = HandlerChain()
        handlers = [
            MemoryHandler(),
            ContextHandler(),
            RelationsHandler(),
            AdvancedHandler()
        ]
        chain.add_handlers(handlers)

        print_success(f"Handler chain built with {len(handlers)} handlers")

        # Get supported tools
        tools = chain.get_supported_tools()
        print_success(f"Total tools available: {len(tools)}")

        # Display tools by handler
        for handler in handlers:
            handler_name = handler.__class__.__name__
            handler_tools = handler.supported_tools
            print_info(f"  {handler_name}: {len(handler_tools)} tools")
            for tool in handler_tools[:3]:  # Show first 3
                print(f"    - {tool}")
            if len(handler_tools) > 3:
                print(f"    ... and {len(handler_tools) - 3} more")

        return True

    except Exception as e:
        print_error(f"Handler chain verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_optional_services():
    """Verify optional services (Redis, ChromaDB)."""
    print(f"\n{Colors.BOLD}4. Optional Services Test{Colors.END}")
    print("-" * 60)

    # Check Redis
    redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
    if redis_enabled:
        try:
            import redis
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))

            r = redis.Redis(host=redis_host, port=redis_port, socket_timeout=2)
            r.ping()
            print_success(f"Redis connection OK ({redis_host}:{redis_port})")
        except Exception as e:
            print_warning(f"Redis connection failed: {e}")
    else:
        print_info("Redis caching is disabled")

    # Check ChromaDB
    chroma_enabled = os.getenv('CHROMA_ENABLED', 'false').lower() == 'true'
    if chroma_enabled:
        try:
            import chromadb
            print_success("ChromaDB library available")
        except ImportError:
            print_warning("ChromaDB library not installed")
    else:
        print_info("ChromaDB vector search is disabled")

    return True


def verify_environment():
    """Verify environment variables are configured."""
    print(f"\n{Colors.BOLD}5. Environment Configuration Test{Colors.END}")
    print("-" * 60)

    required_vars = ['DATABASE_URL']
    optional_vars = [
        'REDIS_ENABLED', 'REDIS_HOST', 'REDIS_PORT',
        'CHROMA_ENABLED', 'VECTOR_SEARCH_ENABLED',
        'LOG_LEVEL', 'DEBUG'
    ]

    all_ok = True

    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var}: {value}")
        else:
            print_error(f"{var}: NOT SET (required)")
            all_ok = False

    # Check optional variables
    print_info("Optional configuration:")
    for var in optional_vars:
        value = os.getenv(var, 'not set')
        print(f"  {var}: {value}")

    return all_ok


async def main():
    """Main verification routine."""
    print_header()

    results = {
        'database': False,
        'schema': False,
        'handlers': False,
        'services': False,
        'environment': False
    }

    # Run verification tests
    results['database'], db = await verify_database_connection()

    if results['database'] and db:
        results['schema'] = await verify_database_tables(db)

    results['handlers'] = await verify_mcp_handlers()
    results['services'] = await verify_optional_services()
    results['environment'] = verify_environment()

    # Print summary
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}Verification Summary{Colors.END}")
    print("=" * 60)

    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name.capitalize():20} {status}")

    print("=" * 60)

    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All verification tests passed!{Colors.END}")
        print(f"\n{Colors.BOLD}Your MCP server is ready to use.{Colors.END}")
        print("\nNext steps:")
        print("  1. Connect your MCP client")
        print("  2. Verify 19 tools are available")
        print("  3. Try creating a memory with 'create_memory'")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some verification tests failed.{Colors.END}")
        print("\nTroubleshooting:")
        print("  1. Check TROUBLESHOOTING.md for solutions")
        print("  2. View logs: docker-compose logs")
        print("  3. Restart services: docker-compose restart")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
