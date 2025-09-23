#!/usr/bin/env python3
"""
Direct Python entry point for the MCP Invoice Server.
This avoids uvx caching issues and ensures we use the latest code.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the server
from src.server import main

if __name__ == "__main__":
    main()