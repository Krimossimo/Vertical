"""Outils sur la transcription : nettoyage des hallucinations de Whisper, corrections
par ligne, rechercher/remplacer, réinsertion d'une portion re-transcrite."""
from __future__ import annotations

import re
import unicodedata

PUNCT_ONLY = re.compile(r"^[\s\W_]+$", re.U)
SENT_END = re.compile(r"[.!?…]$")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9']+", "", s)


def flatten(tr: dict) -> list[dict]:
    out = []
    for s in tr.get("segments", []):
        if s.get("words"):
            out.extend(dict(w) for w in s["words"])
        else:
            toks = s.get("text", "").split()
            if toks:
                d = (s["end"] - s["start"]) / len(toks)
                out += [{"start": s["start"] + i * d, "end": s["start"] + (i + 1) * d, "word": " " + t, "p": 0.5}
                        for i, t in enumerate(toks)]
    out.sort(key=lambda w: w["start"])
    return out


def clean_words(words: list[dict]) -> list[dict]:
    """Supprime la ponctuation isolée et les boucles de répétition typiques de Whisper
    (« wesh wesh wesh… » collés au même instant)."""
    res: list[dict] = []
    for w in words:
        txt = w["word"]
        if not txt.strip():
            continue
        if PUNCT_ONLY.match(txt):
            if res:
                res[-1]["word"] = res[-1]["word"].rstrip() + txt.strip()
            continue
        if res and not w.get("edited"):  # les mots ajoutés/corrigés à la main ne sont jamais filtrés
            prev = res[-1]
            same = norm(prev["word"]) == norm(txt) and norm(txt)
            # même mot répété quasiment au même instant : hallucination
            if same and (w["start"] - prev["start"] < 0.12 or (w["end"] - w["start"]) < 0.04):
                continue
        res.append(dict(w))
    # boucles longues : plus de 4 fois le même mot en 8 s = boucle d'hallucination
    out: list[dict] = []
    for w in res:
        k = norm(w["word"])
        if k and len(k) >= 2 and not w.get("edited"):
            recent = [x for x in out[-12:] if norm(x["word"]) == k and w["start"] - x["start"] < 8.0]
            if len(recent) >= 4:
                continue
        out.append(w)
    return out


def rebuild(words: list[dict], base: dict | None = None) -> dict:
    """Reconstruit des segments (phrases) courts à partir de la liste de mots."""
    segs: list[dict] = []
    cur: list[dict] = []
    for w in sorted(words, key=lambda x: x["start"]):
        if cur:
            gap = w["start"] - cur[-1]["end"]
            dur = cur[-1]["end"] - cur[0]["start"]
            if gap > 0.9 or (SENT_END.search(cur[-1]["word"].strip()) and dur > 1.2) or dur > 14:
                segs.append(cur)
                cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    out = dict(base or {})
    out["segments"] = [{"start": round(s[0]["start"], 3), "end": round(s[-1]["end"], 3),
                        "text": "".join(x["word"] for x in s).strip(), "words": s} for s in segs]
    return out


def distribute(text: str, a: float, b: float, p: float = 1.0) -> list[dict]:
    """Découpe un texte en mots répartis sur [a, b] au prorata de leur longueur."""
    toks = text.split()
    if not toks:
        return []
    b = max(b, a + 0.12 * len(toks))
    total = sum(len(t) + 1 for t in toks)
    out, t = [], a
    for tok in toks:
        d = (b - a) * (len(tok) + 1) / total
        out.append({"start": round(t, 3), "end": round(t + d * 0.92, 3), "word": " " + tok, "p": p, "edited": True})
        t += d
    return out


def replace_span(words: list[dict], a: float, b: float, text: str) -> list[dict]:
    """Remplace tous les mots qui commencent dans [a, b] par `text` (vide = suppression)."""
    keep = [w for w in words if not (a - 0.001 <= w["start"] <= b + 0.001)]
    inside = [w for w in words if a - 0.001 <= w["start"] <= b + 0.001]
    end = max([w["end"] for w in inside], default=b)
    return sorted(keep + distribute(text, a, end), key=lambda w: w["start"])


def in_ranges(t: float, ranges: list[tuple[float, float]] | None) -> bool:
    return ranges is None or any(a <= t <= b for a, b in ranges)


def find_matches(words: list[dict], find: str, ranges=None) -> list[tuple[int, int]]:
    """Occurrences (index début, index fin exclus) d'un mot ou d'une expression, sans tenir
    compte des majuscules, accents et ponctuation."""
    pat = [norm(t) for t in find.split() if norm(t)]
    if not pat:
        return []
    keys = [norm(w["word"]) for w in words]
    out, i, n = [], 0, len(pat)
    while i <= len(words) - n:
        if keys[i:i + n] == pat and in_ranges(words[i]["start"], ranges):
            out.append((i, i + n))
            i += n
        else:
            i += 1
    return out


def find_replace(words: list[dict], find: str, repl: str, ranges=None) -> tuple[list[dict], int]:
    matches = find_matches(words, find, ranges)
    if not matches:
        return words, 0
    out: list[dict] = []
    last = 0
    for i, j in matches:
        out += words[last:i]
        out += distribute(repl, words[i]["start"], words[j - 1]["end"])
        last = j
    out += words[last:]
    return out, len(matches)


def context(words: list[dict], i: int, j: int, k: int = 5) -> dict:
    return {"t": round(words[i]["start"], 2),
            "before": "".join(w["word"] for w in words[max(0, i - k):i]).strip(),
            "match": "".join(w["word"] for w in words[i:j]).strip(),
            "after": "".join(w["word"] for w in words[j:j + k]).strip()}


def splice(words: list[dict], new_words: list[dict], a: float, b: float) -> list[dict]:
    keep = [w for w in words if not (a <= w["start"] < b)]
    add = [w for w in new_words if a <= w["start"] < b]
    return sorted(keep + add, key=lambda w: w["start"])


def set_timed(words: list[dict], a: float | None, b: float | None, new_words: list[dict]) -> list[dict]:
    """Remplace les mots de [a, b] (ou insère si a est None) par des mots au timing précis."""
    keep = words if a is None else [w for w in words if not (a - 0.001 <= w["start"] <= (b if b is not None else a) + 0.001)]
    add = []
    for w in new_words:
        txt = str(w.get("word", "")).strip()
        if not txt:
            continue
        s0, e0 = float(w["start"]), float(w["end"])
        add.append({"start": round(s0, 3), "end": round(max(e0, s0 + 0.05), 3), "word": " " + txt, "p": 1.0,
                    "edited": True})
    return sorted(keep + add, key=lambda w: w["start"])
