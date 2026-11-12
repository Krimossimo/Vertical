"""Titres, descriptions et hashtags pour YouTube Shorts / TikTok / Reels.

Par défaut : générateur local à base de modèles de phrases (aucune dépendance).
Si Ollama tourne sur le PC (gratuit, local), un LLM rédige des propositions plus
naturelles. Le « pack Claude » (claude_pack.py) permet d'utiliser ton abonnement
Claude Pro manuellement, sans clé API.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re

log = logging.getLogger("vertical")

TITLES = {
    "combat": ["Ce combat était complètement IRRÉEL 🔥", "Le combat le plus intense du live ⚔️",
               "J'ai cru que j'allais jamais m'en sortir 😰", "Ce boss ne rigole pas du tout ⚔️"],
    "skill": ["Je sais pas comment j'ai fait ça 🤯", "Le moment où j'ai sorti le grand jeu 😮‍💨",
              "Le clip le plus propre de ma vie ? 🤯", "Timing PARFAIT au dernier moment ⚡"],
    "echec": ["Il m'a DÉTRUIT en une seconde 💀", "Je n'ai rien vu venir… 💀", "Pourquoi ce jeu me fait ça 😭",
              "La mort la plus injuste du live 💀"],
    "victoire": ["ENFIN ! Après tant d'essais 🏆", "Le moment où tout a basculé 🏆",
                 "Cette victoire avait un goût spécial 🔥", "Je l'ai EU ! 🏆"],
    "drole": ["J'ai pas pu m'arrêter de rire 😂", "Le jeu a décidé de me troller 😂",
              "Personne ne s'attendait à ça 😂", "Ce moment m'a achevé 😂"],
    "reaction": ["Ma réaction dit tout 😱", "J'ai hurlé devant tout le live 😱",
                 "Je ne m'en remets toujours pas 😳", "Le chat ne s'en remet pas 😱"],
    "tension": ["Le moment le plus stressant du live 😰", "Un seul coup et c'est fini… 😰",
                "Plus aucune marge d'erreur 😰"],
    "inattendu": ["Personne ne s'attendait à ça 😳", "Attends la fin… 👀", "Ça a complètement dérapé 😳"],
}
SUMMARIES = {
    "combat": "Un combat ultra intense sur {game}.", "skill": "Une action millimétrée sur {game}.",
    "echec": "Quand {game} ne pardonne aucune erreur…", "victoire": "Une victoire méritée sur {game} !",
    "drole": "Un moment complètement absurde sur {game}.", "reaction": "Une réaction à chaud en plein live sur {game}.",
    "tension": "Un moment sous haute tension sur {game}.", "inattendu": "Un retournement de situation sur {game}.",
}
CAT_TAGS = {
    "combat": ["#epic", "#bossfight"], "skill": ["#clutch", "#skill"], "echec": ["#fail", "#rage"],
    "victoire": ["#victory", "#gg"], "drole": ["#funny", "#drole"], "reaction": ["#reaction", "#twitchfr"],
    "tension": ["#intense"], "inattendu": ["#wtf"],
}
PLATFORM_TAGS = {"youtube": ["#shorts"], "tiktok": ["#fyp", "#pourtoi"], "instagram": ["#reels"]}


def _game_tag(game: str) -> str:
    return "#" + re.sub(r"[^A-Za-z0-9]", "", game.title()) if game else ""


def _pick(options: list[str], seed: str, k: int) -> list[str]:
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    start = h % len(options)
    return [options[(start + i) % len(options)] for i in range(min(k, len(options)))]


def best_quote(text: str) -> str | None:
    sents = re.split(r"(?<=[.!?…])\s+", text.strip())
    best, bs = None, 0
    for s in sents:
        n = len(s.split())
        if 2 <= n <= 9:
            sc = s.count("!") * 2 + (1 if any(w in s.lower() for w in ("non", "quoi", "putain", "let's go", "oh")) else 0)
            if sc > bs:
                best, bs = s.strip(" .…"), sc
    return best


def template(clip: dict, game: str, profile: dict, channel_tags: str = "", avoid: set | None = None) -> dict:
    cat = clip.get("category", "reaction")
    pool = TITLES.get(cat, TITLES["reaction"])
    opts = _pick(pool, clip["id"], len(pool))
    if avoid:
        opts = [t for t in opts if t not in avoid] + [t for t in opts if t in avoid]
    opts = opts[:3]
    q = best_quote(clip.get("transcript", ""))
    if q:
        opts.insert(1, f"« {q[:60]} » 😱")
    if avoid is not None:
        avoid.add(opts[0])
    titles = [(f"{t} | {game}" if game and len(t) + len(game) < 72 else t) for t in opts]
    tags = ["#shorts"]
    gt = _game_tag(game)
    if gt:
        tags.append(gt)
    tags += [t for t in profile.get("hashtags", []) if t.lower() != "#shorts"]
    tags += CAT_TAGS.get(cat, [])
    tags += [t if t.startswith("#") else "#" + t for t in channel_tags.split()]
    seen, final = set(), []
    for t in tags:
        if t and t.lower() not in seen:
            seen.add(t.lower())
            final.append(t)
    final = final[:10]
    summary = SUMMARIES.get(cat, "Un moment fort sur {game}.").format(game=game or "ce jeu")
    desc = summary
    if q:
        desc += f"\n« {q} »"
    desc += "\n\n🔴 Extrait de mon live Twitch" + (f"\n🎮 Jeu : {game}" if game else "") + "\n\n" + " ".join(final)
    return {"title": titles[0], "title_options": titles, "description": desc, "hashtags": final, "source": "modèles"}


# --------------------------------------------------------------------------- Ollama
PREFERRED = ["qwen3", "qwen2.5", "llama3.1", "llama3.2", "mistral", "gemma3", "gemma2", "phi4", "phi3"]


def pick_ollama_model(models: list[str], pref: str) -> str | None:
    if pref and pref != "auto":
        return pref if pref in models else None
    for p in PREFERRED:
        for m in models:
            if m.startswith(p) and "embed" not in m and "vl" not in m:
                return m
    return next((m for m in models if "embed" not in m), None)


def with_ollama(clip: dict, game: str, base: dict, url: str, model: str) -> dict | None:
    import urllib.request
    prompt = (
        "Tu es un expert des Shorts gaming francophones (YouTube Shorts, TikTok, Reels).\n"
        f"Jeu : {game or 'inconnu'}\nType de moment : {clip.get('category_label')}\n"
        f"Pourquoi ce moment a été choisi : {'; '.join(clip.get('reasons', []))}\n"
        f"Transcription du streamer : \"{clip.get('transcript', '')[:700]}\"\n\n"
        "Propose en JSON : {\"titles\": [3 titres accrocheurs en français, max 70 caractères, 1 emoji max, "
        "sans mentir sur le contenu], \"description\": \"2 phrases courtes en français\", "
        "\"hashtags\": [6 à 8 hashtags pertinents dont #shorts]}. Réponds uniquement avec le JSON."
    )
    try:
        body = json.dumps({"model": model, "prompt": prompt, "format": "json", "stream": False,
                           "options": {"temperature": 0.8}, "think": False}).encode()
        req = urllib.request.Request(url.rstrip("/") + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(json.loads(r.read().decode()).get("response", "{}"))
        titles = [t.strip() for t in data.get("titles", []) if isinstance(t, str) and t.strip()][:3]
        if not titles:
            return None
        tags = [t if t.startswith("#") else "#" + t for t in data.get("hashtags", []) if isinstance(t, str)]
        tags = list(dict.fromkeys(["#shorts"] + [t.replace(" ", "") for t in tags]))[:10]
        desc = str(data.get("description", "")).strip() or base["description"].split("\n\n")[0]
        desc += "\n\n🔴 Extrait de mon live Twitch" + (f"\n🎮 Jeu : {game}" if game else "") + "\n\n" + " ".join(tags)
        return {"title": titles[0], "title_options": titles + base["title_options"][:2], "description": desc,
                "hashtags": tags, "source": f"Ollama ({model})"}
    except Exception as e:
        log.warning("Ollama indisponible pour %s : %s", clip.get("id"), e)
        return None
