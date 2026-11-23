# video2md

An MCP server that turns video/audio files into transcripts and metadata,
so an agent (e.g. Claude Code) can write reports in Markdown, LaTeX, HTML, etc.

## Tools exposed

- `get_media_info(file_path)` — duration, codecs, streams, size.
- `extract_audio(file_path, output_path?)` — extract audio to 16kHz mono WAV.
- `transcribe(...)` — timestamped transcript. Backends: mlx-whisper (macOS arm64), faster-whisper (cross-platform), openai (cloud). Auto-chunks files > 10 min. Raw Whisper params exposed.
- `list_backends()` — available backends.
- `cache_clear()` — clear transcript cache.
- `get_report_template(format)` — Markdown/LaTeX report skeleton (`markdown`/`md`, `latex`/`tex`).
- `submit_transcription(...)` / `get_job_status(job_id)` / `cancel_job(job_id)` — async jobs for long files.

## Run with uvx

From a local checkout:

```bash
uvx --from . video2md
```

Without cloning (from GitHub, before/without PyPI publishing):

```bash
uvx --from git+https://github.com/<OWNER>/video2md video2md
```

After publishing to PyPI:

```bash
uvx video2md
```

## Claude Code plugin

This repository is also a Claude Code plugin: it bundles the `video2md` MCP server,
reporter personas (skills/agents), and the `/video2md:latex` and `/video2md:markdown`
commands.

Load it for a session:

```bash
claude --plugin-dir /path/to/video2md
```

Or install from a marketplace once published:

```text
/plugin install video2md --marketplace farukerdem34/video2md
```

Then run:

```text
/video2md:latex input.mp4
/video2md:markdown input.webm
```

## Claude Code integration

Add to your MCP config (e.g. `~/.claude.json` or project `.mcp.json`).

Local checkout:

```json
{
  "mcpServers": {
    "video2md": {
      "command": "uvx",
      "args": ["--from", "/path/to/video2md", "video2md"]
    }
  }
}
```

Without cloning (GitHub source):

```json
{
  "mcpServers": {
    "video2md": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/<OWNER>/video2md", "video2md"]
    }
  }
}
```

Published package:

```json
{
  "mcpServers": {
    "video2md": {
      "command": "uvx",
      "args": ["video2md"]
    }
  }
}
```

Then ask Claude Code: "Write a summary report from /path/to/video.mp4 (or .webm, .mkv, .mov, ...) in Markdown."
The agent will call `get_media_info` and `transcribe`, then write the report.

Report skeletons are available via the `get_report_template(format)` tool
(`markdown`/`md` or `latex`/`tex`) and as files under `templates/`.

## Large files

For files of hundreds of MB (hours of audio), transcribe in chunks to keep memory
and context small:

```
transcribe(path, start_seconds=0, end_seconds=600)
transcribe(path, start_seconds=600, end_seconds=1200)
...
```

Segment timestamps are returned in absolute seconds. VAD filtering is on by default.

## Environment variables

- `VIDEO2MD_BACKEND` — `auto`/`mlx-whisper`/`faster-whisper`/`whisper-cpp`/`openai` (default: `auto`).
- `VIDEO2MD_MODEL` — default whisper model size (default: `base`).
- `VIDEO2MD_DEVICE` — `auto`/`cpu`/`cuda`/`mps` (default: `auto`).
- `VIDEO2MD_COMPUTE_TYPE` — compute type (default: `auto`).
- `VIDEO2MD_WORKERS` — parallel workers (default: cpu_count-1).
- `VIDEO2MD_CHUNK_SECONDS` — chunk size for auto-chunking (default: 300).
- `VIDEO2MD_CACHE_DIR` — cache location.
- `OPENAI_API_KEY` — for the openai backend.

## Development

```bash
uv sync
uv run video2md
```
