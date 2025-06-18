#!/bin/bash
set -e

# PRDY Quick Setup Script
# Handles virtual environment creation and installation

echo "🚀 PRDY Quick Setup Script"
echo "=========================="

# Comprehensive pre-installation checks
perform_system_checks() {
    local issues=0
    
    echo "🔍 Performing system checks..."
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed"
        issues=$((issues + 1))
    else
        # Check Python version
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.8"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
            echo "❌ Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
            issues=$((issues + 1))
        else
            echo "✅ Python $PYTHON_VERSION detected"
        fi
        
        # Check if venv module is available
        if ! python3 -c "import venv" 2>/dev/null; then
            echo "❌ Python venv module is not available"
            
            # Get specific Python version for more precise package names
            PYTHON_MINOR_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
            
            if command -v apt &> /dev/null; then
                echo "   Fix: sudo apt install python3-venv python${PYTHON_MINOR_VERSION}-venv"
            elif command -v dnf &> /dev/null; then
                echo "   Fix: sudo dnf install python3-venv"
            elif command -v yum &> /dev/null; then
                echo "   Fix: sudo yum install python3-venv"
            fi
            issues=$((issues + 1))
        else
            echo "✅ Python venv module available"
        fi
        
        # Check if pip is available (try multiple methods)
        pip_available=false
        if python3 -c "import pip" 2>/dev/null; then
            pip_available=true
        elif command -v pip3 &> /dev/null; then
            pip_available=true
        elif command -v pip &> /dev/null; then
            pip_available=true
        elif python3 -m pip --version &> /dev/null; then
            pip_available=true
        fi
        
        if [ "$pip_available" = false ]; then
            # Try to bootstrap pip using ensurepip
            echo "⚠️  Python pip not found, trying to bootstrap..."
            if python3 -m ensurepip --default-pip 2>/dev/null; then
                echo "✅ Successfully bootstrapped pip via ensurepip"
            else
                echo "❌ Python pip is not available and cannot be bootstrapped"
                echo ""
                echo "🔧 Manual installation required:"
                if command -v apt &> /dev/null; then
                    echo "   sudo apt update"
                    echo "   sudo apt install python3-pip python3-ensurepip"
                elif command -v dnf &> /dev/null; then
                    echo "   sudo dnf install python3-pip"
                elif command -v yum &> /dev/null; then
                    echo "   sudo yum install python3-pip"
                elif command -v brew &> /dev/null; then
                    echo "   brew install python"
                elif command -v pacman &> /dev/null; then
                    echo "   sudo pacman -S python-pip"
                fi
                echo ""
                echo "📋 Alternative: Download get-pip.py"
                echo "   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py"
                echo "   python3 get-pip.py --user"
                issues=$((issues + 1))
            fi
        else
            echo "✅ Python pip available"
        fi
    fi
    
    # Check if git is available (for cloning)
    if ! command -v git &> /dev/null; then
        echo "❌ Git is not installed (needed for cloning repository)"
        issues=$((issues + 1))
    else
        echo "✅ Git available"
    fi
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        echo "❌ requirements.txt not found (are you in the PRDY directory?)"
        issues=$((issues + 1))
    else
        echo "✅ requirements.txt found"
    fi
    
    # Check if pyproject.toml exists
    if [ ! -f "pyproject.toml" ]; then
        echo "❌ pyproject.toml not found (are you in the PRDY directory?)"
        issues=$((issues + 1))
    else
        echo "✅ pyproject.toml found"
    fi
    
    if [ $issues -gt 0 ]; then
        echo ""
        echo "❌ Found $issues issue(s) that need to be resolved before installation"
        echo ""
        echo "🔧 Common fixes:"
        # Get specific Python version for more precise package names
        PYTHON_MINOR_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3")
        
        if command -v apt &> /dev/null; then
            echo "  sudo apt update"
            echo "  sudo apt install python3 python3-venv python${PYTHON_MINOR_VERSION}-venv python3-pip python3-dev git"
        elif command -v dnf &> /dev/null; then
            echo "  sudo dnf install python3 python3-venv python3-pip python3-devel git"
        elif command -v yum &> /dev/null; then
            echo "  sudo yum install python3 python3-venv python3-pip python3-devel git"
        elif command -v brew &> /dev/null; then
            echo "  brew install python git"
        fi
        echo ""
        exit 1
    fi
    
    echo "✅ All system checks passed"
}

# Run system checks
perform_system_checks

# Create virtual environment if it doesn't exist or is corrupted
if [ ! -f "prdy-env/bin/activate" ]; then
    if [ -d "prdy-env" ]; then
        echo "🔧 Removing corrupted virtual environment..."
        rm -rf prdy-env
    fi
    
    echo "📦 Creating virtual environment..."
    
    # Try to create virtual environment with better error handling
    if python3 -m venv prdy-env 2>/dev/null; then
        echo "✅ Virtual environment created successfully"
    else
        echo "❌ Failed to create virtual environment"
        echo ""
        echo "🔧 Common fixes:"
        
        # Get specific Python version for more precise package names
        PYTHON_MINOR_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3")
        
        # Check if we're on Debian/Ubuntu
        if command -v apt &> /dev/null; then
            echo "On Debian/Ubuntu, install python3-venv:"
            echo "  sudo apt update"
            echo "  sudo apt install python3-venv python${PYTHON_MINOR_VERSION}-venv python3-dev"
        elif command -v yum &> /dev/null || command -v dnf &> /dev/null; then
            echo "On CentOS/RHEL/Fedora, install python3-venv:"
            echo "  sudo dnf install python3-venv python3-devel"
        elif command -v brew &> /dev/null; then
            echo "On macOS, ensure Python is properly installed:"
            echo "  brew install python"
        fi
        
        echo ""
        echo "Alternative installation without virtual environment:"
        echo "  pip3 install -r requirements.txt --user"
        echo "  pip3 install -e . --user"
        echo ""
        echo "Or use pipx for isolation:"
        echo "  pipx install git+https://github.com/jetrich/prdy.git"
        exit 1
    fi
    
    # Verify creation was successful
    if [ ! -f "prdy-env/bin/activate" ]; then
        echo "❌ Virtual environment creation appeared to succeed but activation script is missing"
        echo "Please try manually:"
        echo "  rm -rf prdy-env"
        echo "  python3 -m venv prdy-env"
        exit 1
    fi
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if source prdy-env/bin/activate; then
    echo "✅ Virtual environment activated"
else
    echo "❌ Failed to activate virtual environment"
    echo "Please try manually:"
    echo "  rm -rf prdy-env"
    echo "  python3 -m venv prdy-env"
    echo "  source prdy-env/bin/activate"
    exit 1
fi

# Verify we're in the virtual environment
if [[ "$VIRTUAL_ENV" != *"prdy-env"* ]]; then
    echo "⚠️  Warning: Virtual environment may not be properly activated"
    echo "   Current VIRTUAL_ENV: $VIRTUAL_ENV"
    echo "   Expected: */prdy-env"
    echo ""
    echo "🔧 If installation fails, try:"
    echo "   deactivate  # if already in a venv"
    echo "   rm -rf prdy-env"
    echo "   python3 -m venv prdy-env"
    echo "   source prdy-env/bin/activate"
    echo "   ./setup.sh"
else
    echo "✅ Virtual environment properly activated: $VIRTUAL_ENV"
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
if pip install --upgrade pip; then
    echo "✅ Pip upgraded successfully"
else
    echo "⚠️  Pip upgrade failed, continuing anyway..."
fi

# Install dependencies with multiple fallback strategies
echo "📚 Installing dependencies..."

# Try multiple pip installation strategies
dependency_installed=false
pip_strategies=(
    "pip install -r requirements.txt"
    "pip install -r requirements.txt --user"
    "pip install -r requirements.txt --no-cache-dir"
    "pip install -r requirements.txt --no-deps --force-reinstall"
    "python3 -m pip install -r requirements.txt"
    "python3 -m pip install -r requirements.txt --user"
)

for strategy in "${pip_strategies[@]}"; do
    echo "🔄 Trying: $strategy"
    if $strategy 2>/dev/null; then
        echo "✅ Dependencies installed successfully with: $strategy"
        dependency_installed=true
        break
    else
        echo "⚠️  Strategy failed, trying next..."
    fi
done

if [ "$dependency_installed" = false ]; then
    echo "❌ Failed to install dependencies with all strategies"
    echo ""
    echo "🔧 Manual troubleshooting steps:"
    echo "1. Check if you're in a virtual environment:"
    echo "   echo \$VIRTUAL_ENV"
    echo ""
    echo "2. Try upgrading pip first:"
    echo "   pip install --upgrade pip"
    echo "   pip install -r requirements.txt"
    echo ""
    echo "3. Check for permission issues:"
    echo "   pip install -r requirements.txt --user"
    echo ""
    echo "4. Check requirements.txt contents:"
    echo "   cat requirements.txt"
    echo ""
    echo "5. Install dependencies one by one:"
    echo "   pip install click rich questionary pydantic sqlalchemy flet"
    exit 1
fi

# Install PRDY package with multiple fallback strategies
echo "🎯 Installing PRDY package..."

package_installed=false
package_strategies=(
    "pip install -e ."
    "pip install -e . --user"
    "pip install -e . --no-cache-dir"
    "python3 -m pip install -e ."
    "python3 -m pip install -e . --user"
)

for strategy in "${package_strategies[@]}"; do
    echo "🔄 Trying: $strategy"
    if $strategy 2>/dev/null; then
        echo "✅ PRDY package installed successfully with: $strategy"
        package_installed=true
        break
    else
        echo "⚠️  Strategy failed, trying next..."
    fi
done

if [ "$package_installed" = false ]; then
    echo "❌ Failed to install PRDY package with all strategies"
    echo ""
    echo "🔧 Manual troubleshooting steps:"
    echo "1. Check if pyproject.toml is valid:"
    echo "   python3 -c \"import tomllib; print('Valid TOML')\""
    echo ""
    echo "2. Try building and installing manually:"
    echo "   pip install build"
    echo "   python3 -m build"
    echo "   pip install dist/*.whl"
    echo ""
    echo "3. Install in development mode manually:"
    echo "   pip install setuptools wheel"
    echo "   pip install -e . --verbose"
    exit 1
fi

# Final validation - test that PRDY is actually working
echo "🧪 Performing final validation..."

if command -v prdy &> /dev/null; then
    echo "✅ PRDY command is available"
    
    # Test that prdy help works
    if prdy --help &> /dev/null; then
        echo "✅ PRDY help command works"
    else
        echo "⚠️  PRDY help command failed - installation may be incomplete"
    fi
else
    echo "⚠️  PRDY command not found in PATH"
    echo "   Try running: source prdy-env/bin/activate"
fi

# Test Python imports
if python3 -c "import prdy; print('✅ PRDY module can be imported')" 2>/dev/null; then
    echo "✅ PRDY module imports successfully"
else
    echo "⚠️  PRDY module import failed"
    echo "   Installation may be incomplete"
fi

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
echo ""
echo "🔧 If you encounter any issues:"
echo "   - Check that you're in the virtual environment: echo \$VIRTUAL_ENV"
echo "   - Try: source prdy-env/bin/activate"
echo "   - For help: prdy --help"