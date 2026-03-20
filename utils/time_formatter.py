"""
Time formatting utilities for subtitle formats (SRT, VTT).
"""

from typing import Union


def format_time_srt(seconds: Union[int, float]) -> str:
    """
    Convert seconds to SRT timestamp format (HH:MM:SS,mmm).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string for SRT files
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def format_time_vtt(seconds: Union[int, float]) -> str:
    """
    Convert seconds to VTT timestamp format (HH:MM:SS.mmm).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string for VTT files
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def format_timestamp_webvtt(seconds: Union[int, float]) -> str:
    """
    Convert seconds to WebVTT timestamp with optional milliseconds.
    Same as format_time_vtt but ensures proper formatting for WebVTT spec.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string compliant with WebVTT specification
    """
    return format_time_vtt(seconds)


def parse_srt_time(time_str: str) -> float:
    """
    Parse SRT timestamp string to seconds.
    
    Args:
        time_str: Timestamp in HH:MM:SS,mmm format
        
    Returns:
        Time in seconds
    """
    # Handle both comma and dot as decimal separator
    time_str = time_str.replace(',', '.')
    
    try:
        parts = time_str.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid time format: {time_str}")
        
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError) as e:
        raise ValueError(f"Failed to parse SRT time '{time_str}': {str(e)}")


def parse_vtt_time(time_str: str) -> float:
    """
    Parse VTT timestamp string to seconds.
    
    Args:
        time_str: Timestamp in HH:MM:SS.mmm format
        
    Returns:
        Time in seconds
    """
    return parse_srt_time(time_str)  # Same parsing logic
