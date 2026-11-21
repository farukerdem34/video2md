"""whisper.cpp backend (CPU/Metal)."""

from __future__ import annotations

from .base import BackendResult, RawWhisperParams, Segment


class WhisperCppBackend:
    name = "whisper-cpp"

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size

    def is_available(self) -> bool:
        try:
            import pywhispercpp  # noqa: F401

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
        from pywhispercpp.model import Model

        model = Model(self.model_size)
        kwargs = {}
        if language:
            kwargs["language"] = language
        result = model.transcribe(audio_path, **kwargs)

        segments = []
        for seg in result or []:
            # pywhispercpp segments use t0/t1 in 10ms units
            t0 = getattr(seg, "t0", 0)
            t1 = getattr(seg, "t1", 0)
            start = t0 / 100.0 if t0 > 100 else float(t0)
            end = t1 / 100.0 if t1 > 100 else float(t1)
            segments.append(
                Segment(start=start, end=end, text=(getattr(seg, "text", "") or "").strip())
            )

        return BackendResult(
            segments=segments,
            language=language,
            language_probability=None,
            duration=segments[-1].end if segments else None,
        )
