"""mlx-whisper backend (Apple Silicon only)."""

from __future__ import annotations

import os
import platform
from typing import Any

from .base import BackendResult, RawWhisperParams, Segment

_SIZE_TO_REPO = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large": "mlx-community/whisper-large-mlx",
    "large-v1": "mlx-community/whisper-large-v1-mlx",
    "large-v2": "mlx-community/whisper-large-v2-mlx",
    "large-v3": "mlx-community/whisper-large-v3-mlx",
    "large-v3-turbo": "mlx-community/whisper-large-v3-turbo",
}


class MlxWhisperBackend:
    name = "mlx-whisper"

    def __init__(self, model_size: str = "base", repo: str | None = None):
        self.model_size = model_size
        self.repo = repo or _SIZE_TO_REPO.get(model_size, f"mlx-community/whisper-{model_size}-mlx")

    def is_available(self) -> bool:
        if platform.system() != "Darwin" or platform.machine() not in ("arm64", "aarch64"):
            return False
        try:
            import mlx_whisper  # noqa: F401

            return True
        except Exception:
            return False

    def transcribe(
        self,
        audio_path: str,
        *,
        language: str | None = None,
        params: RawWhisperParams,
    ) -> BackendResult:
        import mlx_whisper

        kwargs: dict[str, Any] = {
            "path_or_hf_repo": self.repo,
            "temperature": params.temperature if not isinstance(params.temperature, list) else params.temperature[0],
            "compression_ratio_threshold": params.compression_ratio_threshold,
            "logprob_threshold": params.log_prob_threshold,
            "no_speech_threshold": params.no_speech_threshold,
            "condition_on_previous_text": params.condition_on_previous_text,
            "word_timestamps": params.word_timestamps,
        }
        if language:
            kwargs["language"] = language
        if params.initial_prompt is not None:
            kwargs["initial_prompt"] = params.initial_prompt

        result = mlx_whisper.transcribe(audio_path, **kwargs)

        segments = []
        for seg in result.get("segments", []):
            segments.append(
                Segment(
                    start=float(seg["start"]),
                    end=float(seg["end"]),
                    text=(seg.get("text") or "").strip(),
                )
            )

        return BackendResult(
            segments=segments,
            language=result.get("language"),
            language_probability=None,
            duration=segments[-1].end if segments else None,
        )
