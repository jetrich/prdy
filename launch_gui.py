#!/usr/bin/env python3
"""
PRDY GUI Launcher
Comprehensive cross-platform launcher that handles prerequisites, setup, and GUI execution
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Optional, Tuple, List
import json
import tempfile

# Color codes for cross-platform terminal output
class Colors:
    if platform.system() == "Windows":
        # Windows doesn't support ANSI by default, use simple output
        GREEN = ""
        RED = ""
        YELLOW = ""
        BLUE = ""
        PURPLE = ""
        CYAN = ""
        BOLD = ""
        RESET = ""
    else:
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        PURPLE = "\033[95m"
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

def print_colored(message: str, color: str = ""):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def print_header():
    """Print application header"""
    print_colored("╔" + "═" * 50 + "╗", Colors.BLUE)
    print_colored("║" + " " * 18 + "PRDY GUI" + " " * 24 + "║", Colors.BLUE)
    print_colored("║" + " " * 10 + "Product Requirements Document" + " " * 9 + "║", Colors.BLUE)
    print_colored("║" + " " * 19 + "Generator" + " " * 20 + "║", Colors.BLUE)
    print_colored("╚" + "═" * 50 + "╝", Colors.BLUE)
    print()

def check_python_version() -> bool:
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print_colored(f"❌ Python 3.8+ required (found {sys.version_info.major}.{sys.version_info.minor})", Colors.RED)
        return False
    
    print_colored(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected", Colors.GREEN)
    return True

def check_venv_available() -> bool:
    """Check if venv module is available"""
    try:
        import venv
        print_colored("✅ Python venv module available", Colors.GREEN)
        return True
    except ImportError:
        print_colored("❌ Python venv module not available", Colors.RED)
        return False

def check_pip_available() -> Tuple[bool, Optional[str]]:
    """Check if pip is available and return the command to use"""
    pip_commands = [
        [sys.executable, "-m", "pip"],
        ["pip3"],
        ["pip"]
    ]
    
    for cmd in pip_commands:
        try:
            result = subprocess.run(cmd + ["--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print_colored("✅ pip available", Colors.GREEN)
                return True, cmd
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print_colored("❌ pip not available", Colors.RED)
    return False, None

def check_git_available() -> bool:
    """Check if git is available"""
    try:
        subprocess.run(["git", "--version"], capture_output=True, timeout=10)
        print_colored("✅ Git available", Colors.GREEN)
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        print_colored("⚠️  Git not available (optional)", Colors.YELLOW)
        return False

def bootstrap_pip():
    """Try to bootstrap pip using ensurepip"""
    print_colored("🔄 Attempting to bootstrap pip...", Colors.CYAN)
    try:
        subprocess.run([sys.executable, "-m", "ensurepip", "--default-pip"], 
                      check=True, capture_output=True)
        print_colored("✅ Successfully bootstrapped pip", Colors.GREEN)
        return True
    except subprocess.CalledProcessError:
        print_colored("❌ Failed to bootstrap pip", Colors.RED)
        return False

def get_platform_install_commands() -> List[str]:
    """Get platform-specific installation commands"""
    system = platform.system().lower()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    if system == "linux":
        # Detect Linux distribution
        try:
            with open("/etc/os-release", "r") as f:
                os_release = f.read().lower()
            
            if "ubuntu" in os_release or "debian" in os_release:
                return [
                    "sudo apt update",
                    f"sudo apt install python3-venv python{python_version}-venv python3-pip python3-dev git"
                ]
            elif "fedora" in os_release or "centos" in os_release or "rhel" in os_release:
                return [
                    "sudo dnf install python3-venv python3-pip python3-devel git"
                ]
            elif "arch" in os_release:
                return [
                    "sudo pacman -S python-pip git"
                ]
        except FileNotFoundError:
            pass
        
        return [
            "# Install Python development tools for your distribution",
            "# Ubuntu/Debian: sudo apt install python3-venv python3-pip python3-dev git",
            "# Fedora/CentOS: sudo dnf install python3-venv python3-pip python3-devel git",
            "# Arch: sudo pacman -S python-pip git"
        ]
    
    elif system == "darwin":  # macOS
        return [
            "# Install via Homebrew:",
            "brew install python git",
            "# Or install Python from python.org"
        ]
    
    elif system == "windows":
        return [
            "# Install Python from:",
            "# https://www.python.org/downloads/",
            "# Or use Microsoft Store:",
            "# ms-windows-store://pdp/?ProductId=9NRWMJP3717K",
            "# Or use Chocolatey:",
            "# choco install python git"
        ]
    
    return ["# Please install Python 3.8+ and pip for your platform"]

def create_virtual_environment(venv_path: Path) -> bool:
    """Create virtual environment"""
    try:
        print_colored("📦 Creating virtual environment...", Colors.CYAN)
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                      check=True, capture_output=True)
        print_colored("✅ Virtual environment created", Colors.GREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to create virtual environment: {e}", Colors.RED)
        return False

def get_venv_python(venv_path: Path) -> str:
    """Get the python executable path for the virtual environment"""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "python.exe")
    else:
        return str(venv_path / "bin" / "python")

def get_venv_pip(venv_path: Path) -> List[str]:
    """Get the pip command for the virtual environment"""
    python_exe = get_venv_python(venv_path)
    return [python_exe, "-m", "pip"]

def install_requirements(venv_path: Path, requirements_file: Path) -> bool:
    """Install requirements in virtual environment"""
    if not requirements_file.exists():
        print_colored("⚠️  requirements.txt not found, skipping dependency installation", Colors.YELLOW)
        return True
    
    pip_cmd = get_venv_pip(venv_path)
    
    # First, check if dependencies are already installed
    try:
        result = subprocess.run(pip_cmd + ["list"], capture_output=True, text=True, timeout=30)
        if "flet" in result.stdout and "click" in result.stdout:
            print_colored("✅ Dependencies already installed", Colors.GREEN)
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    
    # Try multiple installation strategies
    strategies = [
        pip_cmd + ["install", "-r", str(requirements_file)],
        pip_cmd + ["install", "-r", str(requirements_file), "--user"],
        pip_cmd + ["install", "-r", str(requirements_file), "--no-cache-dir"],
    ]
    
    for i, strategy in enumerate(strategies):
        try:
            print_colored(f"📚 Installing dependencies (strategy {i+1}/{len(strategies)})...", Colors.CYAN)
            result = subprocess.run(strategy, check=True, capture_output=True, text=True, timeout=300)
            print_colored("✅ Dependencies installed successfully", Colors.GREEN)
            return True
        except subprocess.CalledProcessError as e:
            print_colored(f"⚠️  Strategy {i+1} failed: {e}", Colors.YELLOW)
            if i == len(strategies) - 1:  # Last strategy
                print_colored(f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No error details'}", Colors.RED)
        except subprocess.TimeoutExpired:
            print_colored(f"⚠️  Strategy {i+1} timed out", Colors.YELLOW)
    
    print_colored("❌ Failed to install dependencies with all strategies", Colors.RED)
    return False

def install_prdy_package(venv_path: Path, project_dir: Path) -> bool:
    """Install PRDY package in virtual environment"""
    pip_cmd = get_venv_pip(venv_path)
    
    # First, check if PRDY is already installed
    try:
        python_exe = get_venv_python(venv_path)
        result = subprocess.run([python_exe, "-c", "import prdy; print('PRDY already installed')"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_colored("✅ PRDY package already installed", Colors.GREEN)
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    
    strategies = [
        pip_cmd + ["install", "-e", str(project_dir)],
        pip_cmd + ["install", "-e", str(project_dir), "--user"],
    ]
    
    for i, strategy in enumerate(strategies):
        try:
            print_colored(f"🎯 Installing PRDY package (strategy {i+1}/{len(strategies)})...", Colors.CYAN)
            result = subprocess.run(strategy, check=True, capture_output=True, text=True, timeout=120)
            print_colored("✅ PRDY package installed successfully", Colors.GREEN)
            return True
        except subprocess.CalledProcessError as e:
            print_colored(f"⚠️  Strategy {i+1} failed: {e}", Colors.YELLOW)
            if i == len(strategies) - 1:  # Last strategy
                print_colored(f"Error output: {e.stderr if hasattr(e, 'stderr') else 'No error details'}", Colors.RED)
        except subprocess.TimeoutExpired:
            print_colored(f"⚠️  Strategy {i+1} timed out", Colors.YELLOW)
    
    print_colored("❌ Failed to install PRDY package with all strategies", Colors.RED)
    return False

def validate_installation(venv_path: Path) -> bool:
    """Validate that PRDY is properly installed"""
    python_exe = get_venv_python(venv_path)
    
    try:
        # Test import
        result = subprocess.run([python_exe, "-c", "import prdy; print('✅ PRDY module imported successfully')"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_colored("✅ PRDY installation validated", Colors.GREEN)
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    
    print_colored("❌ PRDY installation validation failed", Colors.RED)
    return False

def launch_gui(venv_path: Path) -> bool:
    """Launch the PRDY GUI"""
    python_exe = get_venv_python(venv_path)
    
    try:
        print_colored("🚀 Launching PRDY GUI...", Colors.CYAN)
        # Launch GUI in a way that doesn't block
        if platform.system() == "Windows":
            subprocess.Popen([python_exe, "-m", "prdy.gui"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([python_exe, "-m", "prdy.gui"])
        
        print_colored("✅ PRDY GUI launched successfully!", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"❌ Failed to launch GUI: {e}", Colors.RED)
        return False

def main():
    """Main launcher function"""
    print_header()
    
    # Determine project directory
    project_dir = Path(__file__).parent.absolute()
    venv_path = project_dir / "prdy-env"
    requirements_file = project_dir / "requirements.txt"
    
    print_colored("🔍 Performing system checks...", Colors.CYAN)
    
    # Check prerequisites
    issues = []
    
    if not check_python_version():
        issues.append("Python 3.8+ required")
    
    if not check_venv_available():
        issues.append("Python venv module not available")
    
    pip_available, pip_cmd = check_pip_available()
    if not pip_available:
        if not bootstrap_pip():
            issues.append("pip not available")
    
    check_git_available()  # Optional
    
    if issues:
        print_colored("\n❌ Prerequisites not met:", Colors.RED)
        for issue in issues:
            print_colored(f"   - {issue}", Colors.RED)
        
        print_colored("\n🔧 Installation commands for your platform:", Colors.YELLOW)
        commands = get_platform_install_commands()
        for cmd in commands:
            print_colored(f"   {cmd}", Colors.YELLOW)
        
        return False
    
    print_colored("✅ All system checks passed\n", Colors.GREEN)
    
    # Setup virtual environment if needed
    if not venv_path.exists() or not (venv_path / ("Scripts" if platform.system() == "Windows" else "bin")).exists():
        if venv_path.exists():
            print_colored("🔧 Removing corrupted virtual environment...", Colors.YELLOW)
            shutil.rmtree(venv_path)
        
        if not create_virtual_environment(venv_path):
            return False
    else:
        print_colored("✅ Virtual environment already exists", Colors.GREEN)
    
    # Install dependencies and package
    if not install_requirements(venv_path, requirements_file):
        return False
    
    if not install_prdy_package(venv_path, project_dir):
        return False
    
    # Validate installation
    if not validate_installation(venv_path):
        return False
    
    # Launch GUI
    if not launch_gui(venv_path):
        return False
    
    print_colored("\n🎉 PRDY GUI is now running!", Colors.GREEN)
    print_colored("💡 Check your desktop for the PRDY application window", Colors.CYAN)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print_colored("\n💔 Setup failed. Please check the error messages above.", Colors.RED)
            sys.exit(1)
    except KeyboardInterrupt:
        print_colored("\n\n⏹️  Setup cancelled by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n💥 Unexpected error: {e}", Colors.RED)
        sys.exit(1)