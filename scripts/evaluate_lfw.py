"""Évaluation du moteur de reconnaissance sur le jeu public LFW.

Protocole : on choisit un ensemble d'identités disposant d'assez de photos, on
en *enrôle* quelques-unes par personne (comme le ferait l'administrateur), puis
on teste la reconnaissance sur les photos restantes. On mesure :

  - la précision d'identification (top-1) au seuil courant ;
  - les similarités « genuine » (même personne) vs « impostor » (personnes
    différentes) ;
  - un balayage de seuils donnant FAR (fausses acceptations) et FRR (faux
    rejets), afin de choisir le seuil optimal.

LFW est un jeu de données académique public (personnalités publiques) : il sert
ici uniquement à l'évaluation technique, pas à l'application déployée.

    python scripts/evaluate_lfw.py
"""

import os
import sys
from glob import glob
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.datasets import get_data_home  # noqa: E402

from face_attendance.face.engine import FaceEngine, identify  # noqa: E402

N_IDENTITIES = 15   # nombre d'étudiants simulés
ENROLL_K = 3        # photos d'enrôlement par personne
TEST_K = 5          # photos de test par personne
MIN_IMAGES = ENROLL_K + 2


def _area(face):
    x1, y1, x2, y2 = face.bbox
    return (x2 - x1) * (y2 - y1)


def embed_main_face(engine, path):
    import cv2

    img = cv2.imread(path)
    if img is None:
        return None
    faces = engine.analyze(img)
    if not faces:
        return None
    faces.sort(key=_area, reverse=True)
    return faces[0].embedding


def main() -> None:
    lfw_dir = os.path.join(get_data_home(), "lfw_home", "lfw_funneled")
    if not os.path.isdir(lfw_dir):
        print("LFW introuvable. Lancez d'abord le téléchargement.")
        return

    people = []
    for name in sorted(os.listdir(lfw_dir)):
        pdir = os.path.join(lfw_dir, name)
        if not os.path.isdir(pdir):
            continue
        imgs = sorted(glob(os.path.join(pdir, "*.jpg")))
        if len(imgs) >= MIN_IMAGES:
            people.append((name, imgs))
    # On prend des identités avec suffisamment de photos, mais pas les 2-3
    # personnes hyper-représentées : un échantillon plus réaliste.
    people = [p for p in people if len(p[1]) <= 40][:N_IDENTITIES]
    print(f"{len(people)} identités sélectionnées pour l'évaluation.")

    engine = FaceEngine()

    db = {}
    test_set = []  # (nom_vrai, embedding)
    for name, imgs in people:
        embs = []
        for path in imgs[:ENROLL_K]:
            e = embed_main_face(engine, path)
            if e is not None:
                embs.append(e)
        if not embs:
            continue
        db[name] = np.vstack(embs)
        for path in imgs[ENROLL_K:ENROLL_K + TEST_K]:
            e = embed_main_face(engine, path)
            if e is not None:
                test_set.append((name, e))

    if not test_set:
        print("Aucune image de test exploitable.")
        return

    # --- Précision d'identification au seuil courant ---
    from face_attendance import config

    correct = 0
    genuine, impostor = [], []
    for true_name, emb in test_set:
        pred, _ = identify(emb, db, config.MATCH_THRESHOLD)
        if pred == true_name:
            correct += 1
        e = emb / (np.linalg.norm(emb) + 1e-8)
        genuine.append(float(np.max(db[true_name] @ e)))
        for other, embs in db.items():
            if other != true_name:
                impostor.append(float(np.max(embs @ e)))

    acc = correct / len(test_set)
    genuine = np.array(genuine)
    impostor = np.array(impostor)

    print("\n=== Résultats ===")
    print(f"Identités : {len(db)} | photos de test : {len(test_set)}")
    print(f"Précision (top-1) au seuil {config.MATCH_THRESHOLD} : {acc*100:.1f}%")
    print(f"Similarité genuine  : moy={genuine.mean():.3f}  min={genuine.min():.3f}")
    print(f"Similarité impostor : moy={impostor.mean():.3f}  max={impostor.max():.3f}")

    # --- Balayage de seuils : FAR / FRR ---
    print("\nSeuil |  FRR (faux rejets) |  FAR (fausses accept.)")
    best_t, best_gap = None, 1e9
    for t in np.arange(0.20, 0.55, 0.05):
        frr = float(np.mean(genuine < t))
        far = float(np.mean(impostor >= t))
        print(f" {t:.2f} |      {frr*100:5.1f}%       |      {far*100:5.1f}%")
        if abs(frr - far) < best_gap:
            best_gap, best_t = abs(frr - far), t
    print(f"\nSeuil d'équilibre approx. (FAR≈FRR) : {best_t:.2f}")


if __name__ == "__main__":
    main()
