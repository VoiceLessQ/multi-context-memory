#!/usr/bin/env python3
"""
Updated entry point for the refactored MCP stdio server.
This file now imports the new refactored architecture.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the refactored stdio server
from src.mcp.refactored_stdio_server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())