"""Test de fumée du cœur IA.

Charge le moteur InsightFace (télécharge le modèle ``buffalo_l`` au premier
lancement) et, si une image est fournie, y détecte les visages.

    python scripts/smoke_test.py                    # chargement seul
    python scripts/smoke_test.py data/test/photo.jpg  # + détection
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from face_attendance.face.engine import FaceEngine  # noqa: E402


def main() -> None:
    print("Chargement du moteur IA (InsightFace buffalo_l)…")
    engine = FaceEngine()
    print("Moteur chargé avec succès.")

    if len(sys.argv) > 1:
        import cv2

        img_path = sys.argv[1]
        img = cv2.imread(img_path)
        if img is None:
            print("Image introuvable :", img_path)
            return
        faces = engine.analyze(img)
        print(f"{len(faces)} visage(s) détecté(s).")
        for i, f in enumerate(faces):
            print(
                f"  visage {i} : bbox={f.bbox} "
                f"score={f.det_score:.2f} empreinte={f.embedding.shape[0]}-d"
            )
    else:
        print("Aucune image fournie — test de chargement uniquement (OK).")


if __name__ == "__main__":
    main()
