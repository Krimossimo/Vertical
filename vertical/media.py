"""Accès média via FFmpeg : sonde, extraction audio, échantillonnage d'images."""
from __future__ import annotations

import json
import logging
import subprocess
import wave
from fractions import Fraction
from pathlib import Path
from typing import Callable

import numpy as np

from . import env

log = logging.getLogger("vertical")

SR = 16000  # fréquence d'échantillonnage pour l'analyse et Whisper


def probe(path: str | Path) -> dict:
    out = env.run([env.ffprobe(), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                  text=True, errors="ignore")
    if out.returncode != 0:
        raise RuntimeError(f"Impossible de lire la vidéo : {out.stderr.strip()[:300]}")
    data = json.loads(out.stdout)
    v = next((s for s in data["streams"] if s.get("codec_type") == "video"), None)
    auds = [s for s in data["streams"] if s.get("codec_type") == "audio"]
    a = auds[0] if auds else None
    if v is None:
        raise RuntimeError("Aucune piste vidéo trouvée dans ce fichier.")
    dur = float(data["format"].get("duration") or v.get("duration") or 0)
    try:
        fps = float(Fraction(v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1"))
    except Exception:
        fps = 30.0
    if not fps or fps > 240:
        fps = 30.0
    return {
        "duration": dur,
        "width": int(v["width"]),
        "height": int(v["height"]),
        "fps": round(fps, 3),
        "vcodec": v.get("codec_name"),
        "acodec": a.get("codec_name") if a else None,
        "has_audio": a is not None,
        "n_audio": len(auds),
        "container": data["format"].get("format_name", ""),
        "size": int(data["format"].get("size") or 0),
    }


def _run_with_progress(cmd: list[str], duration: float, on_progress: Callable[[float], None] | None) -> None:
    cmd = cmd[:1] + ["-progress", "pipe:1", "-nostats"] + cmd[1:]
    p = env.popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
    assert p.stdout
    for line in p.stdout:
        if line.startswith("out_time_us=") or line.startswith("out_time_ms="):
            try:
                t = int(line.split("=")[1]) / 1e6
                if on_progress and duration > 0:
                    on_progress(min(1.0, t / duration))
            except ValueError:
                pass
    err = p.stderr.read() if p.stderr else ""
    if p.wait() != 0:
        raise RuntimeError("FFmpeg a échoué : " + err.strip()[-500:])


def extract_audio(src: str | Path, dst: Path, duration: float, on_progress=None) -> Path:
    if dst.exists() and dst.stat().st_size > 1000:
        return dst
    tmp = dst.with_suffix(".tmp.wav")
    _run_with_progress([env.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1",
                        "-ar", str(SR), "-c:a", "pcm_s16le", str(tmp)], duration, on_progress)
    tmp.replace(dst)
    return dst


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        n = w.getnframes()
        raw = w.readframes(n)
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def sample_frames(src: str | Path, duration: float, size=(96, 54), step: float = 2.0,
                  keyframes_only: bool = True, on_progress=None) -> tuple[np.ndarray, np.ndarray]:
    """Images RGB basse résolution échantillonnées sur toute la VOD.

    Par défaut on ne décode que les images clés (très rapide sur une VOD de 2 h,
    Twitch en place une toutes les 2 s). Retourne (temps, images[N,H,W,3]).
    """
    w, h = size
    cmd = [env.ffmpeg(), "-hide_banner", "-loglevel", "error"]
    if keyframes_only:
        cmd += ["-skip_frame", "nokey"]
    cmd += ["-i", str(src), "-an", "-sn", "-vf", f"fps=1/{step},scale={w}:{h}:flags=area,format=rgb24",
            "-f", "rawvideo", "-"]
    p = env.popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    frame_bytes = w * h * 3
    frames = []
    expected = max(1, int(duration / step))
    assert p.stdout
    while True:
        buf = p.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        frames.append(np.frombuffer(buf, np.uint8).reshape(h, w, 3))
        if on_progress and len(frames) % 50 == 0:
            on_progress(min(1.0, len(frames) / expected))
    p.wait()
    if not frames:
        return np.zeros(0), np.zeros((0, h, w, 3), np.uint8)
    arr = np.stack(frames)
    times = np.arange(len(arr)) * step + step / 2
    return times, arr


def frames_in_window(src: str | Path, start: float, end: float, fps: float, size=(224, 224),
                     crop: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Images d'une fenêtre précise (recherche rapide avec -ss avant -i)."""
    w, h = size
    vf = f"fps={fps}"
    if crop:
        vf += f",crop={crop}"
    vf += f",scale={w}:{h}:flags=bilinear,format=rgb24"
    dur = max(0.1, end - start)
    cmd = [env.ffmpeg(), "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, start):.3f}", "-i", str(src),
           "-t", f"{dur:.3f}", "-an", "-sn", "-vf", vf, "-f", "rawvideo", "-"]
    out = env.run(cmd).stdout
    fb = w * h * 3
    n = len(out) // fb
    if n == 0:
        return np.zeros(0), np.zeros((0, h, w, 3), np.uint8)
    arr = np.frombuffer(out[: n * fb], np.uint8).reshape(n, h, w, 3)
    times = start + (np.arange(n) + 0.5) / fps
    return times, arr


def grab_frame(src: str | Path, t: float, dst: Path, width: int = 640) -> Path:
    env.run([env.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(src),
             "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "3", str(dst)])
    return dst


def grab_frame_array(src: str | Path, t: float, width: int, height: int) -> np.ndarray | None:
    out = env.run([env.ffmpeg(), "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(src),
                   "-frames:v", "1", "-vf", f"scale={width}:{height},format=rgb24", "-f", "rawvideo", "-"]).stdout
    if len(out) < width * height * 3:
        return None
    return np.frombuffer(out[: width * height * 3], np.uint8).reshape(height, width, 3)
