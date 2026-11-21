"""Transcription powered by faster-whisper."""

from __future__ import annotations

import os
import wave
from pathlib import Path
from typing import Any

import numpy as np

from .media import extract_audio, get_media_info


def _load_audio_as_float32(path: str) -> "np.ndarray":
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth}")
    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)
    return data


DEFAULT_MODEL = os.environ.get("VIDEO2MD_MODEL", "base")
DEFAULT_DEVICE = os.environ.get("VIDEO2MD_DEVICE", "auto")
DEFAULT_COMPUTE = os.environ.get("VIDEO2MD_COMPUTE_TYPE", "auto")


def _resolve_compute_type(device: str, compute_type: str) -> str:
    if compute_type and compute_type != "auto":
        return compute_type
    if device == "cpu":
        return "int8"
    return "float16"


def _resolve_device(device: str) -> str:
    if device and device != "auto":
        return device
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    import platform

    if platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"):
        return "mps"
    return "cpu"


def transcribe(
    file_path: str,
    model_size: str | None = None,
    language: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    vad_filter: bool = True,
) -> dict[str, Any]:
    """Transcribe a media file (or a slice of it).

    For long files, call repeatedly with ``start_seconds``/``end_seconds`` to
    process in chunks; segment timestamps are returned in absolute seconds.
    """
    model_size = model_size or DEFAULT_MODEL
    device = _resolve_device(device or DEFAULT_DEVICE)
    compute_type = _resolve_compute_type(device, compute_type or DEFAULT_COMPUTE)

    info = get_media_info(file_path)
    if not info.get("has_audio"):
        raise ValueError(f"File has no audio stream: {file_path}")

    total_duration = info.get("duration_seconds")

    offset = float(start_seconds) if start_seconds is not None else 0.0
    if end_seconds is not None:
        duration = float(end_seconds) - offset
        if duration <= 0:
            raise ValueError("end_seconds must be greater than start_seconds")
    else:
        duration = None
        if total_duration is not None:
            duration = float(total_duration) - offset
            if duration <= 0:
                raise ValueError("start_seconds is beyond file duration")

    audio_path = extract_audio(
        file_path, start=offset if offset > 0 else None, duration=duration
    )

    audio_array = _load_audio_as_float32(audio_path)

    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    kwargs: dict[str, Any] = {"beam_size": 5, "vad_filter": vad_filter}
    if language:
        kwargs["language"] = language

    segments_iter, whisper_info = model.transcribe(audio_array, **kwargs)

    segments: list[dict[str, Any]] = []
    full_text_parts: list[str] = []
    for seg in segments_iter:
        text = (seg.text or "").strip()
        segments.append(
            {
                "start": round(float(seg.start) + offset, 3),
                "end": round(float(seg.end) + offset, 3),
                "text": text,
            }
        )
        if text:
            full_text_parts.append(text)

    chunk_duration = getattr(whisper_info, "duration", None)

    return {
        "file_path": str(Path(file_path).expanduser().resolve()),
        "audio_path": str(Path(audio_path).expanduser().resolve()),
        "model": model_size,
        "device": device,
        "compute_type": compute_type,
        "language": getattr(whisper_info, "language", None),
        "language_probability": getattr(whisper_info, "language_probability", None),
        "start_seconds": offset,
        "end_seconds": offset + (chunk_duration if chunk_duration is not None else (duration or 0)),
        "duration_seconds": chunk_duration,
        "segment_count": len(segments),
        "full_text": " ".join(full_text_parts),
        "segments": segments,
    }
