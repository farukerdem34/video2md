"""video2md: MCP server for turning video/audio into transcripts and metadata."""

__version__ = "0.2.0"

from .media import (
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MEDIA_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    SUPPORTED_AUDIO_EXTENSIONS,
    is_supported_media,
)
