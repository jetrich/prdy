#!/bin/bash

# PRDY Cleanup Script
# Removes virtual environment and build artifacts for a fresh start

echo "🧹 PRDY Cleanup Script"
echo "====================="

# Remove virtual environment
if [ -d "prdy-env" ]; then
    echo "🗑️  Removing virtual environment..."
    rm -rf prdy-env
    echo "✅ Virtual environment removed"
else
    echo "ℹ️  No virtual environment found"
fi

# Remove build artifacts
echo "🧽 Cleaning build artifacts..."

# Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Build directories
rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true

# Logs and cache
rm -rf logs/ cache/ temp/ 2>/dev/null || true

# Database files (optional - comment out if you want to keep data)
# rm -f *.db *.sqlite3 2>/dev/null || true

echo "✅ Cleanup completed"
echo ""
echo "📋 To reinstall PRDY:"
echo "  ./setup.sh"
echo ""
echo "💡 To also remove database files (PRD data), run:"
echo "  rm -f *.db *.sqlite3"