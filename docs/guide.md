# video2md — Detailed Guide (English)

## Overview

`video2md` is an MCP server that turns video/audio files into transcripts and
metadata, so an agent (Claude Code, OpenCode, etc.) can write reports in
Markdown, LaTeX, HTML, and other formats.

## Tools exposed

- `get_media_info(file_path)` — duration, codecs, streams, size.
- `extract_audio(file_path, output_path?, start?, duration?)` — extract audio to 16kHz mono WAV.
- `transcribe(...)` — timestamped transcript. Backends: mlx-whisper (macOS arm64), faster-whisper (cross-platform), openai (cloud). Auto-chunks files > 10 min. Raw Whisper params exposed.
- `list_backends()` — available backends.
- `cache_clear()` — clear transcript cache.
- `get_report_template(format)` — Markdown/LaTeX report skeleton (`markdown`/`md`, `latex`/`tex`).
- `submit_transcription(...)` / `get_job_status(job_id)` / `cancel_job(job_id)` — async jobs for long files.

## Running

Local checkout:

```bash
uvx --from . video2md
```

From GitHub (no clone):

```bash
uvx --from git+https://github.com/farukerdem34/video2md video2md
```

After PyPI publishing:

```bash
uvx video2md
```

Development:

```bash
uv sync
uv run video2md
```

## MCP client configuration

### Claude Code (`~/.claude.json` or project `.mcp.json`)

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

From GitHub:

```json
{
  "mcpServers": {
    "video2md": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/farukerdem34/video2md", "video2md"]
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

### OpenCode (`opencode.jsonc`)

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "video2md": {
        "type": "local",
        "command": ["uvx", "--from", ".", "video2md"],
      "protocol": "legacy"
      }
    }
  }
}
```

## Large files

For files of hundreds of MB (hours of audio), transcribe in chunks to keep
memory and context small:

```
transcribe(path, start_seconds=0, end_seconds=600)
transcribe(path, start_seconds=600, end_seconds=1200)
...
```

Segment timestamps are returned in absolute seconds. VAD filtering is on by
default. Prefer `submit_transcription` + `get_job_status` for very long files.

## Environment variables

- `VIDEO2MD_BACKEND` — `auto`/`mlx-whisper`/`faster-whisper`/`whisper-cpp`/`openai` (default: `auto`).
- `VIDEO2MD_MODEL` — default whisper model size (default: `base`).
- `VIDEO2MD_DEVICE` — `auto`/`cpu`/`cuda`/`mps` (default: `auto`).
- `VIDEO2MD_COMPUTE_TYPE` — compute type (default: `auto`).
- `VIDEO2MD_WORKERS` — parallel workers (default: cpu_count-1).
- `VIDEO2MD_CHUNK_SECONDS` — chunk size for auto-chunking (default: 300).
- `VIDEO2MD_CACHE_DIR` — cache location.
- `OPENAI_API_KEY` — for the openai backend.

## Report generation

1. Call `get_media_info` to learn duration, format, streams.
2. Call `transcribe` (choose model size by length; `base` default, `small`/`medium` for accuracy). Pass `language` if known.
3. Read the transcript carefully. Identify structure: topics, sections, key points, decisions, action items, quotes worth preserving.
4. Fetch a skeleton with `get_report_template("markdown"|"latex")` and copy it to the output path, then fill in every `{{PLACEHOLDER}}`. Keep the provided section order.
5. Write the report to the output path. Include title, source file, duration, generated date, executive summary (3-5 sentences), sectioned body, key takeaways, action items, notable quotes with timestamps, transcript appendix.
6. Keep the report faithful to the transcript; do not invent facts. Mark unclear passages as `[inaudible]`.

Timestamps in `mm:ss` form. Long files (> ~30 min): transcribe in chunks.

### Format-specific rules

- Markdown: keep YAML front matter; ATX headings; GFM tables for action items and transcript rows; long transcripts in `<details>`; `>` blockquotes for quotes.
- LaTeX: choose `babel` language to match transcript (default `english`); escape special characters; use `\texttt{}` for file paths; keep units in math mode; keep `\tableofcontents`; verify compilation if a TeX engine is available.

## Claude Code plugin

This repository is also a Claude Code plugin bundling the MCP server, reporter
personas (skills/agents), and `/video2md:latex` & `/video2md:markdown` commands.

Load for a session:

```bash
claude --plugin-dir /path/to/video2md
```

Install from marketplace:

```text
claude plugin marketplace add farukerdem34/video2md
claude plugin install video2md@video2md-marketplace
```

Then run:

```text
/video2md:latex input.mp4
/video2md:markdown input.webm
```

## OpenCode

Install the plugin via CLI:

```bash
opencode plugin add farukerdem34/video2md
```

This registers the `video2md` MCP server (with `protocol: legacy`) plus skills,
commands, and agents. Or open the repo in OpenCode and the `.opencode/` bundle
loads automatically. Commands: `/latex`, `/markdown`. Skills: `reporter`,
`latex-specialist`, `markdown-specialist`, `transcriber`.

## Development

```bash
uv sync
uv run video2md
```

Tests:

```bash
uv run pytest
```
