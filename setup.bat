@echo off
REM PRDY Quick Setup Script for Windows
REM Handles virtual environment creation and installation

echo 🚀 PRDY Quick Setup Script
echo ==========================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo ✅ Python detected

REM Create virtual environment if it doesn't exist
if not exist "prdy-env" (
    echo 📦 Creating virtual environment...
    python -m venv prdy-env
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call prdy-env\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Install PRDY package
echo 🎯 Installing PRDY package...
pip install -e .

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

pause