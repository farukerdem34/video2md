# video2md

Turn video/audio files into transcripts and reports (Markdown or LaTeX) via an MCP server.

## Quick start

```bash
uvx --from git+https://github.com/farukerdem34/video2md video2md
```

Add to your MCP client config (`~/.claude.json`, `.mcp.json`, or `opencode.jsonc`):

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

Then ask your agent: *"Write a Markdown report from /path/to/video.mp4"* — it calls `get_media_info` and `transcribe`, then writes the report.

## Claude Code plugin

```bash
claude --plugin-dir /path/to/video2md
# or
claude plugin marketplace add farukerdem34/video2md
claude plugin install video2md@video2md-marketplace
```
Commands: `/video2md:latex input.mp4`, `/video2md:markdown input.webm`.

## OpenCode

Install the plugin via CLI:

```bash
opencode plugin add farukerdem34/video2md
```

This registers the `video2md` MCP server plus skills, commands, and agents. Or open the repo in OpenCode and the `.opencode/` bundle loads automatically.

## Documentation

- English detailed guide: [docs/guide.md](docs/guide.md)
- Turkish detailed guide: [docs/guide.tr.md](docs/guide.tr.md)
- Turkish quick start: [README.tr.md](README.tr.md)
