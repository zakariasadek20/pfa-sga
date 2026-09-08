"""Évaluation en configuration « salle de classe » (multi-visages).

Contrairement à `evaluate_lfw.py` (une photo = un visage, conditions
contrôlées), ce script reproduit la situation réelle d'une prise de présence :
une **seule photographie** contenant **plusieurs visages** de tailles et
d'orientations variées, dont certains correspondent à des étudiants enrôlés et
d'autres à des personnes inconnues (intrus). On mesure la détection, la
reconnaissance des présents et le rejet des inconnus, et on sauvegarde l'image
annotée servant de figure au rapport.

    python scripts/evaluate_classroom.py
"""

import os
import sys
import time
from glob import glob
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.datasets import get_data_home  # noqa: E402

from face_attendance import config  # noqa: E402
from face_attendance.face.engine import FaceEngine, identify  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "rapport" / "diagrammes" / "fig_classe_annotee.png"
N_ENROLLED = 10     # étudiants inscrits (roster)
N_INTRUDERS = 2     # personnes non inscrites présentes sur la photo
ENROLL_K = 3
COLS = 4
CELL = 240          # taille d'une case de la grille (px)


def rich_people(lfw_dir, need):
    out = []
    for name in sorted(os.listdir(lfw_dir)):
        pdir = os.path.join(lfw_dir, name)
        imgs = sorted(glob(os.path.join(pdir, "*.jpg"))) if os.path.isdir(pdir) else []
        if len(imgs) >= ENROLL_K + 1:
            out.append((name, imgs))
        if len(out) >= need:
            break
    return out


def embed_main(engine, path):
    img = cv2.imread(path)
    if img is None:
        return None
    faces = engine.analyze(img)
    if not faces:
        return None
    faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces[0].embedding


def place(canvas, img, r, c, scale, angle):
    """Colle `img` (redimensionnée+tournée) dans la case (r,c) ; renvoie le centre."""
    size = int(CELL * scale)
    face = cv2.resize(img, (size, size))
    if angle:
        M = cv2.getRotationMatrix2D((size / 2, size / 2), angle, 1.0)
        face = cv2.warpAffine(face, M, (size, size), borderValue=(240, 240, 240))
    y0 = r * CELL + (CELL - size) // 2
    x0 = c * CELL + (CELL - size) // 2
    canvas[y0:y0 + size, x0:x0 + size] = face
    return (c * CELL + CELL // 2, r * CELL + CELL // 2)


def main():
    lfw = os.path.join(get_data_home(), "lfw_home", "lfw_funneled")
    people = rich_people(lfw, N_ENROLLED + N_INTRUDERS)
    roster = people[:N_ENROLLED]
    intruders = people[N_ENROLLED:N_ENROLLED + N_INTRUDERS]

    engine = FaceEngine()

    # --- enrôlement du roster (3 photos/étudiant) ---
    db = {}
    for name, imgs in roster:
        embs = [e for e in (embed_main(engine, p) for p in imgs[:ENROLL_K]) if e is not None]
        if embs:
            db[name] = np.vstack(embs)

    # --- construction de la « photo de classe » (grille multi-visages) ---
    members = ([(n, imgs[ENROLL_K], True) for n, imgs in roster]
               + [(n, imgs[0], False) for n, imgs in intruders])
    rng_scales = [1.0, 0.85, 0.7, 0.95, 0.8, 1.0, 0.75, 0.9, 0.82, 1.0, 0.88, 0.78]
    rng_angles = [0, 0, -12, 0, 8, 0, 0, -8, 0, 12, 0, 0]
    rows = (len(members) + COLS - 1) // COLS
    canvas = np.full((rows * CELL, COLS * CELL, 3), 245, np.uint8)

    truth = []  # (center, nom_vrai ou None si intrus)
    for i, (name, path, enrolled) in enumerate(members):
        img = cv2.imread(path)
        cx, cy = place(canvas, img, i // COLS, i % COLS,
                       rng_scales[i % len(rng_scales)], rng_angles[i % len(rng_angles)])
        truth.append(((cx, cy), name if enrolled else None))

    # --- reconnaissance sur la photo de classe ---
    t0 = time.time()
    faces = engine.analyze(canvas)
    dt = time.time() - t0

    def nearest_truth(bb):
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        return min(truth, key=lambda tc: (tc[0][0] - cx) ** 2 + (tc[0][1] - cy) ** 2)

    present_ok = intruder_ok = present_total = intruder_total = 0
    for _, t in truth:
        if t is None:
            intruder_total += 1
        else:
            present_total += 1

    annotated = canvas.copy()
    for f in faces:
        name, sim = identify(f.embedding, db, config.MATCH_THRESHOLD)
        (_, true_name) = nearest_truth(f.bbox)
        x1, y1, x2, y2 = f.bbox
        if true_name is None:                      # intrus
            ok = name is None
            intruder_ok += 1 if ok else 0
        else:                                      # étudiant présent
            ok = (name == true_name)
            present_ok += 1 if ok else 0
        color = (0, 170, 0) if ok else (0, 0, 220)
        label = (name.replace("_", " ") if name else "Inconnu")
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.rectangle(annotated, (x1, y2), (x2, y2 + 22), color, -1)
        cv2.putText(annotated, label[:16], (x1 + 3, y2 + 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT), annotated)

    print("=== Configuration salle de classe (multi-visages) ===")
    print(f"Roster (étudiants inscrits)  : {len(db)}")
    print(f"Visages sur la photo         : {len(members)} "
          f"({present_total} présents + {intruder_total} intrus)")
    print(f"Visages détectés             : {len(faces)}")
    print(f"Présents correctement reconnus : {present_ok}/{present_total}")
    print(f"Intrus correctement rejetés    : {intruder_ok}/{intruder_total}")
    print(f"Temps de traitement de la photo : {dt*1000:.0f} ms")
    print(f"Figure annotée -> {OUT}")


if __name__ == "__main__":
    main()
