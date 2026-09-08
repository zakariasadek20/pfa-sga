"""Figure du rapport : photo de classe annotée (mêmes étudiants que la démo).

Compose une photo de classe avec les six étudiants enrôlés (base de la démo)
plus deux personnes non inscrites (intrus), lance la reconnaissance réelle et
annote chaque visage : cadre vert + nom pour un étudiant reconnu, cadre rouge
« Inconnu » pour un intrus. Sert de figure à la section « configuration
multi-visages » du rapport et de la présentation.

    python scripts/demo_classroom_figure.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from face_attendance import config                        # noqa: E402
from face_attendance.api import face_service, models      # noqa: E402
from face_attendance.api.database import SessionLocal     # noqa: E402
from face_attendance.face.engine import identify          # noqa: E402
from demo_seed import face_crop, STUDENTS                 # noqa: E402

FACES = config.DATA_DIR / "demo_faces"
INTRUS = [FACES / "intrus" / "37148308.jpg", FACES / "intrus" / "21792041.jpg"]
OUT = Path(__file__).resolve().parent.parent / "rapport" / "diagrammes" / "fig_classe_annotee.png"


def main():
    eng = face_service.get_engine()
    db = SessionLocal()
    emap = face_service.build_enroll_map(db)

    # visages : 6 étudiants (photo d'origine) + 2 intrus
    sources = [FACES / f for *_, f in STUDENTS] + INTRUS
    crops = [face_crop(eng, cv2.imread(str(p)), size=320) for p in sources]

    cols, cell, gap, pad, top = 4, 320, 18, 30, 70
    rows = (len(crops) + cols - 1) // cols
    W = pad * 2 + cols * cell + (cols - 1) * gap
    H = top + pad + rows * cell + (rows - 1) * gap + pad
    canvas = np.full((H, W, 3), 240, np.uint8)
    cv2.rectangle(canvas, (0, 0), (W, 52), (93, 58, 23), -1)
    cv2.putText(canvas, "Prise de presence - Intelligence Artificielle (2A)",
                (pad, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    for i, crop in enumerate(crops):
        r, c = divmod(i, cols)
        x, y = pad + c * (cell + gap), top + pad + r * (cell + gap)
        canvas[y:y + cell, x:x + cell] = crop

    faces = eng.analyze(canvas)
    reconnus = intrus_rejetes = 0
    for f in faces:
        sid, score = identify(f.embedding, emap, config.MATCH_THRESHOLD)
        x1, y1, x2, y2 = f.bbox
        if sid is not None:
            etu = db.get(models.Etudiant, sid)
            label = f"{etu.prenom} {etu.nom}"
            color = (0, 150, 0); reconnus += 1
        else:
            label = "Inconnu"; color = (0, 0, 210); intrus_rejetes += 1
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 3)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(canvas, (x1, y2), (x1 + tw + 10, y2 + 26), color, -1)
        cv2.putText(canvas, label, (x1 + 5, y2 + 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imwrite(str(OUT), canvas)
    print(f"visages : {len(crops)} posés ({len(STUDENTS)} étudiants + {len(INTRUS)} intrus)")
    print(f"détectés : {len(faces)} | reconnus : {reconnus} | intrus rejetés : {intrus_rejetes}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
