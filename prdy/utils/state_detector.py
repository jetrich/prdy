"""
State Detector for PRD Generator
Detects current application state and bootstrap status
"""

import os
import sys
import subprocess
import shutil
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time

from .logger import get_logger
from .settings_manager import SettingsManager

logger = get_logger("state_detector")


class StateDetector:
    """Detects and validates application state"""
    
    def __init__(self, settings_manager: SettingsManager = None):
        self.settings_manager = settings_manager or SettingsManager()
        self.detection_cache = {}
        self.cache_timeout = 300  # 5 minutes
    
    def get_complete_system_state(self) -> Dict[str, any]:
        """Get comprehensive system state"""
        logger.info("Performing complete system state detection")
        
        state = {
            'timestamp': time.time(),
            'python_environment': self._check_python_environment(),
            'dependencies': self._check_dependencies(),
            'system_tools': self._check_system_tools(),
            'ai_providers': self._check_ai_providers(),
            'database': self._check_database(),
            'environments': self._check_environments(),
            'permissions': self._check_permissions(),
            'network': self._check_network_connectivity(),
            'resources': self._check_system_resources(),
            'bootstrap_status': self._determine_bootstrap_status()
        }
        
        # Update settings with current state
        self.settings_manager.update_bootstrap_status({
            'dependencies_installed': state['dependencies']['all_installed'],
            'database_initialized': state['database']['initialized'],
            'claude_code_installed': state['ai_providers']['claude_code']['installed'],
            'ollama_available': state['ai_providers']['ollama']['available']
        })
        
        logger.info(f"System state detection completed. Bootstrap status: {state['bootstrap_status']['is_ready']}")
        return state
    
    def _check_python_environment(self) -> Dict[str, any]:
        """Check Python environment"""
        try:
            result = {
                'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'version_compatible': sys.version_info >= (3, 8),
                'executable': sys.executable,
                'virtual_env': hasattr(sys, 'real_prefix') or (
                    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
                ),
                'platform': sys.platform,
                'architecture': getattr(sys, 'implementation', 'unknown'),
            }
            
            logger.debug(f"Python environment: {result}")
            return result
            
        except Exception as e:
            logger.error("Failed to check Python environment", exception=e)
            return {'error': str(e)}
    
    def _check_dependencies(self) -> Dict[str, any]:
        """Check if all required dependencies are installed"""
        required_deps = [
            'click', 'rich', 'pydantic', 'sqlalchemy', 'alembic',
            'jinja2', 'reportlab', 'markdown', 'pyyaml', 'python-dotenv',
            'questionary', 'requests', 'flet', 'psutil'
        ]
        
        installed = []
        missing = []
        
        for dep in required_deps:
            try:
                spec = importlib.util.find_spec(dep)
                if spec is not None:
                    installed.append(dep)
                else:
                    missing.append(dep)
            except ImportError:
                missing.append(dep)
        
        result = {
            'required': required_deps,
            'installed': installed,
            'missing': missing,
            'all_installed': len(missing) == 0,
            'install_command': f"{sys.executable} -m pip install {' '.join(missing)}" if missing else None
        }
        
        logger.debug(f"Dependencies check: {len(installed)}/{len(required_deps)} installed")
        return result
    
    def _check_system_tools(self) -> Dict[str, any]:
        """Check system tools availability"""
        tools = {
            'node': {'required': True, 'purpose': 'Claude Code installation'},
            'npm': {'required': True, 'purpose': 'Claude Code package management'},
            'git': {'required': False, 'purpose': 'Version control'},
            'ollama': {'required': False, 'purpose': 'Local AI provider'}
        }
        
        results = {}
        for tool, info in tools.items():
            try:
                path = shutil.which(tool)
                if path:
                    # Get version if possible
                    version = None
                    try:
                        if tool in ['node', 'npm', 'git']:
                            result = subprocess.run([tool, '--version'], 
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode == 0:
                                version = result.stdout.strip()
                        elif tool == 'ollama':
                            result = subprocess.run([tool, '--version'], 
                                                  capture_output=True, text=True, timeout=5)
                            if result.returncode == 0:
                                version = result.stdout.strip()
                    except:
                        pass
                    
                    results[tool] = {
                        'available': True,
                        'path': path,
                        'version': version,
                        **info
                    }
                else:
                    results[tool] = {
                        'available': False,
                        'path': None,
                        'version': None,
                        **info
                    }
            except Exception as e:
                results[tool] = {
                    'available': False,
                    'error': str(e),
                    **info
                }
        
        # Summary
        required_available = all(results[tool]['available'] for tool, info in tools.items() if info['required'])
        
        results['summary'] = {
            'all_required_available': required_available,
            'missing_required': [tool for tool, info in tools.items() 
                               if info['required'] and not results[tool]['available']]
        }
        
        logger.debug(f"System tools check: Required tools available: {required_available}")
        return results
    
    def _check_ai_providers(self) -> Dict[str, any]:
        """Check AI provider status"""
        from .environment_manager import EnvironmentManager
        
        try:
            env_manager = EnvironmentManager()
            environments = env_manager.list_environments()
            
            # Check Claude Code
            claude_code_status = {
                'installed': False,
                'environment_path': None,
                'version': None,
                'working': False
            }
            
            if 'claude-code' in environments:
                env_config = environments['claude-code']
                claude_code_status['installed'] = True
                claude_code_status['environment_path'] = env_config.environment_path
                
                # Test if Claude Code is working
                try:
                    result = env_manager.execute_claude_code('claude-code', '--version')
                    if result.returncode == 0:
                        claude_code_status['working'] = True
                        claude_code_status['version'] = result.stdout.strip()
                except:
                    pass
            
            # Check Ollama
            ollama_status = {
                'available': False,
                'running': False,
                'models': [],
                'url': None
            }
            
            if 'ollama' in environments:
                env_config = environments['ollama']
                ollama_status['available'] = True
                ollama_status['url'] = env_config.ollama_url
                
                # Test if Ollama is running
                try:
                    response = env_manager.execute_ollama('ollama', 'test prompt')
                    if 'error' not in response:
                        ollama_status['running'] = True
                except:
                    pass
            
            return {
                'claude_code': claude_code_status,
                'ollama': ollama_status,
                'environments': {name: {'provider': env.ai_provider, 'path': env.environment_path} 
                               for name, env in environments.items()}
            }
            
        except Exception as e:
            logger.error("Failed to check AI providers", exception=e)
            return {'error': str(e)}
    
    def _check_database(self) -> Dict[str, any]:
        """Check database status"""
        try:
            from ..models.database import init_database, get_db_sync
            from ..models.prd import PRDSession
            
            # Try to initialize database
            db_url = self.settings_manager.get_database_url()
            db_manager = init_database(db_url)
            
            # Test database connection
            db = get_db_sync()
            try:
                # Try a simple query
                result = db.query(PRDSession).count()
                
                return {
                    'initialized': True,
                    'url': db_url,
                    'connection_working': True,
                    'session_count': result
                }
            except Exception as e:
                return {
                    'initialized': False,
                    'url': db_url,
                    'connection_working': False,
                    'error': str(e)
                }
            finally:
                db.close()
                
        except Exception as e:
            logger.error("Failed to check database", exception=e)
            return {
                'initialized': False,
                'error': str(e)
            }
    
    def _check_environments(self) -> Dict[str, any]:
        """Check environment directories and permissions"""
        app_info = self.settings_manager.get_app_info()
        
        results = {}
        for name, path in app_info.items():
            if '_directory' in name or name in ['settings_file', 'state_file']:
                path_obj = Path(path)
                results[name] = {
                    'path': str(path_obj),
                    'exists': path_obj.exists(),
                    'readable': path_obj.exists() and os.access(path_obj, os.R_OK),
                    'writable': path_obj.exists() and os.access(path_obj, os.W_OK),
                    'size': path_obj.stat().st_size if path_obj.exists() and path_obj.is_file() else None
                }
        
        return results
    
    def _check_permissions(self) -> Dict[str, any]:
        """Check file system permissions"""
        app_dir = self.settings_manager.app_dir
        
        return {
            'app_directory_writable': os.access(app_dir, os.W_OK),
            'temp_directory_writable': os.access(self.settings_manager.temp_dir, os.W_OK),
            'can_create_files': self._test_file_creation(),
            'can_execute_scripts': self._test_script_execution()
        }
    
    def _test_file_creation(self) -> bool:
        """Test if we can create files"""
        try:
            test_file = self.settings_manager.temp_dir / 'test_write.txt'
            test_file.write_text('test')
            test_file.unlink()
            return True
        except:
            return False
    
    def _test_script_execution(self) -> bool:
        """Test if we can execute scripts"""
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _check_network_connectivity(self) -> Dict[str, any]:
        """Check network connectivity"""
        import socket
        
        def check_host(host: str, port: int, timeout: int = 3) -> bool:
            try:
                socket.setdefaulttimeout(timeout)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                return True
            except:
                return False
        
        return {
            'internet': check_host('8.8.8.8', 53),
            'github': check_host('github.com', 443),
            'npm_registry': check_host('registry.npmjs.org', 443),
            'ollama_local': check_host('localhost', 11434)
        }
    
    def _check_system_resources(self) -> Dict[str, any]:
        """Check system resources"""
        try:
            import psutil
            
            return {
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_free': psutil.disk_usage('/').free,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _determine_bootstrap_status(self) -> Dict[str, any]:
        """Determine if system is properly bootstrapped"""
        # This will be populated by get_complete_system_state
        return {
            'is_ready': False,
            'missing_components': [],
            'recommendations': []
        }
    
    def quick_health_check(self) -> Dict[str, bool]:
        """Quick health check for common issues"""
        return {
            'python_ok': sys.version_info >= (3, 8),
            'dependencies_ok': self._check_dependencies()['all_installed'],
            'database_ok': self._check_database()['initialized'],
            'permissions_ok': self._check_permissions()['app_directory_writable'],
            'network_ok': self._check_network_connectivity()['internet']
        }
    
    def get_installation_recommendations(self, state: Dict[str, any]) -> List[str]:
        """Get recommendations based on current state"""
        recommendations = []
        
        # Python version
        if not state['python_environment'].get('version_compatible', False):
            recommendations.append("Upgrade Python to version 3.8 or higher")
        
        # Dependencies
        missing_deps = state['dependencies'].get('missing', [])
        if missing_deps:
            recommendations.append(f"Install missing dependencies: {', '.join(missing_deps)}")
        
        # System tools
        missing_tools = state['system_tools']['summary'].get('missing_required', [])
        if missing_tools:
            if 'node' in missing_tools or 'npm' in missing_tools:
                recommendations.append("Install Node.js and npm for Claude Code support")
        
        # AI providers
        if not state['ai_providers']['claude_code']['installed']:
            recommendations.append("Set up Claude Code environment")
        
        if not state['ai_providers']['ollama']['available']:
            recommendations.append("Consider installing Ollama for local AI support")
        
        # Database
        if not state['database']['initialized']:
            recommendations.append("Initialize database")
        
        # Network
        if not state['network']['internet']:
            recommendations.append("Check internet connection for cloud features")
        
        return recommendations