import os
import tempfile
import wave
import struct

import pytest

from video2md.media import get_media_info, extract_audio


def make_wav(path, duration=1.0, sr=16000):
    n = int(sr * duration)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(struct.pack("<" + "h" * n, *([0] * n)))


def test_get_media_info():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.wav")
        make_wav(p)
        info = get_media_info(p)
        assert info["has_audio"] is True
        assert info["has_video"] is False
        assert abs(info["duration_seconds"] - 1.0) < 0.01


def test_get_media_info_missing():
    with pytest.raises(FileNotFoundError):
        get_media_info("/no/such/file.wav")


def test_extract_audio_passthrough(tmp_path):
    p = tmp_path / "t.wav"
    make_wav(str(p))
    out = extract_audio(str(p))
    assert os.path.isfile(out)
