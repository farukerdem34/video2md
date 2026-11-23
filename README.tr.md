# video2md

Video/ses dosyalarını MCP sunucusu aracılığıyla transkript ve rapora (Markdown veya LaTeX) dönüştürür.

## Hızlı başlangıç

```bash
uvx --from git+https://github.com/farukerdem34/video2md video2md
```

MCP istemci yapılandırmanıza ekleyin (`~/.claude.json`, `.mcp.json` veya `opencode.jsonc`):

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

Ardından ajanınıza sorun: *" /path/to/video.mp4 dosyasından Markdown rapor yaz"* — ajan `get_media_info` ve `transcribe` çağırır, ardından raporu yazar.

## Claude Code eklentisi

```bash
claude --plugin-dir /path/to/video2md
# veya
claude plugin marketplace add farukerdem34/video2md
claude plugin install video2md@video2md-marketplace
```
Komutlar: `/video2md:latex input.mp4`, `/video2md:markdown input.webm`.

## OpenCode

Eklentiyi CLI ile kurun:

```bash
opencode plugin add farukerdem34/video2md
```

Bu komut `video2md` MCP sunucusunu ve skills, commands, agents'ı kaydeder. Ya da depoyu OpenCode'da açın; `.opencode/` paketi otomatik yüklenir.

## Belgeler

- İngilizce detaylı rehber: [docs/guide.md](docs/guide.md)
- Türkçe detaylı rehber: [docs/guide.tr.md](docs/guide.tr.md)
- İngilizce hızlı başlangıç: [README.md](README.md)
