"""faster-whisper backend (cross-platform, CPU/GPU/MPS)."""

from __future__ import annotations

import os
import platform
import wave
from pathlib import Path
from typing import Any

import numpy as np

from .base import BackendResult, RawWhisperParams, Segment

_DEFAULT_MODEL = os.environ.get("VIDEO2MD_MODEL", "base")


def _resolve_device(device: str) -> str:
    if device and device != "auto":
        return device
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except Exception:
        pass
    if platform.system() == "Darwin" and platform.machine() in ("arm64", "aarch64"):
        return "mps"
    return "cpu"


def _resolve_compute_type(device: str, compute_type: str) -> str:
    if compute_type and compute_type != "auto":
        return compute_type
    if device == "cpu":
        return "int8"
    return "float16"


def _load_audio(path: str) -> np.ndarray:
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


class FasterWhisperBackend:
    name = "faster-whisper"

    def __init__(
        self,
        model_size: str = _DEFAULT_MODEL,
        device: str = "auto",
        compute_type: str = "auto",
    ):
        self.model_size = model_size
        self.device = _resolve_device(device)
        self.compute_type = _resolve_compute_type(self.device, compute_type)
        self._model = None

    def is_available(self) -> bool:
        try:
            import faster_whisper  # noqa: F401

            return True
        except Exception:
            return False

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    def transcribe(
        self,
        audio_path: str,
        *,
        language: str | None = None,
        params: RawWhisperParams,
    ) -> BackendResult:
        model = self._get_model()
        audio = _load_audio(audio_path)

        kwargs: dict[str, Any] = {
            "beam_size": params.beam_size,
            "best_of": params.best_of,
            "patience": params.patience,
            "length_penalty": params.length_penalty,
            "repetition_penalty": params.repetition_penalty,
            "no_repeat_ngram_size": params.no_repeat_ngram_size,
            "temperature": params.temperature,
            "compression_ratio_threshold": params.compression_ratio_threshold,
            "log_prob_threshold": params.log_prob_threshold,
            "no_speech_threshold": params.no_speech_threshold,
            "condition_on_previous_text": params.condition_on_previous_text,
            "prompt_reset_on_temperature": params.prompt_reset_on_temperature,
            "suppress_blank": params.suppress_blank,
            "without_timestamps": params.without_timestamps,
            "max_initial_timestamp": params.max_initial_timestamp,
            "word_timestamps": params.word_timestamps,
            "multilingual": params.multilingual,
            "vad_filter": params.vad_filter,
            "chunk_length": params.chunk_length,
        }
        if params.initial_prompt is not None:
            kwargs["initial_prompt"] = params.initial_prompt
        if params.prefix is not None:
            kwargs["prefix"] = params.prefix
        if params.suppress_tokens is not None:
            kwargs["suppress_tokens"] = params.suppress_tokens
        if params.prepend_punctuations is not None:
            kwargs["prepend_punctuations"] = params.prepend_punctuations
        if params.append_punctuations is not None:
            kwargs["append_punctuations"] = params.append_punctuations
        if params.vad_parameters is not None:
            kwargs["vad_parameters"] = params.vad_parameters
        if params.max_new_tokens is not None:
            kwargs["max_new_tokens"] = params.max_new_tokens
        if params.clip_timestamps and params.clip_timestamps != "0":
            kwargs["clip_timestamps"] = params.clip_timestamps
        if params.hallucination_silence_threshold is not None:
            kwargs["hallucination_silence_threshold"] = params.hallucination_silence_threshold
        if params.hotwords is not None:
            kwargs["hotwords"] = params.hotwords
        if params.language_detection_threshold is not None:
            kwargs["language_detection_threshold"] = params.language_detection_threshold
        kwargs["language_detection_segments"] = params.language_detection_segments
        if language:
            kwargs["language"] = language

        segments_iter, info = model.transcribe(audio, **kwargs)

        segments = []
        for seg in segments_iter:
            segments.append(
                Segment(
                    start=float(seg.start),
                    end=float(seg.end),
                    text=(seg.text or "").strip(),
                )
            )

        return BackendResult(
            segments=segments,
            language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
            duration=getattr(info, "duration", None),
        )
