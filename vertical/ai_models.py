"""Modèles IA locaux optionnels (PyTorch + transformers) :

* CLIP (openai/clip-vit-base-patch16) : reconnaissance d'événements à l'écran
  par description textuelle (« écran de mort », « combat de boss »…) et du genre de jeu.
* AST (MIT/ast-finetuned-audioset) : classification sonore (rires, cris, explosions…).

S'ils ne sont pas disponibles, `available()` renvoie False et l'analyse se
contente des signaux audio/vidéo classiques.
"""
from __future__ import annotations

import gc
import logging

import numpy as np

from . import env

log = logging.getLogger("vertical")

CLIP_ID = "openai/clip-vit-base-patch16"
AST_ID = "MIT/ast-finetuned-audioset-10-10-0.4593"

AUDIO_GROUPS = {
    "laugh": ["Laughter", "Giggle", "Snicker", "Belly laugh", "Chuckle, chortle", "Baby laughter"],
    "scream": ["Screaming", "Yell", "Shout", "Battle cry", "Bellow", "Whoop", "Children shouting", "Wail, moan"],
    "cheer": ["Cheering", "Applause", "Crowd", "Clapping"],
    "gasp": ["Gasp", "Groan", "Grunt"],
    "boom": ["Explosion", "Gunshot, gunfire", "Machine gun", "Artillery fire", "Boom", "Fusillade", "Burst, pop"],
    "impact": ["Smash, crash", "Whack, thwack", "Slam", "Thump, thud", "Clang", "Breaking", "Shatter", "Bang"],
}

NEUTRAL_PROMPTS = [
    "a video game pause menu or inventory screen",
    "a video game loading screen",
    "a calm video game scene with a character walking or exploring",
    "a video game map screen",
    "a streamer talking to the camera",
    "a dialogue cutscene in a video game",
]

_clip = None
_ast = None


def available() -> bool:
    return env.has_module("torch") and env.has_module("transformers")


def _dtype():
    import torch
    return torch.float16 if env.torch_device() == "cuda" else torch.float32


def unload() -> None:
    global _clip, _ast
    _clip = None
    _ast = None
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


# --------------------------------------------------------------------------- CLIP
def _load_clip():
    global _clip
    if _clip is None:
        import torch
        from transformers import CLIPModel, CLIPProcessor
        dev = env.torch_device()
        model = CLIPModel.from_pretrained(CLIP_ID, torch_dtype=_dtype()).to(dev).eval()
        proc = CLIPProcessor.from_pretrained(CLIP_ID)
        _clip = (model, proc, dev, torch)
    return _clip


def clip_text_embed(prompts: list[str]) -> np.ndarray:
    model, proc, dev, torch = _load_clip()
    with torch.no_grad():
        t = proc(text=prompts, return_tensors="pt", padding=True).to(dev)
        e = model.get_text_features(**t)
        e = e / e.norm(dim=-1, keepdim=True)
    return e.float().cpu().numpy()


def clip_image_embed(frames: np.ndarray, batch: int = 64) -> np.ndarray:
    model, proc, dev, torch = _load_clip()
    outs = []
    with torch.no_grad():
        for i in range(0, len(frames), batch):
            px = proc(images=list(frames[i:i + batch]), return_tensors="pt")["pixel_values"].to(dev, _dtype())
            e = model.get_image_features(pixel_values=px)
            e = e / e.norm(dim=-1, keepdim=True)
            outs.append(e.float().cpu().numpy())
    return np.concatenate(outs) if outs else np.zeros((0, 512), np.float32)


def clip_scores(frames: np.ndarray, prompts: list[str]) -> np.ndarray:
    """Probabilités [N_images, N_prompts] (softmax incluant des prompts neutres)."""
    allp = prompts + NEUTRAL_PROMPTS
    te = clip_text_embed(allp)
    ie = clip_image_embed(frames)
    logits = 100.0 * ie @ te.T
    logits -= logits.max(axis=1, keepdims=True)
    p = np.exp(logits)
    p /= p.sum(axis=1, keepdims=True)
    return p[:, : len(prompts)]


# --------------------------------------------------------------------------- AST
def _load_ast():
    global _ast
    if _ast is None:
        import torch
        from transformers import ASTFeatureExtractor, ASTForAudioClassification
        dev = env.torch_device()
        fe = ASTFeatureExtractor.from_pretrained(AST_ID)
        model = ASTForAudioClassification.from_pretrained(AST_ID, torch_dtype=_dtype()).to(dev).eval()
        id2 = model.config.id2label
        groups = {g: [i for i, n in id2.items() if n in names] for g, names in AUDIO_GROUPS.items()}
        _ast = (model, fe, dev, torch, groups)
    return _ast


def audio_events(chunks: list[np.ndarray], batch: int = 16) -> list[dict]:
    """Pour chaque extrait audio 16 kHz : probabilité max par groupe d'événements."""
    model, fe, dev, torch, groups = _load_ast()
    res = []
    with torch.no_grad():
        for i in range(0, len(chunks), batch):
            part = [c if len(c) > 1600 else np.pad(c, (0, 1600 - len(c))) for c in chunks[i:i + batch]]
            inp = fe(part, sampling_rate=16000, return_tensors="pt")["input_values"].to(dev, _dtype())
            prob = torch.sigmoid(model(input_values=inp).logits).float().cpu().numpy()
            for row in prob:
                res.append({g: float(row[idx].max()) if idx else 0.0 for g, idx in groups.items()})
    return res
