"""Enrôlement : calcul et stockage des empreintes de référence des étudiants.

On parcourt ``data/enrollment/<nom_etudiant>/`` et, pour chaque photo, on calcule
l'empreinte du plus grand visage (supposé être l'étudiant au premier plan). Les
empreintes sont regroupées par étudiant et sauvegardées dans un fichier ``.npz``.
On stocke les empreintes plutôt que les images, par souci de minimisation.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

_IMG_EXTS = {".jpg", ".jpeg", ".png"}


def build_enrollment_db(engine, enroll_dir, min_faces: int = 1) -> dict:
    """Construit la base ``{nom_etudiant: ndarray (n, 512)}`` à partir des photos."""
    enroll_dir = Path(enroll_dir)
    db: dict = {}
    if not enroll_dir.exists():
        return db
    for student_dir in sorted(p for p in enroll_dir.iterdir() if p.is_dir()):
        embeddings = []
        for img_path in sorted(student_dir.iterdir()):
            if img_path.suffix.lower() not in _IMG_EXTS:
                continue
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            faces = engine.analyze(img)
            if not faces:
                continue
            # On garde le visage le plus grand (le plus proche de la caméra).
            faces.sort(
                key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
                reverse=True,
            )
            embeddings.append(faces[0].embedding)
        if len(embeddings) >= min_faces:
            db[student_dir.name] = np.vstack(embeddings)
    return db


def save_db(db: dict, path) -> None:
    """Sauvegarde la base d'empreintes au format ``.npz``."""
    np.savez(path, **db)


def load_db(path) -> dict:
    """Recharge la base d'empreintes depuis un fichier ``.npz``."""
    data = np.load(path, allow_pickle=False)
    return {name: data[name] for name in data.files}
