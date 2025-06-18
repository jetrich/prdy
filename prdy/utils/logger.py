"""
Comprehensive logging system for PRD Generator
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import traceback


class PRDLogger:
    """Enhanced logger for PRD Generator"""
    
    def __init__(self, name: str = "prd_generator", log_dir: Optional[Path] = None):
        self.name = name
        self.log_dir = log_dir or Path.home() / ".prd-generator" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up logging handlers"""
        
        # File handler for all logs
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Rotating file handler for errors
        error_file = self.log_dir / f"{self.name}_errors.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", **kwargs)
            self.logger.debug(traceback.format_exc())
        else:
            self.logger.error(message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        if exception:
            self.logger.critical(f"{message}: {str(exception)}", **kwargs)
            self.logger.debug(traceback.format_exc())
        else:
            self.logger.critical(message, **kwargs)
    
    def log_operation(self, operation: str, status: str, details: str = ""):
        """Log an operation with standardized format"""
        message = f"Operation: {operation} | Status: {status}"
        if details:
            message += f" | Details: {details}"
        
        if status.lower() in ['success', 'completed']:
            self.info(message)
        elif status.lower() in ['failed', 'error']:
            self.error(message)
        else:
            self.info(message)
    
    def log_user_action(self, action: str, details: str = ""):
        """Log user actions for analytics"""
        message = f"User Action: {action}"
        if details:
            message += f" | {details}"
        self.info(message)
    
    def log_performance(self, operation: str, duration: float, details: str = ""):
        """Log performance metrics"""
        message = f"Performance: {operation} took {duration:.2f}s"
        if details:
            message += f" | {details}"
        self.debug(message)
    
    def set_level(self, level: str):
        """Set logging level"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            # Also update console handler
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                    handler.setLevel(level_map[level.upper()])


# Global logger instance
logger = PRDLogger()


def get_logger(name: str = "prd_generator") -> PRDLogger:
    """Get logger instance"""
    return PRDLogger(name)