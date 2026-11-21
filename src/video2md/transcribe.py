"""Transcription orchestrator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .backends.base import RawWhisperParams
from .backends.registry import create_backend
from .media import extract_audio, get_media_info

_DEFAULT_MODEL = os.environ.get("VIDEO2MD_MODEL", "base")
_AUTO_CHUNK_THRESHOLD = float(os.environ.get("VIDEO2MD_AUTO_CHUNK_THRESHOLD", "600"))
_DEFAULT_CHUNK_SECONDS = int(os.environ.get("VIDEO2MD_CHUNK_SECONDS", "300"))


def _build_params(**kw) -> RawWhisperParams:
    return RawWhisperParams(**kw)


def _run_one_chunk(
    file_path: str,
    backend,
    offset: float,
    duration: float | None,
    language: str | None,
    params: RawWhisperParams,
) -> dict[str, Any]:
    audio_path = extract_audio(
        file_path, start=offset if offset > 0 else None, duration=duration
    )

    result = backend.transcribe(audio_path, language=language, params=params)

    segments = [
        {"start": round(s.start + offset, 3), "end": round(s.end + offset, 3), "text": s.text}
        for s in result.segments
    ]
    full_text = " ".join(s.text for s in result.segments if s.text)

    chunk_duration = result.duration

    return {
        "audio_path": str(Path(audio_path).expanduser().resolve()),
        "language": result.language,
        "language_probability": result.language_probability,
        "duration": chunk_duration,
        "segments": segments,
        "full_text": full_text,
    }


def transcribe(
    file_path: str,
    model_size: str | None = None,
    language: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
    backend: str | None = None,
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    vad_filter: bool = True,
    workers: int | None = None,
    force: bool = False,
    # raw params
    beam_size: int = 5,
    best_of: int = 5,
    patience: float = 1.0,
    length_penalty: float = 1.0,
    repetition_penalty: float = 1.0,
    no_repeat_ngram_size: int = 0,
    temperature: float | list[float] = 0.0,
    compression_ratio_threshold: float = 2.4,
    log_prob_threshold: float = -1.0,
    no_speech_threshold: float = 0.6,
    condition_on_previous_text: bool = True,
    prompt_reset_on_temperature: float = 0.5,
    initial_prompt: str | None = None,
    prefix: str | None = None,
    suppress_blank: bool = True,
    suppress_tokens: list[int] | None = None,
    without_timestamps: bool = False,
    max_initial_timestamp: float = 1.0,
    word_timestamps: bool = False,
    prepend_punctuations: str = "\"'¿([{-",
    append_punctuations: str = "\"'.。,，!！?？:：)]}、",
    multilingual: bool = False,
    vad_parameters: dict[str, Any] | None = None,
    max_new_tokens: int | None = None,
    chunk_length: int = 30,
    clip_timestamps: str = "0",
    hallucination_silence_threshold: float | None = None,
    hotwords: str | None = None,
    language_detection_threshold: float | None = None,
    language_detection_segments: int = 1,
) -> dict[str, Any]:
    model_size = model_size or _DEFAULT_MODEL
    info = get_media_info(file_path)
    if not info.get("has_audio"):
        raise ValueError(f"File has no audio stream: {file_path}")

    total_duration = info.get("duration_seconds")

    params = RawWhisperParams(
        beam_size=beam_size,
        best_of=best_of,
        patience=patience,
        length_penalty=length_penalty,
        repetition_penalty=repetition_penalty,
        no_repeat_ngram_size=no_repeat_ngram_size,
        temperature=temperature,
        compression_ratio_threshold=compression_ratio_threshold,
        log_prob_threshold=log_prob_threshold,
        no_speech_threshold=no_speech_threshold,
        condition_on_previous_text=condition_on_previous_text,
        prompt_reset_on_temperature=prompt_reset_on_temperature,
        initial_prompt=initial_prompt,
        prefix=prefix,
        suppress_blank=suppress_blank,
        suppress_tokens=suppress_tokens,
        without_timestamps=without_timestamps,
        max_initial_timestamp=max_initial_timestamp,
        word_timestamps=word_timestamps,
        prepend_punctuations=prepend_punctuations,
        append_punctuations=append_punctuations,
        multilingual=multilingual,
        vad_filter=vad_filter,
        vad_parameters=vad_parameters,
        max_new_tokens=max_new_tokens,
        chunk_length=chunk_length,
        clip_timestamps=clip_timestamps,
        hallucination_silence_threshold=hallucination_silence_threshold,
        hotwords=hotwords,
        language_detection_threshold=language_detection_threshold,
        language_detection_segments=language_detection_segments,
    )

    be = create_backend(backend, model_size=model_size, device=device or "auto", compute_type=compute_type or "auto")

    from .cache import cache_key, load, save

    key = cache_key(file_path, be.name, model_size, language, params)
    if not force:
        cached = load(key)
        if cached is not None:
            cached = dict(cached)
            cached["cache_hit"] = True
            return cached

    # Determine chunks
    manual = start_seconds is not None or end_seconds is not None
    offset0 = float(start_seconds) if start_seconds is not None else 0.0
    if end_seconds is not None:
        duration_total = float(end_seconds) - offset0
        if duration_total <= 0:
            raise ValueError("end_seconds must be greater than start_seconds")
        chunks = [(offset0, duration_total)]
    elif manual:
        # start only
        if total_duration is None:
            raise ValueError("Cannot determine duration for chunking")
        duration_total = float(total_duration) - offset0
        if duration_total <= 0:
            raise ValueError("start_seconds is beyond file duration")
        chunks = [(offset0, duration_total)]
    else:
        if total_duration is None:
            chunks = [(0.0, None)]
        elif total_duration > _AUTO_CHUNK_THRESHOLD:
            chunk_seconds = _DEFAULT_CHUNK_SECONDS
            chunks = []
            cur = 0.0
            while cur < total_duration:
                dur = min(chunk_seconds, total_duration - cur)
                chunks.append((cur, dur))
                cur += dur
        else:
            chunks = [(0.0, total_duration)]

    # Parallel execution
    import concurrent.futures

    workers = workers or int(os.environ.get("VIDEO2MD_WORKERS", "0")) or None
    if workers is None:
        import os as _os

        workers = max(1, (_os.cpu_count() or 4) - 1)

    # For a single chunk, just run directly
    if len(chunks) == 1:
        off, dur = chunks[0]
        r = _run_one_chunk(file_path, be, off, dur, language, params)
        chunk_results = [r]
    else:
        # Use thread pool (backends may not be process-safe on MPS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, len(chunks))) as ex:
            futures = [ex.submit(_run_one_chunk, file_path, be, off, dur, language, params) for off, dur in chunks]
            chunk_results = [f.result() for f in concurrent.futures.as_completed(futures)]
        # Re-sort by start (as_completed loses order)
        chunk_results.sort(key=lambda r: r["segments"][0]["start"] if r["segments"] else 0)

    # Merge
    all_segments = []
    full_texts = []
    detected_lang = None
    lang_prob = None
    for r in chunk_results:
        all_segments.extend(r["segments"])
        if r["full_text"]:
            full_texts.append(r["full_text"])
        if detected_lang is None:
            detected_lang = r["language"]
            lang_prob = r["language_probability"]

    # Dedup boundary overlaps: drop segments whose start < previous chunk's last end
    deduped = []
    last_end = -1.0
    for seg in sorted(all_segments, key=lambda s: (s["start"], s["end"])):
        if seg["start"] < last_end - 1e-6 and deduped:
            # likely duplicate boundary; skip if identical text to last
            if seg["text"] == deduped[-1]["text"]:
                continue
        deduped.append(seg)
        last_end = max(last_end, seg["end"])
    all_segments = deduped

    full_text = " ".join(full_texts)

    first_start = chunks[0][0]
    last_end_total = chunks[-1][0] + (chunks[-1][1] or 0)

    result = {
        "file_path": str(Path(file_path).expanduser().resolve()),
        "backend": be.name,
        "model": model_size,
        "device": getattr(be, "device", None),
        "compute_type": getattr(be, "compute_type", None),
        "language": detected_lang,
        "language_probability": lang_prob,
        "start_seconds": first_start,
        "end_seconds": last_end_total,
        "duration_seconds": total_duration,
        "segment_count": len(all_segments),
        "full_text": full_text,
        "segments": all_segments,
        "chunks": len(chunks),
        "workers": min(workers, len(chunks)),
        "cache_hit": False,
    }
    save(key, result)
    return result
