"""Logging configuration for Voice Assistant.

Sets up structured logging with appropriate levels and formatters.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from config import Config


class LoggerSetup:
    """Manages logging configuration for the application."""
    
    _initialized = False
    
    @staticmethod
    def setup(log_file: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
        """Setup logging for the application.
        
        Args:
            log_file: Path to log file (uses config if not provided)
            level: Logging level (uses config if not provided)
            
        Returns:
            Configured root logger
        """
        if LoggerSetup._initialized:
            return logging.getLogger()
        
        config = Config()
        log_config = config.logging_config
        
        # Use provided values or fall back to config
        log_file = log_file or log_config.get('file', 'voice_assistant.log')
        level = level or log_config.get('level', 'INFO')
        format_string = log_config.get(
            'format',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create logs directory if needed
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Create formatters
        formatter = logging.Formatter(format_string)
        
        # File handler (all levels)
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10_485_760,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)-8s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        LoggerSetup._initialized = True
        root_logger.info(f"Logging initialized - Level: {level}, File: {log_file}")
        
        return root_logger
    
    @staticmethod
    def reset() -> None:
        """Reset logging configuration."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        
        LoggerSetup._initialized = False
