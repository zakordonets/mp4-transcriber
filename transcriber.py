"""
Core transcription module using Whisper ASR.
"""

import os
import json
import hashlib
import re
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
    Class for transcribing media files using OpenAI Whisper.
    
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
        Transcribe a media file.
        
        Args:
            video_path: Path to the input media file
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
        Transcribe one or more media files as a single continuous transcript.

        The inputs are converted to mono 16 kHz WAV files, concatenated in the
        provided order, and sent to Whisper once so timestamps remain continuous.

        Args:
            video_paths: List of media file paths in the order they should be read
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
            raise ValueError("At least one media file must be provided")

        for video_path in video_paths:
            if not validate_file(video_path):
                raise FileNotFoundError(
                    f"Media file not found or not accessible: {video_path}"
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
                    result['speaker_turns'] = self._build_speaker_turns_from_result(
                        result,
                        dres.speaker_segments,
                    )
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
        max_length = 120
        stems = [sanitize_filename(Path(path).stem) for path in video_paths]
        joined = "__".join(filter(None, stems))
        if not joined:
            return "transcript"
        if len(joined) <= max_length:
            return joined

        digest = hashlib.sha1("||".join(video_paths).encode("utf-8")).hexdigest()[:10]
        prefix_budget = max_length - len("combined_") - len(digest) - 1
        prefix = joined[:prefix_budget].rstrip("._-")
        if not prefix:
            prefix = "transcript"
        return f"{prefix}_{digest}"

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
        chunk_frames = 16_000 * 30

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
                self._copy_wav_frames(first_wav, out_wav, chunk_frames)

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
                        self._copy_wav_frames(wav_file, out_wav, chunk_frames)

        logger.debug(f"Audio concatenated successfully: {Path(output_path).name}")

    @staticmethod
    def _copy_wav_frames(
        src_wav: wave.Wave_read,
        dst_wav: wave.Wave_write,
        chunk_frames: int,
    ) -> None:
        while True:
            chunk = src_wav.readframes(chunk_frames)
            if not chunk:
                break
            dst_wav.writeframes(chunk)
    
    def extract_audio(self, video_path: str, audio_path: str) -> None:
        """
        Extract and normalize audio from a media file using ffmpeg.
        
        Args:
            video_path: Path to input media file
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
    def _normalize_turn_text(text: str) -> str:
        text = re.sub(r"\s+", " ", (text or "").strip())
        text = re.sub(r"\s+([,.;:?!])", r"\1", text)
        return text.strip()

    def _split_segment_into_phrases(self, segment: Dict) -> List[Dict]:
        text = self._normalize_turn_text(segment.get("text", ""))
        if not text:
            return []

        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", start) or start)
        duration = max(end - start, 0.0)

        parts = [part.strip() for part in re.split(r"(?<=[.!?;:])\s+", text) if part.strip()]
        if len(parts) <= 1 or duration <= 0:
            return [{"text": text, "start": start, "end": end}]

        total_chars = sum(len(part) for part in parts) or len(parts)
        cursor = start
        phrases: List[Dict] = []
        for index, part in enumerate(parts):
            if index == len(parts) - 1:
                part_end = end
            else:
                part_duration = duration * (len(part) / total_chars)
                part_end = min(end, cursor + part_duration)
            phrases.append({
                "text": part,
                "start": cursor,
                "end": part_end,
            })
            cursor = part_end
        return phrases

    def _extract_alignment_items(self, result: Dict) -> List[Dict]:
        items: List[Dict] = []
        for segment_index, segment in enumerate(result.get("segments") or []):
            words = segment.get("words") or []
            if words:
                for word in words:
                    text = self._normalize_turn_text(word.get("word") or word.get("text") or "")
                    if not text:
                        continue
                    start = float(word.get("start", segment.get("start", 0.0)) or 0.0)
                    end = float(word.get("end", start) or start)
                    items.append({
                        "text": text,
                        "start": start,
                        "end": end,
                        "source_segment_index": segment_index,
                    })
                continue

            for phrase in self._split_segment_into_phrases(segment):
                phrase["source_segment_index"] = segment_index
                items.append(phrase)
        return items

    @staticmethod
    def _assign_speaker_to_item(item: Dict, speaker_segments: List[Dict]) -> Dict:
        item_start = float(item.get("start", 0.0) or 0.0)
        item_end = float(item.get("end", item_start) or item_start)
        midpoint = item_start + ((item_end - item_start) / 2.0)

        best_speaker = None
        best_overlap = -1.0
        midpoint_speaker = None

        for segment in speaker_segments:
            seg_start = float(segment.get("start", 0.0) or 0.0)
            seg_end = float(segment.get("end", seg_start) or seg_start)
            overlap = max(0.0, min(item_end, seg_end) - max(item_start, seg_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = segment.get("speaker")
            if seg_start <= midpoint <= seg_end:
                midpoint_speaker = segment.get("speaker")

        assigned = dict(item)
        assigned["speaker"] = best_speaker if best_overlap > 0 else midpoint_speaker
        return assigned

    def _build_speaker_turns(
        self,
        items: List[Dict],
        pause_split_threshold: float = 1.0,
    ) -> List[Dict]:
        turns: List[Dict] = []

        for item in items:
            text = self._normalize_turn_text(item.get("text", ""))
            if not text:
                continue

            speaker = item.get("speaker")
            start = float(item.get("start", 0.0) or 0.0)
            end = float(item.get("end", start) or start)
            word_count = len(text.split())

            if not turns:
                turns.append({
                    "speaker": speaker,
                    "start": start,
                    "end": end,
                    "text": text,
                    "word_count": word_count,
                })
                continue

            previous = turns[-1]
            gap = max(0.0, start - float(previous.get("end", start) or start))
            if previous.get("speaker") == speaker and gap <= pause_split_threshold:
                previous["text"] = self._normalize_turn_text(f"{previous['text']} {text}")
                previous["end"] = end
                previous["word_count"] = int(previous.get("word_count", 0)) + word_count
            else:
                turns.append({
                    "speaker": speaker,
                    "start": start,
                    "end": end,
                    "text": text,
                    "word_count": word_count,
                })

        return turns

    def _build_speaker_turns_from_result(
        self,
        result: Dict,
        speaker_segments: List[Dict],
        pause_split_threshold: float = 1.0,
    ) -> List[Dict]:
        items = self._extract_alignment_items(result)
        if not items:
            return []
        aligned_items = [
            self._assign_speaker_to_item(item, speaker_segments)
            for item in items
        ]
        return self._build_speaker_turns(
            aligned_items,
            pause_split_threshold=pause_split_threshold,
        )

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
        speaker_turns = result.get('speaker_turns') or []
        segments = result.get('segments') or []
        if speaker_turns:
            blocks = []
            for turn in speaker_turns:
                text = self._normalize_turn_text(turn.get('text', ''))
                if not text:
                    continue
                speaker = turn.get('speaker')
                if speaker:
                    blocks.append(f"[{speaker}]\n{text}")
                else:
                    blocks.append(text)
            text = '\n\n'.join(blocks).strip()
        elif segments and any('speaker' in s for s in segments):
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


MediaTranscriber = VideoTranscriber
