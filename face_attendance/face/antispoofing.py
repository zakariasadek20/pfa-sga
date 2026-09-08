"""Détection du vivant (anti-spoofing) via MiniFASNet-V2 (ONNX).

Modèle : garciafido/minifasnet-v2-anti-spoofing-onnx (issu de Silent-Face,
Apache-2.0), exécuté avec onnxruntime — aucune dépendance PyTorch/TensorFlow.
Entrée : visage recadré 80×80, BGR, en valeurs brutes [0, 255]. Sortie : trois
classes dont l'indice 1 correspond à « live » (convention Silent-Face d'origine).
Un visage est jugé réel lorsque la probabilité de la classe « live » dépasse le seuil.

ATTENTION (validation). Le prétraitement (BGR [0, 255]) et l'ordre des classes
(live à l'indice 1) ci-dessus ont été déterminés **empiriquement** : la fiche du
modèle sur Hugging Face les décrit autrement (normalisation /255, live à l'indice
0), ce qui produit des sorties incohérentes. Avec la configuration retenue, les
vrais visages sont correctement classés « live ». En revanche, le **rejet effectif
d'une attaque** (photo imprimée ou écran) n'a pas pu être validé ici faute d'images
d'attaque : il doit être éprouvé sur une machine réelle avec une webcam avant d'être
utilisé en production.
"""

from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np

from .. import config


def _new_box(src_w, src_h, bbox_xywh, scale):
    """Boîte agrandie de ``scale`` autour du centre du visage, bornée à l'image.

    Reproduit le recadrage de Silent-Face (préfixe « 2.7_80x80 »).
    """
    x, y, w, h = bbox_xywh
    scale = min((src_h - 1) / h, (src_w - 1) / w, scale)
    new_w, new_h = w * scale, h * scale
    cx, cy = x + w / 2.0, y + h / 2.0
    left, top = cx - new_w / 2.0, cy - new_h / 2.0
    right, bottom = cx + new_w / 2.0, cy + new_h / 2.0
    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > src_w - 1:
        left -= right - src_w + 1
        right = src_w - 1
    if bottom > src_h - 1:
        top -= bottom - src_h + 1
        bottom = src_h - 1
    return int(left), int(top), int(right), int(bottom)


class LivenessDetector:
    """Classifie un visage comme réel ou factice (photo / écran)."""

    def __init__(self, model_path, scale: float = 2.7, threshold: float = 0.5):
        import onnxruntime as ort

        self._sess = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        self._input = self._sess.get_inputs()[0].name
        self.scale = scale
        self.threshold = threshold

    def _crop(self, image_bgr, bbox_xywh):
        h, w = image_bgr.shape[:2]
        left, top, right, bottom = _new_box(w, h, bbox_xywh, self.scale)
        crop = image_bgr[top:bottom, left:right]
        if crop.size == 0:
            crop = image_bgr
        return cv2.resize(crop, (80, 80))

    def predict(self, image_bgr, bbox_xyxy) -> tuple:
        """Renvoie ``(is_real, live_score)`` pour un visage repéré par sa boîte."""
        x1, y1, x2, y2 = bbox_xyxy
        crop = self._crop(image_bgr, (x1, y1, x2 - x1, y2 - y1)).astype("float32")
        blob = crop.transpose(2, 0, 1)[None, ...]  # BGR [0, 255], NCHW
        logits = self._sess.run(None, {self._input: blob})[0][0]
        exp = np.exp(logits - logits.max())
        probs = exp / exp.sum()
        live = float(probs[1])  # indice 1 = « live »
        return (live >= self.threshold), round(live, 3)


@lru_cache(maxsize=1)
def get_detector():
    """Détecteur si le modèle est présent, sinon ``None`` (anti-spoofing désactivé)."""
    path = config.ANTISPOOF_MODEL_PATH
    if not path.exists():
        return None
    return LivenessDetector(path, config.ANTISPOOF_SCALE, config.ANTISPOOF_THRESHOLD)
