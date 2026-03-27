"""
Configuration management for Media Transcriber.
Loads settings from environment variables and provides defaults.
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


# Available Whisper models
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]

# Supported media formats
VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
AUDIO_FORMATS = [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus"]
MEDIA_FORMATS = VIDEO_FORMATS + AUDIO_FORMATS

# Supported output formats
OUTPUT_FORMATS = ["txt", "srt", "vtt", "json"]

# Default configuration values
DEFAULT_MODEL = "base"
DEFAULT_LANGUAGE = "ru"
DEFAULT_DEVICE = "cpu"
DEFAULT_OUTPUT_DIR = "./transcripts"
DEFAULT_WORKERS = 2
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DIARIZATION_BACKEND = "pyannote"


class Config:
    """
    Configuration manager for the transcriber application.
    
    Loads settings from environment variables with fallback to defaults.
    """
    
    def __init__(self):
        """Initialize configuration from environment or defaults."""
        self.whisper_model = os.getenv('WHISPER_MODEL', DEFAULT_MODEL)
        self.language = os.getenv('LANGUAGE', DEFAULT_LANGUAGE)
        self.device = os.getenv('DEVICE', DEFAULT_DEVICE)
        self.output_dir = os.getenv('OUTPUT_DIR', DEFAULT_OUTPUT_DIR)
        self.max_workers = int(os.getenv('MAX_WORKERS', str(DEFAULT_WORKERS)))
        self.log_level = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL)
        self.diarization_backend = os.getenv(
            'DIARIZATION_BACKEND', DEFAULT_DIARIZATION_BACKEND
        )
        
        # Validate configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration values."""
        if self.whisper_model not in WHISPER_MODELS:
            raise ValueError(
                f"Invalid Whisper model: {self.whisper_model}. "
                f"Must be one of: {WHISPER_MODELS}"
            )
        
        if self.device not in ['cpu']:  # Only CPU supported in this version
            raise ValueError(
                f"Unsupported device: {self.device}. Only 'cpu' is supported."
            )
        
        if self.max_workers < 1:
            raise ValueError(f"MAX_WORKERS must be at least 1, got {self.max_workers}")
        
        if not self.log_level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid log level: {self.log_level}")
    
    def get_model_name(self) -> str:
        """Get full Whisper model name."""
        return f"whisper-{self.whisper_model}"
    
    def get_output_formats(self) -> List[str]:
        """Get list of output formats to generate."""
        # Can be extended to read from env var
        return OUTPUT_FORMATS
    
    def ensure_output_dir(self) -> str:
        """Ensure output directory exists and return its path."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        return self.output_dir
    
    def __repr__(self) -> str:
        return (
            f"Config(model={self.whisper_model}, language={self.language}, "
            f"device={self.device}, output_dir={self.output_dir})"
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Reload configuration from environment variables.
    
    Returns:
        Refreshed Config instance
    """
    global _config
    _config = Config()
    return _config


# Convenience functions
def get_whisper_model() -> str:
    """Get configured Whisper model name."""
    return get_config().whisper_model


def get_language() -> str:
    """Get configured language code."""
    return get_config().language


def get_device() -> str:
    """Get configured device."""
    return get_config().device


def get_output_dir() -> str:
    """Get configured output directory."""
    return get_config().ensure_output_dir()


def get_max_workers() -> int:
    """Get configured number of workers."""
    return get_config().max_workers


def get_log_level() -> str:
    """Get configured log level."""
    return get_config().log_level
