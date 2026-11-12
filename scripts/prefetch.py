"""Télécharge les modèles locaux à l'avance et vérifie qu'ils tournent sur le GPU.

Appelé par setup.ps1. Chaque étape est indépendante : un échec n'empêche pas
les autres (l'application a des solutions de secours).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vertical import config, env  # noqa: E402  (config fixe HF_HOME dans le dossier de l'app)


def step(msg: str) -> None:
    print(f"    - {msg}", flush=True)


def whisper() -> None:
    try:
        env.setup_cuda_dlls()
        from faster_whisper import WhisperModel
        from vertical.transcribe import WHISPER_DIR
        gpu = env.gpu_info()
        name = "large-v3-turbo" if gpu["cuda"] else "small"
        step(f"Whisper « {name} » (téléchargement ~{'1,6 Go' if gpu['cuda'] else '500 Mo'} la première fois)…")
        t = time.time()
        try:
            m = WhisperModel(name, device="cuda" if gpu["cuda"] else "cpu",
                             compute_type="int8_float16" if gpu["cuda"] else "int8", download_root=str(WHISPER_DIR))
            import numpy as np
            list(m.transcribe(np.zeros(16000 * 2, dtype=np.float32), language="fr")[0])
            step(f"Whisper OK sur {'GPU' if gpu['cuda'] else 'CPU'} ({time.time() - t:.0f} s)")
        except Exception as e:
            step(f"Whisper GPU indisponible ({e}) → test CPU")
            WhisperModel("small", device="cpu", compute_type="int8", download_root=str(WHISPER_DIR))
            step("Whisper OK sur CPU (modèle small)")
    except Exception as e:
        step(f"[!] Whisper : {e}")


def hf_models() -> None:
    try:
        import torch  # noqa: F401
        from transformers import (ASTFeatureExtractor, ASTForAudioClassification, CLIPModel,
                                  CLIPProcessor)
        from vertical.ai_models import AST_ID, CLIP_ID
        step("CLIP (reconnaissance d'image, ~600 Mo)…")
        CLIPModel.from_pretrained(CLIP_ID)
        CLIPProcessor.from_pretrained(CLIP_ID)
        step("AST (reconnaissance des sons, ~350 Mo)…")
        ASTFeatureExtractor.from_pretrained(AST_ID)
        ASTForAudioClassification.from_pretrained(AST_ID)
        import torch as t
        step(f"PyTorch {t.__version__} — CUDA : {'oui (' + t.cuda.get_device_name(0) + ')' if t.cuda.is_available() else 'non'}")
    except Exception as e:
        step(f"[!] Modèles image/son : {e}")


if __name__ == "__main__":
    print("    Dossier des modèles :", config.MODELS_DIR, flush=True)
    whisper()
    hf_models()
