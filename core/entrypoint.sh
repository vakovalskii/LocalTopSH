#!/bin/bash
# Entrypoint for core container
# Ensures workspace directory has correct permissions

set -e

echo "🔧 Initializing workspace permissions..."

# Ensure workspace directories exist with correct permissions
mkdir -p /workspace/_shared
chmod -R 777 /workspace

echo "✅ Workspace ready"

# Start the application
exec python -u main.py
