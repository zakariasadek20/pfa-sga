"""Moteur de reconnaissance faciale.

Backend : InsightFace, qui fournit la détection RetinaFace et l'empreinte
ArcFace (vecteur normalisé de 512 dimensions), conformément à la conception
du projet. Le moteur charge un modèle pré-entraîné et expose une opération
`analyze` qui localise chaque visage d'une image et en calcule l'empreinte.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DetectedFace:
    """Un visage détecté : sa position, son empreinte et le score de détection."""

    bbox: tuple  # (x1, y1, x2, y2)
    embedding: np.ndarray  # vecteur normalisé (512-d)
    det_score: float


class FaceEngine:
    """Détection (RetinaFace) + empreinte (ArcFace) via InsightFace."""

    def __init__(self, model_name: str = "buffalo_l", det_size: int = 640):
        # Import différé : InsightFace est lourd et n'est chargé qu'à l'usage.
        from insightface.app import FaceAnalysis

        self._app = FaceAnalysis(
            name=model_name, providers=["CPUExecutionProvider"]
        )
        # ctx_id=-1 force l'exécution sur CPU (pas de GPU requis).
        self._app.prepare(ctx_id=-1, det_size=(det_size, det_size))

    def analyze(self, image_bgr) -> list:
        """Renvoie la liste des visages détectés sur une image BGR (OpenCV)."""
        faces = self._app.get(image_bgr)
        out = []
        for f in faces:
            x1, y1, x2, y2 = (int(v) for v in f.bbox)
            out.append(
                DetectedFace(
                    bbox=(x1, y1, x2, y2),
                    embedding=f.normed_embedding.astype(np.float32),
                    det_score=float(f.det_score),
                )
            )
        return out


def identify(embedding: np.ndarray, db: dict, threshold: float):
    """Compare une empreinte à la base d'étudiants enrôlés.

    Renvoie ``(nom, similarité)`` si la meilleure similarité cosinus dépasse le
    seuil, sinon ``(None, similarité)``. Les empreintes InsightFace étant déjà
    normées, la similarité cosinus se réduit à un produit scalaire ; pour chaque
    étudiant on retient sa meilleure photo de référence.
    """
    e = embedding / (np.linalg.norm(embedding) + 1e-8)
    best_name, best_sim = None, -1.0
    for name, embs in db.items():
        sim = float(np.max(embs @ e))
        if sim > best_sim:
            best_sim, best_name = sim, name
    return (best_name, best_sim) if best_sim >= threshold else (None, best_sim)
