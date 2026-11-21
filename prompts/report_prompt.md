# Report generation prompt template

Use this prompt (or adapt) when asking Claude Code to generate a report from a media file.

---

You have access to the `video2md` MCP server with tools:
- `get_media_info(file_path)` — metadata about the file.
- `transcribe(file_path, model_size?, language?)` — timestamped transcript.

Task: produce a report from the media file at `<PATH>` in `<FORMAT>` (markdown/latex/html).

Steps:
1. Call `get_media_info` to learn duration, format, streams.
2. Call `transcribe` (choose model size based on length; `base` default, `small`/`medium` for accuracy). Pass `language` if known.
3. Read the transcript carefully. Identify structure: topics, sections, key points, decisions, action items, quotes worth preserving.
4. Write the report to `<OUTPUT_PATH>` using your file-writing tool. Include:
   - Title, source file, duration, generated date.
   - Executive summary (3-5 sentences).
   - Sectioned body with headings derived from the transcript.
   - Key takeaways / action items (if applicable).
   - Notable quotes with timestamps.
5. Keep the report faithful to the transcript; do not invent facts. Mark unclear passages as "[inaudible]".

Constraints:
- Timestamps in `mm:ss` form.
- If the file is very long, transcribe in chunks is not supported; rely on the single transcript and summarize.
- Prefer the user's requested format; default to Markdown.
