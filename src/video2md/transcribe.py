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
    # Prefer Apple Metal on macOS arm64.
    import platform
    if platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"):
        try:
            import ctranslate2

            if hasattr(ctranslate2, "get_mps_device_count") and ctranslate2.get_mps_device_count() > 0:
                return "mps"
        except Exception:
            pass
        # ctranslate2 older versions lack the counter; try mps anyway.
        return "mps"
    return "cpu"


def transcribe(
    file_path: str,
    model_size: str | None = None,
    language: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
) -> dict[str, Any]:
    """Transcribe a media file. Extracts audio first if needed."""
    model_size = model_size or DEFAULT_MODEL
    device = _resolve_device(device or DEFAULT_DEVICE)
    compute_type = _resolve_compute_type(device, compute_type or DEFAULT_COMPUTE)

    info = get_media_info(file_path)
    if not info.get("has_audio"):
        raise ValueError(f"File has no audio stream: {file_path}")

    audio_path = extract_audio(file_path)
    audio_array = _load_audio_as_float32(audio_path)

    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    kwargs: dict[str, Any] = {"beam_size": 5}
    if language:
        kwargs["language"] = language

    segments_iter, whisper_info = model.transcribe(audio_array, **kwargs)

    segments: list[dict[str, Any]] = []
    full_text_parts: list[str] = []
    for seg in segments_iter:
        text = (seg.text or "").strip()
        segments.append(
            {
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": text,
            }
        )
        if text:
            full_text_parts.append(text)

    return {
        "file_path": str(Path(file_path).expanduser().resolve()),
        "audio_path": str(Path(audio_path).expanduser().resolve()),
        "model": model_size,
        "device": device,
        "compute_type": compute_type,
        "language": getattr(whisper_info, "language", None),
        "language_probability": getattr(whisper_info, "language_probability", None),
        "duration_seconds": getattr(whisper_info, "duration", None) or info.get("duration_seconds"),
        "segment_count": len(segments),
        "full_text": " ".join(full_text_parts),
        "segments": segments,
    }
