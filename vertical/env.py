"""Détection de l'environnement : FFmpeg, GPU, bibliothèques optionnelles.

Chaque brique a une solution de secours : si une dépendance manque, l'analyse
continue avec les signaux disponibles et le rapport l'indique dans l'interface.
"""
from __future__ import annotations

import functools
import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

from .config import TOOLS_DIR

log = logging.getLogger("vertical")

IS_WIN = os.name == "nt"
CREATE_NO_WINDOW = 0x08000000 if IS_WIN else 0


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    """subprocess.run sans fenêtre console sous Windows."""
    kw.setdefault("capture_output", True)
    if IS_WIN:
        kw.setdefault("creationflags", CREATE_NO_WINDOW)
    return subprocess.run([str(c) for c in cmd], **kw)


def popen(cmd: list[str], **kw) -> subprocess.Popen:
    if IS_WIN:
        kw.setdefault("creationflags", CREATE_NO_WINDOW)
    return subprocess.Popen([str(c) for c in cmd], **kw)


# --------------------------------------------------------------------------- FFmpeg
def _find_tool(name: str) -> str | None:
    exe = name + (".exe" if IS_WIN else "")
    for cand in (TOOLS_DIR / "ffmpeg" / "bin" / exe, TOOLS_DIR / "ffmpeg" / exe):
        if cand.exists():
            return str(cand)
    found = shutil.which(name)
    if found:
        return found
    if IS_WIN:  # emplacements courants (winget, choco, scoop)
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        for pattern in ("Microsoft/WinGet/Packages/*FFmpeg*/**/bin/" + exe,):
            for p in local.glob(pattern):
                return str(p)
        for p in (Path("C:/ffmpeg/bin") / exe, Path("C:/ProgramData/chocolatey/bin") / exe,
                  Path.home() / "scoop/shims" / exe):
            if p.exists():
                return str(p)
    return None


@functools.lru_cache(maxsize=None)
def ffmpeg() -> str:
    p = _find_tool("ffmpeg")
    if not p:
        raise RuntimeError("FFmpeg introuvable. Relance « Installer.bat » pour l'installer automatiquement.")
    return p


@functools.lru_cache(maxsize=None)
def ffprobe() -> str:
    p = _find_tool("ffprobe")
    if not p:
        raise RuntimeError("FFprobe introuvable. Relance « Installer.bat ».")
    return p


@functools.lru_cache(maxsize=None)
def ffmpeg_caps() -> dict:
    caps = {"available": False, "nvenc": False, "libx264": False, "libass": False, "cuda_decode": False, "version": ""}
    try:
        exe = ffmpeg()
    except RuntimeError:
        return caps
    caps["available"] = True
    try:
        caps["version"] = run([exe, "-hide_banner", "-version"], text=True).stdout.splitlines()[0]
    except Exception:
        pass
    enc = run([exe, "-hide_banner", "-encoders"], text=True, errors="ignore").stdout
    flt = run([exe, "-hide_banner", "-filters"], text=True, errors="ignore").stdout
    hw = run([exe, "-hide_banner", "-hwaccels"], text=True, errors="ignore").stdout
    caps["libx264"] = " libx264 " in enc
    caps["libass"] = " subtitles " in flt
    caps["cuda_decode"] = "cuda" in hw
    if " h264_nvenc " in enc:
        # L'encodeur peut être compilé sans GPU compatible : on teste réellement.
        t = run([exe, "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=black:s=256x256:d=0.2",
                 "-c:v", "h264_nvenc", "-f", "null", "-"], text=True, errors="ignore")
        caps["nvenc"] = t.returncode == 0
    return caps


# --------------------------------------------------------------------------- CUDA / DLL
_dll_done = False


def setup_cuda_dlls() -> list[str]:
    """Rend visibles les DLL CUDA/cuDNN fournies par torch ou les paquets nvidia-*.

    faster-whisper (CTranslate2) a besoin de cublas64_12 et cudnn*_9 : sous Windows
    on réutilise celles livrées avec PyTorch pour éviter toute installation manuelle.
    """
    global _dll_done
    added: list[str] = []
    if _dll_done:
        return added
    _dll_done = True
    roots = {Path(sysconfig.get_paths()["purelib"]), Path(sys.prefix) / "Lib" / "site-packages"}
    cands: list[Path] = []
    for r in roots:
        cands.append(r / "torch" / "lib")
        nv = r / "nvidia"
        if nv.exists():
            cands += [p / "bin" for p in nv.iterdir()] + [p / "lib" for p in nv.iterdir()]
        cands.append(r / "ctranslate2")
    for c in cands:
        if c.is_dir() and any(c.glob("*.dll" if IS_WIN else "*.so*")):
            s = str(c)
            if IS_WIN:
                try:
                    os.add_dll_directory(s)
                except Exception:
                    pass
            os.environ["PATH"] = s + os.pathsep + os.environ.get("PATH", "")
            added.append(s)
    return added


def has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


@functools.lru_cache(maxsize=None)
def gpu_info() -> dict:
    info = {"cuda": False, "name": "", "vram_gb": 0.0, "source": ""}
    if has_module("torch"):
        try:
            import torch
            if torch.cuda.is_available():
                p = torch.cuda.get_device_properties(0)
                info.update(cuda=True, name=p.name, vram_gb=round(p.total_memory / 1024 ** 3, 1), source="torch")
                return info
        except Exception as e:  # pragma: no cover
            log.warning("torch CUDA indisponible: %s", e)
    smi = shutil.which("nvidia-smi")
    if smi:
        try:
            out = run([smi, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"], text=True, timeout=10).stdout
            name, mem = [x.strip() for x in out.splitlines()[0].split(",")]
            info.update(name=name, vram_gb=round(float(mem) / 1024, 1), source="nvidia-smi")
            if has_module("ctranslate2"):
                setup_cuda_dlls()
                import ctranslate2
                info["cuda"] = ctranslate2.get_cuda_device_count() > 0
        except Exception:
            pass
    return info


def torch_device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def ollama_status(url: str) -> dict:
    """Ollama est optionnel : utilisé pour des titres plus naturels s'il est installé."""
    try:
        import json
        import urllib.request
        with urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=1.5) as r:
            models = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
        return {"running": True, "models": models}
    except Exception:
        return {"running": False, "models": []}


def report(settings: dict | None = None) -> dict:
    caps = ffmpeg_caps()
    gpu = gpu_info()
    rep = {
        "python": sys.version.split()[0],
        "ffmpeg": caps,
        "gpu": gpu,
        "faster_whisper": has_module("faster_whisper"),
        "torch": has_module("torch"),
        "transformers": has_module("transformers"),
        "opencv": has_module("cv2"),
        "webview": has_module("webview"),
    }
    if settings is not None:
        rep["ollama"] = ollama_status(settings.get("ollama_url", "http://127.0.0.1:11434"))
    notes = []
    if not caps["available"]:
        notes.append("env.no_ffmpeg")
    if caps["available"] and not caps["nvenc"]:
        notes.append("env.no_nvenc")
    if not rep["faster_whisper"]:
        notes.append("env.no_whisper")
    if not gpu["cuda"]:
        notes.append("env.no_cuda")
    if not (rep["torch"] and rep["transformers"]):
        notes.append("env.no_ai")
    rep["note_codes"] = notes  # traduits au moment de l'affichage (i18n)
    return rep
