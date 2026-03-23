"""
Map legacy use_auth_token kwarg to token for huggingface_hub >= 1.0.

pyannote.audio 3.x calls hf_hub_download(..., use_auth_token=...), which newer
huggingface_hub no longer accepts.
"""

from __future__ import annotations

_applied: bool = False


def apply_hf_hub_use_auth_token_patch() -> None:
    """Idempotent monkey-patch; call before importing pyannote.audio."""
    global _applied
    if _applied:
        return

    import huggingface_hub as hf
    import huggingface_hub.file_download as fd

    _orig = fd.hf_hub_download

    def _hf_hub_download(*args, **kwargs):  # type: ignore[no-untyped-def]
        if "use_auth_token" in kwargs:
            tok = kwargs.pop("use_auth_token")
            if kwargs.get("token") is None:
                kwargs["token"] = tok
        return _orig(*args, **kwargs)

    fd.hf_hub_download = _hf_hub_download
    hf.hf_hub_download = _hf_hub_download
    _applied = True
