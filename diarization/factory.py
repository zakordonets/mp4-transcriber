"""
Diarization backend registry and lazy construction.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from diarization.base import BaseDiarizer
from diarization.backends import NoOpDiarizer, PyannoteDiarizer
from diarization.hf_hub_compat import apply_hf_hub_use_auth_token_patch

DIARIZATION_BACKENDS: Tuple[str, ...] = ("noop", "pyannote")


def is_backend_available(name: str) -> Tuple[bool, str]:
    """
    Return (installed, missing_hint). Does not validate HF tokens for pyannote.
    """
    key = name.strip().lower()
    if key == "noop":
        return True, ""
    if key == "pyannote":
        try:
            apply_hf_hub_use_auth_token_patch()
            import pyannote.audio  # noqa: F401
        except Exception as e:
            err = str(e)
            if "AudioMetaData" in err or (
                "torchaudio" in err and "has no attribute" in err
            ):
                return (
                    False,
                    "torchaudio 2.9+ несовместим с pyannote.audio 3.x; "
                    "выполните: pip install -r requirements-diarization.txt "
                    "(зафиксируется torchaudio<2.9 и совместимый torch)",
                )
            short = err if len(err) <= 180 else err[:177] + "..."
            return (
                False,
                f"ошибка импорта pyannote: {short}",
            )
        return True, ""
    return False, f"unknown backend: {name}"


def describe_backend_availability() -> List[Tuple[str, bool, str]]:
    """
    List of (backend_name, available, missing_hint) for diagnostics.
    """
    rows: List[Tuple[str, bool, str]] = []
    for name in DIARIZATION_BACKENDS:
        ok, hint = is_backend_available(name)
        rows.append((name, ok, hint))
    return rows


def create_diarizer(name: str, hf_token: Optional[str] = None) -> BaseDiarizer:
    """
    Build a diarizer by name. Imports optional deps only for pyannote.
    """
    key = name.strip().lower()
    if key == "noop":
        return NoOpDiarizer()
    if key == "pyannote":
        ok, hint = is_backend_available("pyannote")
        if not ok:
            raise RuntimeError(
                f"Backend 'pyannote' недоступен: {hint}. "
                "Базовая транскрибация работает без этих пакетов."
            )
        return PyannoteDiarizer(hf_token=hf_token)
    raise ValueError(
        f"Неизвестный backend диаризации: {name}. "
        f"Доступны: {', '.join(DIARIZATION_BACKENDS)}"
    )
