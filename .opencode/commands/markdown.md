---
description: Generate a Markdown report from a video or audio file. Usage: /markdown <input-media> [output.md]
---

You are running the video2md Markdown report workflow.

Adopt the `reporter` and `markdown-specialist` personas, and delegate writing to the
`markdown-writer` subagent when appropriate.

Arguments: $ARGUMENTS
- First token: input media file path.
- Second token (optional): output `.md` path. Default to `<input basename without extension>.md` next to the input.

Follow the report generation prompt at `prompts/report_prompt.md`
with format = `markdown`, then:

1. Call `get_media_info` on the input.
2. Call `transcribe` (model size by length: `base` default, `small`/`medium` for accuracy; pass `language` if known). For files over ~30 min, chunk with `start_seconds`/`end_seconds` and merge.
3. Read the transcript; identify topics, sections, key points, decisions, action items, notable quotes.
4. Fetch a skeleton with `get_report_template("markdown")`, copy to the output path, replace every `{{PLACEHOLDER}}`.
5. Write the report to the output path. Include title, source, duration, generated date, executive summary, sectioned body, key takeaways, action items, notable quotes with timestamps, transcript appendix (in `<details>`).

Constraints:
- Timestamps in `mm:ss`.
- Keep YAML front matter; ATX headings; GFM tables; `>` blockquotes for quotes.
- Faithful to the transcript; mark unclear passages `[inaudible]`.
