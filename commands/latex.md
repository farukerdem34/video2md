---
description: Generate a LaTeX report from a video or audio file. Usage: /video2md:latex <input-media> [output.tex]
argument-hint: <input-media> [output.tex]
---

You are running the video2md LaTeX report workflow.

Adopt the `reporter` and `latex-specialist` personas, and delegate writing to the
`latex-writer` subagent when appropriate.

Arguments: $ARGUMENTS
- First token: input media file path.
- Second token (optional): output `.tex` path. Default to `<input basename without extension>.tex` next to the input.

Follow the report generation prompt at `${CLAUDE_PLUGIN_ROOT}/prompts/report_prompt.md`
with format = `latex`, then:

1. Call `get_media_info` on the input.
2. Call `transcribe` (model size by length: `base` default, `small`/`medium` for accuracy; pass `language` if known). For files over ~30 min, chunk with `start_seconds`/`end_seconds` and merge.
3. Read the transcript; identify topics, sections, key points, decisions, action items, notable quotes.
4. Fetch a skeleton with `get_report_template("latex")`, copy to the output path, replace every `{{PLACEHOLDER}}`.
5. Write the report to the output path. Include title, source, duration, generated date, executive summary, sectioned body, key takeaways, action items, notable quotes with timestamps, transcript appendix.
6. If a TeX engine is available, compile and verify; fix errors.

Constraints:
- Timestamps in `mm:ss`.
- Escape LaTeX special characters; use `\texttt{}` for file paths; units in math mode.
- Keep `\tableofcontents`.
- Faithful to the transcript; mark unclear passages `[inaudible]`.
