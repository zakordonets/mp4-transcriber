"""
Tests for speaker assignment and diarization helpers.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from diarization.backends import PyannoteDiarizer
from diarization.assignment import assign_speakers_to_segments, unique_speakers_ordered


class TestAssignSpeakers:
    def test_overlap_prefers_max_overlap(self):
        transcript = [
            {"start": 1.5, "end": 2.5, "text": "hello"},
        ]
        speakers = [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0},
            {"speaker": "SPEAKER_01", "start": 1.0, "end": 3.0},
        ]
        out = assign_speakers_to_segments(transcript, speakers)
        assert out[0]["speaker"] == "SPEAKER_01"

    def test_empty_speakers_copies_segments(self):
        transcript = [{"start": 0.0, "end": 1.0, "text": "a"}]
        out = assign_speakers_to_segments(transcript, [])
        assert out == transcript
        assert "speaker" not in out[0]

    def test_unique_speakers_order(self):
        segs = [
            {"speaker": "SPEAKER_01", "start": 0, "end": 1},
            {"speaker": "SPEAKER_00", "start": 1, "end": 2},
            {"speaker": "SPEAKER_01", "start": 2, "end": 3},
        ]
        assert unique_speakers_ordered(segs) == ["SPEAKER_01", "SPEAKER_00"]

    def test_allow_torchversion_safe_global_registers_version_metadata(self):
        calls = []

        class DummyTorchVersion:
            pass

        class DummySerialization:
            @staticmethod
            def add_safe_globals(items):
                calls.append(items)

        class DummyTorch:
            torch_version = type("TorchVersionModule", (), {"TorchVersion": DummyTorchVersion})
            serialization = DummySerialization

        PyannoteDiarizer._allow_torchversion_safe_global(DummyTorch)

        assert calls == [[DummyTorchVersion]]

    def test_trusted_torch_load_forces_weights_only_false(self):
        calls = []

        class DummyTorch:
            @staticmethod
            def load(*args, **kwargs):
                calls.append(kwargs.copy())
                return {"ok": True}

        with PyannoteDiarizer._trusted_torch_load(DummyTorch):
            assert DummyTorch.load("checkpoint.pt") == {"ok": True}

        assert calls == [{"weights_only": False}]
