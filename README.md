# video2md

An MCP server that turns video/audio files into transcripts and metadata,
so an agent (e.g. Claude Code) can write reports in Markdown, LaTeX, HTML, etc.

## Tools exposed

- `get_media_info(file_path)` — duration, codecs, streams, size.
- `extract_audio(file_path, output_path?)` — extract audio to 16kHz mono WAV.
- `transcribe(file_path, model_size?, language?, start_seconds?, end_seconds?, vad_filter?)` — timestamped transcript via faster-whisper. Supports chunking for long files.

## Run with uvx

```bash
uvx --from . video2md
```

Or after publishing:

```bash
uvx video2md
```

## Claude Code integration

Add to your MCP config (e.g. `~/.claude.json` or project `.mcp.json`):

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

Then ask Claude Code: "Write a summary report from /path/to/video.mp4 in Markdown."
The agent will call `get_media_info` and `transcribe`, then write the report.

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

- `VIDEO2MD_MODEL` — default whisper model size (default: `base`).
- `VIDEO2MD_DEVICE` — `auto`/`cpu`/`cuda` (default: `auto`).
- `VIDEO2MD_COMPUTE_TYPE` — compute type (default: `auto`).

## Development

```bash
uv sync
uv run video2md
```
