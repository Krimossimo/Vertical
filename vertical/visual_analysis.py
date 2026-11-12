"""Analyse visuelle : intensité de mouvement, flashs, écrans de mort, facecam,
et suivi de l'action pour le recadrage 9:16."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from . import media
from .audio_analysis import robust_norm

log = logging.getLogger("vertical")


def _gray(fr: np.ndarray) -> np.ndarray:
    return fr[..., 0] * 0.299 + fr[..., 1] * 0.587 + fr[..., 2] * 0.114


def global_features(times: np.ndarray, frames: np.ndarray, nsec: int, mask_box: dict | None = None,
                    src_size: tuple[int, int] | None = None) -> dict:
    """Courbes visuelles par seconde à partir des images échantillonnées."""
    if len(frames) < 3:
        z = np.zeros(nsec, np.float32)
        return {"motion": z, "flash": z, "red": z, "dark": z, "fade_dark": z, "static": z}
    f = frames.astype(np.float32)
    if mask_box and src_size:
        H, W = f.shape[1:3]
        sx, sy = W / src_size[0], H / src_size[1]
        x0, y0 = int(mask_box["x"] * sx), int(mask_box["y"] * sy)
        x1, y1 = int((mask_box["x"] + mask_box["w"]) * sx) + 1, int((mask_box["y"] + mask_box["h"]) * sy) + 1
        f[:, y0:y1, x0:x1, :] = f[:, y0:y1, x0:x1, :].mean(axis=0, keepdims=True)
    g = _gray(f)
    diff = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    diff = np.concatenate([[diff[0]], diff])
    dup = diff < 0.05  # image dupliquée (fps sur images clés)
    if dup.any() and (~dup).sum() > 2:
        idx = np.arange(len(diff))
        diff[dup] = np.interp(idx[dup], idx[~dup], diff[~dup])
    bright = g.mean(axis=(1, 2))
    r, gg, b = f[..., 0], f[..., 1], f[..., 2]
    redness = np.clip(r - (gg + b) / 2 - 25, 0, None).mean(axis=(1, 2))
    bjump = np.abs(np.diff(bright, prepend=bright[0]))

    sec = np.arange(nsec) + 0.5

    def to_sec(x):
        return np.interp(sec, times, x).astype(np.float32)

    motion = to_sec(diff)
    bright_s = to_sec(bright)
    # baseline locale du mouvement (le gameplay varie selon les jeux/scènes)
    from .audio_analysis import _rolling
    mbase = _rolling(motion, 120, np.median)
    motion_rel = np.clip(motion - mbase, 0, None) + 0.25 * motion
    prev_b = _rolling(np.concatenate([[bright_s[0]] * 8, bright_s])[:-8], 8, np.mean)
    fade_dark = np.clip(prev_b - bright_s, 0, None) * (bright_s < 40)
    static = (_rolling(motion, 20, np.max) < np.percentile(motion, 8)).astype(np.float32)
    return {
        "motion": robust_norm(motion_rel, 40, 99.5),
        "flash": robust_norm(to_sec(bjump), 80, 99.7),
        "red": robust_norm(to_sec(redness), 70, 99.5),
        "dark": (bright_s < 18).astype(np.float32),
        "fade_dark": robust_norm(fade_dark, 50, 99.5),
        "static": static,
    }


# --------------------------------------------------------------------------- facecam
def _cascades():
    import cv2
    if not hasattr(cv2, "CascadeClassifier"):
        return []
    from .config import APP_DIR
    out = []
    for name in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml"):
        for base in (Path(getattr(getattr(cv2, "data", None), "haarcascades", "") or "."), APP_DIR / "assets" / "cascades"):
            f = base / name
            if f.exists():
                c = cv2.CascadeClassifier(str(f))
                if not c.empty():
                    out.append(c)
                    break
    return out


def detect_facecam(src: str | Path, duration: float, width: int, height: int, samples: int = 30) -> dict | None:
    """Repère une incrustation webcam fixe : visage récurrent au même endroit + bords
    d'incrustation immobiles (contours moyens sur toute la VOD)."""
    try:
        import cv2
    except Exception:
        return None
    cascades = _cascades()
    if not cascades:
        log.warning("Détection de facecam indisponible (OpenCV sans CascadeClassifier)")
        return None
    pw = 960
    ph = int(round(pw * height / width / 2) * 2)
    ts = np.linspace(duration * 0.04, duration * 0.96, samples)
    boxes, grays = [], []
    for t in ts:
        fr = media.grab_frame_array(src, float(t), pw, ph)
        if fr is None:
            continue
        g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY)
        grays.append(g)
        ge = cv2.equalizeHist(g)
        for c in cascades:
            for (x, y, w, h) in c.detectMultiScale(ge, scaleFactor=1.08, minNeighbors=5, minSize=(16, 16)):
                if w < pw * 0.3:  # un visage plein écran n'est pas une facecam
                    boxes.append((x + w / 2, y + h / 2, w, h))
    if len(grays) < 4 or not boxes:
        return None
    b = np.array(boxes, dtype=np.float32)
    best, best_n = None, 0
    for cx, cy, w, h in b:
        near = (np.abs(b[:, 0] - cx) < w * 0.8) & (np.abs(b[:, 1] - cy) < h * 0.8)
        n_frames = near.sum()
        if n_frames > best_n:
            best_n, best = n_frames, b[near]
    if best is None or best_n < max(3, 0.25 * len(grays)):
        return None
    cx, cy, fw, fh = np.median(best, axis=0)
    # estimation par défaut : cadre carré-ish autour du visage
    cw = fw * 3.3
    ch = cw * 0.9
    x0, y0 = cx - cw / 2, cy - ch * 0.42
    try:
        edges = np.mean([cv2.Canny(g, 50, 150).astype(np.float32) / 255 for g in grays], axis=0)
        x0, y0, cw, ch = _refine_rect(edges, x0, y0, cw, ch, cx, cy, fw, fh)
    except Exception as e:
        log.warning("affinage facecam : %s", e)
    x0, y0 = max(0.0, x0), max(0.0, y0)
    cw, ch = min(cw, pw - x0), min(ch, ph - y0)
    s = width / pw
    return {"x": int(x0 * s), "y": int(y0 * s), "w": int(cw * s), "h": int(ch * s),
            "confidence": round(float(min(1.0, best_n / len(grays))), 2)}


def _refine_rect(edges, x0, y0, cw, ch, cx, cy, fw, fh):
    H, W = edges.shape
    def strongest(profile, lo, hi):
        lo, hi = int(max(0, lo)), int(min(len(profile) - 1, hi))
        if hi <= lo:
            return None
        seg = profile[lo:hi]
        i = int(np.argmax(seg))
        return lo + i if seg[i] > 0.3 else None
    r0, r1 = int(max(0, cy - fh)), int(min(H, cy + fh))
    c0, c1 = int(max(0, cx - fw)), int(min(W, cx + fw))
    col = edges[r0:r1].mean(axis=0)
    row = edges[:, c0:c1].mean(axis=1)
    L = strongest(col, cx - fw * 3, cx - fw * 0.9)
    R = strongest(col, cx + fw * 0.9, cx + fw * 3)
    T = strongest(row, cy - fh * 3, cy - fh * 0.9)
    B = strongest(row, cy + fh * 0.9, cy + fh * 3.5)
    left = L if L is not None else (0 if x0 < fw * 0.6 else x0)
    right = R if R is not None else (W if x0 + cw > W - fw * 0.6 else x0 + cw)
    top = T if T is not None else (0 if y0 < fh * 0.6 else y0)
    bottom = B if B is not None else (H if y0 + ch > H - fh * 0.6 else y0 + ch)
    if right - left < fw * 1.5 or bottom - top < fh * 1.5:
        return x0, y0, cw, ch
    return left, top, right - left, bottom - top


# --------------------------------------------------------------------------- suivi
def track_action(src: str | Path, start: float, end: float, src_w: int, src_h: int, crop_w_frac: float,
                 exclude: dict | None = None, fps: float = 4.0) -> list[tuple[float, float]]:
    """Centre horizontal (0..1) de la zone d'action au cours du temps.

    Combine énergie de mouvement par colonne, biais vers le centre (personnage
    des jeux à la 3e personne) et lissage fort pour éviter les à-coups.
    """
    W, H = 320, int(round(320 * src_h / src_w))
    times, fr = media.frames_in_window(src, start, end, fps, size=(W, H))
    if len(fr) < 3:
        return [(0.0, 0.5)]
    g = _gray(fr.astype(np.float32))
    top, bot = int(H * 0.08), int(H * 0.92)   # ignore les bandeaux HUD haut/bas
    if exclude:
        sx, sy = W / src_w, H / src_h
        x0, y0 = int(exclude["x"] * sx), int(exclude["y"] * sy)
        x1, y1 = int((exclude["x"] + exclude["w"]) * sx) + 1, int((exclude["y"] + exclude["h"]) * sy) + 1
        g[:, y0:y1, x0:x1] = 0
    d = np.abs(np.diff(g[:, top:bot], axis=0))
    d = np.concatenate([d[:1], d])
    col = d.mean(axis=1)                         # [T, W]
    cw = max(4, int(crop_w_frac * W))
    kernel = np.ones(cw) / cw
    xs = np.arange(W)
    prior = np.exp(-0.5 * ((xs - W / 2) / (W * 0.22)) ** 2)
    centers = []
    for t in range(len(col)):
        e = np.convolve(col[t], kernel, mode="same")
        e = e / (e.max() + 1e-6)
        score = 0.65 * e + 0.35 * prior
        c = float(np.argmax(score)) / W
        centers.append(c if e.max() > 0 else 0.5)
    c = np.array(centers)
    # lissage : médiane glissante puis EMA avec vitesse max
    k = 5
    cp = np.pad(c, (k // 2, k // 2), mode="edge")
    c = np.array([np.median(cp[i:i + k]) for i in range(len(c))])
    half = crop_w_frac / 2
    out, cur = [], float(np.clip(c[0], half, 1 - half))
    max_step = 0.06 / fps * 4   # ~6 % de largeur par seconde
    for t, v in zip(times, c):
        v = float(np.clip(v, half, 1 - half))
        delta = np.clip((v - cur) * 0.25, -max_step, max_step)
        if abs(v - cur) < 0.04:   # zone morte : pas de micro-mouvements
            delta = 0.0
        cur += delta
        out.append((float(t - start), cur))
    return out
