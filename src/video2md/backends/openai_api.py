"""OpenAI Whisper API backend (cloud)."""

from __future__ import annotations

import os
from typing import Any

from .base import BackendResult, RawWhisperParams, Segment


class OpenAIBackend:
    name = "openai"

    def __init__(self, model_size: str = "whisper-1"):
        self.model = model_size if model_size.startswith("whisper") else "whisper-1"

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def transcribe(
        self,
        audio_path: str,
        *,
        language: str | None = None,
        params: RawWhisperParams,
    ) -> BackendResult:
        from openai import OpenAI

        client = OpenAI()
        with open(audio_path, "rb") as f:
            kwargs: dict[str, Any] = {"model": self.model, "file": f, "response_format": "verbose_json"}
            if language:
                kwargs["language"] = language
            resp = client.audio.transcriptions.create(**kwargs)

        segments = []
        for seg in getattr(resp, "segments", []) or []:
            segments.append(
                Segment(
                    start=float(seg.get("start", seg.start) if hasattr(seg, "start") else seg["start"]),
                    end=float(seg.get("end", seg.end) if hasattr(seg, "end") else seg["end"]),
                    text=(seg.get("text", seg.text) if hasattr(seg, "text") else seg["text"]).strip(),
                )
            )
        if not segments and getattr(resp, "text", None):
            segments.append(Segment(start=0.0, end=0.0, text=resp.text.strip()))

        return BackendResult(
            segments=segments,
            language=getattr(resp, "language", language),
            language_probability=None,
            duration=getattr(resp, "duration", None),
        )
