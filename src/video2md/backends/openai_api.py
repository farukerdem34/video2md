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
            start = getattr(seg, "start", None)
            if start is None and isinstance(seg, dict):
                start = seg.get("start")
            end = getattr(seg, "end", None)
            if end is None and isinstance(seg, dict):
                end = seg.get("end")
            text = getattr(seg, "text", None)
            if text is None and isinstance(seg, dict):
                text = seg.get("text")
            segments.append(
                Segment(
                    start=float(start or 0.0),
                    end=float(end or 0.0),
                    text=(text or "").strip(),
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
