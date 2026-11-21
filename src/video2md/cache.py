"""Content-addressed transcript cache."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

CACHE_DIR = Path(os.environ.get("VIDEO2MD_CACHE_DIR", str(Path.home() / ".cache" / "video2md")))
TRANSCRIPT_DIR = CACHE_DIR / "transcripts"


def _file_fingerprint(path: str, full: bool = False) -> str:
    p = Path(path)
    size = p.stat().st_size
    h = hashlib.sha256()
    h.update(str(size).encode())
    if full:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    else:
        # hash first + last 1MB + size
        with open(path, "rb") as f:
            h.update(f.read(1 << 20))
            if size > (1 << 20):
                f.seek(max(0, size - (1 << 20)))
                h.update(f.read(1 << 20))
    return h.hexdigest()[:16]


def cache_key(file_path: str, backend: str, model: str, language, params: Any, full_hash: bool = False) -> str:
    params_str = repr(params)
    fp = _file_fingerprint(file_path, full=full_hash)
    raw = f"{fp}|{backend}|{model}|{language}|{params_str}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def load(key: str) -> dict[str, Any] | None:
    p = TRANSCRIPT_DIR / f"{key}.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def save(key: str, value: dict[str, Any]) -> None:
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    (TRANSCRIPT_DIR / f"{key}.json").write_text(json.dumps(value))


def clear() -> int:
    if not TRANSCRIPT_DIR.exists():
        return 0
    n = 0
    for p in TRANSCRIPT_DIR.glob("*.json"):
        try:
            p.unlink()
            n += 1
        except Exception:
            pass
    return n
