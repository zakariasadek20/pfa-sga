"""Valide le détecteur de vivant sur de vrais visages (jeu LFW).

De vraies photographies doivent être classées « live ». La détection d'attaque
(photo présentée à la caméra) ne peut être éprouvée ici faute d'images d'attaque ;
elle se testera sur une machine avec une webcam et une photo affichée à l'écran.

    python scripts/test_antispoofing.py
"""

import glob
import os
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.datasets import get_data_home  # noqa: E402

from face_attendance.face.antispoofing import get_detector  # noqa: E402
from face_attendance.face.engine import FaceEngine  # noqa: E402


def main():
    detector = get_detector()
    if detector is None:
        print("Modèle anti-spoofing absent — détection désactivée.")
        return

    engine = FaceEngine()
    lfw = os.path.join(get_data_home(), "lfw_home", "lfw_funneled")
    people = [d for d in sorted(os.listdir(lfw)) if os.path.isdir(os.path.join(lfw, d))]

    reals, tested = 0, 0
    for name in people[:8]:
        imgs = sorted(glob.glob(os.path.join(lfw, name, "*.jpg")))
        if not imgs:
            continue
        img = cv2.imread(imgs[0])
        faces = engine.analyze(img)
        if not faces:
            continue
        faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
        is_real, score = detector.predict(img, faces[0].bbox)
        tested += 1
        reals += int(is_real)
        print(f"  {name:20s} live={score:.3f}  -> {'RÉEL' if is_real else 'suspect'}")

    print(f"\n{reals}/{tested} vrais visages classés « réel ».")
    print("VALIDATION OK" if tested and reals >= tested * 0.6 else "À VÉRIFIER")


if __name__ == "__main__":
    main()
