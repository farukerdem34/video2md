"""FastMCP server exposing media tools."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from . import __version__
from .media import extract_audio as _extract_audio
from .media import get_media_info as _get_media_info
from .transcribe import transcribe as _transcribe

mcp = MCPServer(
    name="video2md",
    version=__version__,
    instructions=(
        "Tools for inspecting and transcribing video/audio files. "
        "Use get_media_info first, then transcribe to obtain a timestamped transcript. "
        "Transcription runs locally via faster-whisper; first run downloads a model."
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
def extract_audio(file_path: str, output_path: str | None = None) -> dict:
    """Extract the audio track from a media file to a 16kHz mono WAV file.

    Useful when you want to keep the WAV for reuse. Transcription does this
    automatically, so you usually do not need to call this directly.

    Args:
        file_path: Path to a video or audio file.
        output_path: Optional destination WAV path. Defaults to a cache dir.
    """
    out = _extract_audio(file_path, output_path)
    return {"input_path": file_path, "output_path": out}


@mcp.tool()
def transcribe(
    file_path: str,
    model_size: str = "base",
    language: str | None = None,
) -> dict:
    """Transcribe speech in a video or audio file into timestamped segments.

    Runs locally with faster-whisper. The first call downloads the chosen model
    (default 'base', ~150MB). Set language to an ISO-639-1 code to skip
    auto-detection (e.g. 'en', 'tr').

    Args:
        file_path: Path to a video or audio file.
        model_size: Whisper model size: tiny, base, small, medium, large-v3.
        language: Optional ISO language code. Auto-detected if omitted.
    """
    return _transcribe(file_path, model_size=model_size, language=language)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
