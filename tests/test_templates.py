import pytest

from video2md.templates import get_template


def test_markdown_template():
    t = get_template("markdown")
    assert t.strip()
    assert "{{TITLE}}" in t
    assert "---" in t  # front matter


def test_md_alias():
    assert get_template("md") == get_template("markdown")


def test_latex_template():
    t = get_template("latex")
    assert t.strip()
    assert "\\documentclass" in t
    assert "{{TITLE}}" in t


def test_tex_alias():
    assert get_template("tex") == get_template("latex")


def test_unknown_format():
    with pytest.raises(ValueError):
        get_template("html")