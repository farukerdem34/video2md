import time

import pytest

import video2md.jobs as jobs


def test_job_state_machine(monkeypatch):
    monkeypatch.setattr(jobs, "transcribe", lambda **kw: {"full_text": "ok", "segments": []})
    jid = jobs.submit(file_path="/tmp/x.wav")
    assert jobs.status(jid)["state"] in ("queued", "running", "done")
    for _ in range(50):
        st = jobs.status(jid)
        if st["state"] == "done":
            break
        time.sleep(0.05)
    assert jobs.status(jid)["state"] == "done"
    assert jobs.status(jid)["result"]["full_text"] == "ok"


def test_job_cancel(monkeypatch):
    def slow(**kw):
        time.sleep(0.5)
        return {"full_text": "ok", "segments": []}

    monkeypatch.setattr(jobs, "transcribe", slow)
    jid = jobs.submit(file_path="/tmp/x.wav")
    time.sleep(0.05)
    assert jobs.cancel(jid) is True
    # state should not flip back to done
    time.sleep(0.7)
    assert jobs.status(jid)["state"] in ("cancelled", "running")


def test_cache_collision(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO2MD_CACHE_DIR", str(tmp_path))
    import importlib

    import video2md.cache as c

    importlib.reload(c)
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    # same size, same first/last bytes, different middle
    head = b"A" * 1024
    tail = b"Z" * 1024
    f1.write_bytes(head + b"1" * 1000 + tail)
    f2.write_bytes(head + b"2" * 1000 + tail)
    k1 = c.cache_key(str(f1), "faster-whisper", "base", "en", {"a": 1})
    k2 = c.cache_key(str(f2), "faster-whisper", "base", "en", {"a": 1})
    assert k1 != k2
