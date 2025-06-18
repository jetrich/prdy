@echo off
REM PRDY GUI Launcher for Windows
REM Double-click this file to launch PRDY GUI

title PRDY GUI Launcher
echo.
echo ╔══════════════════════════════════════════════════╗
echo ║                    PRDY GUI                      ║
echo ║        Product Requirements Document             ║
echo ║                  Generator                       ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is required but not installed
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Or use Microsoft Store:
    echo ms-windows-store://pdp/?ProductId=9NRWMJP3717K
    echo.
    pause
    exit /b 1
)

REM Launch the GUI
echo 🚀 Launching PRDY GUI...
python launch_gui.py

REM Keep window open if there were errors
if errorlevel 1 (
    echo.
    echo ❌ An error occurred. Please check the messages above.
    pause
)