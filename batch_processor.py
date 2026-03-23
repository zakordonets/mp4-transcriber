"""
Batch processing module for handling multiple video files.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

from transcriber import VideoTranscriber
from utils.logger import setup_logger
from utils.file_handler import get_video_files, validate_file


logger = setup_logger("BatchProcessor")


class BatchProcessor:
    """
    Batch processor for transcribing multiple video files.
    
    Processes files sequentially with progress tracking and error handling.
    When a file fails, it skips to the next one (skip-on-error strategy).
    
    Attributes:
        transcriber: VideoTranscriber instance to use
        max_workers: Maximum workers (kept for compatibility, processes sequentially)
    """
    
    def __init__(self, transcriber: VideoTranscriber, max_workers: int = 2):
        """
        Initialize the BatchProcessor.
        
        Args:
            transcriber: Configured VideoTranscriber instance
            max_workers: Number of workers (currently sequential processing only)
        """
        self.transcriber = transcriber
        self.max_workers = max_workers
        
        # Progress tracking
        self.current_file = 0
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        
        logger.info(f"BatchProcessor initialized (max_workers={max_workers}, sequential mode)")
    
    def process_folder(
        self,
        folder_path: str,
        output_formats: Optional[List[str]] = None,
        recursive: bool = False,
        diarize: bool = False,
        diarization_backend: str = "pyannote",
        diarization_permissive: bool = True,
    ) -> Dict:
        """
        Process all video files in a folder.
        
        Args:
            folder_path: Path to folder containing video files
            output_formats: List of formats to export
            recursive: Whether to search subdirectories
            
        Returns:
            Dictionary with processing statistics
        """
        # Get all video files from folder
        video_files = get_video_files(folder_path)
        
        if not video_files:
            logger.warning(f"No video files found in: {folder_path}")
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'files': []
            }
        
        logger.info(f"Found {len(video_files)} video files in {folder_path}")
        
        return self.process_files(
            video_files,
            output_formats=output_formats,
            diarize=diarize,
            diarization_backend=diarization_backend,
            diarization_permissive=diarization_permissive,
        )
    
    def process_files(
        self,
        file_list: List[str],
        output_formats: Optional[List[str]] = None,
        diarize: bool = False,
        diarization_backend: str = "pyannote",
        diarization_permissive: bool = True,
    ) -> Dict:
        """
        Process a list of video files.
        
        Args:
            file_list: List of video file paths
            output_formats: List of formats to export
            
        Returns:
            Dictionary with processing statistics
        """
        if not file_list:
            logger.warning("No files to process")
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'files': []
            }
        
        # Reset counters
        self.total_files = len(file_list)
        self.current_file = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        
        results = {
            'total': self.total_files,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'files': []
        }
        
        logger.info(f"Starting batch processing of {self.total_files} files")
        
        # Process files sequentially with progress bar
        for file_path in tqdm(file_list, desc="Processing videos", unit="file"):
            self.current_file += 1
            
            try:
                # Validate file
                if not validate_file(file_path):
                    logger.warning(f"File not found or not accessible: {file_path}")
                    self.skipped += 1
                    results['files'].append({
                        'path': file_path,
                        'status': 'skipped',
                        'error': 'File not accessible'
                    })
                    continue
                
                # Transcribe file
                logger.info(f"[{self.current_file}/{self.total_files}] Processing: {Path(file_path).name}")
                
                result = self.transcriber.transcribe(
                    file_path,
                    output_formats=output_formats,
                    save_outputs=True,
                    diarize=diarize,
                    diarization_backend=diarization_backend,
                    diarization_permissive=diarization_permissive,
                )
                
                self.successful += 1
                results['files'].append({
                    'path': file_path,
                    'status': 'success',
                    'language': result.get('language', 'unknown'),
                    'segments': len(result.get('segments', [])),
                    'text_length': len(result.get('text', ''))
                })
                
                logger.info(f"✓ Successfully processed: {Path(file_path).name}")
                
            except KeyboardInterrupt:
                logger.warning("Batch processing interrupted by user")
                raise
            except Exception as e:
                self.failed += 1
                results['files'].append({
                    'path': file_path,
                    'status': 'failed',
                    'error': str(e)
                })
                
                # Skip on error strategy - continue with next file
                logger.error(f"✗ Failed to process {Path(file_path).name}: {e}")
                logger.info("Continuing with next file...")
        
        # Update final counts
        results['successful'] = self.successful
        results['failed'] = self.failed
        results['skipped'] = self.skipped
        
        # Log summary
        logger.info("=" * 60)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info(f"Total files:     {self.total_files}")
        logger.info(f"Successful:      {self.successful}")
        logger.info(f"Failed:          {self.failed}")
        logger.info(f"Skipped:         {self.skipped}")
        logger.info("=" * 60)
        
        return results
    
    def get_progress(self) -> Dict:
        """
        Get current processing progress.
        
        Returns:
            Dictionary with progress information:
                - current: Current file number
                - total: Total files
                - percentage: Progress percentage
                - successful: Count of successful files
                - failed: Count of failed files
        """
        percentage = (self.current_file / self.total_files * 100) if self.total_files > 0 else 0
        
        return {
            'current': self.current_file,
            'total': self.total_files,
            'percentage': round(percentage, 2),
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped
        }
    
    def reset(self) -> None:
        """Reset all progress counters."""
        self.current_file = 0
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        logger.debug("BatchProcessor progress reset")
