#!/usr/bin/env python3
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