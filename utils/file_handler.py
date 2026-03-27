"""
File handling utilities for Media Transcriber.
"""

import os
from pathlib import Path
from typing import List, Optional


# Supported media formats
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.opus'}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


def is_video_file(filename: str) -> bool:
    """
    Check if a file has a supported video extension.
    
    Args:
        filename: Name or path of the file
        
    Returns:
        True if file has a video extension, False otherwise
    """
    return Path(filename).suffix.lower() in VIDEO_EXTENSIONS


def is_audio_file(filename: str) -> bool:
    """
    Check if a file has a supported audio extension.

    Args:
        filename: Name or path of the file

    Returns:
        True if file has a supported audio extension, False otherwise
    """
    return Path(filename).suffix.lower() in AUDIO_EXTENSIONS


def is_media_file(filename: str) -> bool:
    """
    Check if a file has a supported media extension.

    Args:
        filename: Name or path of the file

    Returns:
        True if file has a supported video or audio extension, False otherwise
    """
    return Path(filename).suffix.lower() in MEDIA_EXTENSIONS


def validate_file(file_path: str) -> bool:
    """
    Validate that a file exists and is accessible.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file exists and is readable
    """
    path = Path(file_path)
    return path.exists() and path.is_file() and os.access(path, os.R_OK)


def ensure_dir(dir_path: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        dir_path: Path to the directory
    """
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def _get_files_by_extensions(folder_path: str, extensions: set[str]) -> List[str]:
    """
    Get all files matching the provided extensions from a folder.
    
    Args:
        folder_path: Path to the folder
        extensions: Allowed file extensions
        
    Returns:
        List of matching file paths
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return []
    
    files = []
    for ext in extensions:
        # Case-insensitive search
        files.extend([str(f) for f in folder.glob(f'*{ext}')])
        files.extend([str(f) for f in folder.glob(f'*{ext.upper()}')])
    
    # Remove duplicates and sort
    return sorted(list(set(files)))


def get_video_files(folder_path: str) -> List[str]:
    """
    Get all supported video files from a folder.

    Args:
        folder_path: Path to the folder

    Returns:
        List of absolute paths to video files
    """
    return _get_files_by_extensions(folder_path, VIDEO_EXTENSIONS)


def get_media_files(folder_path: str) -> List[str]:
    """
    Get all supported media files from a folder.

    Args:
        folder_path: Path to the folder

    Returns:
        List of absolute paths to video and audio files
    """
    return _get_files_by_extensions(folder_path, MEDIA_EXTENSIONS)


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    size_bytes = Path(file_path).stat().st_size
    return size_bytes / (1024 * 1024)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    return sanitized.strip()
