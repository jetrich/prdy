#!/bin/bash
# PRDY GUI Launcher for macOS/Linux
# Double-click this file or run ./launch_prdy_gui.sh to launch PRDY GUI

clear
echo "╔══════════════════════════════════════════════════╗"
echo "║                    PRDY GUI                      ║"
echo "║        Product Requirements Document             ║"
echo "║                  Generator                       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo ""
    echo "Please install Python 3.8 or higher:"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install python"
        echo "  or download from: https://www.python.org/downloads/"
    else
        echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
        echo "  Fedora/CentOS: sudo dnf install python3 python3-venv python3-pip"
        echo "  or download from: https://www.python.org/downloads/"
    fi
    
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Launch the GUI
echo "🚀 Launching PRDY GUI..."
python3 launch_gui.py

# Keep terminal open if there were errors
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ An error occurred. Please check the messages above."
    read -p "Press Enter to exit..."
fi