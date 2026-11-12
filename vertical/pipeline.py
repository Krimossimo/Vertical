"""Orchestration de l'analyse d'une VOD."""
from __future__ import annotations

import logging
import math
from pathlib import Path

import numpy as np

from . import (ai_models, audio_analysis, audio_tracks, env, media, metadata, profiles, projects, scoring, text_analysis,
               transcribe, visual_analysis)
from .config import load_settings, read_json, write_json
from .i18n import lang, note, render_reason, tr
from .jobs import Job

log = logging.getLogger("vertical")

_STEP_W = [("probe", 1), ("audio", 4), ("audio_feat", 3), ("visual", 6), ("game", 3), ("transcribe", 40),
           ("text", 1), ("candidates", 1), ("deep", 12), ("select", 1), ("meta", 3), ("thumbs", 1)]


def analysis_steps() -> list[tuple[str, str, float]]:
    return [(k, tr("step." + k), w) for k, w in _STEP_W]


ANALYSIS_STEPS = [(k, k, w) for k, w in _STEP_W]  # compatibilité

FEATURE_KEYS = ["loud", "game_loud", "speech_near", "onset", "scream", "laugh", "excite_db", "silence", "motion", "flash", "red", "dark",
                "fade_dark", "static", "excl", "laugh_txt", "game_kw", "rate", "repeat",
                "clip_event", "ast_laugh", "ast_scream", "ast_cheer", "ast_boom", "ast_impact", "ast_gasp"]


def _fmt(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


# --------------------------------------------------------------------------- analyse complète
def run_analysis(job: Job, pid: str, opts: dict) -> dict:
    settings = load_settings()
    settings.update({k: v for k, v in opts.items() if v not in (None, "")})
    proj = projects.load(pid)
    if not proj:
        raise RuntimeError(tr("err.not_found"))
    vod = proj["vod_path"]
    if not Path(vod).exists():
        raise RuntimeError(tr("err.file_missing", p=vod))
    d = projects.pdir(pid)
    projects.update(pid, lambda p: p.update(status="analyzing", error=None))
    notes: list = []

    # 1. sonde -----------------------------------------------------------------
    job.start("probe")
    info = media.probe(vod)
    if not info["has_audio"]:
        notes.append(note("note.no_audio"))
    projects.update(pid, lambda p: p.update(info=info))
    dur = info["duration"]
    nsec = int(math.ceil(dur))
    job.done("probe", tr("probe_done", dur=_fmt(dur), w=info["width"], h=info["height"], fps=f"{info['fps']:.0f}"))

    # 2. audio -----------------------------------------------------------------
    wav: Path | None = None        # mix (piste 1) : son global du jeu + IA audio
    voice_wav: Path | None = None  # piste où l'on entend le plus la voix
    voice_norm: Path | None = None
    feats: dict[str, np.ndarray] = {}
    audio_meta: dict = {}
    if info["has_audio"]:
        job.start("audio")
        tracks = audio_tracks.extract_all(vod, d, info, lambda p: job.progress("audio", 0.8 * p))
        wav = tracks[0]
        job.progress("audio", 0.85, tr("audio_search_n", n=len(tracks)) if len(tracks) > 1 else tr("audio_search"))
        try:
            audio_meta = audio_tracks.choose_voice(tracks, dur)
        except Exception as e:
            log.warning("choix de piste : %s", e)
            audio_meta = {"voice": 0, "stats": [], "has_voice": True}
        voice_wav = tracks[audio_meta["voice"]]
        voice_norm = audio_tracks.normalized_voice(voice_wav, d / "voice_norm.wav")
        sp = next((x["speech"] for x in audio_meta.get("stats", []) if x["track"] == audio_meta["voice"]), None)
        msg = (tr("audio_tracks", n=len(tracks), t=audio_meta["voice"] + 1)
               + (tr("audio_speech", p=f"{sp:.0%}") if sp is not None else ""))
        if not audio_meta.get("has_voice", True):
            notes.append(note("note.little_voice"))
            msg += tr("audio_little_voice")
        job.done("audio", msg)
        job.start("audio_feat")
        separate = voice_wav != wav
        af_v = audio_analysis.analyze(voice_wav, lambda p: job.progress("audio_feat", (0.5 if separate else 1) * p))
        af_m = audio_analysis.analyze(wav, lambda p: job.progress("audio_feat", 0.5 + 0.5 * p)) if separate else af_v
        for k in ("scream", "laugh", "excite_db", "silence"):
            if k in af_v:
                feats[k] = af_v[k]
        if af_v.get("n"):
            if separate and af_m.get("n"):
                n_ = min(len(af_v["loud"]), len(af_m["loud"]))
                feats["loud"] = af_v["loud"][:n_]
                feats["onset"] = af_v["onset"][:n_]
                feats["game_loud"] = af_m["loud"][:n_]
            else:
                feats["loud"], feats["onset"] = af_v["loud"], af_v["onset"]
        if not audio_meta.get("has_voice", True):  # pas de voix : ce ne sont pas des cris
            feats["game_loud"] = feats.pop("loud", np.zeros(nsec, np.float32))
            for k in ("scream", "laugh"):
                feats[k] = np.zeros(nsec, np.float32)
        job.done("audio_feat", tr("feat_done", n=int((feats.get("loud", feats.get("game_loud", np.zeros(1))) > 0.6).sum())))
    else:
        job.done("audio", tr("audio_none"), "skipped")
        job.done("audio_feat", "", "skipped")

    # 3. image -----------------------------------------------------------------
    job.start("visual", tr("visual_sampling"))
    facecam = proj.get("facecam") if proj.get("facecam_manual") else None
    times, frames = media.sample_frames(vod, dur, step=2.0, keyframes_only=True,
                                        on_progress=lambda p: job.progress("visual", 0.9 * p))
    if len(frames) < max(10, dur / 20):  # VOD sans images clés régulières → décodage complet
        job.progress("visual", 0.1, tr("visual_full"))
        times, frames = media.sample_frames(vod, dur, step=2.0, keyframes_only=False,
                                            on_progress=lambda p: job.progress("visual", 0.9 * p))
    job.done("visual", tr("visual_done", n=len(frames)))

    # 4. jeu + facecam ---------------------------------------------------------
    job.start("game")
    use_ai = ai_models.available() and settings.get("analysis_mode") != "rapide"
    game_sel = settings.get("game") or "auto"
    game = {"profile": "generic", "name": "", "detected_by": "default", "by": {"k": "by.default"}}
    if game_sel != "auto":
        pr = profiles.resolve(game_sel)
        game = {"profile": game_sel, "name": pr["name"] if pr["kind"] == "game" else "", "detected_by": "manual",
                "by": {"k": "by.manual"}}
    else:
        pid_txt, gname = profiles.detect_from_text(Path(vod).stem + " " + Path(vod).parent.name)
        if pid_txt:
            game = {"profile": pid_txt, "name": gname, "detected_by": "filename", "by": {"k": "by.filename"}}
        elif use_ai:
            try:
                job.progress("game", 0.2, tr("game_genre"))
                gp = profiles.genre_prompts()
                ts = np.linspace(dur * 0.08, dur * 0.92, 16)
                imgs = [im for t in ts if (im := media.grab_frame_array(vod, float(t), 398, 224)) is not None]
                if imgs:
                    pr = ai_models.clip_scores(np.stack(imgs), [g[1] for g in gp]).mean(axis=0)
                    i = int(np.argmax(pr))
                    if pr[i] > 0.25:
                        game = {"profile": gp[i][0], "name": "", "detected_by": "image",
                                "by": {"k": "by.image", "v": {"p": f"{pr[i]:.0%}"}}}
            except Exception as e:
                notes.append(note("note.genre_fail", e=e))
    if settings.get("game_name"):
        game["name"] = settings["game_name"]
        if game_sel == "auto":
            pid_name, _ = profiles.detect_from_text(settings["game_name"])
            if pid_name:
                game.update(profile=pid_name, detected_by="gamename", by={"k": "by.gamename"})
    profile = profiles.resolve(game["profile"])
    game["profile_name"] = profile["name"]
    job.progress("game", 0.6, tr("game_facecam"))
    if facecam is None:
        try:
            facecam = visual_analysis.detect_facecam(vod, dur, info["width"], info["height"])
        except Exception as e:
            log.warning("facecam: %s", e)
            facecam = None
    vf = visual_analysis.global_features(times, frames, nsec, facecam, (info["width"], info["height"]))
    feats.update(vf)
    del frames
    projects.update(pid, lambda p: p.update(game=game, facecam=facecam))
    by = game.get("by") or {}
    job.done("game", f"{game['name'] or (profile['name'] if lang() == 'fr' else profile.get('name_en', profile['name']))} ({tr(by.get('k', 'by.default'), **(by.get('v') or {}))})"
             + (tr("facecam_yes") if facecam else tr("facecam_no")))

    # 5. transcription ---------------------------------------------------------
    transcript = {"segments": []}
    if info["has_audio"]:
        job.start("transcribe")
        prompt = f"Live Twitch en français sur {game['name'] or 'un jeu vidéo'}."
        if settings.get("vocabulary"):
            prompt += " " + settings["vocabulary"].strip()
        transcript = transcribe.transcribe(
            voice_norm or voice_wav, d / "transcript.json", dur, language=settings.get("language", "fr"),
            model_pref=settings.get("whisper_model", "auto"), initial_prompt=prompt,
            on_progress=lambda p, m: job.progress("transcribe", p, m))
        if transcript.get("error"):
            notes.append(note("note.transcribe_fail", e=transcript["error"]))
            job.done("transcribe", transcript["error"], "skipped")
        else:
            job.done("transcribe", tr("transcribe_done", n=len(transcript["segments"]), engine=transcript.get("engine")))
    else:
        job.done("transcribe", "", "skipped")
    words = transcribe.words_flat(transcript)

    # 6. paroles ---------------------------------------------------------------
    job.start("text")
    ta = text_analysis.analyze(words, nsec, profile)
    for k in ("excl", "laugh_txt", "game_kw", "rate", "repeat"):
        feats[k] = ta[k]
    # présence de parole autour de chaque seconde : un « cri » sans voix est un bruit de jeu
    near = np.zeros(nsec, np.float32)
    for w in words:
        a_, b_ = int(max(0, w["start"] - 2)), int(min(nsec, w["end"] + 2))
        near[a_:b_] = 1.0
    feats["speech_near"] = near
    if words:
        for k, base_ in (("scream", 0.35), ("laugh", 0.5)):
            if k in feats:
                m = np.maximum(near[:len(feats[k])], feats["laugh_txt"][:len(feats[k])]) if k == "laugh" else near[:len(feats[k])]
                feats[k] = (feats[k] * (base_ + (1 - base_) * m)).astype(np.float32)
    job.done("text", tr("text_done", n=len(ta["hits"])))

    # 7. candidats -------------------------------------------------------------
    job.start("candidates")
    n_target = int(settings.get("clip_count", 8))
    dmin, dmax = float(settings.get("duration_min", 25)), float(settings.get("duration_max", 50))
    base = scoring.combine(feats, nsec, profile.get("weights"))
    k_cand = max(24, n_target * 4)
    cands = scoring.pick_peaks(base, k_cand, min_gap=max(20.0, dmax * 0.7), skip_start=min(60, dur * 0.02))
    job.done("candidates", tr("cand_done", n=len(cands)))

    # 8. IA approfondie --------------------------------------------------------
    clip_info: dict[int, tuple[str, str, float]] = {}
    for k in ("clip_event", "ast_laugh", "ast_scream", "ast_cheer", "ast_boom", "ast_impact", "ast_gasp"):
        feats[k] = np.zeros(nsec, np.float32)
    if use_ai and cands:
        job.start("deep")
        try:
            _deep_analysis(job, vod, wav, info, cands, nsec, profile, facecam, feats, clip_info,
                           voice_wav=voice_wav if (voice_wav is not None and voice_wav != wav) else None)
            job.done("deep", tr("deep_done", n=len(cands)))
        except Exception as e:
            log.exception("deep")
            notes.append(note("note.deep_fail", e=e))
            job.done("deep", tr("deep_fail"), "skipped")
        finally:
            ai_models.unload()
        if not audio_meta.get("has_voice", True):
            for k in ("ast_laugh", "ast_scream", "ast_gasp"):
                feats[k] = (feats[k] * 0.3).astype(np.float32)
    else:
        job.done("deep", tr("deep_skip"), "skipped")

    # sauvegarde des courbes pour pouvoir re-sélectionner sans tout recalculer
    np.savez_compressed(d / "features.npz", **{k: feats[k] for k in FEATURE_KEYS if k in feats})
    write_json(d / "analysis.json", {"candidates": cands, "clip_info": {str(k): v for k, v in clip_info.items()},
                                     "text_cats": {k: v.tolist() for k, v in ta["cats"].items()},
                                     "hits": ta["hits"]})

    # 9-11. sélection, métadonnées, miniatures --------------------------------
    clips = select_clips(job, pid, settings, feats=feats, cands=cands, clip_info=clip_info,
                         text_cats=ta["cats"], words=words, transcript=transcript, profile=profile,
                         game=game, info=info)
    projects.update(pid, lambda p: p.update(status="ready", clips=clips, notes=notes,
                                            analysis={"engine": transcript.get("engine"), "ai": use_ai,
                                                      "audio": audio_meta,
                                                      "settings": {k: settings.get(k) for k in (
                                                          "clip_count", "duration_min", "duration_max",
                                                          "analysis_mode", "language")}}))
    return {"clips": len(clips), "notes": notes}


VOICE_GROUPS = ("laugh", "scream", "gasp")


def _ast_fill(path, a, b, nsec, feats, groups):
    seg = audio_analysis.read_segment(path, a, b + 2)
    chunks, starts = [], []
    for s in range(0, max(1, b - a)):
        chunks.append(seg[s * 16000:(s + 3) * 16000])
        starts.append(a + s)
    if not chunks:
        return
    ev = ai_models.audio_events(chunks)
    for s0, e in zip(starts, ev):
        for g, v in e.items():
            if g not in groups:
                continue
            arr = feats["ast_" + g]
            for s in range(s0, min(nsec, s0 + 3)):
                arr[s] = max(arr[s], v)


def _deep_analysis(job, vod, wav, info, cands, nsec, profile, facecam, feats, clip_info, voice_wav=None):
    prompts = profile["clip_prompts"]
    texts = [p["text"] for p in prompts]
    wts = np.array([p.get("weight", 1.0) for p in prompts])
    regions = sorted((max(0, c - 35), min(nsec, c + 25)) for c in cands)
    merged: list[list[int]] = []
    for a, b in regions:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    total = sum(b - a for a, b in merged) or 1
    done = 0
    W, H = 398, 224
    for a, b in merged:
        job.check()
        # --- images (1 i/s)
        ts, fr = media.frames_in_window(vod, a, b, 1.0, size=(W, H))
        if len(fr):
            if facecam:
                fr = fr.copy()
                sx, sy = W / info["width"], H / info["height"]
                fr[:, int(facecam["y"] * sy):int((facecam["y"] + facecam["h"]) * sy) + 1,
                   int(facecam["x"] * sx):int((facecam["x"] + facecam["w"]) * sx) + 1] = 0
            p = ai_models.clip_scores(fr, texts) * wts
            for t, row in zip(ts, p):
                s = int(t)
                if 0 <= s < nsec:
                    i = int(np.argmax(row))
                    v = float(min(1.0, row[i] / 0.45))
                    if v > feats["clip_event"][s]:
                        feats["clip_event"][s] = v
                        clip_info[s] = (prompts[i]["label"], prompts[i].get("category", "combat"), float(row[i]),
                                        prompts[i].get("label_en", prompts[i]["label"]))
        # --- sons (fenêtres de 3 s, pas de 1 s) : voix sur la piste micro, le reste sur le mix
        all_groups = ("laugh", "scream", "cheer", "gasp", "boom", "impact")
        if wav is not None:
            if voice_wav is not None:
                _ast_fill(wav, a, b, nsec, feats, [g for g in all_groups if g not in VOICE_GROUPS])
                _ast_fill(voice_wav, a, b, nsec, feats, VOICE_GROUPS)
            else:
                _ast_fill(wav, a, b, nsec, feats, all_groups)
        done += b - a
        job.progress("deep", done / total, tr("deep_zone", a=_fmt(a), b=_fmt(b)))
    # normalisation douce des sorties AST (probabilités souvent faibles)
    for g in ("laugh", "scream", "cheer", "boom", "impact", "gasp"):
        arr = feats["ast_" + g]
        feats["ast_" + g] = np.clip((arr - 0.08) / 0.5, 0, 1).astype(np.float32)


# --------------------------------------------------------------------------- sélection
def select_clips(job: Job | None, pid: str, settings: dict, feats=None, cands=None, clip_info=None, text_cats=None,
                 words=None, transcript=None, profile=None, game=None, info=None) -> list[dict]:
    proj = projects.load(pid)
    d = projects.pdir(pid)
    if feats is None:  # re-sélection depuis le cache
        z = np.load(d / "features.npz")
        feats = {k: z[k] for k in z.files}
        an = read_json(d / "analysis.json", {})
        cands = an.get("candidates", [])
        clip_info = {int(k): tuple(v) for k, v in an.get("clip_info", {}).items()}
        text_cats = {k: np.array(v, np.float32) for k, v in an.get("text_cats", {}).items()}
        transcript = read_json(d / "transcript.json", {"segments": []})
        words = transcribe.words_flat(transcript)
        game = proj.get("game") or {"profile": "generic", "name": ""}
        profile = profiles.resolve(game.get("profile", "generic"))
        info = proj["info"]
    if job:
        job.start("select")
    dur = info["duration"]
    nsec = int(math.ceil(dur))
    n_target = int(settings.get("clip_count", 8))
    dmin, dmax = float(settings.get("duration_min", 25)), float(settings.get("duration_max", 50))
    if dmax < dmin + 3:
        dmax = dmin + 3
    # vidéo courte : on ne propose pas plus de moments que la vidéo n'en contient
    n_fit = max(1, int(dur / (dmax * 2.5)))
    if n_fit < n_target:
        n_target = n_fit
    if dur < dmin * 1.5:
        dmin, dmax = max(5.0, dur * 0.3), max(8.0, dur * 0.6)
    curve = scoring.combine(feats, nsec, profile.get("weights"))
    ref = float(np.percentile(curve, 99.7)) if len(curve) else 1.0
    excl_strong = {k for k, v in text_analysis.EXCLAMATIONS.items() if v >= 0.6}

    proposals = []
    for c in cands:
        lo, hi = max(0, c - 10), min(nsec, c + 11)
        peak = lo + int(np.argmax(curve[lo:hi])) if hi > lo else c
        start, end = scoring.refine_window(peak, curve, dmin, dmax, words, dur)
        rel = scoring.relevance(curve, start, end, ref)
        proposals.append((rel, peak, start, end))
    proposals.sort(key=lambda x: -x[0])
    chosen = []
    for rel, peak, start, end in proposals:
        if any(not (end + 2 < s or start - 2 > e) for _, _, s, e in chosen):
            continue
        if len(chosen) >= min(5, n_target) and rel < 25:  # au-delà de 5, on ne garde que des moments vraiment forts
            continue
        chosen.append((rel, peak, start, end))
        if len(chosen) >= n_target:
            break

    old = {c["id"]: c for c in (proj.get("clips") or [])}
    clips = []
    for i, (rel, peak, start, end) in enumerate(chosen):
        s, e = int(start), int(math.ceil(end))
        labels: dict[str, float] = {}
        labels_en: dict[str, str] = {}
        cats: dict[str, float] = {}
        for t in range(s, e):
            if t in clip_info:
                ci = clip_info[t]
                lab, cat, p = ci[0], ci[1], ci[2]
                labels_en[lab] = ci[3] if len(ci) > 3 else lab
                labels[lab] = max(labels.get(lab, 0), p)
                cats[cat] = max(cats.get(cat, 0), p)
        w_in = [w for w in words if start <= w["start"] < end]
        ex_words = []
        for w in w_in:
            tok, el = text_analysis._clean_token(w["word"])
            if (tok in excl_strong or el) and tok not in ex_words:
                ex_words.append(w["word"].strip(" ,.!?").lower())
        g_words = []
        for w in w_in:
            tok, _ = text_analysis._clean_token(w["word"])
            for kw in profile.get("keywords", {}):
                if profiles.norm(kw).split()[:1] == [tok] and kw not in g_words:
                    g_words.append(kw)
        hits = {"excl_words": ex_words[:5], "game_words": g_words[:5]}
        codes, contrib, _ = scoring.explain(feats, start, end, hits, labels, profile.get("weights"), labels_en)
        codes = codes or [{"k": "intense", "v": {}}]
        cat = scoring.categorize(feats, start, end, text_cats, cats)
        cid = f"c{peak:06d}"
        prev = old.get(cid, {})
        clip = {
            "id": cid, "rank": i + 1, "start": start, "end": end, "peak": float(peak),
            "auto_start": start, "auto_end": end,
            "score": rel, "category": cat, "category_label": scoring.CATEGORY_LABELS.get(cat, cat),
            "reason_codes": codes, "reasons": [render_reason(x, "fr") for x in codes], "contrib": contrib,
            "events": [{"label": k, "label_en": labels_en.get(k, k), "p": round(v, 2)}
                       for k, v in sorted(labels.items(), key=lambda x: -x[1])[:4]],
            "transcript": transcribe.text_between(transcript, start, end),
            "status": prev.get("status", "pending"),
            "layout": prev.get("layout", "auto"),
        }
        for k in ("title", "title_options", "description", "hashtags", "meta_source", "thumb", "export",
                  "claude_comment", "claude_score", "claude_keep"):
            if k in prev:
                clip[k] = prev[k]
        if prev and (prev.get("start") != prev.get("auto_start") or prev.get("end") != prev.get("auto_end")):
            clip["start"], clip["end"] = prev["start"], prev["end"]  # garde les retouches manuelles
        clips.append(clip)
    if job:
        job.done("select", tr("select_done", n=len(clips)))

    # métadonnées
    if job:
        job.start("meta")
    gname = (game or {}).get("name") or ""
    oll_model = None
    if settings.get("use_ollama", True):
        st = env.ollama_status(settings.get("ollama_url", "http://127.0.0.1:11434"))
        if st["running"]:
            oll_model = metadata.pick_ollama_model(st["models"], settings.get("ollama_model", "auto"))
    used_titles: set = set()
    for i, c in enumerate(clips):
        if "title" in c:
            continue
        base = metadata.template(c, gname, profile, settings.get("channel_hashtags", ""), used_titles)
        m = metadata.with_ollama(c, gname, base, settings["ollama_url"], oll_model) if oll_model else None
        m = m or base
        c.update(title=m["title"], title_options=m["title_options"], description=m["description"],
                 hashtags=m["hashtags"], meta_source=m["source"])
        if job:
            job.progress("meta", (i + 1) / max(1, len(clips)))
    if job:
        job.done("meta", tr("meta_ollama", m=oll_model) if oll_model else tr("meta_local"))

    # miniatures
    if job:
        job.start("thumbs")
    td = d / "thumbs"
    td.mkdir(exist_ok=True)
    for i, c in enumerate(clips):
        f = td / f"{c['id']}.jpg"
        if not f.exists():
            try:
                media.grab_frame(proj["vod_path"], c["peak"], f, 480)
            except Exception:
                pass
        c["thumb"] = f.exists()
        if job:
            job.progress("thumbs", (i + 1) / max(1, len(clips)))
    if job:
        job.done("thumbs")
    return clips


def reselect(job: Job, pid: str, opts: dict) -> dict:
    settings = load_settings()
    settings.update({k: v for k, v in opts.items() if v not in (None, "")})
    clips = select_clips(job, pid, settings)
    projects.update(pid, lambda p: p.update(clips=clips, status="ready"))
    return {"clips": len(clips)}
