"""Backend abstraction for transcription."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class BackendResult:
    segments: list[Segment] = field(default_factory=list)
    language: str | None = None
    language_probability: float | None = None
    duration: float | None = None


@dataclass
class RawWhisperParams:
    """Raw Whisper decoding params passed through to backends."""

    beam_size: int = 5
    best_of: int = 5
    patience: float = 1.0
    length_penalty: float = 1.0
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0
    temperature: float | list[float] = 0.0
    compression_ratio_threshold: float = 2.4
    log_prob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    condition_on_previous_text: bool = True
    prompt_reset_on_temperature: float = 0.5
    initial_prompt: str | None = None
    prefix: str | None = None
    suppress_blank: bool = True
    suppress_tokens: list[int] | None = None
    without_timestamps: bool = False
    max_initial_timestamp: float = 1.0
    word_timestamps: bool = False
    prepend_punctuations: str = "\"'¿([{-"
    append_punctuations: str = "\"'.。,，!！?？:：)]}、"
    multilingual: bool = False
    vad_filter: bool = True
    vad_parameters: dict[str, Any] | None = None
    max_new_tokens: int | None = None
    chunk_length: int = 30
    clip_timestamps: str = "0"
    hallucination_silence_threshold: float | None = None
    hotwords: str | None = None
    language_detection_threshold: float | None = None
    language_detection_segments: int = 1


class TranscriptionBackend(Protocol):
    name: str

    def is_available(self) -> bool: ...

    def transcribe(
        self,
        audio_path: str,
        *,
        language: str | None = None,
        params: RawWhisperParams,
    ) -> BackendResult: ...
