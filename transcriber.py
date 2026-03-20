"""
Core transcription module using Whisper ASR.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import whisper
import ffmpeg

from config import WHISPER_MODELS, OUTPUT_FORMATS
from utils.logger import setup_logger
from utils.file_handler import validate_file, ensure_dir
from utils.time_formatter import format_time_srt, format_time_vtt


logger = setup_logger("VideoTranscriber")


class VideoTranscriber:
    """
    Class for transcribing video files using OpenAI Whisper.
    
    Attributes:
        model_name: Name of the Whisper model to use
        language: Language code for transcription
        device: Device for inference ('cpu' only in this version)
        output_dir: Directory to save transcript outputs
    """
    
    def __init__(
        self,
        model_name: str = "base",
        language: str = "ru",
        device: str = "cpu",
        output_dir: str = "./transcripts"
    ):
        """
        Initialize the VideoTranscriber.
        
        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
            language: ISO 639-1 language code (default: 'ru' for Russian)
            device: Device for inference ('cpu' supported)
            output_dir: Directory to save transcripts
        """
        # Validate model name
        if model_name not in WHISPER_MODELS:
            raise ValueError(
                f"Invalid model: {model_name}. Must be one of {WHISPER_MODELS}"
            )
        
        self.model_name = model_name
        self.language = language
        self.device = device
        self.output_dir = output_dir
        
        # Ensure output directory exists
        ensure_dir(output_dir)
        
        # Load Whisper model
        logger.info(f"Loading Whisper model: {model_name}")
        try:
            self.model = whisper.load_model(model_name, device=device)
            logger.info(f"Model loaded successfully: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
        
        logger.info(f"VideoTranscriber initialized with language={language}, device={device}")
    
    def transcribe(
        self,
        video_path: str,
        output_formats: Optional[List[str]] = None,
        save_outputs: bool = True
    ) -> Dict:
        """
        Transcribe a video file.
        
        Args:
            video_path: Path to the video file
            output_formats: List of formats to export (txt, srt, vtt, json)
            save_outputs: Whether to save output files automatically
            
        Returns:
            Dictionary containing:
                - text: Full transcription text
                - segments: List of segments with timestamps
                - language: Detected language
                - audio_path: Path to extracted audio (temporary)
        """
        # Validate input file
        if not validate_file(video_path):
            raise FileNotFoundError(f"Video file not found or not accessible: {video_path}")
        
        logger.info(f"Starting transcription: {Path(video_path).name}")
        
        # Create temporary directory for audio extraction
        temp_dir = tempfile.mkdtemp(prefix="whisper_audio_")
        audio_path = os.path.join(temp_dir, "audio.wav")
        
        try:
            # Extract audio from video
            logger.debug(f"Extracting audio to: {audio_path}")
            self.extract_audio(video_path, audio_path)
            
            # Transcribe audio with Whisper
            logger.info("Running Whisper inference...")
            result = self.model.transcribe(
                audio_path,
                language=self.language if self.language else None,
                task="transcribe",
                verbose=False
            )
            
            logger.info(f"Transcription complete. Detected language: {result.get('language', 'unknown')}")
            
            # Add source file info to result
            result['source_file'] = video_path
            result['model_used'] = self.model_name
            
            # Export to requested formats
            if save_outputs and output_formats:
                base_name = Path(video_path).stem
                for fmt in output_formats:
                    try:
                        output_path = os.path.join(self.output_dir, f"{base_name}.{fmt}")
                        self._export_by_format(result, output_path, fmt)
                        logger.info(f"Exported {fmt.upper()} to: {output_path}")
                    except Exception as e:
                        logger.error(f"Failed to export {fmt}: {e}")
                        raise
            
            return result
            
        except KeyboardInterrupt:
            logger.warning("Transcription interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
        finally:
            # Cleanup temporary audio file
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.debug(f"Cleaned up temporary audio file: {audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up audio file: {e}")
            
            # Try to remove temp directory
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass  # Directory not empty or other issue
    
    def extract_audio(self, video_path: str, audio_path: str) -> None:
        """
        Extract audio stream from video file using ffmpeg.
        
        Args:
            video_path: Path to input video file
            audio_path: Path to save extracted audio (WAV format)
        """
        logger.debug(f"Extracting audio from {Path(video_path).name}")
        
        try:
            # Use ffmpeg to extract audio and convert to WAV
            (
                ffmpeg
                .input(video_path)
                .output(
                    audio_path,
                    acodec='pcm_s16le',  # PCM 16-bit little-endian
                    ar='16000',          # 16kHz sample rate (Whisper requirement)
                    ac=1                 # Mono audio
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.debug(f"Audio extracted successfully: {Path(audio_path).name}")
            
        except ffmpeg.Error as e:
            error_message = f"FFmpeg failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}"
            logger.error(error_message)
            raise RuntimeError(error_message)
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise
    
    def export_txt(self, result: Dict, output_path: str) -> None:
        """
        Export transcription as plain text.
        
        Args:
            result: Transcription result from Whisper
            output_path: Path to save TXT file
        """
        text = result.get('text', '').strip()
        
        ensure_dir(os.path.dirname(output_path))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.debug(f"TXT exported: {output_path}")
    
    def export_srt(self, result: Dict, output_path: str) -> None:
        """
        Export transcription as SRT subtitle file.
        
        Args:
            result: Transcription result from Whisper
            output_path: Path to save SRT file
        """
        segments = result.get('segments', [])
        
        ensure_dir(os.path.dirname(output_path))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, start=1):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '').strip()
                
                # SRT format:
                # Sequence number
                # Start time --> End time
                # Text
                # Blank line
                
                f.write(f"{i}\n")
                f.write(f"{format_time_srt(start)} --> {format_time_srt(end)}\n")
                f.write(f"{text}\n")
                f.write("\n")
        
        logger.debug(f"SRT exported: {output_path}")
    
    def export_vtt(self, result: Dict, output_path: str) -> None:
        """
        Export transcription as WebVTT subtitle file.
        
        Args:
            result: Transcription result from Whisper
            output_path: Path to save VTT file
        """
        segments = result.get('segments', [])
        
        ensure_dir(os.path.dirname(output_path))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # WebVTT header
            f.write("WEBVTT\n\n")
            
            for segment in segments:
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '').strip()
                
                # VTT format:
                # Start time --> End time
                # Text
                # Blank line
                
                f.write(f"{format_time_vtt(start)} --> {format_time_vtt(end)}\n")
                f.write(f"{text}\n")
                f.write("\n")
        
        logger.debug(f"VTT exported: {output_path}")
    
    def export_json(self, result: Dict, output_path: str) -> None:
        """
        Export transcription as JSON file with full metadata.
        
        Args:
            result: Transcription result from Whisper
            output_path: Path to save JSON file
        """
        ensure_dir(os.path.dirname(output_path))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"JSON exported: {output_path}")
    
    def _export_by_format(self, result: Dict, output_path: str, fmt: str) -> None:
        """
        Export result based on format string.
        
        Args:
            result: Transcription result
            output_path: Output file path
            fmt: Format string (txt, srt, vtt, json)
        """
        fmt = fmt.lower()
        
        if fmt == 'txt':
            self.export_txt(result, output_path)
        elif fmt == 'srt':
            self.export_srt(result, output_path)
        elif fmt == 'vtt':
            self.export_vtt(result, output_path)
        elif fmt == 'json':
            self.export_json(result, output_path)
        else:
            raise ValueError(f"Unsupported export format: {fmt}")
