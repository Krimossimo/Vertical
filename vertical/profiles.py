"""Profils de jeux : mots-clés, descriptions visuelles CLIP, hashtags, pondérations.

Un profil « jeu » hérite d'un profil « genre », qui hérite du profil générique.
Pour ajouter un jeu : déposer un .json dans vertical/profiles (voir phantom_blade_zero.json).
"""
from __future__ import annotations

import json
import re
import unicodedata

from .config import PROFILES_DIR


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9' ]+", " ", s).strip()


def load_all() -> dict[str, dict]:
    out = {}
    for p in sorted(PROFILES_DIR.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            out[d["id"]] = d
        except Exception:
            continue
    return out


def resolve(pid: str) -> dict:
    allp = load_all()
    chain = []
    cur = allp.get(pid) or allp["generic"]
    while cur is not None and cur not in chain:
        chain.append(cur)
        parent = cur.get("extends") or ("generic" if cur["id"] != "generic" else None)
        cur = allp.get(parent) if parent else None
    res = {"id": chain[0]["id"], "name": chain[0]["name"], "kind": chain[0].get("kind", "genre"),
           "keywords": {}, "clip_prompts": [], "hashtags": [], "weights": {},
           "genre": next((c["id"] for c in chain if c.get("kind") == "genre"), "generic")}
    for c in reversed(chain):  # le plus spécifique écrase
        res["keywords"].update(c.get("keywords", {}))
        res["weights"].update(c.get("weights", {}))
    seen = set()
    for c in chain:
        for pr in c.get("clip_prompts", []):
            if pr["text"] not in seen:
                seen.add(pr["text"])
                res["clip_prompts"].append(pr)
        for h in c.get("hashtags", []):
            if h.lower() not in {x.lower() for x in res["hashtags"]}:
                res["hashtags"].append(h)
    return res


def listing() -> list[dict]:
    items = [{"id": p["id"], "name": p["name"], "name_en": p.get("name_en", p["name"]), "kind": p.get("kind", "genre")}
             for p in load_all().values()]
    items.sort(key=lambda x: (x["kind"] != "game", x["id"] != "generic", x["name"]))
    return items


def detect_from_text(text: str) -> tuple[str | None, str | None]:
    """Cherche un jeu connu dans le nom du fichier / dossier. Retourne (profil, nom du jeu)."""
    t = " " + norm(text.replace("_", " ").replace("-", " ").replace(".", " ")) + " "
    allp = load_all()
    for p in allp.values():
        if p.get("kind") == "game":
            for a in p.get("aliases", []) + [p["name"]]:
                if f" {norm(a)} " in t:
                    return p["id"], p["name"]
    for p in allp.values():
        for g in p.get("games", []):
            if f" {norm(g)} " in t:
                return p["id"], g.title()
    return None, None


def genre_prompts() -> list[tuple[str, str]]:
    return [(p["id"], p["genre_prompt"]) for p in load_all().values()
            if p.get("kind") == "genre" and p.get("genre_prompt") and p["id"] != "generic"]
