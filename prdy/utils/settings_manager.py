"""
Settings Manager for PRD Generator
Handles persistent user settings and application configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class UserSettings:
    """User preference settings"""
    ai_provider: str = "none"
    default_export_format: str = "markdown"
    auto_bootstrap: bool = True
    theme: str = "light"
    language: str = "en"
    export_directory: str = "./exports"
    database_url: str = "sqlite:///./prd_generator.db"
    
    # AI Provider specific settings
    claude_code_auto_install: bool = True
    ollama_auto_start: bool = False
    ollama_model: str = "llama2"
    
    # Interface settings
    window_width: int = 1200
    window_height: int = 800
    remember_window_size: bool = True
    show_tooltips: bool = True
    auto_save_interval: int = 300  # seconds
    
    # Advanced settings
    max_concurrent_sessions: int = 5
    log_level: str = "INFO"
    enable_telemetry: bool = False
    check_updates: bool = True
    
    # Internal tracking
    first_run: bool = True
    last_version: str = "0.1.0"
    installation_date: Optional[str] = None
    last_bootstrap_check: Optional[str] = None


@dataclass
class AppState:
    """Application state tracking"""
    is_bootstrapped: bool = False
    claude_code_installed: bool = False
    ollama_available: bool = False
    database_initialized: bool = False
    last_state_check: Optional[str] = None
    
    # Environment status
    environments: Dict[str, Dict[str, Any]] = None
    active_sessions: int = 0
    
    # Error tracking
    last_error: Optional[str] = None
    error_count: int = 0
    
    def __post_init__(self):
        if self.environments is None:
            self.environments = {}


class SettingsManager:
    """Manages application settings and state persistence"""
    
    def __init__(self, app_name: str = "prd-generator"):
        self.app_name = app_name
        self._setup_directories()
        self.settings = self._load_settings()
        self.state = self._load_state()
        
    def _setup_directories(self):
        """Set up application directories"""
        # Cross-platform app data directory
        if os.name == 'nt':  # Windows
            self.app_dir = Path(os.environ.get('APPDATA', '~')) / self.app_name
        elif os.name == 'posix':  # macOS/Linux
            if os.uname().sysname == 'Darwin':  # macOS
                self.app_dir = Path.home() / 'Library' / 'Application Support' / self.app_name
            else:  # Linux
                self.app_dir = Path.home() / f'.{self.app_name}'
        else:
            self.app_dir = Path.home() / f'.{self.app_name}'
        
        # Create directories
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir = self.app_dir / 'config'
        self.logs_dir = self.app_dir / 'logs'
        self.cache_dir = self.app_dir / 'cache'
        self.temp_dir = self.app_dir / 'temp'
        
        for directory in [self.config_dir, self.logs_dir, self.cache_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)
        
        # File paths
        self.settings_file = self.config_dir / 'settings.json'
        self.state_file = self.config_dir / 'state.json'
    
    def _load_settings(self) -> UserSettings:
        """Load user settings from file"""
        if not self.settings_file.exists():
            settings = UserSettings()
            # Set installation date on first run
            settings.installation_date = datetime.now().isoformat()
            self._save_settings(settings)
            return settings
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle version migrations if needed
            data = self._migrate_settings(data)
            
            return UserSettings(**data)
            
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # If settings are corrupted, create backup and use defaults
            if self.settings_file.exists():
                backup_file = self.settings_file.with_suffix('.json.backup')
                self.settings_file.rename(backup_file)
            
            settings = UserSettings()
            self._save_settings(settings)
            return settings
    
    def _load_state(self) -> AppState:
        """Load application state from file"""
        if not self.state_file.exists():
            return AppState()
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AppState(**data)
            
        except (json.JSONDecodeError, TypeError, ValueError):
            return AppState()
    
    def _migrate_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate settings from older versions"""
        # Example migration logic
        if 'version' not in data:
            data['last_version'] = '0.1.0'
        
        # Add any new settings with defaults
        default_settings = asdict(UserSettings())
        for key, value in default_settings.items():
            if key not in data:
                data[key] = value
        
        return data
    
    def _save_settings(self, settings: UserSettings = None):
        """Save settings to file"""
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(settings), f, indent=2)
        except Exception as e:
            # Log error but don't crash
            print(f"Warning: Could not save settings: {e}")
    
    def _save_state(self, state: AppState = None):
        """Save state to file"""
        if state is None:
            state = self.state
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(state), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def update_setting(self, key: str, value: Any):
        """Update a specific setting"""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self._save_settings()
        else:
            raise ValueError(f"Unknown setting: {key}")
    
    def update_state(self, key: str, value: Any):
        """Update application state"""
        if hasattr(self.state, key):
            setattr(self.state, key, value)
            self.state.last_state_check = datetime.now().isoformat()
            self._save_state()
        else:
            raise ValueError(f"Unknown state: {key}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return getattr(self.settings, key, default)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value"""
        return getattr(self.state, key, default)
    
    def mark_first_run_complete(self):
        """Mark that first run setup is complete"""
        self.settings.first_run = False
        self._save_settings()
    
    def record_error(self, error_message: str):
        """Record an error for tracking"""
        self.state.last_error = error_message
        self.state.error_count += 1
        self._save_state()
    
    def clear_errors(self):
        """Clear error tracking"""
        self.state.last_error = None
        self.state.error_count = 0
        self._save_state()
    
    def update_bootstrap_status(self, status: Dict[str, bool]):
        """Update bootstrap status"""
        self.state.is_bootstrapped = all([
            status.get('dependencies_installed', False),
            status.get('database_initialized', False),
        ])
        self.state.claude_code_installed = status.get('claude_code_installed', False)
        self.state.ollama_available = status.get('ollama_available', False)
        self.state.database_initialized = status.get('database_initialized', False)
        self.state.last_bootstrap_check = datetime.now().isoformat()
        self._save_state()
    
    def get_export_directory(self) -> Path:
        """Get resolved export directory path"""
        export_dir = Path(self.settings.export_directory)
        if not export_dir.is_absolute():
            export_dir = self.app_dir / export_dir
        
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir
    
    def get_database_url(self) -> str:
        """Get resolved database URL"""
        db_url = self.settings.database_url
        if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
            # Relative SQLite path
            db_path = db_url[10:]  # Remove 'sqlite:///'
            if not Path(db_path).is_absolute():
                db_path = str(self.app_dir / db_path)
            db_url = f'sqlite:///{db_path}'
        
        return db_url
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not clean temp files: {e}")
    
    def export_settings(self, file_path: str):
        """Export settings to a file for backup"""
        export_data = {
            'settings': asdict(self.settings),
            'export_date': datetime.now().isoformat(),
            'version': '0.1.0'
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
    
    def import_settings(self, file_path: str):
        """Import settings from a backup file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'settings' in data:
            imported_settings = UserSettings(**data['settings'])
            # Preserve some current values
            imported_settings.installation_date = self.settings.installation_date
            imported_settings.last_bootstrap_check = self.settings.last_bootstrap_check
            
            self.settings = imported_settings
            self._save_settings()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        # Preserve some values
        installation_date = self.settings.installation_date
        
        self.settings = UserSettings()
        self.settings.installation_date = installation_date
        self._save_settings()
        
        # Also reset state
        self.state = AppState()
        self._save_state()
    
    def get_app_info(self) -> Dict[str, Any]:
        """Get application information"""
        return {
            'app_directory': str(self.app_dir),
            'settings_file': str(self.settings_file),
            'state_file': str(self.state_file),
            'logs_directory': str(self.logs_dir),
            'cache_directory': str(self.cache_dir),
            'temp_directory': str(self.temp_dir),
            'export_directory': str(self.get_export_directory()),
            'database_url': self.get_database_url(),
            'first_run': self.settings.first_run,
            'installation_date': self.settings.installation_date,
            'last_version': self.settings.last_version,
            'is_bootstrapped': self.state.is_bootstrapped
        }