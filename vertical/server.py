"""Serveur local (Starlette) : API + interface web servie à 127.0.0.1."""
from __future__ import annotations

import logging
import mimetypes
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import __version__, claude_pack, env, exporter, media, pipeline, profiles, projects, render, subtitles
from .config import FONTS_DIR, WEB_DIR, load_settings, save_settings
from .i18n import note, render_note, tr, ui_clip
from .jobs import Job, manager

log = logging.getLogger("vertical")
WINDOW = None  # fenêtre pywebview (si disponible)

VIDEO_TYPES = [("Vidéos", "*.mp4;*.mkv;*.mov;*.ts;*.flv;*.webm;*.avi;*.m4v")]


def ok(data=None, status=200):
    return JSONResponse(data if data is not None else {"ok": True}, status_code=status)


def err(msg, status=400):
    return JSONResponse({"error": msg}, status_code=status)


def _project_or_404(pid: str):
    p = projects.load(pid)
    if not p:
        raise FileNotFoundError("Projet introuvable")
    return p


# --------------------------------------------------------------------------- dialogues natifs
def _dialog(kind: str) -> str | None:
    if WINDOW is not None:
        import webview
        if kind == "file":
            r = WINDOW.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False,
                                          file_types=("Vidéos (*.mp4;*.mkv;*.mov;*.ts;*.flv;*.webm;*.avi;*.m4v)",
                                                      "Tous les fichiers (*.*)"))
        else:
            r = WINDOW.create_file_dialog(webview.FOLDER_DIALOG)
        if not r:
            return None
        return r[0] if isinstance(r, (list, tuple)) else r
    result: dict = {}

    def tk():
        import tkinter as t
        from tkinter import filedialog
        root = t.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if kind == "file":
            result["p"] = filedialog.askopenfilename(title="Choisir une VOD", filetypes=VIDEO_TYPES + [("Tous", "*.*")])
        else:
            result["p"] = filedialog.askdirectory(title="Choisir un dossier")
        root.destroy()

    th = threading.Thread(target=tk)
    th.start()
    th.join()
    return result.get("p") or None


async def pick(request: Request):
    kind = request.path_params["kind"]
    try:
        p = await _run_sync(lambda: _dialog("file" if kind == "file" else "folder"))
    except Exception as e:
        return err(tr("err.dialog", e=e))
    return ok({"path": p})


async def _run_sync(fn):
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(fn)


# --------------------------------------------------------------------------- état / réglages
_ENV = {"report": None, "started": False, "lock": threading.Lock()}


def warm_env() -> None:
    """Diagnostic lourd (import de PyTorch, test NVENC…) calculé une fois en arrière-plan au démarrage."""
    with _ENV["lock"]:
        if _ENV["started"]:
            return
        _ENV["started"] = True

    def run():
        try:
            _ENV["report"] = env.report(None)
        except Exception as e:  # pragma: no cover
            log.exception("diagnostic")
            _ENV["report"] = {"error": str(e), "gpu": {"cuda": False, "name": ""}, "ffmpeg": {"available": False},
                              "note_codes": []}
    threading.Thread(target=run, daemon=True, name="env-warmup").start()


async def status(request: Request):
    warm_env()
    s = load_settings()
    rep = _ENV["report"]
    if rep is not None:
        rep = dict(rep)
        rep["notes"] = [tr(k) for k in rep.get("note_codes", [])]
        if request.query_params.get("ollama", "1") == "1":
            rep["ollama"] = await _run_sync(lambda: env.ollama_status(s.get("ollama_url", "http://127.0.0.1:11434")))
    return ok({"version": __version__, "ready": rep is not None, "env": rep, "settings": s,
               "profiles": profiles.listing(), "layouts": list(render.LAYOUTS.keys()), "fonts": subtitles.FONTS})


async def settings_post(request: Request):
    return ok(save_settings(await request.json()))


# --------------------------------------------------------------------------- projets
async def projects_list(request: Request):
    return ok(projects.list_all())


async def project_create(request: Request):
    body = await request.json()
    path = (body.get("path") or "").strip().strip('"')
    if not path or not Path(path).is_file():
        return err(tr("err.file_missing", p=path))
    try:
        info = await _run_sync(lambda: media.probe(path))
    except Exception as e:
        return err(str(e))
    proj = projects.create(path)
    proj["info"] = info
    projects.save(proj)
    return ok(proj)


async def project_get(request: Request):
    pid = request.path_params["pid"]
    p = projects.load(pid)
    if not p:
        return err(tr("err.not_found"), 404)
    j = manager.active_for(pid)
    p["active_job"] = j.id if j else None
    p["export_dir"] = str(exporter.export_dir_for(p, load_settings()))
    p["vod_exists"] = Path(p["vod_path"]).exists()
    p["has_proxy"] = (projects.pdir(pid) / "proxy.mp4").exists()
    p["notes_text"] = [render_note(n) for n in (p.get("notes") or [])]
    for c in p.get("clips", []):
        ui_clip(c)
    return ok(p)


async def project_patch(request: Request):
    """Renommer la VOD dans Vertical (ex. « Phantom Blade Zero EP1 ») : sert au dossier d'export et aux noms de fichiers."""
    pid = request.path_params["pid"]
    body = await request.json()
    name = " ".join(str(body.get("name", "")).split())[:120]
    if not name:
        return err(tr("err.name_empty"))
    proj = projects.update(pid, lambda p: p.update(name=name))
    return ok({"name": proj["name"], "export_dir": str(exporter.export_dir_for(proj, load_settings()))})


async def project_delete(request: Request):
    pid = request.path_params["pid"]
    d = projects.pdir(pid)
    shutil.rmtree(d, ignore_errors=True)
    return ok()


async def analyze(request: Request):
    pid = request.path_params["pid"]
    _project_or_404(pid)
    if manager.active_for(pid):
        return err(tr("err.busy"))
    opts = await request.json()
    if opts.get("force"):
        d = projects.pdir(pid)
        for f in ("transcript.json", "features.npz", "analysis.json"):
            (d / f).unlink(missing_ok=True)
        shutil.rmtree(d / "thumbs", ignore_errors=True)
        projects.update(pid, lambda p: p.update(clips=[]))
    job = Job("analyze", pid, pipeline.analysis_steps())
    manager.submit(job, lambda j: pipeline.run_analysis(j, pid, opts))
    return ok({"job": job.id})


async def reselect(request: Request):
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    if not (projects.pdir(pid) / "features.npz").exists():
        return err(tr("err.need_analysis"))
    opts = await request.json()
    if opts.get("reset"):
        projects.update(pid, lambda pr: pr.update(clips=[]))
    job = Job("reselect", pid, [("select", tr("step.select"), 1), ("meta", tr("step.meta"), 2), ("thumbs", tr("step.thumbs"), 1)])
    manager.submit(job, lambda j: pipeline.reselect(j, pid, opts))
    return ok({"job": job.id})


async def clip_patch(request: Request):
    pid, cid = request.path_params["pid"], request.path_params["cid"]
    body = await request.json()
    allowed = {"start", "end", "status", "title", "description", "hashtags", "layout", "game_crop", "sub_pos"}
    found = {}

    def fn(p):
        dur = (p.get("info") or {}).get("duration", 1e9)
        for c in p["clips"]:
            if c["id"] == cid:
                for k, v in body.items():
                    if k in allowed:
                        c[k] = v
                c["start"] = round(max(0.0, float(c["start"])), 2)
                c["end"] = round(min(dur, max(c["start"] + 1, float(c["end"]))), 2)
                found.update(c)
    projects.update(pid, fn)
    return ok(found) if found else err(tr("err.clip_missing"), 404)


async def clip_add(request: Request):
    """Ajout manuel d'un passage (si l'utilisateur repère un moment oublié)."""
    pid = request.path_params["pid"]
    body = await request.json()
    start, end = float(body["start"]), float(body["end"])
    p = _project_or_404(pid)
    from . import transcribe, metadata
    tr = __import__("json").loads((projects.pdir(pid) / "transcript.json").read_text(encoding="utf-8")) \
        if (projects.pdir(pid) / "transcript.json").exists() else {"segments": []}
    cid = f"m{int(start):06d}"
    clip = {"id": cid, "rank": len(p["clips"]) + 1, "start": start, "end": end, "peak": (start + end) / 2,
            "auto_start": start, "auto_end": end, "score": None, "category": "manual",
            "category_label": "Ajout manuel", "reasons": ["Passage ajouté manuellement"],
            "reason_codes": [{"k": "manual", "v": {}}], "contrib": {}, "events": [],
            "transcript": transcribe.text_between(tr, start, end), "status": "accepted", "layout": "auto"}
    prof = profiles.resolve((p.get("game") or {}).get("profile", "generic"))
    m = metadata.template(clip, (p.get("game") or {}).get("name", ""), prof, load_settings().get("channel_hashtags", ""))
    clip.update(title=m["title"], title_options=m["title_options"], description=m["description"],
                hashtags=m["hashtags"], meta_source=m["source"])
    thumb = projects.pdir(pid) / "thumbs" / f"{cid}.jpg"
    thumb.parent.mkdir(exist_ok=True)
    await _run_sync(lambda: media.grab_frame(p["vod_path"], clip["peak"], thumb, 480))
    clip["thumb"] = thumb.exists()
    projects.update(pid, lambda pr: pr["clips"].append(clip))
    return ok(clip)


async def transcript_range(request: Request):
    pid = request.path_params["pid"]
    a, b = float(request.query_params.get("start", 0)), float(request.query_params.get("end", 0))
    from . import transcribe
    f = projects.pdir(pid) / "transcript.json"
    if not f.exists():
        return ok({"words": []})
    import json
    tr = json.loads(f.read_text(encoding="utf-8"))
    words = [w for w in transcribe.words_flat(tr) if w["end"] > a and w["start"] < b]
    return ok({"words": words})


def _tr_load(pid):
    from .config import read_json
    return read_json(projects.pdir(pid) / "transcript.json", {"segments": []})


def _tr_save(pid, tr, words):
    """Enregistre la transcription corrigée et met à jour le texte des passages."""
    from . import transcribe, transcript_tools
    from .config import write_json
    tr = transcript_tools.rebuild(words, tr)
    tr["edited"] = True
    write_json(projects.pdir(pid) / "transcript.json", tr)

    def fn(p):
        for c in p["clips"]:
            c["transcript"] = transcribe.text_between(tr, c["start"], c["end"])
    projects.update(pid, fn)
    return tr


def _scope_ranges(p: dict, scope: str, clip_id: str | None, pad: float = 0.0):
    if scope == "all":
        return None
    if scope == "clip":
        cl = [c for c in p["clips"] if c["id"] == clip_id]
    elif scope == "accepted":
        cl = [c for c in p["clips"] if c.get("status") == "accepted"]
    else:  # tous les moments proposés
        cl = list(p["clips"])
    return [(max(0.0, c["start"] - pad), c["end"] + pad) for c in cl]


async def transcript_edit(request: Request):
    """Corrections mot à mot (repérés par leur début) : remplacement, suppression, ou
    remplacement par plusieurs mots (le temps est réparti entre eux)."""
    from . import transcript_tools as tt
    pid = request.path_params["pid"]
    body = await request.json()
    tr = _tr_load(pid)
    words = tt.flatten(tr)
    n = 0
    for e in body.get("edits", []):
        s0 = round(float(e["s"]), 3)
        w = next((x for x in words if abs(x["start"] - s0) < 0.002), None)
        if w is None:
            continue
        n += 1
        words = tt.replace_span(words, w["start"], w["start"], (e.get("w") or "").strip())
    _tr_save(pid, tr, words)
    return ok({"changed": n})


async def transcript_lines(request: Request):
    """Corrections par ligne de sous-titre : chaque ligne {a, b, text} remplace les mots de [a, b]."""
    from . import transcript_tools as tt
    pid = request.path_params["pid"]
    body = await request.json()
    tr = _tr_load(pid)
    words = tt.flatten(tr)
    edits = sorted(body.get("lines", []), key=lambda x: -float(x["a"]))
    for e in edits:
        words = tt.replace_span(words, float(e["a"]), float(e["b"]), (e.get("text") or "").strip())
    _tr_save(pid, tr, words)
    return ok({"changed": len(edits)})


async def transcript_words(request: Request):
    """Mots au timing précis : ajout d'un sous-titre oublié ou re-synchronisation d'une ligne."""
    from . import transcript_tools as tt
    pid = request.path_params["pid"]
    body = await request.json()
    a = body.get("a")
    b = body.get("b")
    tr = _tr_load(pid)
    words = tt.set_timed(tt.flatten(tr), None if a is None else float(a), None if b is None else float(b),
                         body.get("words", []))
    _tr_save(pid, tr, words)
    return ok({"words": len(body.get("words", []))})


async def wave(request: Request):
    """Forme d'onde de la voix (enveloppe 100 points/s) pour caler les mots à l'oreille et à l'œil."""
    import numpy as np
    from .audio_analysis import read_segment
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    a, b = float(request.query_params.get("start", 0)), float(request.query_params.get("end", 0))
    b = min(b, a + 60)
    d = projects.pdir(pid)
    voice = ((p.get("analysis") or {}).get("audio") or {}).get("voice", 0)
    wav = next((f for f in (d / f"track{voice}.wav", d / "track0.wav", d / "audio.wav") if f.exists()), None)
    if wav is None:
        return ok({"rate": 100, "values": []})
    x = read_segment(wav, max(0.0, a), b)
    hop = 160
    n = len(x) // hop
    if n == 0:
        return ok({"rate": 100, "values": []})
    env_ = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    ref = float(np.percentile(env_, 99)) + 1e-6
    return ok({"rate": 100, "start": max(0.0, a), "values": [round(float(v), 3) for v in np.clip(env_ / ref, 0, 1)]})


async def reimport(request: Request):
    """Retrouve le projet et le passage d'un Short déjà exporté pour le corriger et le ré-exporter."""
    body = await request.json()
    path = (body.get("path") or "").strip().strip('"')
    if not path or not Path(path).is_file():
        return err(tr("err.file_missing", p=path))
    pid = cid = None
    try:
        import json as _j
        out = env.run([env.ffprobe(), "-v", "error", "-show_entries", "format_tags=comment", "-of", "json", path],
                      text=True, errors="ignore")
        tag = (_j.loads(out.stdout or "{}").get("format", {}).get("tags", {}) or {}).get("comment", "")
        if tag.startswith("vertical:"):
            _, pid, cid = tag.split(":", 2)
    except Exception:
        pass
    if not pid:  # Shorts exportés avant l'ajout de la signature : recherche par chemin / nom de fichier
        target = os.path.normcase(os.path.abspath(path))
        name = Path(path).name.lower()
        for pr in projects.list_all():
            pj = projects.load(pr["id"]) or {}
            for c in pj.get("clips", []):
                f = (c.get("export") or {}).get("file")
                if f and (os.path.normcase(os.path.abspath(f)) == target or Path(f).name.lower() == name):
                    pid, cid = pj["id"], c["id"]
                    break
            if pid:
                break
    if not pid or not projects.load(pid):
        return err(tr("err.not_vertical"))
    proj = projects.load(pid)
    if not any(c["id"] == cid for c in proj["clips"]):
        return err(tr("err.clip_gone"))

    def fn(p):  # le ré-export remplacera ce fichier
        for c in p["clips"]:
            if c["id"] == cid:
                c["export"] = dict(c.get("export") or {}, file=path)
    projects.update(pid, fn)
    return ok({"project_id": pid, "clip_id": cid, "vod_exists": Path(proj["vod_path"]).exists()})


async def transcript_replace(request: Request):
    """Rechercher / remplacer un mot ou une expression (vide = supprimer)."""
    from . import transcript_tools as tt
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    body = await request.json()
    find = (body.get("find") or "").strip()
    if not find:
        return err(tr("err.find_empty"))
    ranges = _scope_ranges(p, body.get("scope", "clip"), body.get("clip_id"))
    tr = _tr_load(pid)
    words = tt.flatten(tr)
    if body.get("preview"):
        m = tt.find_matches(words, find, ranges)
        return ok({"count": len(m), "matches": [tt.context(words, i, j) for i, j in m[:200]]})
    words, n = tt.find_replace(words, find, (body.get("replace") or "").strip(), ranges)
    if n:
        _tr_save(pid, tr, words)
    return ok({"count": n})


async def transcript_redo(request: Request):
    """Recalcule les sous-titres des passages choisis avec la précision maximale."""
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    body = await request.json()
    ranges = _scope_ranges(p, body.get("scope", "clip"), body.get("clip_id"), pad=1.5)
    if ranges is None:
        ranges = [(0.0, p["info"]["duration"])]
    if not ranges:
        return err(tr("err.no_range"))
    d = projects.pdir(pid)
    voice = ((p.get("analysis") or {}).get("audio") or {}).get("voice", 0)
    wav = d / f"track{voice}.wav"
    if not wav.exists():
        wav = d / "audio.wav" if (d / "audio.wav").exists() else d / "track0.wav"
    if not wav.exists():
        return err(tr("err.audio_missing"))
    settings = load_settings()
    vocab = body.get("vocabulary")
    if vocab is not None:
        settings = save_settings({"vocabulary": vocab})
    vocab = settings.get("vocabulary", "")
    game = (p.get("game") or {}).get("name") or ""
    if game and game.lower() not in vocab.lower():
        vocab = (game + ", " + vocab).strip(", ")
    job = Job("retranscribe", pid, [("redo", tr("step.redo"), 1)])

    def run(j):
        from . import transcribe
        from . import transcript_tools as tt
        j.start("redo")
        merged = []
        for a, b in sorted(ranges):
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        new_words, engine = transcribe.retranscribe_ranges(
            wav, merged, language=settings.get("language", "fr"), precision=body.get("precision", "max"),
            vocabulary=vocab, on_progress=lambda x, m: j.progress("redo", x, m))
        tr = _tr_load(pid)
        words = tt.flatten(tr)
        for a, b in merged:
            words = tt.splice(words, new_words, a, b)
        _tr_save(pid, tr, words)
        j.done("redo", tr("redo_done", n=len(new_words), engine=engine))
        return {"words": len(new_words), "engine": engine}
    manager.submit(job, run)
    return ok({"job": job.id})


async def media_file(request: Request):
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    proxy = projects.pdir(pid) / "proxy.mp4"
    path = Path(proxy if (request.query_params.get("proxy") and proxy.exists()) else p["vod_path"])
    if not path.exists():
        return err("Vidéo introuvable", 404)
    mt = mimetypes.guess_type(str(path))[0] or "video/mp4"
    if path.suffix.lower() == ".mkv":
        mt = "video/webm"  # Chromium lit le H.264 en MKV via ce type
    return FileResponse(path, media_type=mt)


async def thumb(request: Request):
    pid, cid = request.path_params["pid"], request.path_params["cid"]
    f = projects.pdir(pid) / "thumbs" / f"{cid}.jpg"
    return FileResponse(f, media_type="image/jpeg") if f.exists() else Response(status_code=404)


async def frame(request: Request):
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    t = float(request.query_params.get("t", 0))
    f = projects.pdir(pid) / "frame.jpg"
    await _run_sync(lambda: media.grab_frame(p["vod_path"], t, f, 960))
    return FileResponse(f, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


async def facecam(request: Request):
    pid = request.path_params["pid"]
    body = await request.json()
    box = body.get("box")
    if box:
        box = {k: int(box[k]) for k in ("x", "y", "w", "h")}
    projects.update(pid, lambda p: p.update(facecam=box, facecam_manual=True))
    return ok({"facecam": box})


async def detect_cam(request: Request):
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    from . import visual_analysis
    info = p["info"]
    box = await _run_sync(lambda: visual_analysis.detect_facecam(p["vod_path"], info["duration"], info["width"],
                                                                 info["height"]))
    return ok({"facecam": box})


async def layout_save(request: Request):
    """Cadrage façon clips Twitch : zone caméra + zone jeu + taille/position de la caméra."""
    pid = request.path_params["pid"]
    body = await request.json()

    def rect(r):
        return {k: int(round(float(r[k]))) for k in ("x", "y", "w", "h")} if r else None
    cam = rect(body.get("cam"))
    cfg = {"cam_frac": float(body.get("cam_frac", 0.36)), "cam_pos": body.get("cam_pos", "top"),
           "game": rect(body.get("game")), "track": bool(body.get("track"))}

    def fn(p):
        p.update(facecam=cam, facecam_manual=True, layout_cfg=cfg)
        if cam:  # le nouveau cadrage s'applique aux passages en « automatique »
            for c in p["clips"]:
                if c.get("layout") in ("smart_crop", "center_crop", "facecam_top", "facecam_fixed") and body.get("apply_all"):
                    c["layout"] = "auto"
    projects.update(pid, fn)
    return ok({"facecam": cam, "layout_cfg": cfg})


async def preview(request: Request):
    pid, cid = request.path_params["pid"], request.path_params["cid"]
    p = _project_or_404(pid)
    body = await request.json() if (await request.body()) else {}
    clip = next((c for c in p["clips"] if c["id"] == cid), None)
    if not clip:
        return err(tr("err.clip_missing"), 404)
    settings = load_settings()
    settings.update(body.get("settings") or {})
    d = projects.pdir(pid)
    out = d / "previews" / f"{cid}.mp4"
    p["_dir"] = str(d)
    job = Job("preview", pid, [("render", tr("step.render"), 1)])

    def run(j):
        j.start("render")
        render.render_clip(p, clip, settings, out, d / "tmp" / f"prev_{cid}", preview=True,
                           on_progress=lambda x: j.progress("render", x))
        j.done("render")
        return {"url": f"/api/projects/{pid}/previews/{cid}.mp4?v={int(time.time())}"}
    threading.Thread(target=lambda: _run_preview(job, run), daemon=True).start()
    manager.jobs[job.id] = job
    return ok({"job": job.id})


def _run_preview(job, fn):  # les aperçus ne bloquent pas derrière une analyse longue
    try:
        job.result = fn(job)
        job.status = "done"
    except Exception as e:
        job.status, job.error = "error", str(e)
        log.exception("preview")
    job.ended = time.time()


async def preview_file(request: Request):
    pid, cid = request.path_params["pid"], request.path_params["cid"]
    f = projects.pdir(pid) / "previews" / f"{cid}.mp4"
    return FileResponse(f, media_type="video/mp4") if f.exists() else Response(status_code=404)


async def make_proxy(request: Request):
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    out = projects.pdir(pid) / "proxy.mp4"
    job = Job("proxy", pid, [("proxy", tr("step.proxy"), 1)])

    def run(j):
        j.start("proxy")
        caps = env.ffmpeg_caps()
        enc = ["-c:v", "h264_nvenc", "-preset", "p3", "-cq", "30"] if caps["nvenc"] else \
            ["-c:v", "libx264", "-preset", "veryfast", "-crf", "30"]
        tmp = out.with_suffix(".part.mp4")
        media._run_with_progress([env.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", p["vod_path"],
                                  "-vf", "scale=-2:540,fps=30", *enc, "-c:a", "aac", "-b:a", "96k",
                                  "-movflags", "+faststart", str(tmp)], p["info"]["duration"],
                                 lambda x: j.progress("proxy", x))
        tmp.replace(out)
        j.done("proxy")
    manager.submit(job, run)
    return ok({"job": job.id})


async def export(request: Request):
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    body = await request.json()
    ids = body.get("clip_ids") or [c["id"] for c in p["clips"] if c.get("status") == "accepted"]
    if not ids:
        return err(tr("err.need_accept"))
    steps = [(c["id"], f"#{i + 1} {c.get('title', '')[:50]}", max(1, c["end"] - c["start"]))
             for i, c in enumerate(sorted([c for c in p["clips"] if c["id"] in ids], key=lambda x: x["start"]))]
    job = Job("export", pid, steps)
    manager.submit(job, lambda j: exporter.run_export(j, pid, {"clip_ids": ids, "settings": body.get("settings"),
                                                              "reexport": bool(body.get("reexport"))}))
    return ok({"job": job.id})


async def job_get(request: Request):
    j = manager.get(request.path_params["jid"])
    return ok(j.to_dict()) if j else err("Tâche inconnue", 404)


async def job_cancel(request: Request):
    j = manager.get(request.path_params["jid"])
    if j:
        j.cancel_flag = True
    return ok()


async def open_folder(request: Request):
    body = await request.json()
    path = body.get("path", "")
    target = Path(path)
    if not target.exists():
        return err("Dossier introuvable")
    if env.IS_WIN:
        if target.is_file():
            subprocess.Popen(["explorer", "/select,", str(target)])
        else:
            os.startfile(str(target))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])
    return ok()


async def open_url(request: Request):
    import webbrowser
    url = (await request.json()).get("url", "")
    if url.startswith("https://"):
        webbrowser.open(url)
    return ok()


_curve_cache: dict = {}


async def curve(request: Request):
    """Courbe d'intérêt par seconde (affichée dans la timeline de l'éditeur)."""
    pid = request.path_params["pid"]
    a, b = int(float(request.query_params.get("start", 0))), int(float(request.query_params.get("end", 0)))
    f = projects.pdir(pid) / "features.npz"
    if not f.exists():
        return ok({"values": []})
    key = (pid, f.stat().st_mtime)
    if key not in _curve_cache:
        import numpy as np
        from . import scoring
        z = np.load(f)
        feats = {k: z[k] for k in z.files}
        n = max(len(v) for v in feats.values())
        c = scoring.combine(feats, n)
        _curve_cache.clear()
        _curve_cache[key] = (c / (float(np.percentile(c, 99.7)) + 1e-6)).clip(0, 1.2)
    c = _curve_cache[key]
    return ok({"values": [round(float(x), 3) for x in c[max(0, a):max(0, b)]]})


async def claude_prompt(request: Request):
    pid = request.path_params["pid"]
    p = _project_or_404(pid)
    prompt, folder = await _run_sync(lambda: claude_pack.build_prompt(p))
    return ok({"prompt": prompt, "folder": folder})


async def claude_import(request: Request):
    pid = request.path_params["pid"]
    body = await request.json()
    try:
        res = claude_pack.apply_response(pid, body.get("text", ""))
    except Exception as e:
        return err(tr("err.bad_reply", e=e))
    return ok(res)


async def index(request: Request):
    return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-store"})


async def on_error(request: Request, exc: Exception):
    log.exception("API")
    return err(str(exc), 404 if isinstance(exc, FileNotFoundError) else 500)


routes = [
    Route("/", index),
    Route("/api/status", status),
    Route("/api/settings", settings_post, methods=["POST"]),
    Route("/api/pick/{kind}", pick, methods=["POST"]),
    Route("/api/open-folder", open_folder, methods=["POST"]),
    Route("/api/open-url", open_url, methods=["POST"]),
    Route("/api/projects/{pid}/curve", curve),
    Route("/api/projects", projects_list),
    Route("/api/projects", project_create, methods=["POST"]),
    Route("/api/projects/{pid}", project_get),
    Route("/api/projects/{pid}", project_delete, methods=["DELETE"]),
    Route("/api/projects/{pid}", project_patch, methods=["PATCH"]),
    Route("/api/projects/{pid}/analyze", analyze, methods=["POST"]),
    Route("/api/projects/{pid}/reselect", reselect, methods=["POST"]),
    Route("/api/projects/{pid}/clips", clip_add, methods=["POST"]),
    Route("/api/projects/{pid}/clips/{cid}", clip_patch, methods=["PATCH"]),
    Route("/api/projects/{pid}/clips/{cid}/preview", preview, methods=["POST"]),
    Route("/api/projects/{pid}/previews/{cid}.mp4", preview_file),
    Route("/api/projects/{pid}/transcript", transcript_range),
    Route("/api/projects/{pid}/transcript/edit", transcript_edit, methods=["POST"]),
    Route("/api/projects/{pid}/transcript/lines", transcript_lines, methods=["POST"]),
    Route("/api/projects/{pid}/transcript/replace", transcript_replace, methods=["POST"]),
    Route("/api/projects/{pid}/transcript/words", transcript_words, methods=["POST"]),
    Route("/api/projects/{pid}/wave", wave),
    Route("/api/reimport", reimport, methods=["POST"]),
    Route("/api/projects/{pid}/transcript/redo", transcript_redo, methods=["POST"]),
    Route("/api/projects/{pid}/media", media_file),
    Route("/api/projects/{pid}/proxy", make_proxy, methods=["POST"]),
    Route("/api/projects/{pid}/thumb/{cid}", thumb),
    Route("/api/projects/{pid}/frame", frame),
    Route("/api/projects/{pid}/facecam", facecam, methods=["POST"]),
    Route("/api/projects/{pid}/detect-facecam", detect_cam, methods=["POST"]),
    Route("/api/projects/{pid}/layout", layout_save, methods=["POST"]),
    Route("/api/projects/{pid}/export", export, methods=["POST"]),
    Route("/api/projects/{pid}/claude-prompt", claude_prompt),
    Route("/api/projects/{pid}/claude-import", claude_import, methods=["POST"]),
    Route("/api/jobs/{jid}", job_get),
    Route("/api/jobs/{jid}/cancel", job_cancel, methods=["POST"]),
    Mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static"),
    Mount("/fonts", StaticFiles(directory=str(FONTS_DIR)), name="fonts"),
]

app = Starlette(routes=routes, exception_handlers={Exception: on_error, FileNotFoundError: on_error})
