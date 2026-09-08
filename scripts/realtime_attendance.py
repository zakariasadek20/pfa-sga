"""Prise de présence en temps réel via webcam.

À exécuter sur une machine équipée d'une caméra (ne fonctionne pas en headless).
Charge la base d'empreintes, ouvre la webcam, reconnaît les visages en direct,
affiche les noms, cumule les étudiants vus, puis permet d'enregistrer la liste.

Touches :  's' = afficher/mémoriser les présents  ·  'q' = quitter.

    python scripts/realtime_attendance.py --camera 0
"""

import argparse
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from face_attendance import config
from face_attendance.face.engine import FaceEngine, identify
from face_attendance.face.enrollment import load_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Prise de présence temps réel (webcam).")
    parser.add_argument("--camera", type=int, default=0, help="Index de la caméra.")
    args = parser.parse_args()

    if not config.DB_PATH.exists():
        print("Base d'empreintes absente. Lancez d'abord l'enrôlement "
              "(python -m face_attendance.cli.enroll).")
        return

    db = load_db(config.DB_PATH)
    engine = FaceEngine(config.MODEL_NAME, config.DET_SIZE)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print("Impossible d'ouvrir la caméra", args.camera)
        return

    present = set()
    print("Caméra ouverte. Touche 's' = présents, 'q' = quitter.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        for f in engine.analyze(frame):
            name, sim = identify(f.embedding, db, config.MATCH_THRESHOLD)
            x1, y1, x2, y2 = f.bbox
            color = (0, 170, 0) if name else (40, 40, 220)
            label = f"{name} ({sim:.2f})" if name else "Inconnu"
            if name:
                present.add(name)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, max(14, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.putText(frame, f"Presents cumules : {len(present)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("AI Class Attendance - temps reel", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("s"):
            print("Présents :", sorted(present))

    cap.release()
    cv2.destroyAllWindows()
    print("Liste finale des présents :", sorted(present))


if __name__ == "__main__":
    main()
