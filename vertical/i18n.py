"""Textes affichés par le serveur (progression, notes, erreurs), en anglais ou en français.

La langue suit le réglage « ui_lang » de l'interface. Les textes de l'interface
elle-même sont dans web/i18n.js.
"""
from __future__ import annotations

from .config import load_settings

STR: dict[str, dict[str, str]] = {
    "en": {
        # étapes d'analyse
        "step.probe": "Reading the video", "step.audio": "Extracting audio", "step.audio_feat": "Analyzing vocal reactions",
        "step.visual": "Analyzing the picture", "step.game": "Detecting the game and facecam",
        "step.transcribe": "Transcription (Whisper)", "step.text": "Analyzing speech",
        "step.candidates": "Pre-selecting moments", "step.deep": "Deep AI analysis (image + sound)",
        "step.select": "Final selection and trimming", "step.meta": "Titles, descriptions and hashtags",
        "step.thumbs": "Thumbnails", "step.render": "9:16 preview", "step.proxy": "Preview version (540p)",
        "step.redo": "Recomputing subtitles",
        # messages
        "probe_done": "{dur} — {w}×{h} @ {fps} fps",
        "audio_tracks": "{n} track(s) · voice on track {t}", "audio_speech": " ({p} speech)",
        "audio_little_voice": " · very little voice", "audio_search": "looking for your voice",
        "audio_search_n": "looking for your voice among {n} tracks", "audio_none": "no audio track",
        "audio_ready": "16 kHz audio ready", "feat_done": "{n} sound peaks found",
        "visual_sampling": "sampling keyframes", "visual_full": "full decode (keyframes too far apart)",
        "visual_done": "{n} frames analyzed", "game_genre": "recognizing the game genre (CLIP)",
        "game_facecam": "looking for a facecam", "facecam_yes": " · facecam found", "facecam_no": " · no facecam",
        "by.manual": "manual choice", "by.filename": "file name", "by.image": "image analysis ({p})",
        "by.gamename": "game name you entered", "by.default": "default",
        "transcribe_done": "{n} sentences — {engine}", "text_done": "{n} game keywords",
        "cand_done": "{n} candidate zones", "deep_done": "{n} zones analyzed by CLIP + AST",
        "deep_skip": "quick mode or AI models missing", "deep_fail": "unavailable — fallback used",
        "deep_zone": "zone {a} – {b}", "select_done": "{n} moments selected",
        "meta_local": "built-in generator", "meta_ollama": "via Ollama ({m})",
        "wh_loading": "Loading Whisper “{m}” ({dev})…", "wh_running": "Transcribing ({m}, {dev})",
        "wh_retry": "Little speech detected: retrying with more sensitive detection…",
        "wh_redo_loading": "Loading Whisper “{m}” ({dev}) — the first use downloads the model…",
        "wh_redo_running": "Re-transcribing ({m})", "redo_done": "{n} words · {engine}",
        # notes
        "note.no_audio": "The video has no audio track: picture-only analysis.",
        "note.little_voice": "Very little voice detected: the selection relies mostly on game sound and picture. If you were talking, check that your mic is recorded in the video.",
        "note.genre_fail": "AI genre detection unavailable ({e}).",
        "note.deep_fail": "Deep AI analysis unavailable ({e}): classic signals used.",
        "note.no_whisper": "faster-whisper is not installed: no transcription.",
        "note.transcribe_fail": "Transcription failed: {e}",
        "err.no_whisper": "faster-whisper is not installed", "err.transcribe": "Transcription failed: {e}",
        "env.no_ffmpeg": "FFmpeg is missing: run Installer.bat.",
        "env.no_nvenc": "GPU encoding (NVENC) unavailable: export uses libx264 (slower, same quality).",
        "env.no_whisper": "faster-whisper missing: no transcription (subtitles disabled).",
        "env.no_cuda": "CUDA GPU not used: CPU transcription with a lighter model.",
        "env.no_ai": "Image/sound AI models missing: analysis uses audio/video signals only.",
        # erreurs
        "err.not_found": "Project not found", "err.file_missing": "Video file not found: {p}",
        "err.busy": "A task is already running for this VOD.", "err.need_analysis": "Run a full analysis first.",
        "err.need_accept": "Accept at least one moment before exporting.", "err.none_accepted": "No accepted moment to export.",
        "err.render": "FFmpeg rendering failed: {e}", "err.clip_missing": "Moment not found",
        "err.dialog": "File dialog unavailable: {e}. Paste the path instead.",
        "err.not_vertical": "This file wasn't made by Vertical (or its project was deleted).",
        "err.clip_gone": "This Short's moment no longer exists in the project.",
        "err.audio_missing": "Audio not found: run the VOD analysis again.", "err.no_range": "No moment to recompute for this choice.",
        "err.find_empty": "Enter the word or phrase to find.", "err.bad_reply": "Unreadable reply: {e}. Paste the JSON block returned by Claude.",
        "err.name_empty": "The name can't be empty.", "err.no_audio_file": "Audio not found",
        "err.read_video": "Can't read the video: {e}", "err.no_video_stream": "No video track found in this file.",
        "cancelled": "Task cancelled.", "error": "Error: {e}",
        "r.voice_up": "Your voice rises: +{db} dB above your usual level", "r.sound_peak": "Sound peak: +{db} dB above the usual level",
        "r.scream": "Very strong vocal reaction / scream", "r.game_loud": "Big in-game sound (impacts, explosions, music)",
        "r.ast_scream": "Scream detected by audio AI", "r.laugh": "Laughter detected", "r.excl": "Exclamations: {words}",
        "r.excl0": "Exclamations", "r.game_kw": "Game keywords: {words}", "r.repeat": "Repetitions in the heat of the moment",
        "r.motion": "Very intense on-screen action", "r.flash": "Flashes / sudden changes in the picture",
        "r.red": "Red tint on screen (damage, critical health)", "r.fade_dark": "Fade to black after the action (likely death or end of fight)",
        "r.ast_cheer": "Cheering / victory music", "r.ast_boom": "Explosions / gunfire", "r.ast_impact": "Impact sounds (hits, crashes)",
        "r.event": "Picture: {en} ({p})", "r.intense": "Strong overall intensity", "r.manual": "Manually added moment",
        "cat.combat": "Epic fight", "cat.skill": "Skill play", "cat.echec": "Fail / death", "cat.victoire": "Victory",
        "cat.drole": "Funny moment", "cat.reaction": "Big reaction", "cat.tension": "Tense moment", "cat.inattendu": "Unexpected",
        "cat.manual": "Manual",
    },
    "fr": {
        "step.probe": "Lecture de la vidéo", "step.audio": "Extraction de l'audio", "step.audio_feat": "Analyse des réactions vocales",
        "step.visual": "Analyse de l'image", "step.game": "Détection du jeu et de la facecam",
        "step.transcribe": "Transcription (Whisper)", "step.text": "Analyse des paroles",
        "step.candidates": "Pré-sélection des moments", "step.deep": "Analyse IA approfondie (images + sons)",
        "step.select": "Sélection finale et découpage", "step.meta": "Titres, descriptions et hashtags",
        "step.thumbs": "Miniatures", "step.render": "Aperçu 9:16", "step.proxy": "Version de prévisualisation (540p)",
        "step.redo": "Recalcul des sous-titres",
        "probe_done": "{dur} — {w}×{h} @ {fps} i/s",
        "audio_tracks": "{n} piste(s) · voix sur la piste {t}", "audio_speech": " ({p} de parole)",
        "audio_little_voice": " · très peu de voix", "audio_search": "recherche de ta voix",
        "audio_search_n": "recherche de ta voix parmi {n} pistes", "audio_none": "aucune piste audio",
        "audio_ready": "audio 16 kHz prêt", "feat_done": "{n} pics sonores repérés",
        "visual_sampling": "échantillonnage des images clés", "visual_full": "décodage complet (images clés trop espacées)",
        "visual_done": "{n} images analysées", "game_genre": "reconnaissance du genre de jeu (CLIP)",
        "game_facecam": "recherche d'une facecam", "facecam_yes": " · facecam détectée", "facecam_no": " · pas de facecam",
        "by.manual": "choix manuel", "by.filename": "nom du fichier", "by.image": "analyse d'image ({p})",
        "by.gamename": "nom du jeu indiqué", "by.default": "défaut",
        "transcribe_done": "{n} phrases — {engine}", "text_done": "{n} mots-clés du jeu",
        "cand_done": "{n} zones candidates", "deep_done": "{n} zones analysées par CLIP + AST",
        "deep_skip": "mode rapide ou modèles IA absents", "deep_fail": "indisponible — solution de secours utilisée",
        "deep_zone": "zone {a} – {b}", "select_done": "{n} moments retenus",
        "meta_local": "générateur local", "meta_ollama": "via Ollama ({m})",
        "wh_loading": "Chargement du modèle Whisper « {m} » ({dev})…", "wh_running": "Transcription ({m}, {dev})",
        "wh_retry": "Peu de parole détectée : nouvel essai avec une détection plus sensible…",
        "wh_redo_loading": "Chargement de Whisper « {m} » ({dev}) — le premier usage télécharge le modèle…",
        "wh_redo_running": "Re-transcription ({m})", "redo_done": "{n} mots · {engine}",
        "note.no_audio": "La vidéo n'a pas de piste audio : analyse par l'image uniquement.",
        "note.little_voice": "Très peu de voix détectée dans l'audio : la sélection s'appuie surtout sur le son du jeu et l'image. Si tu parlais, vérifie que ton micro est bien enregistré dans la vidéo.",
        "note.genre_fail": "Détection du genre par IA impossible ({e}).",
        "note.deep_fail": "Analyse IA approfondie indisponible ({e}) : signaux classiques utilisés.",
        "note.no_whisper": "faster-whisper non installé : pas de transcription.",
        "note.transcribe_fail": "Transcription impossible : {e}",
        "err.no_whisper": "faster-whisper non installé", "err.transcribe": "Transcription impossible : {e}",
        "env.no_ffmpeg": "FFmpeg manquant : lance Installer.bat.",
        "env.no_nvenc": "Encodage GPU NVENC indisponible : export en libx264 (plus lent, même qualité).",
        "env.no_whisper": "faster-whisper absent : pas de transcription (les sous-titres seront désactivés).",
        "env.no_cuda": "GPU CUDA non utilisé : transcription sur CPU avec un modèle plus léger.",
        "env.no_ai": "Modèles IA image/son absents : analyse par signaux audio/vidéo uniquement.",
        "err.not_found": "Projet introuvable", "err.file_missing": "Fichier vidéo introuvable : {p}",
        "err.busy": "Une tâche est déjà en cours pour cette VOD.", "err.need_analysis": "Lance d'abord une analyse complète.",
        "err.need_accept": "Valide au moins un passage avant d'exporter.", "err.none_accepted": "Aucun passage validé à exporter.",
        "err.render": "Le rendu FFmpeg a échoué : {e}", "err.clip_missing": "Passage introuvable",
        "err.dialog": "Boîte de dialogue indisponible : {e}. Colle le chemin à la main.",
        "err.not_vertical": "Ce fichier ne vient pas de Vertical (ou son projet a été supprimé).",
        "err.clip_gone": "Le passage de ce Short n'existe plus dans le projet.",
        "err.audio_missing": "Audio introuvable : relance l'analyse de la VOD.", "err.no_range": "Aucun passage à recalculer pour ce choix.",
        "err.find_empty": "Indique le mot ou l'expression à chercher.", "err.bad_reply": "Réponse illisible : {e}. Colle le bloc JSON renvoyé par Claude.",
        "err.name_empty": "Le nom ne peut pas être vide.", "err.no_audio_file": "Audio introuvable",
        "err.read_video": "Impossible de lire la vidéo : {e}", "err.no_video_stream": "Aucune piste vidéo trouvée dans ce fichier.",
        "cancelled": "Tâche annulée.", "error": "Erreur : {e}",
        "r.voice_up": "Ta voix monte : +{db} dB au-dessus de ton niveau habituel", "r.sound_peak": "Pic sonore : +{db} dB au-dessus du niveau habituel",
        "r.scream": "Cri / réaction vocale très forte", "r.game_loud": "Gros son dans le jeu (impacts, explosions, musique)",
        "r.ast_scream": "Cri détecté par l'IA audio", "r.laugh": "Rires détectés", "r.excl": "Exclamations : {words}",
        "r.excl0": "Exclamations", "r.game_kw": "Mots-clés du jeu : {words}", "r.repeat": "Répétitions sous le coup de l'émotion",
        "r.motion": "Action très intense à l'écran", "r.flash": "Flashs / changements brusques à l'image",
        "r.red": "Teinte rouge à l'écran (dégâts, santé critique)", "r.fade_dark": "Fondu au noir après l'action (mort ou fin de combat probable)",
        "r.ast_cheer": "Acclamations / musique de victoire", "r.ast_boom": "Explosions / tirs", "r.ast_impact": "Impacts sonores (coups, chocs)",
        "r.event": "Image : {fr} ({p})", "r.intense": "Moment de forte intensité globale", "r.manual": "Passage ajouté manuellement",
        "cat.combat": "Combat épique", "cat.skill": "Action technique", "cat.echec": "Échec / mort", "cat.victoire": "Victoire",
        "cat.drole": "Moment drôle", "cat.reaction": "Grosse réaction", "cat.tension": "Moment tendu", "cat.inattendu": "Inattendu",
        "cat.manual": "Ajout manuel",
    },
}


def lang() -> str:
    try:
        lg = load_settings().get("ui_lang", "en")
    except Exception:
        lg = "en"
    return lg if lg in STR else "en"


def tr(key: str, **kw) -> str:
    table = STR[lang()]
    s = table.get(key) or STR["en"].get(key) or key
    try:
        return s.format(**kw)
    except Exception:
        return s


def note(key: str, **kw) -> dict:
    """Note stockée sous forme de code : traduite au moment de l'affichage."""
    return {"k": key, "v": {k: str(v) for k, v in kw.items()}}


def render_note(n) -> str:
    if isinstance(n, dict):
        return tr(n.get("k", ""), **(n.get("v") or {}))
    return str(n)


def render_reason(code: dict, lg: str | None = None) -> str:
    table = STR.get(lg or lang(), STR["en"])
    s = table.get("r." + code.get("k", ""), code.get("k", ""))
    try:
        return s.format(**(code.get("v") or {}))
    except Exception:
        return s


_LEGACY: list | None = None


def _legacy_code(text: str) -> dict | None:
    """Retrouve le code d'une raison enregistrée en texte français (projets analysés avant la v2)."""
    global _LEGACY
    import re
    if _LEGACY is None:
        _LEGACY = []
        for k, tpl in STR["fr"].items():
            if not k.startswith("r."):
                continue
            pat = re.escape(tpl)
            pat = re.sub(r"\\\{(\w+)\\\}", lambda m: f"(?P<{m.group(1)}>.+?)", pat)
            _LEGACY.append((k[2:], re.compile("^" + pat + "$")))
    for code, rx in _LEGACY:
        m = rx.match(text.strip())
        if m:
            v = m.groupdict()
            if code == "event":
                v.setdefault("en", v.get("fr", ""))
            return {"k": code, "v": v}
    return None


def ui_clip(c: dict) -> dict:
    """Ajoute au Short les textes affichés dans la langue de l'interface (raisons, catégorie)."""
    codes = c.get("reason_codes")
    if codes:
        c["reasons_ui"] = [render_reason(x) for x in codes]
    else:
        out = []
        for r in c.get("reasons") or []:
            code = _legacy_code(str(r)) if lang() != "fr" else None
            out.append(render_reason(code) if code else str(r))
        c["reasons_ui"] = out
    cat = c.get("category") or ""
    c["category_ui"] = STR.get(lang(), STR["en"]).get("cat." + cat) or c.get("category_label") or cat
    return c
