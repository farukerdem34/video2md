"""Media helpers built on ffmpeg/ffprobe."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

CACHE_DIR = Path.home() / ".cache" / "video2md"

# Common media file extensions handled via ffmpeg/ffprobe. WebM is supported
# alongside MP4/MKV/MOV/etc.; this set is advisory (we never reject a file by
# extension, since ffmpeg is the source of truth).
SUPPORTED_VIDEO_EXTENSIONS = {
    ".mp4", ".m4v", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv",
    ".ogv", ".3gp", ".ts", ".mts", ".m2ts", ".vob",
}
SUPPORTED_AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".flac",
    ".wma", ".weba", ".aiff", ".aif", ".alac",
}
SUPPORTED_EXTENSIONS = SUPPORTED_VIDEO_EXTENSIONS | SUPPORTED_AUDIO_EXTENSIONS
SUPPORTED_MEDIA_EXTENSIONS = SUPPORTED_EXTENSIONS
MEDIA_EXTENSIONS = SUPPORTED_EXTENSIONS
VIDEO_EXTENSIONS = SUPPORTED_VIDEO_EXTENSIONS
AUDIO_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS


def is_supported_media(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def is_supported_file(path: str | Path) -> bool:
    return is_supported_media(path)


def supports_extension(ext: str) -> bool:
    if not ext.startswith("."):
        ext = "." + ext
    return ext.lower() in SUPPORTED_EXTENSIONS


def _which(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required binary '{name}' not found on PATH. Install ffmpeg.")
    return path


def get_media_info(file_path: str) -> dict[str, Any]:
    """Return metadata for a media file using ffprobe."""
    ffprobe = _which("ffprobe")
    path = Path(file_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    if path.name.startswith("-"):
        raise ValueError(f"Unsafe filename (starts with '-'): {path.name}")

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("ffprobe timed out") from e
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {proc.stderr.strip()}")

    data = json.loads(proc.stdout or "{}")
    fmt = data.get("format", {}) or {}
    streams = data.get("streams", []) or []

    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video_streams = [s for s in streams if s.get("codec_type") == "video"]

    def _dur(s: dict[str, Any]) -> float | None:
        v = s.get("duration")
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    duration = _dur(fmt)
    if duration is None and streams:
        durations = [d for d in (_dur(s) for s in streams) if d is not None]
        duration = max(durations) if durations else None

    size = None
    try:
        size = int(fmt.get("size")) if fmt.get("size") is not None else path.stat().st_size
    except (TypeError, ValueError):
        size = path.stat().st_size

    return {
        "path": str(path),
        "filename": path.name,
        "size_bytes": size,
        "duration_seconds": duration,
        "format_name": fmt.get("format_name"),
        "format_long_name": fmt.get("format_long_name"),
        "bit_rate": _int_or_none(fmt.get("bit_rate")),
        "has_audio": bool(audio_streams),
        "has_video": bool(video_streams),
        "audio_streams": [
            {
                "index": s.get("index"),
                "codec": s.get("codec_name"),
                "sample_rate": _int_or_none(s.get("sample_rate")),
                "channels": s.get("channels"),
                "channel_layout": s.get("channel_layout"),
                "duration_seconds": _dur(s),
            }
            for s in audio_streams
        ],
        "video_streams": [
            {
                "index": s.get("index"),
                "codec": s.get("codec_name"),
                "width": s.get("width"),
                "height": s.get("height"),
                "r_frame_rate": s.get("r_frame_rate"),
                "duration_seconds": _dur(s),
            }
            for s in video_streams
        ],
    }


def _int_or_none(v: Any) -> int | None:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def extract_audio(
    input_path: str,
    output_path: str | None = None,
    start: float | None = None,
    duration: float | None = None,
) -> str:
    """Extract the first audio stream to a 16kHz mono WAV file.

    If ``start``/``duration`` are given, only that slice is extracted, which keeps
    memory low for very long files.
    """
    ffmpeg = _which("ffmpeg")
    src = Path(input_path).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"File not found: {src}")
    if src.name.startswith("-"):
        raise ValueError(f"Unsafe filename (starts with '-'): {src.name}")

    if output_path is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        src_hash = hashlib.sha256(str(src).encode()).hexdigest()[:12]
        suffix = ""
        if start is not None:
            suffix = f"_{int(start)}"
        if duration is not None:
            suffix += f"_{int(duration)}"
        out = CACHE_DIR / f"{src.stem}_{src_hash}{suffix}.wav"
    else:
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [ffmpeg, "-y"]
    if start is not None and start > 0:
        cmd += ["-ss", str(start)]
    cmd += ["-i", str(src)]
    if duration is not None and duration > 0:
        cmd += ["-t", str(duration)]
    cmd += [
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(out),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("ffmpeg timed out") from e
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {proc.stderr.strip()}")
    if not out.is_file():
        raise RuntimeError("ffmpeg produced no output file")
    return str(out)



