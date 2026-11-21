# Report generation prompt template

Use this prompt (or adapt) when asking Claude Code to generate a report from a media file.

---

You have access to the `video2md` MCP server with tools:
- `get_media_info(file_path)` — metadata about the file.
- `transcribe(file_path, model_size?, language?)` — timestamped transcript.
- `get_report_template(format)` — starter skeleton for a Markdown or LaTeX report.

Task: produce a report from the media file at `<PATH>` in `<FORMAT>` (markdown/latex/html).

Steps:
1. Call `get_media_info` to learn duration, format, streams.
2. Call `transcribe` (choose model size based on length; `base` default, `small`/`medium` for accuracy). Pass `language` if known.
3. Read the transcript carefully. Identify structure: topics, sections, key points, decisions, action items, quotes worth preserving.
4. Fetch a skeleton with `get_report_template("<FORMAT>")` (markdown or latex) and copy it to `<OUTPUT_PATH>`, then fill in every `{{PLACEHOLDER}}`. Keep the provided section order.
5. Write the report to `<OUTPUT_PATH>` using your file-writing tool. Include:
   - Title, source file, duration, generated date.
   - Executive summary (3-5 sentences).
   - Sectioned body with headings derived from the transcript.
   - Key takeaways / action items (if applicable).
   - Notable quotes with timestamps.
6. Keep the report faithful to the transcript; do not invent facts. Mark unclear passages as "[inaudible]".

Constraints:
- Timestamps in `mm:ss` form.
- If the file is very long (> ~30 min), transcribe in chunks: call transcribe with start_seconds/end_seconds windows (e.g. 600s) and merge the segments. Timestamps are absolute.
- Prefer the user's requested format; default to Markdown.

Format-specific rules:
- Markdown: keep the YAML front matter block; use ATX headings (`#`, `##`); use GFM tables for action items and transcript rows; put long transcripts inside a `<details>` block; use `>` blockquotes for quotes.
- LaTeX: choose the `babel` language to match the transcript (default `english`); escape special characters (`\ & % $ # _ { } ~ ^`) in substituted text, using `\texttt{}` for file paths; keep units in math mode (e.g. `$\sim$600`); verify the document compiles if a TeX engine is available; keep `\tableofcontents`.
- Consistent section order: metadata → executive summary → body sections → key takeaways → action items → notable quotes → transcript appendix.