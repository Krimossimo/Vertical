"""Analyse des paroles : exclamations, jurons, rires, répétitions, débit,
et mots-clés propres au jeu (FR + EN)."""
from __future__ import annotations

import re

import numpy as np

from .audio_analysis import robust_norm
from .profiles import norm

# poids d'excitation des expressions courantes en stream
EXCLAMATIONS: dict[str, float] = {
    # français
    "non": 0.5, "nan": 0.4, "noon": 0.8, "oh": 0.4, "ah": 0.25, "aie": 0.6, "ouch": 0.6, "oula": 0.5, "oulala": 0.7,
    "oh la la": 0.7, "putain": 0.9, "ptn": 0.8, "merde": 0.8, "bordel": 0.8, "wesh": 0.6, "quoi": 0.4,
    "serieux": 0.6, "c'est pas possible": 1.0, "pas possible": 0.8, "c'est quoi ca": 0.8, "mais quoi": 0.8,
    "incroyable": 0.9, "trop fort": 0.9, "trop bien": 0.7, "magnifique": 0.8, "enorme": 0.8, "dingue": 0.8, "de ouf": 0.9,
    "c'est chaud": 0.7, "chaud": 0.4, "let's go": 1.0, "lets go": 1.0, "allez": 0.5, "vas y": 0.6, "go go": 0.6,
    "je suis mort": 0.9, "j'suis mort": 0.9, "il m'a eu": 0.8, "au secours": 0.9, "a l'aide": 0.7, "pitie": 0.8,
    "c'est mort": 0.7, "j'en peux plus": 0.9, "ca me saoule": 0.8, "abuse": 0.7, "n'importe quoi": 0.8, "jamais": 0.4,
    "oui": 0.3, "ouiii": 0.8, "yes": 0.6, "enfin": 0.6, "gg": 0.9, "ez": 0.6, "mdr": 0.8, "ptdr": 0.9, "jpp": 0.8,
    "attends": 0.3, "qu'est ce que": 0.4, "comment": 0.3, "non mais": 0.7, "c'est une blague": 0.9, "tu rigoles": 0.8,
    "fou": 0.5, "masterclass": 1.0, "propre": 0.6, "trop propre": 0.9, "le skill": 0.8, "aimbot": 0.8,
    # anglais
    "no": 0.4, "what": 0.4, "oh my god": 0.9, "omg": 0.8, "wtf": 0.9, "holy": 0.7, "dude": 0.5, "bro": 0.4, "nice": 0.5,
    "insane": 0.9, "crazy": 0.7, "no way": 0.9, "come on": 0.7, "let's go": 1.0, "lol": 0.6, "lmao": 0.8, "clean": 0.6,
    "shit": 0.8, "fuck": 0.9, "damn": 0.6, "yeah": 0.3, "wow": 0.6, "ouais": 0.2,
}
LAUGH_RE = re.compile(r"^(ha|ah|he|hi|ho|xa){2,}h?$|^(mdr+|ptdr+|lol+|lmao+|jpp+|xd)$|rire|laugh")
ELONG_RE = re.compile(r"([a-z])\1{2,}")


def _clean_token(w: str) -> tuple[str, bool]:
    t = norm(w).replace(" ", "")
    elong = bool(ELONG_RE.search(t))
    t = ELONG_RE.sub(r"\1", t) if elong else t
    return t, elong


def _phrase_index(phr: dict[str, float]) -> dict[str, list[tuple[list[str], float, object]]]:
    idx: dict[str, list] = {}
    for p, v in phr.items():
        toks = [ELONG_RE.sub(r"\1", x) for x in norm(p).split()]
        if toks:
            idx.setdefault(toks[0], []).append((toks, v))
    return idx


def analyze(words: list[dict], nsec: int, profile: dict) -> dict:
    excl = np.zeros(nsec, np.float32)
    laugh = np.zeros(nsec, np.float32)
    game = np.zeros(nsec, np.float32)
    rate = np.zeros(nsec, np.float32)
    rep = np.zeros(nsec, np.float32)
    cats: dict[str, np.ndarray] = {}
    hits: list[dict] = []
    if not words or nsec == 0:
        return {"excl": excl, "laugh_txt": laugh, "game_kw": game, "rate": rate, "repeat": rep, "cats": cats, "hits": hits}

    toks, times, elongs = [], [], []
    for w in words:
        t, e = _clean_token(w["word"])
        if not t:
            continue
        toks.append(t)
        times.append(0.5 * (w["start"] + w["end"]))
        elongs.append(e)
    ex_idx = _phrase_index(EXCLAMATIONS)
    kw = {k: v[0] for k, v in profile.get("keywords", {}).items()}
    kw_cat = {" ".join(norm(k).split()): v[1] for k, v in profile.get("keywords", {}).items()}
    kw_idx = _phrase_index(kw)

    for i, (t, tm) in enumerate(zip(toks, times)):
        s = int(tm)
        if s >= nsec:
            continue
        rate[s] += 1
        if elongs[i]:
            excl[s] += 0.5
        if LAUGH_RE.search(t):
            laugh[s] += 1.0
        for idx, arr, is_game in ((ex_idx, excl, False), (kw_idx, game, True)):
            for ptoks, val in idx.get(t, []):
                if toks[i:i + len(ptoks)] == ptoks:
                    arr[s] += val
                    if is_game:
                        key = " ".join(ptoks)
                        c = kw_cat.get(key, "combat")
                        cats.setdefault(c, np.zeros(nsec, np.float32))[s] += val
                        hits.append({"t": round(tm, 2), "kw": key, "cat": c})
        # répétitions rapprochées « non non non », « go go go »
        j = i - 1
        n_same = 0
        while j >= 0 and times[i] - times[j] < 3.0:
            if toks[j] == t and len(t) > 1:
                n_same += 1
            j -= 1
        if n_same >= 2:
            rep[s] += 0.5 * n_same

    from .audio_analysis import _rolling
    rate_rel = np.clip(rate - _rolling(rate, 60, np.mean), 0, None)
    excl_s = _rolling(excl, 3, np.max)
    return {
        "excl": robust_norm(excl_s, 60, 99.5) if excl_s.max() > 0 else excl_s,
        "laugh_txt": np.clip(_rolling(laugh, 3, np.max), 0, 1),
        "game_kw": np.clip(_rolling(game, 5, np.max), 0, 1.5) / 1.5,
        "rate": robust_norm(rate_rel, 60, 99.5) if rate_rel.max() > 0 else rate_rel,
        "repeat": np.clip(_rolling(rep, 3, np.max), 0, 1),
        "cats": cats,
        "hits": hits,
    }
