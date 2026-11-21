# video2md

An MCP server that turns video/audio files into transcripts and metadata,
so an agent (e.g. Claude Code) can write reports in Markdown, LaTeX, HTML, etc.

## Tools exposed

- `get_media_info(file_path)` — duration, codecs, streams, size.
- `extract_audio(file_path, output_path?)` — extract audio to 16kHz mono WAV.
- `transcribe(file_path, model_size?, language?)` — timestamped transcript via faster-whisper.

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

## Environment variables

- `VIDEO2MD_MODEL` — default whisper model size (default: `base`).
- `VIDEO2MD_DEVICE` — `auto`/`cpu`/`cuda` (default: `auto`).
- `VIDEO2MD_COMPUTE_TYPE` — compute type (default: `auto`).

## Development

```bash
uv sync
uv run video2md
```
