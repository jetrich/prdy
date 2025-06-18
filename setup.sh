#!/bin/bash
set -e

# PRDY Quick Setup Script
# Handles virtual environment creation and installation

echo "🚀 PRDY Quick Setup Script"
echo "=========================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "prdy-env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv prdy-env
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source prdy-env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install PRDY package
echo "🎯 Installing PRDY package..."
pip install -e .

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate the virtual environment:"
echo "   source prdy-env/bin/activate"
echo ""
echo "2. Run PRDY:"
echo "   prdy                # GUI interface"
echo "   prdy --cli          # CLI interface"
echo "   prdy --help         # Show all options"
echo ""
echo "3. Create your first PRD:"
echo "   prdy new"
echo ""
echo "💡 To deactivate the virtual environment later, just run: deactivate"