"""Fusion des signaux, sélection des meilleurs moments, découpage propre et explications."""
from __future__ import annotations

import math

import numpy as np

DEFAULT_WEIGHTS = {
    # audio
    "loud": 1.0, "game_loud": 0.45, "onset": 0.6, "scream": 1.0, "laugh": 0.7,
    # paroles
    "excl": 0.9, "laugh_txt": 0.8, "game_kw": 0.8, "rate": 0.3, "repeat": 0.5,
    # image
    "motion": 0.6, "flash": 0.35, "red": 0.3, "fade_dark": 0.5,
    # IA (zones candidates uniquement)
    "clip_event": 1.1, "ast_laugh": 0.9, "ast_scream": 0.9, "ast_cheer": 0.5, "ast_boom": 0.35,
    "ast_impact": 0.3, "ast_gasp": 0.3,
    # pénalités
    "static": -0.7, "dark": -0.25,
}

CATEGORY_LABELS = {
    "combat": "Combat épique", "skill": "Action technique", "echec": "Échec / mort", "victoire": "Victoire",
    "drole": "Moment drôle", "reaction": "Grosse réaction", "tension": "Moment tendu", "inattendu": "Inattendu",
}


def gauss_smooth(x: np.ndarray, sigma: float) -> np.ndarray:
    if len(x) == 0 or sigma <= 0:
        return x
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(x, (r, r), mode="edge"), k, mode="valid")


def max_filter(x: np.ndarray, w: int) -> np.ndarray:
    from .audio_analysis import _rolling
    return _rolling(x, w, np.max)


def combine(feats: dict[str, np.ndarray], n: int, weights: dict | None = None) -> np.ndarray:
    w = dict(DEFAULT_WEIGHTS)
    w.update(weights or {})
    raw = np.zeros(n, np.float32)
    for k, wk in w.items():
        f = feats.get(k)
        if f is None or len(f) == 0:
            continue
        f = f[:n] if len(f) >= n else np.pad(f, (0, n - len(f)))
        raw += wk * f
    raw = np.clip(raw, 0, None)
    return (0.6 * gauss_smooth(raw, 3.0) + 0.4 * max_filter(raw, 5)).astype(np.float32)


def pick_peaks(curve: np.ndarray, k: int, min_gap: float, skip_start: float = 0, skip_end: float = 0) -> list[int]:
    c = curve.copy()
    n = len(c)
    c[: int(skip_start)] = 0
    if skip_end:
        c[max(0, n - int(skip_end)):] = 0
    peaks = []
    floor = np.percentile(curve, 60) if n else 0
    while len(peaks) < k:
        i = int(np.argmax(c))
        if c[i] <= floor or c[i] <= 0:
            break
        peaks.append(i)
        a, b = max(0, int(i - min_gap)), min(n, int(i + min_gap) + 1)
        c[a:b] = 0
    return peaks


# --------------------------------------------------------------------------- découpe
def _gaps(words: list[dict]) -> list[tuple[float, float]]:
    return [(words[i]["end"], words[i + 1]["start"]) for i in range(len(words) - 1)
            if words[i + 1]["start"] - words[i]["end"] > 0.25]


def snap_start(t: float, words: list[dict], gaps: list[tuple[float, float]], lo: float, hi: float) -> float:
    best, best_cost = None, 1e9
    for g0, g1 in gaps:
        cut = max(g0, g1 - 0.2)
        if lo <= cut <= hi:
            cost = abs(cut - t) - 1.2 * min(g1 - g0, 1.5)
            if cost < best_cost:
                best, best_cost = cut, cost
    if best is not None:
        return best
    for w in words:  # pas de pause : on évite au moins de couper un mot
        if w["start"] < t < w["end"]:
            return max(0.0, w["start"] - 0.05)
    return t


def snap_end(t: float, words: list[dict], gaps: list[tuple[float, float]], lo: float, hi: float) -> float:
    best, best_cost = None, 1e9
    for g0, g1 in gaps:
        cut = g0 + min(0.35, (g1 - g0) / 2)
        if lo <= cut <= hi:
            cost = abs(cut - t) - 1.2 * min(g1 - g0, 1.5)
            if cost < best_cost:
                best, best_cost = cut, cost
    if best is not None:
        return best
    for w in words:
        if w["start"] < t < w["end"]:
            return w["end"] + 0.1
    return t


def refine_window(peak: int, curve: np.ndarray, dmin: float, dmax: float, words: list[dict],
                  duration: float) -> tuple[float, float]:
    n = len(curve)
    pv = curve[peak]
    target = (dmin + dmax) / 2
    # zone d'événement autour du pic
    a = peak
    while a > 0 and peak - a < 25 and curve[a - 1] > 0.45 * pv:
        a -= 1
    b = peak
    while b < n - 1 and b - peak < 20 and curve[b + 1] > 0.45 * pv:
        b += 1
    pre = min(15.0, max(5.0, 0.35 * target))
    post = min(8.0, max(2.5, 0.15 * target))
    start, end = a - pre, b + 1 + post
    L = end - start
    if L < dmin:
        extra = dmin - L
        start -= 0.6 * extra
        end += 0.4 * extra
    elif L > dmax:
        best, best_s = None, -1
        lo = peak + 3 - dmax
        hi = peak - min(5.0, 0.25 * dmax)
        s = lo
        while s <= hi:
            i0, i1 = int(max(0, s)), int(min(n, s + dmax))
            val = float(curve[i0:i1].sum())
            if val > best_s:
                best_s, best = val, s
            s += 0.5
        start = best if best is not None else peak - dmax * 0.6
        end = start + dmax
    # bornes vidéo
    if start < 0:
        end -= start
        start = 0.0
    if end > duration:
        start -= end - duration
        end = duration
        start = max(0.0, start)
    # alignement sur les pauses de parole pour éviter les coupures brutales
    if words:
        lw = [w for w in words if start - 4 < w["end"] and w["start"] < end + 4]
        gaps = _gaps(lw)
        start = snap_start(start, lw, gaps, start - 2.5, start + 1.0)
        end = snap_end(end, lw, gaps, end - 1.0, end + 2.5)
    start, end = max(0.0, start), min(duration, end)
    if end - start > dmax + 3:
        end = start + dmax + 3
    return round(start, 2), round(end, 2)


# --------------------------------------------------------------------------- score & explications
def relevance(curve: np.ndarray, start: float, end: float, ref: float) -> float:
    seg = curve[int(start): max(int(start) + 1, int(math.ceil(end)))]
    if len(seg) == 0:
        return 0.0
    top = np.sort(seg)[-max(3, len(seg) // 6):]
    intensity = float(top.mean()) / (ref + 1e-6)
    return round(min(99.0, 100 * (1 - math.exp(-1.25 * intensity))), 1)


def _win_mean_top(x: np.ndarray | None, s: int, e: int, k: int = 3) -> float:
    if x is None or len(x) == 0:
        return 0.0
    seg = x[s:e]
    if len(seg) == 0:
        return 0.0
    return float(np.sort(seg)[-k:].mean())


def explain(feats: dict, start: float, end: float, transcript_hits: dict, clip_labels: dict, weights: dict | None = None,
            clip_labels_en: dict | None = None) -> tuple[list[dict], dict[str, float], str]:
    """Raisons (codes traduisibles), contributions par signal."""
    w = dict(DEFAULT_WEIGHTS)
    w.update(weights or {})
    s, e = int(start), int(math.ceil(end))
    contrib = {k: _win_mean_top(feats.get(k), s, e) * w[k] for k in w if w[k] > 0}
    reasons: list[tuple[float, dict]] = []
    exdb = _win_mean_top(feats.get("excite_db"), s, e, 2)

    def add(key, code, thr=0.25, **v):
        val = contrib.get(key, 0)
        if val >= thr:
            reasons.append((val, {"k": code, "v": v}))

    voice = _win_mean_top(feats.get("speech_near"), s, e, 3) > 0.5 if feats.get("speech_near") is not None else True
    add("loud", "voice_up" if voice else "sound_peak", db=f"{exdb:.0f}")
    if voice:
        add("scream", "scream")
    add("game_loud", "game_loud")
    add("ast_scream", "ast_scream")
    lt = max(contrib.get("laugh", 0), contrib.get("laugh_txt", 0), contrib.get("ast_laugh", 0))
    if lt >= 0.25:
        reasons.append((lt, {"k": "laugh", "v": {}}))
    ex_words = transcript_hits.get("excl_words") or []
    if contrib.get("excl", 0) >= 0.25:
        reasons.append((contrib["excl"], {"k": "excl" if ex_words else "excl0", "v": {"words": ", ".join(f"« {x} »" for x in ex_words[:3])}}))
    kws = transcript_hits.get("game_words") or []
    if contrib.get("game_kw", 0) >= 0.2 and kws:
        reasons.append((contrib["game_kw"], {"k": "game_kw", "v": {"words": ", ".join(kws[:4])}}))
    add("repeat", "repeat")
    add("motion", "motion")
    add("flash", "flash", 0.2)
    add("red", "red", 0.2)
    add("fade_dark", "fade_dark", 0.2)
    add("ast_cheer", "ast_cheer", 0.2)
    add("ast_boom", "ast_boom", 0.2)
    add("ast_impact", "ast_impact", 0.2)
    for lab, p in sorted(clip_labels.items(), key=lambda x: -x[1])[:2]:
        if p >= 0.2:
            en = (clip_labels_en or {}).get(lab, lab)
            reasons.append((1.0 * p + 0.3, {"k": "event", "v": {"fr": lab.lower(), "en": en.lower(), "p": f"{p:.0%}"}}))
    reasons.sort(key=lambda x: -x[0])
    return [r[1] for r in reasons[:5]], {k: round(v, 3) for k, v in contrib.items() if v > 0.01}, ""


def categorize(feats: dict, start: float, end: float, text_cats: dict, clip_cats: dict) -> str:
    s, e = int(start), int(math.ceil(end))
    votes: dict[str, float] = {}

    def v(c, x):
        votes[c] = votes.get(c, 0) + x

    for c, arr in text_cats.items():
        v(c, 0.8 * _win_mean_top(arr, s, e, 2))
    for c, p in clip_cats.items():
        v(c, 1.3 * p)
    v("drole", 1.2 * max(_win_mean_top(feats.get("laugh_txt"), s, e), _win_mean_top(feats.get("ast_laugh"), s, e),
                         0.7 * _win_mean_top(feats.get("laugh"), s, e)))
    v("reaction", 0.6 * max(_win_mean_top(feats.get("scream"), s, e), _win_mean_top(feats.get("ast_scream"), s, e)))
    v("echec", 0.8 * _win_mean_top(feats.get("fade_dark"), s, e))
    v("victoire", 0.7 * _win_mean_top(feats.get("ast_cheer"), s, e))
    v("combat", 0.4 * _win_mean_top(feats.get("motion"), s, e) + 0.2 * _win_mean_top(feats.get("ast_impact"), s, e))
    best = max(votes.items(), key=lambda x: x[1]) if votes else ("reaction", 0)
    return best[0] if best[1] > 0.15 else "reaction"
