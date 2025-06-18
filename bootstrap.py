#!/usr/bin/env python3
"""
Bootstrap script for PRDY
Automatically sets up the complete environment including AI providers
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def print_header():
    print("""
    ╔══════════════════════════════════════╗
    ║           PRD Generator              ║
    ║        Bootstrap Installer           ║
    ╚══════════════════════════════════════╝
    """)

def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_system_dependencies():
    """Check for required system dependencies"""
    deps = {
        "node": "Node.js (for Claude Code)",
        "npm": "npm (for Claude Code)", 
        "git": "Git (for version control)",
        "pip": "pip (Python package manager)"
    }
    
    missing = []
    for cmd, desc in deps.items():
        if cmd == "pip":
            # Check for pip in various forms
            pip_found = (shutil.which("pip") or 
                        shutil.which("pip3") or 
                        shutil.which("python3") and subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                                                  capture_output=True).returncode == 0)
        else:
            pip_found = shutil.which(cmd)
            
        if pip_found:
            print(f"✅ {desc}")
        else:
            print(f"❌ {desc} - not found")
            missing.append((cmd, desc))
    
    return missing

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        # Try different pip commands
        pip_commands = ["pip", "pip3", f"{sys.executable} -m pip"]
        
        for pip_cmd in pip_commands:
            try:
                result = subprocess.run(
                    f"{pip_cmd} install -r requirements.txt".split(),
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("✅ Python dependencies installed successfully")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        print("❌ Failed to install dependencies with any pip command")
        return False
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def install_package():
    """Install the PRD generator package"""
    print("\n📦 Installing PRD Generator package...")
    
    try:
        pip_commands = ["pip", "pip3", f"{sys.executable} -m pip"]
        
        for pip_cmd in pip_commands:
            try:
                result = subprocess.run(
                    f"{pip_cmd} install -e .".split(),
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("✅ PRD Generator package installed successfully")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        print("❌ Failed to install package")
        return False
        
    except Exception as e:
        print(f"❌ Error installing package: {e}")
        return False

def setup_ai_environment():
    """Set up AI environment interactively"""
    print("\n🤖 Setting up AI environment...")
    
    try:
        # Import after package installation
        sys.path.insert(0, '.')
        from prd_generator.utils.ai_integration import AIIntegration, AIProvider
        
        ai_integration = AIIntegration()
        capabilities = ai_integration.env_manager.detect_capabilities()
        
        print("\nSystem capabilities:")
        for cap, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"  {status} {cap.replace('_', ' ').title()}")
        
        # Auto-setup available providers
        if capabilities.get("node_js") and capabilities.get("npm"):
            print("\n🚀 Setting up Claude Code environment...")
            if ai_integration.setup_ai_provider(AIProvider.CLAUDE_CODE):
                print("✅ Claude Code environment ready!")
            else:
                print("⚠️  Claude Code setup had issues, but you can try manually later")
        
        if capabilities.get("ollama"):
            print("\n🚀 Setting up Ollama environment...")
            if ai_integration.setup_ai_provider(AIProvider.OLLAMA):
                print("✅ Ollama environment ready!")
            else:
                print("⚠️  Ollama setup had issues, but you can try manually later")
        
        return True
        
    except Exception as e:
        print(f"⚠️  AI setup encountered issues: {e}")
        print("   You can set up AI providers later with: prd ai setup")
        return True  # Non-blocking

def create_sample_config():
    """Create sample configuration files"""
    print("\n📝 Creating sample configuration...")
    
    try:
        config_dir = Path.home() / ".prd-generator"
        config_dir.mkdir(exist_ok=True)
        
        sample_config = {
            "default_ai_provider": "claude-code",
            "export_directory": "./exports",
            "database_url": "sqlite:///./prd_generator.db"
        }
        
        config_file = config_dir / "config.json"
        if not config_file.exists():
            import json
            with open(config_file, 'w') as f:
                json.dump(sample_config, f, indent=2)
            print(f"✅ Configuration created at {config_file}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Could not create configuration: {e}")
        return True  # Non-blocking

def run_basic_test():
    """Run a basic test to verify installation"""
    print("\n🧪 Running basic functionality test...")
    
    try:
        result = subprocess.run(
            ["prd", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ PRD Generator CLI is working!")
            return True
        else:
            print("❌ CLI test failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ CLI test timed out")
        return False
    except Exception as e:
        print(f"❌ CLI test error: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("""
    ╔══════════════════════════════════════╗
    ║             SUCCESS! 🎉              ║
    ╚══════════════════════════════════════╝
    
    🚀 PRD Generator is ready to use!
    
    📋 Quick Start:
        prd new                    # Create your first PRD
        prd list                   # List all PRDs
        prd ai status              # Check AI provider status
        prd ai setup               # Set up AI providers (if needed)
    
    📖 Full Command List:
        prd --help                 # Show all commands
        prd ai --help              # AI provider commands
    
    🔧 Configuration:
        ~/.prd-generator/config.json  # Main configuration
        ~/.prd-generator/environments/ # AI environments
    
    💡 Tips:
        - Start with a simple project to get familiar
        - Use 'prd ai setup' to configure Claude Code or Ollama
        - Export PRDs in multiple formats (markdown, PDF, text)
        - All data is stored locally in SQLite database
    
    🆘 Support:
        - Check CLAUDE.md for development guidance
        - Review README.md for comprehensive documentation
        - All issues are tracked with unique identifiers
    """)

def main():
    """Main bootstrap function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    print("\n🔍 Checking system dependencies...")
    missing_deps = check_system_dependencies()
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies:")
        for cmd, desc in missing_deps:
            print(f"   - {desc}")
        
        print("\n💡 Installation suggestions:")
        if platform.system() == "Windows":
            print("   - Install Node.js from: https://nodejs.org/")
            print("   - Install Git from: https://git-scm.com/")
        elif platform.system() == "Darwin":  # macOS
            print("   - Install with Homebrew: brew install node git")
        else:  # Linux
            print("   - Ubuntu/Debian: sudo apt install nodejs npm git")
            print("   - CentOS/RHEL: sudo yum install nodejs npm git")
        
        if not any(cmd in ["node", "npm"] for cmd, _ in missing_deps):
            # Can proceed without Node.js/npm, just won't have Claude Code
            print("\n✅ Can proceed with basic functionality (no Claude Code)")
        else:
            proceed = input("\nContinue anyway? (y/N): ").lower().strip()
            if proceed != 'y':
                print("Installation cancelled.")
                sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        sys.exit(1)
    
    # Install package
    if not install_package():
        print("\n❌ Failed to install package")
        sys.exit(1)
    
    # Set up AI environment
    setup_ai_environment()
    
    # Create configuration
    create_sample_config()
    
    # Test installation
    if not run_basic_test():
        print("\n⚠️  Installation completed but CLI test failed")
        print("   Try running: prd --help")
    
    # Show next steps
    print_next_steps()

if __name__ == "__main__":
    main()