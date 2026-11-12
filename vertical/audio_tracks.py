"""Gestion des pistes audio multiples (enregistrements OBS : mix, micro, jeu, Discord…).

* extrait toutes les pistes en une seule passe de décodage ;
* repère automatiquement la piste où l'on entend le plus ta voix (VAD Silero) ;
* prépare une version normalisée de cette piste pour Whisper (voix faible → audible).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from . import env, media
from .audio_analysis import read_segment

log = logging.getLogger("vertical")


def extract_all(src: str, d: Path, info: dict, on_progress=None) -> list[Path]:
    n = max(1, int(info.get("n_audio", 1)))
    outs = [d / f"track{i}.wav" for i in range(n)]
    if all(o.exists() and o.stat().st_size > 1000 for o in outs):
        return outs
    cmd = [env.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(src)]
    tmp = [o.with_suffix(".tmp.wav") for o in outs]
    for i, t in enumerate(tmp):
        cmd += ["-map", f"0:a:{i}", "-vn", "-ac", "1", "-ar", str(media.SR), "-c:a", "pcm_s16le", str(t)]
    media._run_with_progress(cmd, info["duration"], on_progress)
    for t, o in zip(tmp, outs):
        t.replace(o)
    return outs


def _speech_fraction(path: Path, duration: float, n_samples: int = 16, win: float = 30.0) -> tuple[float | None, float, float]:
    """(part de parole, niveau RMS dB, propreté) estimés sur des extraits répartis dans la vidéo."""
    try:
        from faster_whisper.vad import VadOptions, get_speech_timestamps
    except Exception:
        get_speech_timestamps = None
    starts = np.linspace(0, max(0.0, duration - win), n_samples) if duration > win else [0.0]
    speech, total, rms_all, rms_speech, rms_other = 0.0, 0.0, [], [], []
    for s in starts:
        x = read_segment(path, float(s), float(s) + win)
        if len(x) < 1600:
            continue
        r = float(np.sqrt(np.mean(x ** 2)) + 1e-9)
        rms_all.append(r)
        total += len(x) / media.SR
        if get_speech_timestamps is None:
            continue
        peak = float(np.percentile(np.abs(x), 99.5)) + 1e-6
        xn = np.clip(x * (0.5 / peak), -1, 1).astype(np.float32)  # normalise : voix faible OK
        ts = get_speech_timestamps(xn, VadOptions(threshold=0.45, min_speech_duration_ms=250))
        mask = np.zeros(len(x), bool)
        for t in ts:
            mask[t["start"]:t["end"]] = True
            speech += (t["end"] - t["start"]) / media.SR
        if mask.any():
            rms_speech.append(float(np.sqrt(np.mean(x[mask] ** 2))))
        if (~mask).any():
            rms_other.append(float(np.sqrt(np.mean(x[~mask] ** 2))))
    frac = (speech / total if total else 0.0) if get_speech_timestamps is not None else None
    level = 20 * np.log10(np.mean(rms_all)) if rms_all else -90.0
    clean = (20 * np.log10((np.mean(rms_speech) + 1e-9) / (np.mean(rms_other) + 1e-9))
             if rms_speech and rms_other else 0.0)
    return frac, float(level), float(clean)


def choose_voice(tracks: list[Path], duration: float) -> dict:
    stats = []
    for i, t in enumerate(tracks):
        frac, level, clean = _speech_fraction(t, duration)
        stats.append({"track": i, "speech": None if frac is None else round(frac, 3), "level_db": round(level, 1), "clean_db": round(clean, 1)})
    log.info("Pistes audio : %s", stats)
    if not stats or any(s["speech"] is None for s in stats):  # VAD indisponible : piste 1 par défaut
        return {"voice": 0, "stats": stats, "has_voice": True}
    # piste la plus « parlée », départagée par la propreté (micro seul > mix)
    best = max(stats, key=lambda s: s["speech"] + 0.01 * max(0.0, s["clean_db"]))
    near = [s for s in stats if s["speech"] >= best["speech"] - 0.03]
    best = max(near, key=lambda s: s["clean_db"])
    return {"voice": best["track"], "stats": stats, "has_voice": best["speech"] >= 0.02}


def normalized_voice(track: Path, dst: Path) -> Path:
    """Version normalisée (compresseur dynamique) pour la transcription."""
    if dst.exists() and dst.stat().st_size > 1000:
        return dst
    tmp = dst.with_suffix(".tmp.wav")
    r = env.run([env.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(track),
                 "-af", "highpass=f=80,dynaudnorm=f=250:g=15:p=0.9:m=30", "-c:a", "pcm_s16le", str(tmp)])
    if r.returncode != 0 or not tmp.exists():
        return track
    tmp.replace(dst)
    return dst
