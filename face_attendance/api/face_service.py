"""Service reliant l'API au moteur de reconnaissance faciale.

Charge le moteur une seule fois (coûteux), décode les images reçues et fournit
les opérations d'enrôlement (empreinte d'une photo) et de reconnaissance (mise
en correspondance des visages d'une image avec les étudiants enrôlés).
"""

from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np

from .. import config
from ..face.engine import FaceEngine, identify


@lru_cache(maxsize=1)
def get_engine() -> FaceEngine:
    return FaceEngine(config.MODEL_NAME, config.DET_SIZE)


def decode_image(data: bytes):
    """Décode des octets d'image en tableau BGR (OpenCV)."""
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _largest(faces):
    faces.sort(
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
        reverse=True,
    )
    return faces


def main_face_embedding(data: bytes):
    """Empreinte du visage principal d'une photo (enrôlement). None si absent."""
    img = decode_image(data)
    if img is None:
        return None
    faces = get_engine().analyze(img)
    if not faces:
        return None
    return _largest(faces)[0].embedding


def build_enroll_map(db) -> dict:
    """Construit ``{etudiant_id: ndarray (n, 512)}`` depuis la base."""
    from .models import EmpreinteReference

    tmp: dict = {}
    for row in db.query(EmpreinteReference).all():
        vec = np.frombuffer(row.vecteur, dtype=np.float32)
        tmp.setdefault(row.etudiant_id, []).append(vec)
    return {sid: np.vstack(vs) for sid, vs in tmp.items()}


def recognize(data: bytes, enroll_map: dict, threshold: float) -> list:
    """Reconnaît chaque visage d'une image. Renvoie une liste de résultats."""
    img = decode_image(data)
    results = []
    if img is None:
        return results
    for f in get_engine().analyze(img):
        sid, score = identify(f.embedding, enroll_map, threshold)
        results.append(
            {"etudiant_id": sid, "score": round(float(score), 3),
             "bbox": [int(v) for v in f.bbox]}
        )
    return results
