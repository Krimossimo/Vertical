"""Sous-titres dynamiques au format ASS (mot actif surligné, style Shorts)."""
from __future__ import annotations

import re

FONTS = [
    {"name": "Anton", "file": "Anton-Regular.ttf"},
    {"name": "Bebas Neue", "file": "BebasNeue-Regular.ttf"},
    {"name": "Luckiest Guy", "file": "LuckiestGuy-Regular.ttf"},
    {"name": "Bangers", "file": "Bangers-Regular.ttf"},
    {"name": "Poppins ExtraBold", "file": "Poppins-ExtraBold.ttf"},
    {"name": "Archivo Black", "file": "ArchivoBlack-Regular.ttf"},
    {"name": "Arial Black", "file": None},
    {"name": "Impact", "file": None},
]


def ass_color(hex_color: str, alpha: int = 0) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        r, g, b = 255, 255, 255
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def _ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _clean(w: str, upper: bool) -> str:
    w = w.strip()
    w = re.sub(r"[,.;:…]+$", "", w)
    w = w.replace("{", "(").replace("}", ")").replace("\\", "/")
    return w.upper() if upper else w


def chunk_words(words: list[dict], max_words: int, max_chars: int) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    cur: list[dict] = []
    for i, w in enumerate(words):
        txt = w["text"]
        if cur:
            gap = w["start"] - cur[-1]["end"]
            length = sum(len(x["text"]) + 1 for x in cur) + len(txt)
            if len(cur) >= max_words or length > max_chars or gap > 0.6 or re.search(r"[.!?]$", cur[-1]["raw"]):
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def build_ass(words: list[dict], clip_start: float, clip_end: float, style: dict, width: int, height: int,
              y_pos: int, x_pos: int | None = None, extras: dict | None = None) -> str:
    upper = bool(style.get("uppercase", True))
    size = int(style.get("size", 82) * width / 1080)
    outline = float(style.get("outline", 6)) * width / 1080
    shadow = float(style.get("shadow", 2)) * width / 1080
    base = ass_color(style.get("color", "#FFFFFF"))
    hl = ass_color(style.get("highlight", "#FFE14D"))
    oc = ass_color(style.get("outline_color", "#000000"))
    font = style.get("font", "Anton")
    max_words = int(style.get("max_words", 3))
    max_chars = max(8, int(20 * 82 / max(40, style.get("size", 82))))
    anim = bool(style.get("animation", True))

    ws = []
    for w in words:
        if w["end"] <= clip_start or w["start"] >= clip_end:
            continue
        t = _clean(w["word"], upper)
        if not t:
            continue
        ws.append({"start": max(0.0, w["start"] - clip_start), "end": min(clip_end, w["end"]) - clip_start,
                   "text": t, "raw": w["word"].strip()})
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},{size},{base},{hl},{oc},&H80000000,0,0,0,0,100,100,1,0,1,{outline:.1f},{shadow:.1f},5,40,40,0,1
{(extras or {}).get("styles", "")}
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    chunks = chunk_words(ws, max_words, max_chars)
    x = int(x_pos) if x_pos is not None else width // 2
    for ci, ch in enumerate(chunks):
        c_start = ch[0]["start"]
        nxt = chunks[ci + 1][0]["start"] if ci + 1 < len(chunks) else clip_end - clip_start
        c_end = min(ch[-1]["end"] + 0.35, nxt)
        if c_end - c_start < 0.25:
            c_end = c_start + 0.25
        # un événement par mot actif (karaoké)
        for wi, w in enumerate(ch):
            s = c_start if wi == 0 else w["start"]
            e = ch[wi + 1]["start"] if wi + 1 < len(ch) else c_end
            if e <= s:
                continue
            parts = []
            for wj, w2 in enumerate(ch):
                col = hl if wj == wi else base
                parts.append(f"{{\\c{col}}}{w2['text']}")
            pre = f"{{\\an5\\pos({x},{y_pos})"
            if anim and wi == 0:
                pre += "\\fscx80\\fscy80\\t(0,90,\\fscx108\\fscy108)\\t(90,170,\\fscx100\\fscy100)"
            pre += "}"
            lines.append(f"Dialogue: 0,{_ts(s)},{_ts(e)},Main,,0,0,0,,{pre}{' '.join(parts)}")
    lines += (extras or {}).get("events", [])
    return head + "\n".join(lines) + "\n"


def extras(settings: dict, title: str, dur: float, width: int, height: int, top_safe: float = 0.1) -> dict:
    """Titre d'accroche (premières secondes) et filigrane (pseudo de la chaîne)."""
    st = settings.get("subtitles", {}) or {}
    font = st.get("font", "Anton")
    sc = width / 1080
    styles, events = [], []
    hook = settings.get("hook") or {}
    if hook.get("enabled") and title.strip():
        col = ass_color(hook.get("color", "#7C6CFF"))
        styles.append(f"Style: Hook,{font},{int(70 * sc)},&H00FFFFFF,&H00FFFFFF,{col},{col},0,0,0,0,100,100,1,0,3,"
                      f"{int(14 * sc)},0,8,{int(70 * sc)},{int(70 * sc)},{int(height * top_safe)},1")
        secs = max(1.0, min(float(hook.get("seconds", 3)), dur))
        txt = _clean(re.sub(r"[\U00010000-\U0010ffff]", "", title), bool(st.get("uppercase", True)))
        events.append(f"Dialogue: 2,{_ts(0.05)},{_ts(secs)},Hook,,0,0,0,,{{\\q0\\fad(150,250)"
                      f"\\fscx85\\fscy85\\t(0,160,\\fscx100\\fscy100)}}{txt}")
    wm = settings.get("watermark") or {}
    if wm.get("enabled") and wm.get("text", "").strip():
        pos = wm.get("position", "bottom")
        align = {"top": 8, "bottom": 2, "top-right": 9, "bottom-right": 3, "top-left": 7, "bottom-left": 1}.get(pos, 2)
        styles.append(f"Style: Mark,{font},{int(38 * sc)},&H55FFFFFF,&H55FFFFFF,&H90000000,&H00000000,0,0,0,0,100,100,1,0,1,"
                      f"{2 * sc:.1f},0,{align},{int(46 * sc)},{int(46 * sc)},{int(60 * sc)},1")
        events.append(f"Dialogue: 1,{_ts(0)},{_ts(dur)},Mark,,0,0,0,,{_clean(wm['text'], False)}")
    return {"styles": "\n".join(styles) + ("\n" if styles else ""), "events": events}
