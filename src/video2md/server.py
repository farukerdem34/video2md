"""MCP server exposing media tools."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from . import __version__
from .backends.registry import available_backends, create_backend
from .cache import clear as _cache_clear
from .jobs import cancel as _cancel_job
from .jobs import status as _job_status
from .jobs import submit as _submit_job
from .media import extract_audio as _extract_audio
from .media import get_media_info as _get_media_info
from .transcribe import transcribe as _transcribe

mcp = MCPServer(
    name="video2md",
    version=__version__,
    instructions=(
        "Tools for inspecting and transcribing video/audio files. "
        "Use get_media_info first, then transcribe to obtain a timestamped transcript. "
        "For long files, transcribe auto-chunks; or pass start_seconds/end_seconds. "
        "Backends: mlx-whisper (macOS arm64), faster-whisper (cross-platform CPU), "
        "openai (cloud). Transcription runs locally by default."
    ),
)


@mcp.tool()
def get_media_info(file_path: str) -> dict:
    """Return metadata (duration, codecs, streams, size) for a video or audio file.

    Args:
        file_path: Absolute or relative path to a media file.
    """
    return _get_media_info(file_path)


@mcp.tool()
def extract_audio(file_path: str, output_path: str | None = None, start: float | None = None, duration: float | None = None) -> dict:
    """Extract the audio track from a media file to a 16kHz mono WAV file.

    Args:
        file_path: Path to a video or audio file.
        output_path: Optional destination WAV path. Defaults to a cache dir.
        start: Start offset in seconds (optional).
        duration: Duration in seconds (optional).
    """
    out = _extract_audio(file_path, output_path, start=start, duration=duration)
    return {"input_path": file_path, "output_path": out}


@mcp.tool()
def list_backends() -> dict:
    """List available transcription backends on this machine."""
    return {"backends": available_backends()}


@mcp.tool()
def cache_clear() -> dict:
    """Clear the transcript cache. Returns number of files removed."""
    return {"removed": _cache_clear()}


@mcp.tool()
def submit_transcription(
    file_path: str,
    model_size: str = "base",
    language: str | None = None,
    backend: str | None = None,
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    vad_filter: bool = True,
    workers: int | None = None,
    force: bool = False,
    beam_size: int = 5,
    best_of: int = 5,
    patience: float = 1.0,
    length_penalty: float = 1.0,
    repetition_penalty: float = 1.0,
    no_repeat_ngram_size: int = 0,
    temperature: float = 0.0,
    compression_ratio_threshold: float = 2.4,
    log_prob_threshold: float = -1.0,
    no_speech_threshold: float = 0.6,
    condition_on_previous_text: bool = True,
    prompt_reset_on_temperature: float = 0.5,
    initial_prompt: str | None = None,
    prefix: str | None = None,
    suppress_blank: bool = True,
    without_timestamps: bool = False,
    max_initial_timestamp: float = 1.0,
    word_timestamps: bool = False,
    multilingual: bool = False,
    max_new_tokens: int | None = None,
    chunk_length: int = 30,
    clip_timestamps: str = "0",
    hallucination_silence_threshold: float | None = None,
    hotwords: str | None = None,
) -> dict:
    """Submit a transcription job to run in the background. Returns a job_id.

    Poll with get_job_status(job_id). Use for long files to avoid timeouts.
    Accepts the same parameters as transcribe.
    """
    job_id = _submit_job(
        file_path=file_path,
        model_size=model_size,
        language=language,
        backend=backend,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        vad_filter=vad_filter,
        workers=workers,
        force=force,
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
        without_timestamps=without_timestamps,
        max_initial_timestamp=max_initial_timestamp,
        word_timestamps=word_timestamps,
        multilingual=multilingual,
        max_new_tokens=max_new_tokens,
        chunk_length=chunk_length,
        clip_timestamps=clip_timestamps,
        hallucination_silence_threshold=hallucination_silence_threshold,
        hotwords=hotwords,
    )
    return {"job_id": job_id}


@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """Get status of a background transcription job."""
    return _job_status(job_id)


@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """Cancel a queued/running background transcription job."""
    return {"cancelled": _cancel_job(job_id)}


@mcp.tool()
def transcribe(
    file_path: str,
    model_size: str = "base",
    language: str | None = None,
    backend: str | None = None,
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    vad_filter: bool = True,
    workers: int | None = None,
    force: bool = False,
    beam_size: int = 5,
    best_of: int = 5,
    patience: float = 1.0,
    length_penalty: float = 1.0,
    repetition_penalty: float = 1.0,
    no_repeat_ngram_size: int = 0,
    temperature: float = 0.0,
    compression_ratio_threshold: float = 2.4,
    log_prob_threshold: float = -1.0,
    no_speech_threshold: float = 0.6,
    condition_on_previous_text: bool = True,
    prompt_reset_on_temperature: float = 0.5,
    initial_prompt: str | None = None,
    prefix: str | None = None,
    suppress_blank: bool = True,
    without_timestamps: bool = False,
    max_initial_timestamp: float = 1.0,
    word_timestamps: bool = False,
    multilingual: bool = False,
    max_new_tokens: int | None = None,
    chunk_length: int = 30,
    clip_timestamps: str = "0",
    hallucination_silence_threshold: float | None = None,
    hotwords: str | None = None,
) -> dict:
    """Transcribe speech in a video or audio file into timestamped segments.

    Backends: mlx-whisper (macOS arm64), faster-whisper (cross-platform), openai (cloud).
    Auto-chunks files longer than 10 minutes. Pass start_seconds/end_seconds for manual chunks.
    """
    return _transcribe(
        file_path,
        model_size=model_size,
        language=language,
        backend=backend,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        vad_filter=vad_filter,
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
        without_timestamps=without_timestamps,
        max_initial_timestamp=max_initial_timestamp,
        word_timestamps=word_timestamps,
        multilingual=multilingual,
        max_new_tokens=max_new_tokens,
        chunk_length=chunk_length,
        clip_timestamps=clip_timestamps,
        hallucination_silence_threshold=hallucination_silence_threshold,
        hotwords=hotwords,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
