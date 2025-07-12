"""
Logging configuration for LinkedIn automation system.
"""

import logging
import logging.handlers
from datetime import datetime
from config import config

class Logger:
    """Logger class for the LinkedIn automation system."""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Set up logging configuration."""
        log_level = getattr(logging, config.get("logging.level", "INFO"))
        log_file = config.get("logging.file", "linkedin_automation.log")
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create root logger
        self.logger = logging.getLogger("linkedin_automation")
        self.logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Get logger instance."""
        if name:
            return logging.getLogger(f"linkedin_automation.{name}")
        return self.logger
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)

# Global logger instance
logger = Logger()