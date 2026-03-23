"""
Diarization backend implementations (heavy deps imported inside methods).
"""

from __future__ import annotations

import os
from contextlib import ExitStack, contextmanager
from typing import Any, Dict, List, Optional

from diarization.base import DiarizationResult


class NoOpDiarizer:
    """Backend that performs no diarization (empty speaker timeline)."""

    name = "noop"

    def diarize(self, audio_path: str) -> DiarizationResult:
        _ = audio_path
        return DiarizationResult(speaker_segments=[])


class PyannoteDiarizer:
    """pyannote.audio speaker diarization (CPU)."""

    name = "pyannote"

    def __init__(self, hf_token: Optional[str] = None) -> None:
        self._hf_token = hf_token

    def diarize(self, audio_path: str) -> DiarizationResult:
        from diarization.hf_hub_compat import apply_hf_hub_use_auth_token_patch

        apply_hf_hub_use_auth_token_patch()

        import torch

        self._allow_torchversion_safe_global(torch)
        from pyannote.audio import Pipeline

        token = self._hf_token or os.environ.get("HF_TOKEN") or os.environ.get(
            "HUGGING_FACE_HUB_TOKEN"
        )
        if not token:
            raise RuntimeError(
                "Для диаризации pyannote нужен токен Hugging Face. "
                "Задайте переменную окружения HF_TOKEN или установите переменную "
                "HUGGING_FACE_HUB_TOKEN, затем примите условия модели на huggingface.co."
            )

        with self._trusted_torch_load(torch):
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=token,
            )
        if pipeline is None:
            raise RuntimeError(
                "Не удалось загрузить модель pyannote/speaker-diarization-3.1. "
                "Проверьте HF_TOKEN и условия использования модели на Hugging Face."
            )
        pipeline.to(torch.device("cpu"))

        annotation = pipeline({"audio": audio_path})

        speaker_segments: List[Dict[str, Any]] = []
        for segment, _, label in annotation.itertracks(yield_label=True):
            speaker_segments.append(
                {
                    "speaker": self._normalize_label(str(label)),
                    "start": float(segment.start),
                    "end": float(segment.end),
                }
            )

        speaker_segments.sort(key=lambda x: (x["start"], x["end"]))
        return DiarizationResult(speaker_segments=speaker_segments)

    @staticmethod
    def _normalize_label(label: str) -> str:
        if label.upper().startswith("SPEAKER_"):
            return label.upper()
        return label

    @staticmethod
    def _allow_torchversion_safe_global(torch_module: Any) -> None:
        """Allow pyannote checkpoints that serialize torch version metadata."""
        torch_version = getattr(getattr(torch_module, "torch_version", None), "TorchVersion", None)
        serialization = getattr(torch_module, "serialization", None)
        if torch_version is None or serialization is None:
            return

        add_safe_globals = getattr(serialization, "add_safe_globals", None)
        if callable(add_safe_globals):
            add_safe_globals([torch_version])

    @staticmethod
    @contextmanager
    def _trusted_torch_load(torch_module: Any):
        """Temporarily default torch.load to weights_only=False for trusted checkpoints."""
        original_load = torch_module.load

        def _load(*args, **kwargs):  # type: ignore[no-untyped-def]
            if kwargs.get("weights_only") is None:
                kwargs["weights_only"] = False
            return original_load(*args, **kwargs)

        torch_module.load = _load
        stack = ExitStack()
        try:
            serialization = getattr(torch_module, "serialization", None)
            if serialization is not None:
                try:
                    from pyannote.audio.core.task import Specifications
                except Exception:
                    Specifications = None  # type: ignore[assignment]
                else:
                    safe_globals = getattr(serialization, "safe_globals", None)
                    if callable(safe_globals):
                        stack.enter_context(safe_globals([Specifications]))
                    else:
                        add_safe_globals = getattr(serialization, "add_safe_globals", None)
                        if callable(add_safe_globals):
                            add_safe_globals([Specifications])
            with stack:
                yield
        finally:
            torch_module.load = original_load
