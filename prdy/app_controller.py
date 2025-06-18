"""
Application Controller for PRD Generator
Orchestrates the entire application lifecycle
"""

import sys
import os
import signal
import atexit
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import subprocess
import json

from .utils.settings_manager import SettingsManager
from .utils.state_detector import StateDetector
from .utils.logger import get_logger
from .utils.environment_manager import EnvironmentManager
from .utils.ai_integration import AIIntegration
from .models.database import init_database

logger = get_logger("app_controller")


class ApplicationController:
    """Main application controller"""
    
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.state_detector = StateDetector(self.settings_manager)
        self.env_manager = EnvironmentManager()
        self.ai_integration = AIIntegration()
        
        # Application state
        self.is_running = False
        self.cleanup_registered = False
        self.background_tasks = []
        self.process_registry = {}
        
        # Performance monitoring
        self.start_time = time.time()
        self.performance_metrics = {}
        
        logger.info("Application controller initialized")
    
    def start_application(self, mode: str = "gui") -> bool:
        """Start the application in specified mode"""
        logger.info(f"Starting PRD Generator in {mode} mode")
        
        try:
            # Register cleanup
            if not self.cleanup_registered:
                self._register_cleanup_handlers()
            
            # Pre-flight checks
            if not self._pre_flight_checks():
                logger.error("Pre-flight checks failed")
                return False
            
            # Initialize core systems
            if not self._initialize_core_systems():
                logger.error("Core system initialization failed")
                return False
            
            # Check and handle bootstrap if needed
            bootstrap_status = self._check_bootstrap_status()
            if not bootstrap_status['is_ready']:
                if self.settings_manager.settings.auto_bootstrap:
                    logger.info("Auto-bootstrapping system")
                    if not self._auto_bootstrap():
                        logger.error("Auto-bootstrap failed")
                        return False
                else:
                    logger.warning("System not bootstrapped, manual setup required")
            
            # Start the appropriate interface
            self.is_running = True
            
            if mode == "gui":
                return self._start_gui()
            elif mode == "cli":
                return self._start_cli()
            else:
                logger.error(f"Unknown mode: {mode}")
                return False
                
        except Exception as e:
            logger.error("Failed to start application", exception=e)
            self._emergency_cleanup()
            return False
    
    def _pre_flight_checks(self) -> bool:
        """Perform pre-flight system checks"""
        logger.debug("Performing pre-flight checks")
        
        checks = {
            'python_version': sys.version_info >= (3, 8),
            'permissions': self._check_permissions(),
            'disk_space': self._check_disk_space(),
            'memory': self._check_memory(),
        }
        
        failed_checks = [name for name, result in checks.items() if not result]
        
        if failed_checks:
            logger.error(f"Pre-flight checks failed: {failed_checks}")
            return False
        
        logger.debug("Pre-flight checks passed")
        return True
    
    def _check_permissions(self) -> bool:
        """Check if we have necessary permissions"""
        try:
            app_dir = self.settings_manager.app_dir
            
            # Test write access
            test_file = app_dir / 'permission_test.tmp'
            test_file.write_text('test')
            test_file.unlink()
            
            return True
        except Exception:
            return False
    
    def _check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            import shutil
            free_bytes = shutil.disk_usage(self.settings_manager.app_dir).free
            required_bytes = 100 * 1024 * 1024  # 100 MB minimum
            return free_bytes > required_bytes
        except Exception:
            return True  # Assume OK if we can't check
    
    def _check_memory(self) -> bool:
        """Check available memory"""
        try:
            import psutil
            available_mb = psutil.virtual_memory().available / (1024 * 1024)
            return available_mb > 256  # 256 MB minimum
        except ImportError:
            return True  # Assume OK if psutil not available
        except Exception:
            return True
    
    def _initialize_core_systems(self) -> bool:
        """Initialize core application systems"""
        logger.debug("Initializing core systems")
        
        try:
            # Initialize database
            db_url = self.settings_manager.get_database_url()
            init_database(db_url)
            logger.debug("Database initialized")
            
            # Set up logging level
            from .utils.logger import logger as main_logger
            main_logger.set_level(self.settings_manager.settings.log_level)
            
            # Initialize AI integration if configured
            ai_provider = self.settings_manager.settings.ai_provider
            if ai_provider != "none":
                try:
                    if ai_provider == "claude-code":
                        self.ai_integration.setup_ai_provider(AIIntegration.AIProvider.CLAUDE_CODE, auto_install=False)
                    elif ai_provider == "ollama":
                        self.ai_integration.setup_ai_provider(AIIntegration.AIProvider.OLLAMA, auto_install=False)
                except Exception as e:
                    logger.warning(f"AI provider setup failed: {e}")
            
            # Start background tasks
            self._start_background_tasks()
            
            logger.debug("Core systems initialized")
            return True
            
        except Exception as e:
            logger.error("Core system initialization failed", exception=e)
            return False
    
    def _check_bootstrap_status(self) -> Dict[str, Any]:
        """Check if system is properly bootstrapped"""
        logger.debug("Checking bootstrap status")
        
        try:
            system_state = self.state_detector.get_complete_system_state()
            bootstrap_status = system_state.get('bootstrap_status', {})
            
            # Determine if system is ready
            is_ready = all([
                system_state.get('dependencies', {}).get('all_installed', False),
                system_state.get('database', {}).get('initialized', False),
                system_state.get('permissions', {}).get('app_directory_writable', False)
            ])
            
            missing_components = []
            recommendations = []
            
            if not system_state.get('dependencies', {}).get('all_installed', False):
                missing_components.append('dependencies')
                recommendations.append('Install missing Python dependencies')
            
            if not system_state.get('database', {}).get('initialized', False):
                missing_components.append('database')
                recommendations.append('Initialize application database')
            
            ai_status = system_state.get('ai_providers', {})
            if not ai_status.get('claude_code', {}).get('installed', False) and not ai_status.get('ollama', {}).get('available', False):
                missing_components.append('ai_providers')
                recommendations.append('Set up at least one AI provider')
            
            return {
                'is_ready': is_ready,
                'missing_components': missing_components,
                'recommendations': recommendations,
                'system_state': system_state
            }
            
        except Exception as e:
            logger.error("Bootstrap status check failed", exception=e)
            return {
                'is_ready': False,
                'missing_components': ['unknown'],
                'recommendations': ['Manual system check required'],
                'error': str(e)
            }
    
    def _auto_bootstrap(self) -> bool:
        """Automatically bootstrap the system"""
        logger.info("Starting auto-bootstrap process")
        
        try:
            # Check what needs to be done
            bootstrap_status = self._check_bootstrap_status()
            missing = bootstrap_status.get('missing_components', [])
            
            # Install dependencies if needed
            if 'dependencies' in missing:
                logger.info("Installing dependencies")
                if not self._install_dependencies():
                    return False
            
            # Initialize database if needed
            if 'database' in missing:
                logger.info("Initializing database")
                if not self._initialize_database():
                    return False
            
            # Set up AI providers if needed
            if 'ai_providers' in missing:
                logger.info("Setting up AI providers")
                self._setup_ai_providers()  # Non-blocking
            
            # Update bootstrap status
            final_status = self._check_bootstrap_status()
            if final_status['is_ready']:
                logger.info("Auto-bootstrap completed successfully")
                return True
            else:
                logger.warning("Auto-bootstrap completed with issues")
                return False
                
        except Exception as e:
            logger.error("Auto-bootstrap failed", exception=e)
            return False
    
    def _install_dependencies(self) -> bool:
        """Install missing dependencies"""
        try:
            deps_check = self.state_detector._check_dependencies()
            missing = deps_check.get('missing', [])
            
            if not missing:
                return True
            
            # Try to install using pip
            import subprocess
            
            cmd = [sys.executable, '-m', 'pip', 'install'] + missing
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Successfully installed dependencies: {missing}")
                return True
            else:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error("Dependency installation failed", exception=e)
            return False
    
    def _initialize_database(self) -> bool:
        """Initialize the database"""
        try:
            db_url = self.settings_manager.get_database_url()
            init_database(db_url)
            
            # Test database connection
            from .models.database import get_db_sync
            from .models.prd import PRDSession
            
            db = get_db_sync()
            try:
                db.query(PRDSession).count()
                logger.info("Database initialized and tested successfully")
                return True
            except Exception as e:
                logger.error("Database test failed", exception=e)
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error("Database initialization failed", exception=e)
            return False
    
    def _setup_ai_providers(self):
        """Set up AI providers (non-blocking)"""
        def setup_async():
            try:
                # Check system capabilities
                tools = self.state_detector._check_system_tools()
                
                # Try Claude Code if Node.js available
                if tools.get('node', {}).get('available', False) and tools.get('npm', {}).get('available', False):
                    logger.info("Setting up Claude Code environment")
                    try:
                        self.ai_integration.setup_ai_provider(AIIntegration.AIProvider.CLAUDE_CODE)
                        self.settings_manager.update_setting('ai_provider', 'claude-code')
                    except Exception as e:
                        logger.warning(f"Claude Code setup failed: {e}")
                
                # Try Ollama if available
                if tools.get('ollama', {}).get('available', False):
                    logger.info("Setting up Ollama environment")
                    try:
                        self.ai_integration.setup_ai_provider(AIIntegration.AIProvider.OLLAMA)
                        if self.settings_manager.settings.ai_provider == 'none':
                            self.settings_manager.update_setting('ai_provider', 'ollama')
                    except Exception as e:
                        logger.warning(f"Ollama setup failed: {e}")
                        
            except Exception as e:
                logger.error("AI provider setup failed", exception=e)
        
        # Run in background thread
        thread = threading.Thread(target=setup_async, daemon=True)
        thread.start()
        self.background_tasks.append(thread)
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        
        def maintenance_task():
            """Periodic maintenance"""
            while self.is_running:
                try:
                    # Clean up temp files every hour
                    self.settings_manager.cleanup_temp_files()
                    
                    # Update performance metrics
                    self._update_performance_metrics()
                    
                    # Sleep for 1 hour
                    time.sleep(3600)
                    
                except Exception as e:
                    logger.error("Maintenance task error", exception=e)
        
        def auto_save_task():
            """Auto-save user data"""
            while self.is_running:
                try:
                    # Auto-save interval from settings
                    interval = self.settings_manager.settings.auto_save_interval
                    time.sleep(interval)
                    
                    # Trigger auto-save for active sessions
                    # This would save any unsaved PRD work
                    
                except Exception as e:
                    logger.error("Auto-save task error", exception=e)
        
        # Start background threads
        maintenance_thread = threading.Thread(target=maintenance_task, daemon=True)
        auto_save_thread = threading.Thread(target=auto_save_task, daemon=True)
        
        maintenance_thread.start()
        auto_save_thread.start()
        
        self.background_tasks.extend([maintenance_thread, auto_save_thread])
    
    def _start_gui(self) -> bool:
        """Start the GUI interface"""
        try:
            from .gui import PRDGeneratorGUI
            
            logger.info("Starting GUI interface")
            gui_app = PRDGeneratorGUI()
            gui_app.run()
            
            return True
            
        except Exception as e:
            logger.error("GUI startup failed", exception=e)
            return False
    
    def _start_cli(self) -> bool:
        """Start the CLI interface"""
        try:
            from .cli import main as cli_main
            
            logger.info("Starting CLI interface")
            cli_main()
            
            return True
            
        except Exception as e:
            logger.error("CLI startup failed", exception=e)
            return False
    
    def _register_cleanup_handlers(self):
        """Register cleanup handlers for graceful shutdown"""
        def cleanup_handler(signum=None, frame=None):
            logger.info("Cleanup signal received")
            self._graceful_shutdown()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, cleanup_handler)
        signal.signal(signal.SIGINT, cleanup_handler)
        
        # Register atexit handler
        atexit.register(self._graceful_shutdown)
        
        self.cleanup_registered = True
        logger.debug("Cleanup handlers registered")
    
    def _graceful_shutdown(self):
        """Perform graceful shutdown"""
        if not self.is_running:
            return
        
        logger.info("Starting graceful shutdown")
        self.is_running = False
        
        try:
            # Save current window size if GUI
            if hasattr(self, 'page') and self.page:
                self.settings_manager.update_setting('window_width', self.page.window_width)
                self.settings_manager.update_setting('window_height', self.page.window_height)
            
            # Stop background tasks
            for task in self.background_tasks:
                if task.is_alive():
                    # Tasks are daemon threads, they'll stop when main thread stops
                    pass
            
            # Clean up temporary files
            self.settings_manager.cleanup_temp_files()
            
            # Terminate any spawned processes
            self._cleanup_processes()
            
            # Save performance metrics
            self._save_performance_metrics()
            
            logger.info("Graceful shutdown completed")
            
        except Exception as e:
            logger.error("Error during graceful shutdown", exception=e)
    
    def _emergency_cleanup(self):
        """Emergency cleanup for unexpected failures"""
        logger.critical("Performing emergency cleanup")
        
        try:
            self.is_running = False
            self._cleanup_processes()
            self.settings_manager.cleanup_temp_files()
        except Exception as e:
            logger.critical("Emergency cleanup failed", exception=e)
    
    def _cleanup_processes(self):
        """Clean up spawned processes"""
        for process_id, process in self.process_registry.items():
            try:
                if process.poll() is None:  # Process still running
                    process.terminate()
                    process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.warning(f"Failed to cleanup process {process_id}: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            import psutil
            
            self.performance_metrics.update({
                'uptime': time.time() - self.start_time,
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent(),
                'active_sessions': len(self.background_tasks),
                'timestamp': time.time()
            })
            
        except ImportError:
            # psutil not available
            self.performance_metrics.update({
                'uptime': time.time() - self.start_time,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.warning(f"Performance metrics update failed: {e}")
    
    def _save_performance_metrics(self):
        """Save performance metrics"""
        try:
            metrics_file = self.settings_manager.logs_dir / 'performance.json'
            with open(metrics_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save performance metrics: {e}")
    
    def get_application_info(self) -> Dict[str, Any]:
        """Get comprehensive application information"""
        return {
            'version': '0.1.0',
            'is_running': self.is_running,
            'uptime': time.time() - self.start_time,
            'settings': self.settings_manager.get_app_info(),
            'performance': self.performance_metrics,
            'background_tasks': len(self.background_tasks),
            'process_registry': list(self.process_registry.keys())
        }