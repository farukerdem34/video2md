"""Backend registry with auto-selection and fallback."""

from __future__ import annotations

import os
import platform
from typing import Any

from .base import TranscriptionBackend
from .faster_whisper import FasterWhisperBackend


def available_backends() -> list[str]:
    names = ["faster-whisper"]
    # mlx
    try:
        from .mlx_whisper import MlxWhisperBackend

        if MlxWhisperBackend().is_available():
            names.insert(0, "mlx-whisper")
    except Exception:
        pass
    # openai
    if os.environ.get("OPENAI_API_KEY"):
        names.append("openai")
    # whisper.cpp
    try:
        import pywhispercpp  # noqa: F401

        names.append("whisper-cpp")
    except Exception:
        pass
    return names


def create_backend(
    name: str | None = None,
    *,
    model_size: str = "base",
    device: str = "auto",
    compute_type: str = "auto",
) -> TranscriptionBackend:
    requested = (name or os.environ.get("VIDEO2MD_BACKEND") or "auto").lower()

    if requested == "auto":
        # platform-aware default
        if platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"):
            requested = "mlx-whisper"
        else:
            requested = "faster-whisper"

    # fallback chain: always end with the platform default so an unavailable
    # requested backend (e.g. openai without a key) still falls back.
    default = "faster-whisper"
    if platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"):
        default = "mlx-whisper"
    chain = [requested] + [b for b in available_backends() if b != requested]
    if default not in chain:
        chain.append(default)
    if "faster-whisper" not in chain:
        chain.append("faster-whisper")

    last_err: Exception | None = None
    for candidate in chain:
        try:
            backend = _instantiate(candidate, model_size, device, compute_type)
            if backend is not None and backend.is_available():
                return backend
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"No transcription backend available: {last_err}")


def _instantiate(name: str, model_size, device, compute_type) -> TranscriptionBackend | None:
    if name in ("faster-whisper", "faster_whisper"):
        return FasterWhisperBackend(model_size=model_size, device=device, compute_type=compute_type)
    if name in ("mlx", "mlx-whisper", "mlx_whisper"):
        from .mlx_whisper import MlxWhisperBackend

        b = MlxWhisperBackend(model_size=model_size)
        return b
    if name in ("openai", "openai-api", "openai_api"):
        try:
            from .openai_api import OpenAIBackend

            return OpenAIBackend(model_size=model_size)
        except Exception:
            return None
    if name in ("whisper-cpp", "whisper_cpp", "whispercpp"):
        try:
            from .whisper_cpp import WhisperCppBackend

            return WhisperCppBackend(model_size=model_size)
        except Exception:
            return None
    return None
