#!/bin/bash
# Shell wrapper to start the MCP Invoice Server with virtual environment.

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Run the Python server
exec python3 "$SCRIPT_DIR/run_server.py"