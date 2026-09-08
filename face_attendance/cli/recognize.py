"""Reconnaissance des étudiants présents sur une photo de classe.

    python -m face_attendance.cli.recognize data/test/classe.jpg

Produit la liste des étudiants reconnus et une image annotée.
"""

import sys

import cv2

from .. import config
from ..face.engine import FaceEngine, identify
from ..face.enrollment import load_db


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage : python -m face_attendance.cli.recognize <photo.jpg>")
        return
    photo = sys.argv[1]
    img = cv2.imread(photo)
    if img is None:
        print("Image introuvable :", photo)
        return
    if not config.DB_PATH.exists():
        print("Base d'empreintes absente. Lancez d'abord l'enrôlement.")
        return

    db = load_db(config.DB_PATH)
    engine = FaceEngine(config.MODEL_NAME, config.DET_SIZE)
    faces = engine.analyze(img)

    present = []
    for f in faces:
        name, sim = identify(f.embedding, db, config.MATCH_THRESHOLD)
        label = f"{name} ({sim:.2f})" if name else f"Inconnu ({sim:.2f})"
        if name:
            present.append(name)
        x1, y1, x2, y2 = f.bbox
        color = (0, 180, 0) if name else (0, 0, 200)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            img, label, (x1, max(0, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
        )

    out = config.DATA_DIR / "resultat_reconnaissance.jpg"
    cv2.imwrite(str(out), img)
    print(f"{len(faces)} visage(s) détecté(s), {len(set(present))} reconnu(s).")
    for name in sorted(set(present)):
        print("  présent :", name)
    print("Image annotée :", out)


if __name__ == "__main__":
    main()
