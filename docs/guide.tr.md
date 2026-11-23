# video2md — Detaylı Rehber (Türkçe)

## Genel bakış

`video2md`, video/ses dosyalarını transkript ve meta veriye dönüştüren bir MCP
sunucusudur; böylece bir ajan (Claude Code, OpenCode vb.) Markdown, LaTeX, HTML
ve diğer formatlarda rapor yazabilir.

## Sunulan araçlar

- `get_media_info(file_path)` — süre, codec'ler, akışlar, boyut.
- `extract_audio(file_path, output_path?, start?, duration?)` — sesi 16kHz mono WAV olarak çıkarır.
- `transcribe(...)` — zaman damgalı transkript. Backend'ler: mlx-whisper (macOS arm64), faster-whisper (çapraz platform), openai (bulut). 10 dk üzeri dosyaları otomatik böler. Ham Whisper parametreleri açıktır.
- `list_backends()` — kullanılabilir backend'ler.
- `cache_clear()` — transkript önbelleğini temizler.
- `get_report_template(format)` — Markdown/LaTeX rapor iskeleti (`markdown`/`md`, `latex`/`tex`).
- `submit_transcription(...)` / `get_job_status(job_id)` / `cancel_job(job_id)` — uzun dosyalar için asenkron işler.

## Çalıştırma

Yerel checkout:

```bash
uvx --from . video2md
```

GitHub'dan (clone olmadan):

```bash
uvx --from git+https://github.com/farukerdem34/video2md video2md
```

PyPI yayınından sonra:

```bash
uvx video2md
```

Geliştirme:

```bash
uv sync
uv run video2md
```

## MCP istemci yapılandırması

### Claude Code (`~/.claude.json` veya proje `.mcp.json`)

Yerel checkout:

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

GitHub'dan:

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

Yayınlanmış paket:

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

## Büyük dosyalar

Yüzlerce MB'lık (saatlerce ses) dosyalar için bellek ve bağlamı küçük tutmak
adına parçalar halinde transkript alın:

```
transcribe(path, start_seconds=0, end_seconds=600)
transcribe(path, start_seconds=600, end_seconds=1200)
...
```

Segment zaman damgaları mutlak saniye cinsindendir. VAD filtreleme varsayılan
olarak açıktır. Çok uzun dosyalar için `submit_transcription` + `get_job_status`
tercih edin.

## Ortam değişkenleri

- `VIDEO2MD_BACKEND` — `auto`/`mlx-whisper`/`faster-whisper`/`whisper-cpp`/`openai` (varsayılan: `auto`).
- `VIDEO2MD_MODEL` — varsayılan whisper model boyutu (varsayılan: `base`).
- `VIDEO2MD_DEVICE` — `auto`/`cpu`/`cuda`/`mps` (varsayılan: `auto`).
- `VIDEO2MD_COMPUTE_TYPE` — hesaplama türü (varsayılan: `auto`).
- `VIDEO2MD_WORKERS` — paralel worker sayısı (varsayılan: cpu_count-1).
- `VIDEO2MD_CHUNK_SECONDS` — otomatik bölmek için chunk boyutu (varsayılan: 300).
- `VIDEO2MD_CACHE_DIR` — önbellek konumu.
- `OPENAI_API_KEY` — openai backend için.

## Rapor oluşturma

1. Süre, format ve akışları öğrenmek için `get_media_info` çağırın.
2. `transcribe` çağırın (uzunluğa göre model boyutu seçin; varsayılan `base`, doğruluk için `small`/`medium`). Biliniyorsa `language` geçin.
3. Transkripti dikkatle okuyun. Yapı belirleyin: konular, bölümler, temel noktalar, kararlar, eylem maddeleri, korunmaya değer alıntılar.
4. `get_report_template("markdown"|"latex")` ile iskelet alın, çıktı yoluna kopyalayın ve tüm `{{PLACEHOLDER}}` değerlerini doldurun. Verilen bölüm sırasını koruyun.
5. Raporu çıktı yoluna yazın. Başlık, kaynak dosya, süre, üretilme tarihi, yönetici özeti (3-5 cümle), bölümlenmiş gövde, temel çıkarımlar, eylem maddeleri, zaman damgalı dikkate değer alıntılar ve transkript eki dahil edin.
6. Raporu transkripte sadık tutun; olgu uydurmayın. Anlaşılmayan kısımları `[inaudible]` olarak işaretleyin.

Zaman damgaları `mm:ss` biçiminde. Uzun dosyalar (> ~30 dk): parçalar halinde transkript alın.

### Format kuralları

- Markdown: YAML front matter korunur; ATX başlıklar; eylem maddeleri ve transkript satırları için GFM tabloları; uzun transkriptler `<details>` içinde; alıntılar için `>` blockquote.
- LaTeX: transkript diline uygun `babel` dili seçin (varsayılan `english`); özel karakterleri escape edin; dosya yolları için `\texttt{}`; birimleri matematik modunda tutun; `\tableofcontents` korunur; TeX motoru varsa derlemeyi doğrulayın.

## Claude Code eklentisi

Bu depo ayrıca MCP sunucusunu, raporcu personallerini (skills/agents) ve
`/video2md:latex` & `/video2md:markdown` komutlarını içeren bir Claude Code
eklentisidir.

Oturum için yükleme:

```bash
claude --plugin-dir /path/to/video2md
```

Marketplace'ten kurulum:

```text
claude plugin marketplace add farukerdem34/video2md
claude plugin install video2md@video2md-marketplace
```

Ardından çalıştırın:

```text
/video2md:latex input.mp4
/video2md:markdown input.webm
```

## OpenCode paketi

Depo `.opencode/` altında bir OpenCode paketi (skills, commands, agents, MCP
yapılandırması) içerir. Depoyu OpenCode'da açtığınızda paket otomatik
yüklenir. Komutlar: `/latex`, `/markdown`. Skills: `reporter`,
`latex-specialist`, `markdown-specialist`, `transcriber`.

## Geliştirme

```bash
uv sync
uv run video2md
```

Testler:

```bash
uv run pytest
```
