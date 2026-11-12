"""Export final : un dossier par VOD avec les MP4 et les textes de publication."""
from __future__ import annotations

import re
import time
from pathlib import Path

from . import projects, render
from .config import load_settings, write_json
from .jobs import Job


def safe_name(s: str, maxlen: int = 60) -> str:
    s = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "", s)
    s = re.sub(r"[\U00010000-\U0010ffff]", "", s)  # emojis : noms de fichiers plus sûrs
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s[:maxlen].strip() or "short"


def export_dir_for(proj: dict, settings: dict) -> Path:
    base = settings.get("export_dir") or ""
    root = Path(base) if base else Path(proj["vod_path"]).parent
    return root / f"{safe_name(proj['name'], 80)} - Shorts"


def _fmt(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def short_numbers(proj: dict) -> dict[str, int]:
    """Numéro de chaque Short validé dans l'ordre de la VOD (Short 1 = le premier moment)."""
    acc = sorted([c for c in proj["clips"] if c.get("status") == "accepted"], key=lambda c: c["start"])
    return {c["id"]: i + 1 for i, c in enumerate(acc)}


def file_stem(proj: dict, clip: dict, n: int, mode: str) -> str:
    title = safe_name(clip.get("title", "short"))
    series = safe_name(proj.get("name", "VOD"), 80)
    if mode == "series":
        return f"{series} - Short {n}"
    if mode == "series_title":
        return f"{series} - Short {n} - {title}"
    return f"{n:02d} - {title}"


def publication_text(clip: dict) -> str:
    tags = " ".join(clip.get("hashtags", []))
    tiktok = " ".join([t for t in clip.get("hashtags", []) if t.lower() != "#shorts"] + ["#fyp", "#pourtoi"])
    insta = " ".join([t for t in clip.get("hashtags", []) if t.lower() != "#shorts"] + ["#reels"])
    desc_body = clip.get("description", "").split("\n\n#")[0].strip()
    return (f"TITRE\n{clip.get('title', '')}\n\n"
            f"Autres idées de titres :\n" + "\n".join(f"- {t}" for t in clip.get("title_options", [])[1:]) + "\n\n"
            f"=== YouTube Shorts ===\n{clip.get('title', '')}\n\n{clip.get('description', '')}\n\n"
            f"=== TikTok ===\n{clip.get('title', '')} {tiktok}\n\n"
            f"=== Instagram Reels ===\n{clip.get('title', '')}\n\n{desc_body}\n\n{insta}\n\n"
            f"---\nSource : {_fmt(clip['start'])} → {_fmt(clip['end'])} de la VOD · score {clip.get('score')}/100\n"
            f"Pourquoi : {'; '.join(clip.get('reasons', []))}\n")


def run_export(job: Job, pid: str, opts: dict) -> dict:
    settings = load_settings()
    settings.update({k: v for k, v in (opts.get("settings") or {}).items() if v is not None})
    proj = projects.load(pid)
    proj["_dir"] = str(projects.pdir(pid))
    ids = opts.get("clip_ids")
    clips = [c for c in proj["clips"] if (c["id"] in ids if ids else c.get("status") == "accepted")]
    if not clips:
        raise RuntimeError("Aucun passage validé à exporter.")
    out_dir = export_dir_for(proj, settings)
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp_root = projects.pdir(pid) / "tmp"
    results = []
    numbers = short_numbers(proj)
    extra = dict(settings.get("export_files") or {})
    mode = settings.get("file_naming", "title")
    for i, c in enumerate(sorted(clips, key=lambda x: x["start"])):
        key = c["id"]
        job.start(key)
        old = Path((c.get("export") or {}).get("file") or "")
        if opts.get("reexport") and old.name and old.parent.exists():
            mp4 = old  # ré-export : on remplace le fichier existant, même nom, même dossier
            fname = mp4.stem
            cdir = mp4.parent
        else:
            fname = file_stem(proj, c, numbers.get(key, i + 1), mode)
            cdir = out_dir
            mp4 = cdir / f"{fname}.mp4"
        render.render_clip(proj, c, settings, mp4, tmp_root / key, preview=False,
                           on_progress=lambda p, k=key: job.progress(k, p),
                           metadata={"comment": f"vertical:{pid}:{key}", "title": c.get("title", "")})
        if extra.get("txt"):
            (cdir / f"{fname}.txt").write_text(publication_text(c), encoding="utf-8")
        results.append({"id": key, "file": str(mp4), "title": c.get("title"), "start": c["start"], "end": c["end"],
                        "duration": round(c["end"] - c["start"], 1), "description": c.get("description"),
                        "hashtags": c.get("hashtags"), "score": c.get("score"), "category": c.get("category_label")})

        def mark(p, k=key, f=str(mp4)):
            for cc in p["clips"]:
                if cc["id"] == k:
                    cc["export"] = {"file": f, "at": time.time()}
        projects.update(pid, mark)
        job.done(key, mp4.name)
    # shorts.json : on fusionne avec l'existant (ré-export d'un seul Short)
    from .config import read_json
    for d in ({Path(r_["file"]).parent for r_ in results} if extra.get("json") else set()):
        prev = read_json(d / "shorts.json", {}) or {}
        mine = [r_ for r_ in results if Path(r_["file"]).parent == d]
        ids = {r_["id"] for r_ in mine}
        merged = [x for x in prev.get("shorts", []) if x.get("id") not in ids] + mine
        write_json(d / "shorts.json", {"vod": proj["vod_path"], "project": pid,
                                       "game": (proj.get("game") or {}).get("name"),
                                       "exported": time.strftime("%Y-%m-%d %H:%M"),
                                       "shorts": sorted(merged, key=lambda x: x.get("start", 0))})
    if opts.get("reexport") or not extra.get("md"):
        return {"dir": str(Path(results[0]["file"]).parent), "files": [r_["file"] for r_ in results]}
    lines = [f"# Shorts — {proj['name']}\n"]
    for r_ in results:
        lines.append(f"## {Path(r_['file']).name}\n**{r_['title']}**  \n{r_['duration']} s · score {r_['score']} · "
                     f"{r_['category']}\n\n{r_['description']}\n")
    (out_dir / "PUBLICATION.md").write_text("\n".join(lines), encoding="utf-8")
    return {"dir": str(out_dir), "files": [r_["file"] for r_ in results]}
