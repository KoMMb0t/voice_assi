"""Configuration module for Voice Assistant.

This module loads and manages all configuration settings for the voice assistant.
Settings are loaded from config.yaml and provide centralized parameter management.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the voice assistant.
    
    Loads configuration from config.yaml and provides typed access to all settings.
    """
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration by loading from YAML file."""
        if not self._config:
            self._load_config()
    
    @classmethod
    def _load_config(cls) -> None:
        """Load configuration from config.yaml file."""
        config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            logger.warning(f"Config file not found at {config_path}, using defaults")
            cls._config = cls._get_default_config()
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                cls._config = loaded_config if loaded_config else cls._get_default_config()
            logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            cls._config = cls._get_default_config()
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'audio': {
                'sample_rate': 16000,
                'chunk_samples': 1280,
                'device_index': None,
            },
            'wake_word': {
                'model_name': 'hey_jarvis',
                'threshold': 0.5,
                'cooldown_seconds': 4.0,
                'buffer_clear_chunks': 15,
            },
            'speech_recognition': {
                'model_language': 'de',
                'silence_timeout': 2.0,
                'max_record_time': 30,
            },
            'text_to_speech': {
                'voice': 'de-DE-KatjaNeural',
                'engine': 'edge',
            },
            'logging': {
                'level': 'INFO',
                'file': 'voice_assistant.log',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
            'commands': {
                'enable_web_search': True,
                'enable_system_commands': True,
            },
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.
        
        Args:
            key: Configuration key in dot notation (e.g., 'audio.sample_rate')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access to configuration."""
        return self.get(key)
    
    @property
    def audio(self) -> Dict[str, Any]:
        """Get audio configuration."""
        return self._config.get('audio', {})
    
    @property
    def wake_word(self) -> Dict[str, Any]:
        """Get wake word configuration."""
        return self._config.get('wake_word', {})
    
    @property
    def speech_recognition(self) -> Dict[str, Any]:
        """Get speech recognition configuration."""
        return self._config.get('speech_recognition', {})
    
    @property
    def text_to_speech(self) -> Dict[str, Any]:
        """Get text-to-speech configuration."""
        return self._config.get('text_to_speech', {})
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get('logging', {})
    
    @property
    def commands_config(self) -> Dict[str, Any]:
        """Get commands configuration."""
        return self._config.get('commands', {})
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._config.clear()
        self._load_config()
        logger.info("Configuration reloaded")
