"""
Environment Manager for PRD Generator
Handles Claude Code and Ollama setup in isolated environments
"""

import os
import sys
import subprocess
import shutil
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import venv

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class EnvironmentConfig:
    """Configuration for AI environment"""
    ai_provider: str  # "claude-code" or "ollama"
    environment_path: str
    node_version: Optional[str] = None
    claude_code_version: str = "latest"
    ollama_model: str = "llama2"
    ollama_url: str = "http://localhost:11434"


class EnvironmentManager:
    """Manages isolated environments for AI providers"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or os.path.expanduser("~/.prd-generator"))
        self.environments_path = self.base_path / "environments"
        self.config_path = self.base_path / "config.json"
        
        # Ensure directories exist
        self.base_path.mkdir(exist_ok=True)
        self.environments_path.mkdir(exist_ok=True)
    
    def detect_capabilities(self) -> Dict[str, bool]:
        """Detect what AI capabilities are available on the system"""
        capabilities = {
            "node_js": shutil.which("node") is not None,
            "npm": shutil.which("npm") is not None,
            "python": shutil.which("python3") is not None,
            "git": shutil.which("git") is not None,
            "ollama": shutil.which("ollama") is not None or self._check_ollama_service()
        }
        
        if capabilities["node_js"] and capabilities["npm"]:
            try:
                result = subprocess.run(
                    ["node", "--version"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                capabilities["node_version"] = result.stdout.strip()
            except subprocess.CalledProcessError:
                capabilities["node_js"] = False
        
        return capabilities
    
    def _check_ollama_service(self) -> bool:
        """Check if Ollama service is running"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def setup_claude_code_environment(self, environment_name: str = "claude-code") -> bool:
        """Set up isolated Claude Code environment"""
        env_path = self.environments_path / environment_name
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Check prerequisites
            task = progress.add_task("Checking prerequisites...", total=None)
            capabilities = self.detect_capabilities()
            
            if not capabilities["node_js"] or not capabilities["npm"]:
                console.print("❌ Node.js and npm are required for Claude Code", style="red")
                return False
            
            progress.update(task, description="Creating environment directory...")
            env_path.mkdir(exist_ok=True)
            
            # Create package.json for the environment
            progress.update(task, description="Setting up package.json...")
            package_json = {
                "name": "prd-generator-claude-env",
                "version": "1.0.0",
                "description": "Claude Code environment for PRD Generator",
                "private": True,
                "dependencies": {
                    "@anthropic-ai/claude-code": "^1.0.27"
                }
            }
            
            with open(env_path / "package.json", "w") as f:
                json.dump(package_json, f, indent=2)
            
            # Install Claude Code
            progress.update(task, description="Installing Claude Code...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=env_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                console.print(f"❌ Failed to install Claude Code: {e}", style="red")
                return False
            
            # Create wrapper script
            progress.update(task, description="Creating wrapper script...")
            self._create_claude_wrapper(env_path)
            
            # Save environment configuration
            config = EnvironmentConfig(
                ai_provider="claude-code",
                environment_path=str(env_path),
                node_version=capabilities.get("node_version"),
                claude_code_version="1.0.27"
            )
            self._save_environment_config(environment_name, config)
            
            progress.update(task, description="✅ Claude Code environment ready!")
        
        console.print(f"✅ Claude Code environment created at: {env_path}", style="green")
        return True
    
    def setup_ollama_environment(self, environment_name: str = "ollama") -> bool:
        """Set up Ollama environment"""
        capabilities = self.detect_capabilities()
        
        if not capabilities["ollama"]:
            console.print("❌ Ollama not found. Please install Ollama first.", style="red")
            console.print("📥 Install from: https://ollama.ai/download", style="blue")
            return False
        
        # Test Ollama connection
        if not self._check_ollama_service():
            console.print("❌ Ollama service not running. Please start Ollama.", style="red")
            console.print("💡 Run: ollama serve", style="blue")
            return False
        
        env_path = self.environments_path / environment_name
        env_path.mkdir(exist_ok=True)
        
        # Save environment configuration
        config = EnvironmentConfig(
            ai_provider="ollama",
            environment_path=str(env_path),
            ollama_model="llama2",
            ollama_url="http://localhost:11434"
        )
        self._save_environment_config(environment_name, config)
        
        console.print(f"✅ Ollama environment configured at: {env_path}", style="green")
        return True
    
    def _create_claude_wrapper(self, env_path: Path):
        """Create a wrapper script for Claude Code"""
        wrapper_content = f"""#!/bin/bash
# Claude Code wrapper for PRD Generator
cd "{env_path}"
exec ./node_modules/.bin/claude "$@"
"""
        
        wrapper_path = env_path / "claude-wrapper.sh"
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)
        
        # Make executable
        os.chmod(wrapper_path, 0o755)
        
        # Create Windows batch file too
        windows_wrapper = f"""@echo off
cd /d "{env_path}"
node_modules\\.bin\\claude.cmd %*
"""
        
        with open(env_path / "claude-wrapper.bat", "w") as f:
            f.write(windows_wrapper)
    
    def _save_environment_config(self, env_name: str, config: EnvironmentConfig):
        """Save environment configuration"""
        configs = self._load_all_configs()
        configs[env_name] = {
            "ai_provider": config.ai_provider,
            "environment_path": config.environment_path,
            "node_version": config.node_version,
            "claude_code_version": config.claude_code_version,
            "ollama_model": config.ollama_model,
            "ollama_url": config.ollama_url
        }
        
        with open(self.config_path, "w") as f:
            json.dump(configs, f, indent=2)
    
    def _load_all_configs(self) -> Dict[str, Any]:
        """Load all environment configurations"""
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def list_environments(self) -> Dict[str, EnvironmentConfig]:
        """List all configured environments"""
        configs = self._load_all_configs()
        environments = {}
        
        for name, config_data in configs.items():
            environments[name] = EnvironmentConfig(**config_data)
        
        return environments
    
    def get_environment(self, name: str) -> Optional[EnvironmentConfig]:
        """Get specific environment configuration"""
        configs = self._load_all_configs()
        config_data = configs.get(name)
        
        if config_data:
            return EnvironmentConfig(**config_data)
        return None
    
    def execute_claude_code(self, env_name: str, command: str, working_dir: str = None) -> subprocess.CompletedProcess:
        """Execute Claude Code command in specified environment"""
        env_config = self.get_environment(env_name)
        if not env_config or env_config.ai_provider != "claude-code":
            raise ValueError(f"Claude Code environment '{env_name}' not found")
        
        env_path = Path(env_config.environment_path)
        
        # Use wrapper script
        if os.name == "nt":  # Windows
            wrapper = env_path / "claude-wrapper.bat"
        else:
            wrapper = env_path / "claude-wrapper.sh"
        
        cmd = [str(wrapper)] + command.split()
        
        return subprocess.run(
            cmd,
            cwd=working_dir or os.getcwd(),
            capture_output=True,
            text=True
        )
    
    def execute_ollama(self, env_name: str, prompt: str, model: str = None) -> Dict[str, Any]:
        """Execute Ollama query"""
        env_config = self.get_environment(env_name)
        if not env_config or env_config.ai_provider != "ollama":
            raise ValueError(f"Ollama environment '{env_name}' not found")
        
        try:
            import requests
            
            model = model or env_config.ollama_model
            url = f"{env_config.ollama_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            return {"error": str(e)}
    
    def delete_environment(self, env_name: str) -> bool:
        """Delete an environment"""
        env_config = self.get_environment(env_name)
        if not env_config:
            return False
        
        # Remove directory
        env_path = Path(env_config.environment_path)
        if env_path.exists():
            shutil.rmtree(env_path)
        
        # Remove from config
        configs = self._load_all_configs()
        if env_name in configs:
            del configs[env_name]
            with open(self.config_path, "w") as f:
                json.dump(configs, f, indent=2)
        
        return True