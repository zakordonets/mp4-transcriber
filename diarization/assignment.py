"""
Map transcript segments to speaker labels using diarization timeline.
"""

from typing import Any, Dict, List, Optional, Tuple


def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def assign_speakers_to_segments(
    transcript_segments: List[Dict[str, Any]],
    speaker_segments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Add \"speaker\" to each transcript segment.

    Chooses the speaker interval with maximum time overlap with the transcript
    segment; ties break by earlier speaker segment start time.
    If speaker_segments is empty, returns copies without \"speaker\" keys.
    """
    if not speaker_segments:
        return [dict(s) for s in transcript_segments]

    sorted_spk = sorted(
        speaker_segments,
        key=lambda x: (float(x["start"]), float(x["end"])),
    )

    out: List[Dict[str, Any]] = []
    for seg in transcript_segments:
        row = dict(seg)
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", start))
        if end < start:
            start, end = end, start

        best_speaker: Optional[str] = None
        best_overlap = -1.0
        best_key: Tuple[float, float] = (0.0, 0.0)

        for sp in sorted_spk:
            s0 = float(sp["start"])
            s1 = float(sp["end"])
            ov = _overlap(start, end, s0, s1)
            key = (s0, s1)
            if ov > best_overlap or (ov == best_overlap and key < best_key):
                best_overlap = ov
                best_key = key
                best_speaker = str(sp["speaker"])

        if best_speaker is not None and best_overlap > 0.0:
            row["speaker"] = best_speaker
        out.append(row)
    return out


def unique_speakers_ordered(speaker_segments: List[Dict[str, Any]]) -> List[str]:
    """Stable unique speaker ids in first-seen order."""
    seen: List[str] = []
    for seg in speaker_segments:
        spk = str(seg.get("speaker", ""))
        if spk and spk not in seen:
            seen.append(spk)
    return seen
