"""Async (background) transcription jobs."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from .transcribe import transcribe

JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()
_TTL_SECONDS = 24 * 3600


def _purge_old() -> None:
    now = time.time()
    with _LOCK:
        stale = [jid for jid, j in JOBS.items() if now - j.get("created_at", now) > _TTL_SECONDS and j.get("state") in ("done", "failed", "cancelled")]
        for jid in stale:
            del JOBS[jid]


def _run_job(job_id: str, kwargs: dict[str, Any]) -> None:
    with _LOCK:
        JOBS[job_id]["state"] = "running"
        JOBS[job_id]["started_at"] = time.time()
    try:
        result = transcribe(**kwargs)
        with _LOCK:
            JOBS[job_id]["state"] = "done"
            JOBS[job_id]["result"] = result
            JOBS[job_id]["finished_at"] = time.time()
    except Exception as e:
        with _LOCK:
            JOBS[job_id]["state"] = "failed"
            JOBS[job_id]["error"] = str(e)
            JOBS[job_id]["finished_at"] = time.time()


def submit(**kwargs: Any) -> str:
    _purge_old()
    job_id = uuid.uuid4().hex[:12]
    with _LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "state": "queued",
            "created_at": time.time(),
            "kwargs": kwargs,
        }
    t = threading.Thread(target=_run_job, args=(job_id, kwargs), daemon=True)
    t.start()
    return job_id


def status(job_id: str) -> dict[str, Any]:
    with _LOCK:
        job = JOBS.get(job_id)
    if job is None:
        return {"job_id": job_id, "state": "not_found"}
    out = {"job_id": job_id, "state": job["state"]}
    if job["state"] == "done":
        out["result"] = job.get("result")
    if job["state"] == "failed":
        out["error"] = job.get("error")
    if "started_at" in job:
        out["started_at"] = job["started_at"]
    if "finished_at" in job:
        out["finished_at"] = job["finished_at"]
    return out


def cancel(job_id: str) -> bool:
    with _LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return False
        if job["state"] in ("done", "failed", "cancelled"):
            return False
        job["state"] = "cancelled"
    return True
