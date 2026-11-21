# video2md design

**Date:** 2026-11-21
**Status:** Approved (implementation complete)

## Intent

Generate reports from video/audio files by combining code (media processing) with an
agent (Claude Code). The code exposes media capabilities as MCP tools; the agent
orchestrates them and writes the report in the requested format (Markdown, LaTeX,
HTML, ...).

## Goals

- MCP server runnable via `uvx` exposing `get_media_info`, `extract_audio`, `transcribe`.
- Local transcription via faster-whisper (no API key).
- Support common video/audio formats via ffmpeg.
- Agent-friendly tool descriptions and a report prompt template.

## Non-goals (v1)

- Frame/screenshot extraction.
- Speaker diarization, word-level timestamps.
- Built-in report formatting (agent writes the file).
- Cloud transcription backends.

## Approaches considered

1. **MCP server first (chosen):** Python package with FastMCP/MCPServer. Agent is
   the orchestrator. Smallest coherent unit; matches the requested workflow.
2. CLI first: standalone pipeline calling an LLM API. Rejected: duplicates agent
   orchestration and loses Claude Code integration.
3. Both equally: more scope than needed for v1.

## Architecture

- `src/video2md/media.py` — ffmpeg/ffprobe helpers.
- `src/video2md/transcribe.py` — faster-whisper wrapper; always extracts audio to
  WAV first, loads as float32 ndarray (avoids PyAV version issues), prefers MPS on
  Apple Silicon.
- `src/video2md/server.py` — MCPServer registration + `main()`.
- Packaging: hatchling, src layout, console script `video2md`.

## Key decisions

- Pin `mcp>=2.3,<3`, `faster-whisper>=1.2`, Python `>=3.10,<3.13`.
- Extract audio always (robust decoding) instead of relying on PyAV.
- Default model `base`; env overrides `VIDEO2MD_MODEL/DEVICE/COMPUTE_TYPE`.
- Cache extracted WAVs in `~/.cache/video2md`.

## Open items

- Publish to PyPI for bare `uvx video2md`.
- v2: frame extraction, diarization.
