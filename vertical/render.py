"""Montage vertical 9:16 avec FFmpeg : recadrage intelligent, sous-titres, encodage GPU."""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from . import env, subtitles, transcribe, visual_analysis
from .config import FONTS_DIR, read_json

log = logging.getLogger("vertical")

LAYOUTS = {
    "facecam_fixed": "Facecam en haut + jeu fixe",
    "facecam_top": "Facecam en haut + jeu qui suit l'action",
    "center_crop": "Plein écran fixe (centré ou recadré)",
    "smart_crop": "Plein écran qui suit l'action",
    "blur_fill": "Image entière + fond flou",
}
CAM_FRAC = 0.36  # part de la hauteur occupée par la facecam


def resolve_layout(clip: dict, settings: dict, facecam: dict | None, track_default: bool = False) -> str:
    lay = clip.get("layout") or "auto"
    if lay == "auto":
        lay = settings.get("layout", "auto")
    if lay == "auto":
        if facecam:
            lay = "facecam_top" if (track_default and not clip.get("game_crop")) else "facecam_fixed"
        else:
            lay = "center_crop" if clip.get("game_crop") else "smart_crop"
    if lay in FACECAM and not facecam:
        lay = "smart_crop" if lay == "facecam_top" else "center_crop"
    return lay if lay in LAYOUTS else "smart_crop"


FACECAM = ("facecam_top", "facecam_fixed")
TRACKING = ("facecam_top", "smart_crop")  # ces cadrages suivent l'action : pas de zone fixe


def _even(x: float) -> int:
    return int(round(x / 2)) * 2


def _fonts_arg(tmp: Path) -> str:
    rel = os.path.relpath(FONTS_DIR, tmp).replace("\\", "/")
    if re.search(r"[:'\s,\[\];]", rel):
        dst = tmp / "fonts"
        if not dst.exists():
            shutil.copytree(FONTS_DIR, dst)
        rel = "fonts"
    return rel


def layout_cfg(proj: dict) -> dict:
    cfg = dict(proj.get("layout_cfg") or {})
    cfg.setdefault("cam_frac", CAM_FRAC)
    cfg.setdefault("cam_pos", "top")
    cfg.setdefault("game", None)
    cfg.setdefault("track", False)
    cfg["cam_frac"] = float(min(0.55, max(0.15, cfg["cam_frac"])))
    return cfg


def _cover(rect: dict, sw: int, sh: int, aspect: float) -> tuple[int, int, int, int]:
    """Recadre `rect` (pixels source) au ratio `aspect` (l/h) sans déformer, centré."""
    x, y, w, h = float(rect["x"]), float(rect["y"]), float(rect["w"]), float(rect["h"])
    if w / max(h, 1) > aspect:
        nw = h * aspect
        x += (w - nw) / 2
        w = nw
    else:
        nh = w / aspect
        y += (h - nh) / 2
        h = nh
    w, h = max(16, _even(w)), max(16, _even(h))
    x = max(0, min(sw - w, _even(x)))
    y = max(0, min(sh - h, _even(y)))
    return min(w, sw), min(h, sh), x, y


def build_filter(layout: str, info: dict, facecam: dict | None, track: list[tuple[float, float]] | None,
                 W: int, H: int, fps: float, dur: float, sub_file: str | None, fonts_rel: str,
                 fade: bool, tmp: Path, cfg: dict | None = None, bar: dict | None = None) -> str:
    sw, sh = info["width"], info["height"]
    chains = []
    track_cmds = []

    def crop_track(label_in: str, label_out: str, cw: int, ch: int, y: int, name: str):
        x0 = _even(((track[0][1] if track else 0.5) * sw) - cw / 2)
        x0 = max(0, min(sw - cw, x0))
        chains.append(f"[{label_in}]crop@{name}=w={cw}:h={ch}:x={x0}:y={y}[{label_out}]")
        if track and len(track) > 1:
            last = None
            for t, c in track:
                x = max(0, min(sw - cw, _even(c * sw - cw / 2)))
                if x != last:
                    track_cmds.append(f"{t:.3f} crop@{name} x {x};")
                    last = x

    if layout in FACECAM:
        cfg = cfg or {"cam_frac": CAM_FRAC, "cam_pos": "top", "game": None}
        cam_h = _even(H * cfg["cam_frac"])
        game_h = H - cam_h
        cw_, ch_, cx_, cy_ = _cover(facecam, sw, sh, W / cam_h)
        chains.append("[0:v]split=2[camsrc][gsrc]")
        chains.append(f"[camsrc]crop={cw_}:{ch_}:{cx_}:{cy_},scale={W}:{cam_h}:flags=lanczos,setsar=1[cam]")
        if cfg.get("game"):
            gw, gh, gx, gy = _cover(cfg["game"], sw, sh, W / game_h)
            chains.append(f"[gsrc]crop={gw}:{gh}:{gx}:{gy}[gcrop]")
        else:
            ch = sh
            cw = min(sw, _even(ch * W / game_h))
            crop_track("gsrc", "gcrop", cw, ch, 0, "track")
        chains.append(f"[gcrop]scale={W}:{game_h}:flags=lanczos,setsar=1[game]")
        if cfg.get("cam_pos") == "bottom":
            chains.append("[game][cam]vstack=inputs=2[base]")
        else:
            chains.append("[cam][game]vstack=inputs=2[base]")
    elif layout in ("smart_crop", "center_crop") and cfg and cfg.get("game"):
        gw, gh, gx, gy = _cover(cfg["game"], sw, sh, W / H)
        chains.append(f"[0:v]crop={gw}:{gh}:{gx}:{gy},scale={W}:{H}:flags=lanczos,setsar=1[base]")
    elif layout in ("smart_crop", "center_crop"):
        ch = sh
        cw = min(sw, _even(ch * W / H))
        if layout == "center_crop":
            track = [(0.0, 0.5)]
        crop_track("0:v", "vc", cw, ch, 0, "track")
        chains.append(f"[vc]scale={W}:{H}:flags=lanczos[base]")
    else:  # blur_fill
        chains.append("[0:v]split=2[bgsrc][fgsrc]")
        chains.append(f"[bgsrc]scale={W // 4}:{H // 4}:force_original_aspect_ratio=increase,crop={W // 4}:{H // 4},"
                      f"boxblur=10:2,eq=brightness=-0.08:saturation=1.2,scale={W}:{H}[bg]")
        if cfg and cfg.get("game"):
            gw, gh, gx, gy = _cover(cfg["game"], sw, sh, 16 / 9)
            chains.append(f"[fgsrc]crop={gw}:{gh}:{gx}:{gy},scale={W}:-2:flags=lanczos,setsar=1[fg]")
        else:
            chains.append(f"[fgsrc]scale={W}:-2:flags=lanczos[fg]")
        chains.append("[bg][fg]overlay=(W-w)/2:(H-h)/2[base]")

    if track_cmds:
        (tmp / "cmds.txt").write_text("\n".join(track_cmds) + "\n", encoding="utf-8")
        # sendcmd doit précéder le filtre crop visé dans la chaîne
        for i, c in enumerate(chains):
            if "crop@track" in c:
                lbl, rest = c.split("]", 1)
                chains[i] = f"{lbl}]sendcmd=f=cmds.txt,{rest}"
                break
    post = f"fps={fps:g}"
    if sub_file:
        post += f",subtitles={sub_file}:fontsdir={fonts_rel}"
    if fade:
        post += f",fade=t=in:st=0:d=0.12,fade=t=out:st={max(0.0, dur - 0.3):.3f}:d=0.3"
    post += ",format=yuv420p"
    if bar and bar.get("enabled"):  # barre de progression en bas de l'écran
        bh = max(4, min(40, int(bar.get("height", 10)) * H // 1920))
        col = str(bar.get("color", "#FFFFFF")).lstrip("#")[:6] or "FFFFFF"
        chains.append(f"[base]{post}[pre]")
        chains.append(f"color=c=0x{col}:s={W}x{bh}:r={fps:g}:d={dur:.3f}[bar]")
        chains.append(f"[pre][bar]overlay=x='-w+w*t/{dur:.3f}':y=H-h:eval=frame:shortest=1,format=yuv420p[vout]")
    else:
        chains.append(f"[base]{post}[vout]")
    return ";".join(chains)


def encoder_args(quality: str, preview: bool, use_nvenc: bool) -> list[str]:
    if preview:
        if use_nvenc:
            return ["-c:v", "h264_nvenc", "-preset", "p2", "-cq", "28", "-b:v", "0"]
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28"]
    cq = {"standard": 23, "haute": 19, "max": 16}.get(quality, 19)
    if use_nvenc:
        return ["-c:v", "h264_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", str(cq), "-b:v", "0",
                "-maxrate", "30M", "-bufsize", "60M", "-profile:v", "high", "-spatial-aq", "1", "-temporal-aq", "1",
                "-rc-lookahead", "20", "-bf", "3"]
    crf = cq - 1
    preset = {"standard": "fast", "haute": "medium", "max": "slow"}.get(quality, "medium")
    return ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high"]


def render_clip(proj: dict, clip: dict, settings: dict, out: Path, tmp: Path, preview: bool = False,
                on_progress: Callable[[float], None] | None = None, metadata: dict | None = None) -> Path:
    info = proj["info"]
    vod = proj["vod_path"]
    facecam = proj.get("facecam")
    start, end = float(clip["start"]), float(clip["end"])
    dur = max(1.0, end - start)
    W, H = (540, 960) if preview else (1080, 1920)
    fps = min(float(info.get("fps") or 30), float(settings.get("fps", 60)))
    if preview:
        fps = min(fps, 30)
    cfg = layout_cfg(proj)
    layout = resolve_layout(clip, settings, facecam, bool(cfg.get("track")))
    if layout in TRACKING:
        cfg["game"] = None  # suivi de l'action demandé : on ignore les zones fixes
    elif clip.get("game_crop"):  # recadrage de la scène propre à ce Short
        cfg["game"] = clip["game_crop"]
    elif layout == "blur_fill":
        cfg["game"] = None
    tmp.mkdir(parents=True, exist_ok=True)

    track = None
    if layout in TRACKING:
        sw, sh = info["width"], info["height"]
        if layout == "smart_crop":
            frac = min(1.0, (sh * W / H) / sw)
        else:
            frac = min(1.0, (sh * W / (H - _even(H * cfg["cam_frac"]))) / sw)
        try:
            track = visual_analysis.track_action(vod, start, end, sw, sh, frac, exclude=facecam)
        except Exception as e:
            log.warning("suivi d'action impossible : %s", e)
            track = [(0.0, 0.5)]

    # sous-titres
    sub_file = None
    st = settings.get("subtitles", {})
    top_safe = (cfg["cam_frac"] + 0.04) if layout in FACECAM and cfg.get("cam_pos") != "bottom" else 0.1
    extra = subtitles.extras(settings, str(clip.get("title") or ""), dur, W, H, top_safe)
    if extra["events"] and not st.get("enabled", True):
        (tmp / "subs.ass").write_text(subtitles.build_ass([], start, end, st, W, H, int(H * 0.7), None, extra),
                                      encoding="utf-8")
        sub_file = "subs.ass"
    if st.get("enabled", True):
        tr = read_json(Path(proj["_dir"]) / "transcript.json", {"segments": []})
        words = transcribe.words_flat(tr)
        if words:
            pos = st.get("position", "auto")
            if pos == "custom" and not st.get("pos"):
                pos = "auto"
            if pos == "auto":
                pos = "seam" if layout in FACECAM else ("bas" if layout == "blur_fill" else "bas_haut")
            seam = (cfg["cam_frac"] + 0.09) if cfg.get("cam_pos") != "bottom" else (1 - cfg["cam_frac"] - 0.09)
            y = {"haut": 0.2, "milieu": 0.5, "bas": 0.8, "bas_haut": 0.70, "seam": seam}.get(pos, 0.72)
            x = 0.5
            custom = clip.get("sub_pos") or (st.get("pos") if pos == "custom" else None)
            if custom:  # position placée à la souris (par Short ou pour tous)
                x = min(0.95, max(0.05, float(custom.get("x", 0.5))))
                y = min(0.97, max(0.03, float(custom.get("y", 0.7))))
            ass = subtitles.build_ass(words, start, end, st, W, H, int(H * y), int(W * x), extra)
            (tmp / "subs.ass").write_text(ass, encoding="utf-8")
            sub_file = "subs.ass"
        elif extra["events"]:
            (tmp / "subs.ass").write_text(subtitles.build_ass([], start, end, st, W, H, int(H * 0.7), None, extra),
                                          encoding="utf-8")
            sub_file = "subs.ass"

    caps = env.ffmpeg_caps()
    fonts_rel = _fonts_arg(tmp)
    fade = bool(settings.get("fade", True))
    fg = build_filter(layout, info, facecam, track, W, H, fps, dur, sub_file, fonts_rel, fade, tmp, cfg,
                      settings.get("progress_bar"))
    (tmp / "graph.txt").write_text(fg, encoding="utf-8")  # pour le débogage

    af = ["aresample=48000"]
    if fade:
        af += ["afade=t=in:st=0:d=0.15", f"afade=t=out:st={max(0.0, dur - 0.35):.3f}:d=0.35"]
    if settings.get("loudnorm", True) and not preview:
        af.append("loudnorm=I=-14:TP=-1.5:LRA=11")

    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.stem + ".part.mp4")

    def cmd(nvenc: bool) -> list[str]:
        c = [env.ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
             "-i", vod, "-filter_complex", fg, "-map", "[vout]"]
        if info.get("has_audio", True):
            c += ["-map", "0:a:0?", "-af", ",".join(af), "-c:a", "aac", "-b:a", "128k" if preview else "192k",
                  "-ar", "48000"]
        c += encoder_args(settings.get("quality", "haute"), preview, nvenc)
        for k, v in (metadata or {}).items():  # permet de retrouver le projet en réimportant le Short
            c += ["-metadata", f"{k}={v}"]
        c += ["-pix_fmt", "yuv420p", "-movflags", "+faststart", "-progress", "pipe:1", "-nostats", str(part)]
        return c

    attempts = [True, False] if caps.get("nvenc") else [False]
    last_err = ""
    for nv in attempts:
        p = env.popen(cmd(nv), cwd=str(tmp), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                      errors="ignore")
        assert p.stdout
        for line in p.stdout:
            if line.startswith("out_time_us=") and on_progress:
                try:
                    on_progress(min(1.0, int(line.split("=")[1]) / 1e6 / dur))
                except ValueError:
                    pass
        last_err = p.stderr.read() if p.stderr else ""
        if p.wait() == 0 and part.exists() and part.stat().st_size > 1000:
            part.replace(out)
            return out
        log.warning("Encodage %s échoué : %s", "NVENC" if nv else "x264", last_err[-400:])
    raise RuntimeError("Le rendu FFmpeg a échoué : " + last_err.strip()[-400:])
