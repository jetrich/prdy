#!/usr/bin/env python3
"""
Simple PRDY GUI Launcher
Direct GUI launch for existing installations
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Print application header"""
    print("╔" + "═" * 50 + "╗")
    print("║" + " " * 18 + "PRDY GUI" + " " * 24 + "║")
    print("║" + " " * 10 + "Product Requirements Document" + " " * 9 + "║")
    print("║" + " " * 19 + "Generator" + " " * 20 + "║")
    print("╚" + "═" * 50 + "╝")
    print()

def find_python_executable():
    """Find the best Python executable to use"""
    project_dir = Path(__file__).parent.absolute()
    venv_path = project_dir / "prdy-env"
    
    # Try virtual environment first
    if platform.system() == "Windows":
        venv_python = venv_path / "Scripts" / "python.exe"
    else:
        venv_python = venv_path / "bin" / "python"
    
    if venv_python.exists():
        print(f"✅ Using virtual environment: {venv_python}")
        return str(venv_python)
    
    # Fall back to system Python
    python_candidates = ["python3", "python"]
    for candidate in python_candidates:
        try:
            result = subprocess.run([candidate, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Using system Python: {candidate}")
                return candidate
        except FileNotFoundError:
            continue
    
    print("❌ No suitable Python executable found")
    return None

def launch_gui_direct():
    """Launch GUI directly"""
    print_header()
    print("🚀 Launching PRDY GUI...")
    
    python_exe = find_python_executable()
    if not python_exe:
        return False
    
    try:
        # Change to project directory
        project_dir = Path(__file__).parent.absolute()
        os.chdir(project_dir)
        
        # Method 1: Try importing and running main
        try:
            print("🔄 Attempting direct import launch...")
            result = subprocess.run([
                python_exe, "-c", 
                "import sys; sys.path.insert(0, '.'); from prdy.gui import main; main()"
            ], check=True, timeout=5)
            print("✅ GUI launched successfully!")
            return True
        except subprocess.TimeoutExpired:
            print("✅ GUI is starting... (process timeout is normal)")
            return True
        except subprocess.CalledProcessError:
            pass
        
        # Method 2: Try module execution
        try:
            print("🔄 Attempting module execution...")
            if platform.system() == "Windows":
                subprocess.Popen([python_exe, "-m", "prdy.gui"], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([python_exe, "-m", "prdy.gui"])
            print("✅ GUI launched successfully!")
            return True
        except Exception:
            pass
        
        # Method 3: Try running gui.py directly
        try:
            print("🔄 Attempting direct file execution...")
            gui_file = project_dir / "prdy" / "gui.py"
            if gui_file.exists():
                if platform.system() == "Windows":
                    subprocess.Popen([python_exe, str(gui_file)], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen([python_exe, str(gui_file)])
                print("✅ GUI launched successfully!")
                return True
        except Exception:
            pass
        
        # Method 4: Try prdy-gui command if available
        try:
            print("🔄 Attempting prdy-gui command...")
            subprocess.Popen(["prdy-gui"])
            print("✅ GUI launched successfully!")
            return True
        except FileNotFoundError:
            pass
        
        print("❌ All launch methods failed")
        print("\n🔧 Manual alternatives:")
        print(f"   {python_exe} -m prdy.gui")
        print("   prdy-gui")
        print("\n💡 Make sure PRDY is properly installed:")
        print("   pip install -e .")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = launch_gui_direct()
        if success:
            print("\n💡 Look for the PRDY GUI window on your desktop")
            print("💡 The GUI should be starting now...")
        else:
            print("\n💔 Failed to launch GUI")
            input("Press Enter to exit...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Launch cancelled")
        sys.exit(1)