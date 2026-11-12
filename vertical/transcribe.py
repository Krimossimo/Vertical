"""Transcription locale avec faster-whisper (timestamps au mot).

Chaîne de secours : GPU large-v3-turbo → GPU medium → CPU small → CPU base.
"""
from __future__ import annotations

import gc
import logging
import re
from pathlib import Path
from typing import Callable

from . import env
from . import transcript_tools
from .i18n import tr
from .config import MODELS_DIR, read_json, write_json

log = logging.getLogger("vertical")

WHISPER_DIR = MODELS_DIR / "whisper"
# découpage de la parole plus fin que le réglage par défaut (2 s de silence) : segments
# plus courts = horodatage des mots plus précis et moins de boucles de répétition
VAD_PARAMS = {"threshold": 0.5, "min_silence_duration_ms": 500, "speech_pad_ms": 250}
# phrases fantômes typiques de Whisper sur du silence / de la musique
HALLU = re.compile(r"sous-titr|amara\.org|merci d'avoir regard|abonnez-vous|thanks for watching|subtitles by", re.I)


def _plan(pref: str) -> list[tuple[str, str, str]]:
    gpu = env.gpu_info()
    plans: list[tuple[str, str, str]] = []
    if gpu["cuda"]:
        big = "large-v3-turbo" if gpu["vram_gb"] >= 5 else "medium"
        first = big if pref in ("auto", "", None) else pref
        plans += [("cuda", first, "int8_float16"), ("cuda", "medium", "int8_float16"), ("cuda", "small", "int8_float16")]
    cpu_first = "small" if pref in ("auto", "", None, "large-v3-turbo", "large-v3", "medium") else pref
    plans += [("cpu", cpu_first, "int8"), ("cpu", "base", "int8")]
    seen, out = set(), []
    for p in plans:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _free(model) -> None:
    del model
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def transcribe(audio: Path, out_json: Path, duration: float, language: str | None = "fr",
               model_pref: str = "auto", initial_prompt: str | None = None,
               on_progress: Callable[[float, str], None] | None = None) -> dict:
    cached = read_json(out_json)
    if cached and cached.get("segments") is not None and cached.get("source") == Path(audio).name:
        return cached
    if not env.has_module("faster_whisper"):
        res = {"segments": [], "engine": None, "error": tr("err.no_whisper")}
        write_json(out_json, res)
        return res

    env.setup_cuda_dlls()
    from faster_whisper import WhisperModel  # import tardif (lourd)

    try:
        from faster_whisper import BatchedInferencePipeline
    except ImportError:  # anciennes versions
        BatchedInferencePipeline = None

    lang = None if language in (None, "", "auto") else language
    last_err = None
    for device, name, ctype in _plan(model_pref):
        model = None
        try:
            if on_progress:
                on_progress(0.0, tr("wh_loading", m=name, dev="GPU" if device == "cuda" else "CPU"))
            model = WhisperModel(name, device=device, compute_type=ctype, download_root=str(WHISPER_DIR),
                                 cpu_threads=0 if device == "cuda" else 6)
            kwargs = dict(language=lang, word_timestamps=True, vad_filter=True, condition_on_previous_text=False,
                          beam_size=5 if device == "cuda" else 2, vad_parameters=dict(VAD_PARAMS))
            if initial_prompt:
                kwargs["initial_prompt"] = initial_prompt
            pipe = BatchedInferencePipeline(model=model) if (BatchedInferencePipeline is not None
                                                             and device == "cuda") else None

            def run(kw):
                if pipe is not None:
                    try:
                        it, inf = pipe.transcribe(str(audio), batch_size=8, **kw)
                    except TypeError:
                        kw.pop("condition_on_previous_text", None)
                        it, inf = pipe.transcribe(str(audio), batch_size=8, **kw)
                else:
                    it, inf = model.transcribe(str(audio), **kw)
                out = []
                for s in it:
                    if getattr(s, "no_speech_prob", 0) > 0.85 and getattr(s, "avg_logprob", 0) < -1.0:
                        continue
                    text = s.text.strip()
                    if not text or HALLU.search(text):
                        continue
                    words = [{"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word,
                              "p": round(float(getattr(w, "probability", 1.0)), 3)} for w in (s.words or [])]
                    out.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": text, "words": words})
                    if on_progress and duration > 0:
                        on_progress(min(0.999, s.end / duration),
                                    tr("wh_running", m=name, dev="GPU" if device == "cuda" else "CPU"))
                return out, inf

            segments, info = run(dict(kwargs))
            if not segments:  # voix très faible : VAD plus sensible
                if on_progress:
                    on_progress(0.0, tr("wh_retry"))
                kw2 = dict(kwargs)
                kw2["vad_parameters"] = {"threshold": 0.2, "min_silence_duration_ms": 600, "speech_pad_ms": 300}
                segments, info = run(kw2)
            segments = transcript_tools.rebuild(transcript_tools.clean_words(
                transcript_tools.flatten({"segments": segments})))["segments"]
            res = {"segments": segments, "engine": f"faster-whisper {name} ({device}/{ctype})",
                   "language": getattr(info, "language", lang), "source": Path(audio).name}
            write_json(out_json, res)
            _free(model)
            return res
        except Exception as e:  # on essaie la configuration suivante
            last_err = e
            log.warning("Whisper %s/%s a échoué : %s", device, name, e)
            if model is not None:
                _free(model)
    res = {"segments": [], "engine": None, "error": tr("err.transcribe", e=last_err)}
    write_json(out_json, res)
    return res


def words_flat(transcript: dict) -> list[dict]:
    """Mots de la transcription, nettoyés des boucles d'hallucination de Whisper."""
    return transcript_tools.clean_words(_words_raw(transcript))


def _words_raw(transcript: dict) -> list[dict]:
    out = []
    for s in transcript.get("segments", []):
        if s.get("words"):
            out.extend(s["words"])
        else:  # pas de mots : on répartit le texte sur la durée du segment
            toks = s["text"].split()
            if not toks:
                continue
            d = (s["end"] - s["start"]) / len(toks)
            for i, t in enumerate(toks):
                out.append({"start": s["start"] + i * d, "end": s["start"] + (i + 1) * d, "word": " " + t, "p": 0.5})
    return out


def text_between(transcript: dict, start: float, end: float) -> str:
    return " ".join(s["text"] for s in transcript.get("segments", []) if s["end"] > start and s["start"] < end).strip()


# --------------------------------------------------------------------------- re-transcription ciblée
def retranscribe_ranges(voice_wav: Path, ranges: list[tuple[float, float]], language: str | None = "fr",
                        precision: str = "max", vocabulary: str = "",
                        on_progress: Callable[[float, str], None] | None = None) -> tuple[list[dict], str]:
    """Re-transcrit uniquement les passages demandés avec les réglages les plus précis :
    modèle large-v3 (plus fiable que turbo), décodage séquentiel avec beam search,
    filtre anti-hallucination sur les silences, vocabulaire personnalisé."""
    import numpy as np
    from .audio_analysis import read_segment
    if not env.has_module("faster_whisper"):
        raise RuntimeError("faster-whisper n'est pas installé.")
    env.setup_cuda_dlls()
    from faster_whisper import WhisperModel
    gpu = env.gpu_info()
    plans = []
    if gpu["cuda"]:
        if precision == "max":
            plans.append(("cuda", "large-v3", "int8_float16"))
        plans.append(("cuda", "large-v3-turbo", "int8_float16"))
    plans += [("cpu", "medium" if precision == "max" else "small", "int8")]
    lang = None if language in (None, "", "auto") else language
    vocab = " ".join(vocabulary.replace(",", " ").split())
    last_err = None
    for device, name, ctype in plans:
        model = None
        try:
            if on_progress:
                on_progress(0.0, tr("wh_redo_loading", m=name, dev="GPU" if device == "cuda" else "CPU"))
            model = WhisperModel(name, device=device, compute_type=ctype, download_root=str(WHISPER_DIR))
            out: list[dict] = []
            total = sum(b - a for a, b in ranges) or 1
            done = 0.0
            for a, b in ranges:
                x = read_segment(voice_wav, a, b)
                if len(x) < 1600:
                    continue
                peak = float(np.percentile(np.abs(x), 99.9)) + 1e-6
                x = np.clip(x * min(20.0, 0.7 / peak), -1, 1).astype(np.float32)  # normalisation douce
                kw = dict(language=lang, word_timestamps=True, beam_size=5, best_of=5,
                          condition_on_previous_text=False, vad_filter=True, vad_parameters=dict(VAD_PARAMS),
                          hallucination_silence_threshold=1.5, no_speech_threshold=0.6)
                if vocab:
                    kw["initial_prompt"] = vocab
                    kw["hotwords"] = vocab
                try:
                    it, _ = model.transcribe(x, **kw)
                except TypeError:  # anciennes versions sans hotwords / hallucination_silence_threshold
                    kw.pop("hotwords", None)
                    kw.pop("hallucination_silence_threshold", None)
                    it, _ = model.transcribe(x, **kw)
                for seg in it:
                    if HALLU.search(seg.text or ""):
                        continue
                    for w in seg.words or []:
                        out.append({"start": round(a + w.start, 3), "end": round(a + w.end, 3), "word": w.word,
                                    "p": round(float(getattr(w, "probability", 1.0)), 3)})
                    if on_progress:
                        on_progress(min(0.999, (done + seg.end) / total), tr("wh_redo_running", m=name))
                done += b - a
            _free(model)
            return transcript_tools.clean_words(out), f"faster-whisper {name} ({device})"
        except Exception as e:
            last_err = e
            log.warning("Re-transcription %s/%s impossible : %s", device, name, e)
            if model is not None:
                _free(model)
    raise RuntimeError(f"Re-transcription impossible : {last_err}")
