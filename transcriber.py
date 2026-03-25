"""
Core transcription module using Whisper ASR.
"""

import os
import json
import tempfile
import shutil
import wave
from pathlib import Path
from typing import Dict, List, Optional

import whisper
import ffmpeg

from config import WHISPER_MODELS, OUTPUT_FORMATS
from utils.logger import setup_logger
from utils.file_handler import sanitize_filename, validate_file, ensure_dir
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
        save_outputs: bool = True,
        diarize: bool = False,
        diarization_backend: str = "pyannote",
        diarization_permissive: bool = True,
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
                - speaker_segments / speakers: when diarize=True and successful
        """
        return self.transcribe_many(
            [video_path],
            output_formats=output_formats,
            save_outputs=save_outputs,
            diarize=diarize,
            diarization_backend=diarization_backend,
            diarization_permissive=diarization_permissive,
        )

    def transcribe_many(
        self,
        video_paths: List[str],
        output_formats: Optional[List[str]] = None,
        save_outputs: bool = True,
        diarize: bool = False,
        diarization_backend: str = "pyannote",
        diarization_permissive: bool = True,
        output_basename: Optional[str] = None,
    ) -> Dict:
        """
        Transcribe one or more video files as a single continuous transcript.

        The videos are converted to mono 16 kHz WAV files, concatenated in the
        provided order, and sent to Whisper once so timestamps remain continuous.

        Args:
            video_paths: List of video file paths in the order they should be read
            output_formats: List of formats to export (txt, srt, vtt, json)
            save_outputs: Whether to save output files automatically
            diarize: Whether to run speaker diarization on the combined audio
            diarization_backend: Backend name for diarization
            diarization_permissive: Keep transcript even if diarization fails
            output_basename: Optional custom output filename stem

        Returns:
            Dictionary with Whisper output plus source metadata.
        """
        if not video_paths:
            raise ValueError("At least one video file must be provided")

        for video_path in video_paths:
            if not validate_file(video_path):
                raise FileNotFoundError(
                    f"Video file not found or not accessible: {video_path}"
                )

        if len(video_paths) == 1:
            logger.info(f"Starting transcription: {Path(video_paths[0]).name}")
        else:
            names = ", ".join(Path(p).name for p in video_paths)
            logger.info(f"Starting combined transcription: {names}")

        temp_dir = tempfile.mkdtemp(prefix="whisper_audio_")
        merged_audio_path = os.path.join(temp_dir, "merged_audio.wav")
        extracted_audio_paths: List[str] = []

        try:
            for index, video_path in enumerate(video_paths, start=1):
                audio_path = os.path.join(temp_dir, f"audio_{index}.wav")
                logger.debug(f"Extracting audio to: {audio_path}")
                self.extract_audio(video_path, audio_path)
                extracted_audio_paths.append(audio_path)

            if len(extracted_audio_paths) == 1:
                merged_audio_path = extracted_audio_paths[0]
            else:
                logger.debug(f"Concatenating {len(extracted_audio_paths)} audio tracks")
                self._concat_wav_files(extracted_audio_paths, merged_audio_path)

            logger.info("Running Whisper inference...")
            result = self.model.transcribe(
                merged_audio_path,
                language=self.language if self.language else None,
                task="transcribe",
                verbose=False
            )

            logger.info(f"Transcription complete. Detected language: {result.get('language', 'unknown')}")

            if len(video_paths) == 1:
                result['source_file'] = video_paths[0]
            else:
                result.pop('source_file', None)
            result['source_files'] = list(video_paths)
            result['model_used'] = self.model_name

            if diarize:
                from diarization.assignment import (
                    assign_speakers_to_segments,
                    unique_speakers_ordered,
                )
                from diarization.factory import create_diarizer

                try:
                    diarizer = create_diarizer(diarization_backend)
                    dres = diarizer.diarize(merged_audio_path)
                    raw_segments = result.get('segments') or []
                    labeled = assign_speakers_to_segments(
                        list(raw_segments),
                        dres.speaker_segments,
                    )
                    result['segments'] = labeled
                    result['speaker_segments'] = dres.speaker_segments
                    result['speakers'] = unique_speakers_ordered(dres.speaker_segments)
                    result['text'] = self._join_segment_texts(labeled)
                except Exception as e:
                    msg = str(e)
                    if not diarization_permissive:
                        logger.error(f"Diarization failed: {msg}")
                        raise
                    logger.warning(
                        f"Diarization failed (transcript kept without speakers): {msg}"
                    )
                    result['diarization_warning'] = msg

            if save_outputs and output_formats:
                base_name = self._normalize_output_basename(output_basename, video_paths)
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
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary files: {e}")

    def _build_output_basename(self, video_paths: List[str]) -> str:
        stems = [sanitize_filename(Path(path).stem) for path in video_paths]
        joined = "__".join(filter(None, stems))
        return joined or "transcript"

    def _normalize_output_basename(
        self,
        output_basename: Optional[str],
        video_paths: List[str],
    ) -> str:
        if output_basename:
            sanitized = sanitize_filename(Path(output_basename).name).strip()
            if sanitized:
                return sanitized
        return self._build_output_basename(video_paths)

    def _concat_wav_files(self, audio_paths: List[str], output_path: str) -> None:
        if not audio_paths:
            raise ValueError("No audio files provided for concatenation")

        ensure_dir(os.path.dirname(output_path))

        with wave.open(audio_paths[0], "rb") as first_wav:
            params = (
                first_wav.getnchannels(),
                first_wav.getsampwidth(),
                first_wav.getframerate(),
                first_wav.getcomptype(),
                first_wav.getcompname(),
            )
            with wave.open(output_path, "wb") as out_wav:
                out_wav.setnchannels(params[0])
                out_wav.setsampwidth(params[1])
                out_wav.setframerate(params[2])
                out_wav.setcomptype(params[3], params[4])
                out_wav.writeframes(first_wav.readframes(first_wav.getnframes()))

                for audio_path in audio_paths[1:]:
                    with wave.open(audio_path, "rb") as wav_file:
                        current = (
                            wav_file.getnchannels(),
                            wav_file.getsampwidth(),
                            wav_file.getframerate(),
                            wav_file.getcomptype(),
                            wav_file.getcompname(),
                        )
                        if current != params:
                            raise RuntimeError(
                                "Audio files must share the same format before concatenation"
                            )
                        out_wav.writeframes(wav_file.readframes(wav_file.getnframes()))

        logger.debug(f"Audio concatenated successfully: {Path(output_path).name}")
    
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

    @staticmethod
    def _join_segment_texts(segments: List[Dict]) -> str:
        parts: List[str] = []
        for seg in segments:
            t = (seg.get('text') or '').strip()
            if t:
                parts.append(t)
        return ' '.join(parts).strip()

    @staticmethod
    def _format_segment_line(segment: Dict) -> str:
        text = (segment.get('text') or '').strip()
        spk = segment.get('speaker')
        if spk:
            return f'[{spk}] {text}'
        return text

    @staticmethod
    def _format_subtitle_text(segment: Dict) -> str:
        text = (segment.get('text') or '').strip()
        spk = segment.get('speaker')
        if spk:
            return f'{spk}: {text}'
        return text
    
    def export_txt(self, result: Dict, output_path: str) -> None:
        """
        Export transcription as plain text.
        
        Args:
            result: Transcription result from Whisper
            output_path: Path to save TXT file
        """
        segments = result.get('segments') or []
        if segments and any('speaker' in s for s in segments):
            text = '\n'.join(
                self._format_segment_line(s) for s in segments
                if (s.get('text') or '').strip()
            ).strip()
        else:
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
                # SRT format:
                # Sequence number
                # Start time --> End time
                # Text
                # Blank line
                
                f.write(f"{i}\n")
                f.write(f"{format_time_srt(start)} --> {format_time_srt(end)}\n")
                f.write(f"{self._format_subtitle_text(segment)}\n")
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
                # VTT format:
                # Start time --> End time
                # Text
                # Blank line
                
                f.write(f"{format_time_vtt(start)} --> {format_time_vtt(end)}\n")
                f.write(f"{self._format_subtitle_text(segment)}\n")
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
