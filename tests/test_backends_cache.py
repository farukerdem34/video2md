import os
import tempfile

from video2md.backends.registry import available_backends, create_backend
from video2md.cache import cache_key, clear, load, save


def test_available_backends():
    bs = available_backends()
    assert "faster-whisper" in bs


def test_create_backend_default():
    b = create_backend(None)
    assert b.name in ("mlx-whisper", "faster-whisper")


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO2MD_CACHE_DIR", str(tmp_path))
    import importlib
    import video2md.cache as c

    importlib.reload(c)
    f = tmp_path / "media.bin"
    f.write_bytes(b"hello")
    key = c.cache_key(str(f), "faster-whisper", "base", "en", {"a": 1})
    assert c.load(key) is None
    c.save(key, {"x": 1})
    assert c.load(key) == {"x": 1}
    assert c.clear() == 1
    assert c.load(key) is None
