"""
Diarization abstractions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass
class DiarizationResult:
    """Output of a diarization backend."""

    speaker_segments: List[Dict[str, Any]] = field(default_factory=list)
    """Each item: {\"speaker\": \"SPEAKER_00\", \"start\": float, \"end\": float}."""


class BaseDiarizer(Protocol):
    """Pluggable speaker diarization backend."""

    name: str

    def diarize(self, audio_path: str) -> DiarizationResult:
        """
        Run diarization on a WAV (or supported) audio file.

        Args:
            audio_path: Path to mono 16 kHz WAV used by Whisper extraction.
        """
        ...
