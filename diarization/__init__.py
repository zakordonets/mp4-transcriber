"""
Optional speaker diarization layer (lazy-loaded backends).
"""

from diarization.assignment import assign_speakers_to_segments
from diarization.base import BaseDiarizer, DiarizationResult
from diarization.factory import (
    DIARIZATION_BACKENDS,
    create_diarizer,
    describe_backend_availability,
    is_backend_available,
)

__all__ = [
    "BaseDiarizer",
    "DiarizationResult",
    "assign_speakers_to_segments",
    "create_diarizer",
    "DIARIZATION_BACKENDS",
    "describe_backend_availability",
    "is_backend_available",
]
