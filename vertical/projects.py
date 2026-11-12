"""Projets : un dossier de travail par VOD (cache d'analyse, clips, réglages)."""
from __future__ import annotations

import hashlib
import re
import threading
import time
import unicodedata
from pathlib import Path

from .config import PROJECTS_DIR, read_json, write_json

_lock = threading.RLock()


def slugify(s: str, maxlen: int = 40) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:maxlen] or "vod"


def project_id_for(path: str) -> str:
    p = Path(path)
    try:
        st = p.stat()
        key = f"{p.resolve()}|{st.st_size}"
    except OSError:
        key = str(p)
    return slugify(p.stem) + "-" + hashlib.sha1(key.encode("utf-8", "ignore")).hexdigest()[:8]


def pdir(pid: str) -> Path:
    if not re.fullmatch(r"[a-z0-9\-]+", pid):
        raise ValueError("identifiant de projet invalide")
    d = PROJECTS_DIR / pid
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(pid: str) -> dict | None:
    return read_json(PROJECTS_DIR / pid / "project.json")


def save(proj: dict) -> dict:
    with _lock:
        proj["updated"] = time.time()
        write_json(pdir(proj["id"]) / "project.json", proj)
    return proj


def update(pid: str, fn) -> dict:
    with _lock:
        proj = load(pid)
        if proj is None:
            raise KeyError(pid)
        fn(proj)
        return save(proj)


def create(vod_path: str) -> dict:
    pid = project_id_for(vod_path)
    existing = load(pid)
    if existing:
        existing["vod_path"] = vod_path
        return save(existing)
    proj = {"id": pid, "vod_path": vod_path, "name": Path(vod_path).stem, "created": time.time(),
            "status": "new", "info": None, "game": None, "facecam": None, "clips": [], "analysis": {}}
    return save(proj)


def list_all() -> list[dict]:
    out = []
    for f in PROJECTS_DIR.glob("*/project.json"):
        p = read_json(f)
        if not p:
            continue
        out.append({"id": p["id"], "name": p["name"], "vod_path": p["vod_path"], "status": p.get("status"),
                    "updated": p.get("updated", 0), "n_clips": len(p.get("clips", [])),
                    "duration": (p.get("info") or {}).get("duration"),
                    "game": (p.get("game") or {}).get("name"),
                    "thumb": next((c["id"] for c in p.get("clips", []) if c.get("thumb")), None)})
    out.sort(key=lambda x: -x["updated"])
    return out
