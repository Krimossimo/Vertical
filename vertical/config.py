"""Chemins de l'application et réglages persistants."""
from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
APP_DIR = PKG_DIR.parent
DATA_DIR = Path(os.environ.get("VERTICAL_DATA", APP_DIR / "data"))
PROJECTS_DIR = DATA_DIR / "projects"
MODELS_DIR = APP_DIR / "models"
TOOLS_DIR = APP_DIR / "tools"
FONTS_DIR = APP_DIR / "assets" / "fonts"
WEB_DIR = PKG_DIR / "web"
PROFILES_DIR = PKG_DIR / "profiles"
SETTINGS_FILE = DATA_DIR / "settings.json"

for _d in (DATA_DIR, PROJECTS_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Tous les modèles téléchargés restent dans le dossier de l'application.
os.environ.setdefault("HF_HOME", str(MODELS_DIR / "hf"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

DEFAULT_SETTINGS: dict = {
    "language": "fr",
    "whisper_model": "auto",          # auto | large-v3-turbo | medium | small | base
    "analysis_mode": "complet",       # rapide | complet
    "clip_count": 8,
    "duration_min": 25,
    "duration_max": 50,
    "game": "auto",
    "export_dir": "",                 # vide = à côté de la VOD
    "layout": "auto",                 # auto | facecam_top | smart_crop | blur_fill | center_crop
    "fps": 60,
    "quality": "haute",               # standard | haute | max
    "loudnorm": True,
    "fade": True,
    "subtitles": {
        "enabled": True,
        "font": "Anton",
        "size": 82,
        "uppercase": True,
        "max_words": 3,
        "color": "#FFFFFF",
        "highlight": "#FFE14D",
        "outline_color": "#000000",
        "outline": 6,
        "shadow": 2,
        "position": "auto",           # auto | haut | milieu | bas
        "animation": True,
    },
    "ollama_url": "http://127.0.0.1:11434",
    "ollama_model": "auto",
    "use_ollama": True,
    "channel_hashtags": "#twitch #gaming",
    "vocabulary": "",
    "ui_lang": "en",                  # en | fr (langue de l'interface)
    "welcomed": False,                # écran de bienvenue déjà vu
    "accent": "iris",                 # couleur d'accent de l'interface
    "sound": True,                    # petit son quand une tâche longue se termine
    "open_after_export": False,       # ouvrir le dossier à la fin de l'export
    "hook": {"enabled": False, "seconds": 3.0, "color": "#7C6CFF"},          # titre d'accroche au début
    "progress_bar": {"enabled": False, "color": "#FFFFFF", "height": 10},    # barre de progression
    "watermark": {"enabled": False, "text": "", "position": "bottom"},       # pseudo / filigrane
    "moments_sort": "score",          # score | time (ordre de la VOD)
    "file_naming": "title",           # title | series | series_title
    "export_files": {"txt": False, "md": False, "json": False},  # fichiers en plus des MP4                 # noms propres / termes du jeu pour aider Whisper
}

_lock = threading.Lock()


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_settings() -> dict:
    with _lock:
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        return _merge(DEFAULT_SETTINGS, data)


def save_settings(new: dict) -> dict:
    merged = _merge(load_settings(), new or {})
    with _lock:
        tmp = SETTINGS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(SETTINGS_FILE)
    return merged


def write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default
