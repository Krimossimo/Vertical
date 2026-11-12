"""Construit release/Vertical-Setup.zip : le paquet à publier sur GitHub Releases.

Contient le code, l'installateur et le lanceur — PAS le venv, les modèles, FFmpeg ni tes données
(Installer.bat les télécharge chez l'utilisateur).   Usage :  python scripts/build_release.py
"""
import os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "release", "Vertical-Setup.zip")
TOP = "Vertical"  # dossier à l'intérieur du zip

INCLUDE = ["Installer.bat", "Lancer Vertical.bat", "README.md", "requirements.txt", "Vertical.exe",
           "assets", "scripts", "vertical"]
SKIP_DIRS = {"__pycache__", ".git", ".venv", "tools", "models", "data", "release", "docs"}
SKIP_EXT = {".pyc", ".log", ".tgz"}


def add(z, path, arc):
    if os.path.isdir(path):
        for name in sorted(os.listdir(path)):
            if name in SKIP_DIRS:
                continue
            add(z, os.path.join(path, name), arc + "/" + name)
    elif os.path.splitext(path)[1].lower() not in SKIP_EXT:
        z.write(path, arc)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for item in INCLUDE:
            p = os.path.join(ROOT, item)
            if os.path.exists(p):
                add(z, p, TOP + "/" + item)
            else:
                print("  (absent, ignoré)", item)
    print("OK ->", OUT, round(os.path.getsize(OUT) / 1e6, 1), "Mo")


if __name__ == "__main__":
    sys.exit(main())
