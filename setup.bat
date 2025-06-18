@echo off
REM PRDY Quick Setup Script for Windows
REM Handles virtual environment creation and installation with comprehensive error handling

echo 🚀 PRDY Quick Setup Script
echo ==========================

REM Comprehensive pre-installation checks
echo 🔍 Performing system checks...

REM Check if Python is available and version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed
    echo Please install Python 3.8 or higher from https://python.org
    echo.
    echo 🔧 Installation options:
    echo   - Download from: https://www.python.org/downloads/
    echo   - Or use Microsoft Store: ms-windows-store://pdp/?ProductId=9NRWMJP3717K
    echo   - Or use Chocolatey: choco install python
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detected

REM Check if venv module is available
python -c "import venv" >nul 2>&1
if errorlevel 1 (
    echo ❌ Python venv module is not available
    echo Please reinstall Python with all optional components
    pause
    exit /b 1
) else (
    echo ✅ Python venv module available
)

REM Check if pip is available (multiple methods)
set PIP_AVAILABLE=false
python -c "import pip" >nul 2>&1
if not errorlevel 1 set PIP_AVAILABLE=true
if %PIP_AVAILABLE%==false (
    pip --version >nul 2>&1
    if not errorlevel 1 set PIP_AVAILABLE=true
)
if %PIP_AVAILABLE%==false (
    python -m pip --version >nul 2>&1
    if not errorlevel 1 set PIP_AVAILABLE=true
)

if %PIP_AVAILABLE%==false (
    echo ❌ Python pip is not available
    echo Trying to bootstrap pip...
    python -m ensurepip --default-pip >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Successfully bootstrapped pip via ensurepip
    ) else (
        echo ❌ Cannot bootstrap pip - please reinstall Python with pip included
        pause
        exit /b 1
    )
) else (
    echo ✅ Python pip available
)

REM Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed (recommended for updates)
    echo Install from: https://git-scm.com/download/win
) else (
    echo ✅ Git available
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found (are you in the PRDY directory?)
    pause
    exit /b 1
) else (
    echo ✅ requirements.txt found
)

REM Check if pyproject.toml exists
if not exist "pyproject.toml" (
    echo ❌ pyproject.toml not found (are you in the PRDY directory?)
    pause
    exit /b 1
) else (
    echo ✅ pyproject.toml found
)

echo ✅ All system checks passed

REM Create virtual environment if it doesn't exist or is corrupted
if not exist "prdy-env\Scripts\activate.bat" (
    if exist "prdy-env" (
        echo 🔧 Removing corrupted virtual environment...
        rmdir /s /q prdy-env
    )
    
    echo 📦 Creating virtual environment...
    python -m venv prdy-env
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo.
        echo 🔧 Troubleshooting:
        echo   - Ensure Python is properly installed
        echo   - Try running as administrator
        echo   - Check for antivirus interference
        pause
        exit /b 1
    )
    
    if not exist "prdy-env\Scripts\activate.bat" (
        echo ❌ Virtual environment creation appeared to succeed but activation script is missing
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created successfully
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call prdy-env\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    echo Try manually:
    echo   rmdir /s /q prdy-env
    echo   python -m venv prdy-env
    echo   prdy-env\Scripts\activate.bat
    pause
    exit /b 1
)
echo ✅ Virtual environment activated

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Pip upgrade failed, continuing anyway...
) else (
    echo ✅ Pip upgraded successfully
)

REM Install dependencies with multiple fallback strategies
echo 📚 Installing dependencies...

set DEPS_INSTALLED=false
pip install -r requirements.txt >nul 2>&1
if not errorlevel 1 (
    echo ✅ Dependencies installed successfully
    set DEPS_INSTALLED=true
) else (
    echo 🔄 Trying alternative installation methods...
    
    pip install -r requirements.txt --user >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Dependencies installed with --user flag
        set DEPS_INSTALLED=true
    ) else (
        python -m pip install -r requirements.txt >nul 2>&1
        if not errorlevel 1 (
            echo ✅ Dependencies installed with python -m pip
            set DEPS_INSTALLED=true
        )
    )
)

if %DEPS_INSTALLED%==false (
    echo ❌ Failed to install dependencies with all strategies
    echo.
    echo 🔧 Manual troubleshooting:
    echo   1. Check internet connection
    echo   2. Try: pip install -r requirements.txt --verbose
    echo   3. Install individually: pip install click rich questionary pydantic sqlalchemy flet
    pause
    exit /b 1
)

REM Install PRDY package with multiple fallback strategies
echo 🎯 Installing PRDY package...

set PKG_INSTALLED=false
pip install -e . >nul 2>&1
if not errorlevel 1 (
    echo ✅ PRDY package installed successfully
    set PKG_INSTALLED=true
) else (
    echo 🔄 Trying alternative installation methods...
    
    pip install -e . --user >nul 2>&1
    if not errorlevel 1 (
        echo ✅ PRDY package installed with --user flag
        set PKG_INSTALLED=true
    ) else (
        python -m pip install -e . >nul 2>&1
        if not errorlevel 1 (
            echo ✅ PRDY package installed with python -m pip
            set PKG_INSTALLED=true
        )
    )
)

if %PKG_INSTALLED%==false (
    echo ❌ Failed to install PRDY package with all strategies
    echo.
    echo 🔧 Manual troubleshooting:
    echo   1. Check pyproject.toml is valid
    echo   2. Try: pip install setuptools wheel
    echo   3. Try: pip install -e . --verbose
    pause
    exit /b 1
)

REM Final validation
echo 🧪 Performing final validation...

where prdy >nul 2>&1
if not errorlevel 1 (
    echo ✅ PRDY command is available
    
    prdy --help >nul 2>&1
    if not errorlevel 1 (
        echo ✅ PRDY help command works
    ) else (
        echo ⚠️  PRDY help command failed - installation may be incomplete
    )
) else (
    echo ⚠️  PRDY command not found in PATH
)

python -c "import prdy; print('✅ PRDY module can be imported')" >nul 2>&1
if not errorlevel 1 (
    echo ✅ PRDY module imports successfully
) else (
    echo ⚠️  PRDY module import failed - installation may be incomplete
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Activate the virtual environment:
echo    prdy-env\Scripts\activate.bat
echo.
echo 2. Run PRDY:
echo    prdy                # GUI interface
echo    prdy --cli          # CLI interface
echo    prdy --help         # Show all options
echo.
echo 3. Create your first PRD:
echo    prdy new
echo.
echo 💡 To deactivate the virtual environment later, just run: deactivate
echo.
echo 🔧 If you encounter any issues:
echo   - Ensure virtual environment is active
echo   - Try: prdy-env\Scripts\activate.bat
echo   - For help: prdy --help

pause