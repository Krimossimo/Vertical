"""Gestion des tâches longues (analyse, rendu) exécutées en arrière-plan."""
from __future__ import annotations

import logging
import threading
import time
import traceback
import uuid
from typing import Callable

from .i18n import tr

log = logging.getLogger("vertical")


class Cancelled(Exception):
    pass


class Job:
    def __init__(self, kind: str, project_id: str, steps: list[tuple[str, str, float]]):
        self.id = uuid.uuid4().hex[:10]
        self.kind = kind
        self.project_id = project_id
        self.steps = [{"key": k, "label": l, "weight": w, "status": "pending", "progress": 0.0, "message": "",
                       "started": None, "ended": None} for k, l, w in steps]
        self.status = "running"
        self.error = ""
        self.result = None
        self.started = time.time()
        self.ended = None
        self.cancel_flag = False
        self.log: list[str] = []
        self._lock = threading.Lock()

    def _step(self, key: str) -> dict:
        for s in self.steps:
            if s["key"] == key:
                return s
        s = {"key": key, "label": key, "weight": 1, "status": "pending", "progress": 0.0, "message": "",
             "started": None, "ended": None}
        self.steps.append(s)
        return s

    def check(self):
        if self.cancel_flag:
            raise Cancelled()

    def start(self, key: str, message: str = ""):
        self.check()
        with self._lock:
            s = self._step(key)
            s.update(status="running", progress=0.0, message=message, started=time.time())
        self.note(f"▶ {s['label']}" + (f" — {message}" if message else ""))

    def progress(self, key: str, p: float, message: str | None = None):
        self.check()
        with self._lock:
            s = self._step(key)
            s["progress"] = float(max(0.0, min(1.0, p)))
            if message is not None:
                s["message"] = message

    def done(self, key: str, message: str = "", status: str = "done"):
        with self._lock:
            s = self._step(key)
            s.update(status=status, progress=1.0, ended=time.time())
            if message:
                s["message"] = message
        if message:
            self.note(f"✓ {s['label']} — {message}")

    def note(self, msg: str):
        log.info(msg)
        with self._lock:
            self.log.append(time.strftime("%H:%M:%S ") + msg)
            self.log = self.log[-300:]

    def overall(self) -> float:
        tot = sum(s["weight"] for s in self.steps) or 1
        return sum(s["weight"] * (1.0 if s["status"] in ("done", "skipped") else s["progress"]) for s in self.steps) / tot

    def to_dict(self) -> dict:
        with self._lock:
            el = (self.ended or time.time()) - self.started
            ov = self.overall()
            eta = (el / ov - el) if 0.03 < ov < 1 and self.status == "running" else None
            return {"id": self.id, "kind": self.kind, "project_id": self.project_id, "status": self.status,
                    "error": self.error, "steps": [dict(s) for s in self.steps], "overall": round(ov, 4),
                    "elapsed": round(el, 1), "eta": round(eta, 0) if eta else None, "log": self.log[-60:],
                    "result": self.result}


class JobManager:
    def __init__(self):
        self.jobs: dict[str, Job] = {}
        self._gpu_lock = threading.Lock()  # une seule tâche lourde à la fois (VRAM 12 Go)

    def submit(self, job: Job, fn: Callable[[Job], object]) -> Job:
        self.jobs[job.id] = job

        def runner():
            with self._gpu_lock:
                try:
                    job.result = fn(job)
                    job.status = "done"
                except Cancelled:
                    job.status = "cancelled"
                    job.note(tr("cancelled"))
                except Exception as e:
                    job.status = "error"
                    job.error = str(e)
                    job.note(tr("error", e=e))
                    log.error(traceback.format_exc())
                    for s in job.steps:
                        if s["status"] == "running":
                            s["status"] = "error"
                finally:
                    job.ended = time.time()

        threading.Thread(target=runner, daemon=True, name=f"job-{job.id}").start()
        return job

    def get(self, jid: str) -> Job | None:
        return self.jobs.get(jid)

    def active_for(self, project_id: str) -> Job | None:
        for j in reversed(list(self.jobs.values())):
            if j.project_id == project_id and j.status == "running":
                return j
        return None


manager = JobManager()
