"""Analyse audio : volume relatif, pics soudains, cris, rires, silences.

Tout est calculé en streaming (la VOD de 2 h n'est jamais chargée entièrement
en mémoire) et ramené à une résolution d'une seconde.
"""
from __future__ import annotations

import wave
from pathlib import Path
from typing import Callable

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

SR = 16000
HOP = 800  # 50 ms → 20 images/s pour l'enveloppe


def _rolling(x: np.ndarray, win: int, fn) -> np.ndarray:
    if len(x) == 0:
        return x
    win = max(1, min(win, len(x)))
    pad = win // 2
    xp = np.pad(x, (pad, win - 1 - pad), mode="edge")
    return fn(sliding_window_view(xp, win), axis=1)


def robust_norm(x: np.ndarray, lo_q: float = 50, hi_q: float = 99.3) -> np.ndarray:
    if len(x) == 0:
        return x
    lo, hi = np.percentile(x, lo_q), np.percentile(x, hi_q)
    if hi - lo < 1e-9:
        return np.zeros_like(x, dtype=np.float32)
    return np.clip((x - lo) / (hi - lo), 0, 1).astype(np.float32)


def read_segment(path: Path, start: float, end: float) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        a = max(0, int(start * sr))
        b = min(n, int(end * sr))
        w.setpos(a)
        raw = w.readframes(max(0, b - a))
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def analyze(path: Path, on_progress: Callable[[float], None] | None = None) -> dict:
    """Retourne des courbes par seconde (toutes normalisées 0..1 sauf mention)."""
    env_db: list[np.ndarray] = []
    cent: list[np.ndarray] = []
    hfr: list[np.ndarray] = []
    with wave.open(str(path), "rb") as w:
        total = w.getnframes()
        chunk = SR * 60
        done = 0
        win = np.hanning(HOP * 2).astype(np.float32)
        freqs = np.fft.rfftfreq(HOP * 2, 1 / SR)
        hf_mask = freqs > 2000
        while True:
            raw = w.readframes(chunk)
            if not raw:
                break
            x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
            n = len(x) // HOP
            if n == 0:
                break
            fr = x[: n * HOP].reshape(n, HOP)
            rms = np.sqrt(np.mean(fr ** 2, axis=1) + 1e-10)
            env_db.append(20 * np.log10(rms + 1e-6))
            # Spectre sur des fenêtres de 100 ms (une sur deux pour aller vite)
            m = n // 2
            if m > 0:
                fr2 = x[: m * HOP * 2].reshape(m, HOP * 2) * win
                mag = np.abs(np.fft.rfft(fr2, axis=1)) + 1e-9
                tot = mag.sum(axis=1)
                c = (mag * freqs).sum(axis=1) / tot
                h = mag[:, hf_mask].sum(axis=1) / tot
                cent.append(np.repeat(c, 2))
                hfr.append(np.repeat(h, 2))
                if n % 2:
                    cent.append(c[-1:])
                    hfr.append(h[-1:])
            done += len(x)
            if on_progress:
                on_progress(done / max(1, total))
    if not env_db:
        return {"n": 0}
    db = np.concatenate(env_db)
    c = np.concatenate(cent) if cent else np.zeros_like(db)
    h = np.concatenate(hfr) if hfr else np.zeros_like(db)
    c, h = c[: len(db)], h[: len(db)]
    if len(c) < len(db):
        c = np.pad(c, (0, len(db) - len(c)), mode="edge")
        h = np.pad(h, (0, len(db) - len(h)), mode="edge")

    fps = SR // HOP  # 20
    nsec = len(db) // fps
    db = db[: nsec * fps].reshape(nsec, fps)
    c = c[: nsec * fps].reshape(nsec, fps)
    h = h[: nsec * fps].reshape(nsec, fps)

    db_mean = db.mean(axis=1)
    db_max = db.max(axis=1)
    p_floor = np.percentile(db_mean, 10)
    voiced = db > (p_floor + 6)

    baseline = _rolling(db_mean, 90, np.median)
    excite = np.clip(db_max - baseline, 0, None)           # dB au-dessus du niveau habituel
    prev = np.concatenate([[db_mean[0]] * 3, db_mean])[:-3]
    prev3 = _rolling(prev, 3, np.mean)
    onset = np.clip(db_max - prev3, 0, None)               # montée soudaine

    # Cri : fort ET aigu/brillant
    w_c = np.where(voiced, c, np.nan)
    cent_sec = np.nan_to_num(np.nanmean(w_c, axis=1) if voiced.any() else np.zeros(nsec), nan=0.0)
    hf_sec = np.nan_to_num(np.nanmean(np.where(voiced, h, np.nan), axis=1) if voiced.any() else np.zeros(nsec), nan=0.0)
    cent_z = (cent_sec - np.median(cent_sec)) / (np.std(cent_sec) + 1e-6)
    hf_z = (hf_sec - np.median(hf_sec)) / (np.std(hf_sec) + 1e-6)
    scream_raw = excite * np.clip(0.5 + 0.35 * cent_z + 0.35 * hf_z, 0, 2.5)

    # Rire : enveloppe modulée à 3,5–7 Hz (rafales de syllabes « ha-ha-ha »)
    env_lin = 10 ** (db / 20)
    sig = np.concatenate([env_lin.reshape(-1), np.zeros(fps)])
    laugh = np.zeros(nsec, np.float32)
    L = int(fps * 1.6)
    freqs = np.fft.rfftfreq(L, 1 / fps)
    band = (freqs >= 3.5) & (freqs <= 7.0)
    other = (freqs >= 0.6) & ~band
    hann = np.hanning(L)
    for s in range(nsec):
        seg = sig[s * fps: s * fps + L]
        if len(seg) < L:
            break
        if db_mean[s] < baseline[s] - 3:
            continue
        seg = (seg - seg.mean()) * hann
        sp = np.abs(np.fft.rfft(seg)) ** 2
        ratio = sp[band].sum() / (sp[other].sum() + sp[band].sum() + 1e-12)
        laugh[s] = ratio
    laugh_raw = np.clip(laugh - 0.35, 0, None) * (voiced.mean(axis=1) > 0.4)

    silence = (db_mean < baseline - 8) | (db_max < p_floor + 4)

    return {
        "n": int(nsec),
        "db_mean": db_mean.astype(np.float32),
        "excite_db": excite.astype(np.float32),
        "loud": robust_norm(excite, 50, 99.5),
        "onset": robust_norm(onset, 60, 99.5),
        "scream": robust_norm(scream_raw, 70, 99.7),
        "laugh": robust_norm(laugh_raw, 80, 99.7),
        "silence": silence.astype(np.float32),
    }
