"""Analyse Claude « manuelle » avec l'abonnement Claude Pro (aucune clé API).

1. Vertical génère un prompt complet (+ miniatures des moments) ;
2. tu le colles dans claude.ai (et glisses les images si tu veux) ;
3. tu recolles la réponse JSON de Claude dans Vertical, qui met à jour
   titres, descriptions, hashtags, bornes et avis de chaque passage.
"""
from __future__ import annotations

import json
import re
import shutil

from . import projects


def _fmt(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def build_prompt(proj: dict) -> tuple[str, str]:
    game = (proj.get("game") or {}).get("name") or (proj.get("game") or {}).get("profile_name") or "inconnu"
    lines = [
        "Tu es un monteur expert en Shorts gaming francophones (YouTube Shorts, TikTok, Instagram Reels).",
        f"Voici les moments forts détectés automatiquement dans ma VOD Twitch « {proj['name']} » (jeu : {game}).",
        "Pour chaque moment : la transcription de ce que je dis, les signaux détectés et le score automatique.",
        "Si je joins des images, elles portent le nom de l'identifiant du moment (ex. c001234.jpg).",
        "",
        "Ta mission pour CHAQUE moment :",
        "- dire s'il mérite d'être publié (keep true/false) et lui donner un score sur 100 ;",
        "- proposer un titre accrocheur en français (max 70 caractères, 1 emoji max, sans mentir) + 2 variantes ;",
        "- une description courte (2 phrases) et 6 à 8 hashtags dont #shorts ;",
        "- éventuellement décaler le début/la fin (en secondes, négatif = plus tôt) pour un meilleur rythme",
        "  (accroche dans les 2 premières secondes, sans couper le contexte) ;",
        "- un commentaire d'une phrase.",
        "",
        "Réponds UNIQUEMENT avec un bloc JSON de cette forme :",
        '```json\n{"clips": [{"id": "c001234", "keep": true, "score": 85, "title": "…", "title_options": ["…", "…"], '
        '"description": "…", "hashtags": ["#shorts", "…"], "start_offset": 0, "end_offset": 0, "comment": "…"}]}\n```',
        "",
        "=== MOMENTS ===",
    ]
    for c in proj.get("clips", []):
        lines += [
            f"\n--- id: {c['id']} ---",
            f"Position : {_fmt(c['start'])} → {_fmt(c['end'])} ({c['end'] - c['start']:.0f} s), pic à {_fmt(c['peak'])}",
            f"Score auto : {c.get('score')}/100 · Catégorie : {c.get('category_label')}",
            f"Signaux : {'; '.join(c.get('reasons', []))}",
        ]
        if c.get("events"):
            lines.append("Événements vus à l'image : " + ", ".join(f"{e['label']} ({e['p']:.0%})" for e in c["events"]))
        lines.append(f"Transcription : « {c.get('transcript', '')[:1200]} »")
        lines.append(f"Titre actuel : {c.get('title', '')}")
    prompt = "\n".join(lines)
    # dossier d'images à glisser dans claude.ai
    d = projects.pdir(proj["id"])
    pack = d / "pack_claude"
    pack.mkdir(exist_ok=True)
    for c in proj.get("clips", []):
        src = d / "thumbs" / f"{c['id']}.jpg"
        if src.exists():
            shutil.copy2(src, pack / src.name)
    (pack / "prompt.txt").write_text(prompt, encoding="utf-8")
    return prompt, str(pack)


def parse_response(text: str) -> dict:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    data = json.loads(raw)
    if isinstance(data, list):
        data = {"clips": data}
    return data


def apply_response(pid: str, text: str) -> dict:
    data = parse_response(text)
    items = {str(x.get("id")): x for x in data.get("clips", []) if isinstance(x, dict)}
    updated = []

    def fn(p):
        dur = (p.get("info") or {}).get("duration", 1e9)
        for c in p["clips"]:
            x = items.get(c["id"])
            if not x:
                continue
            if x.get("title"):
                c["title"] = str(x["title"])
                opts = [str(t) for t in x.get("title_options", []) if t]
                c["title_options"] = list(dict.fromkeys([c["title"]] + opts + c.get("title_options", [])))[:6]
            if x.get("description"):
                tags = [t if str(t).startswith("#") else "#" + str(t) for t in x.get("hashtags", [])]
                if tags:
                    c["hashtags"] = tags[:10]
                c["description"] = str(x["description"]).strip() + "\n\n🔴 Extrait de mon live Twitch\n\n" + " ".join(
                    c.get("hashtags", []))
            try:
                so, eo = float(x.get("start_offset") or 0), float(x.get("end_offset") or 0)
                if so or eo:
                    c["start"] = round(max(0.0, c["start"] + max(-30, min(30, so))), 2)
                    c["end"] = round(min(dur, c["end"] + max(-30, min(30, eo))), 2)
            except (TypeError, ValueError):
                pass
            if "score" in x:
                c["claude_score"] = x["score"]
            if "keep" in x:
                c["claude_keep"] = bool(x["keep"])
                if c.get("status", "pending") == "pending":
                    c["status"] = "accepted" if x["keep"] else "rejected"
            if x.get("comment"):
                c["claude_comment"] = str(x["comment"])
            c["meta_source"] = "Claude (manuel)"
            updated.append(c["id"])
    projects.update(pid, fn)
    return {"updated": updated}
