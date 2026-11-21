"""Content-addressed transcript cache."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

CACHE_DIR = Path(os.environ.get("VIDEO2MD_CACHE_DIR", str(Path.home() / ".cache" / "video2md")))
TRANSCRIPT_DIR = CACHE_DIR / "transcripts"


def _file_fingerprint(path: str) -> str:
    # Hash the whole file. Transcription is far slower than hashing, so the
    # cost is negligible and it avoids collisions between files that only
    # differ in the middle.
    p = Path(path)
    size = p.stat().st_size
    h = hashlib.sha256()
    h.update(str(size).encode())
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def cache_key(file_path: str, backend: str, model: str, language, params: Any) -> str:
    params_str = repr(params)
    fp = _file_fingerprint(file_path)
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
    target = TRANSCRIPT_DIR / f"{key}.json"
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(value))
    os.replace(tmp, target)


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
