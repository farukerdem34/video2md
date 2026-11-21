"""Helpers for loading report templates bundled with the package."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

_MARKDOWN_NAMES = {"md", "markdown"}
_LATEX_NAMES = {"tex", "latex", "latex"}
_FILENAMES = {
    "markdown": "report.md",
    "latex": "report.tex",
}


def _normalize(fmt: str) -> str:
    key = fmt.strip().lower()
    if key in _MARKDOWN_NAMES:
        return "markdown"
    if key in _LATEX_NAMES:
        return "latex"
    raise ValueError(
        f"Unknown template format: {fmt!r}. "
        "Use 'markdown' (or 'md') or 'latex' (or 'tex')."
    )


def get_template(fmt: str) -> str:
    """Return the bundled report template for *fmt* (markdown or latex)."""
    kind = _normalize(fmt)
    filename = _FILENAMES[kind]

    # Prefer packaged resource
    try:
        ref = resources.files("video2md").joinpath("templates", filename)
        return ref.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        pass

    # Fallback: repo-root templates/ directory
    here = Path(__file__).resolve().parent.parent.parent
    candidate = here / "templates" / filename
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8")

    # Last resort: prompts/ directory
    alt_name = "report_template.md" if filename == "report.md" else "report_template.tex"
    candidate = here / "prompts" / alt_name
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8")

    raise FileNotFoundError(f"Template not found: {filename}")