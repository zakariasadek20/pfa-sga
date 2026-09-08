"""Génère les figures du chapitre Résultats à partir des vraies données LFW.

Produit deux images dans rapport/diagrammes/ :
  - fig_similarites.png : distributions des similarités (même personne vs différentes)
  - fig_far_frr.png     : FAR et FRR en fonction du seuil de décision

Paire de couleurs bleu / orange (sûre pour le daltonisme).
    python scripts/make_figures.py
"""

import glob
import os
import sys
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.datasets import get_data_home  # noqa: E402

from face_attendance.face.engine import FaceEngine  # noqa: E402

BLUE, ORANGE, GRAY = "#2563eb", "#ea580c", "#6b7280"
THRESHOLD = 0.35
OUT = Path(__file__).resolve().parent.parent / "rapport" / "diagrammes"


def _area(f):
    x1, y1, x2, y2 = f.bbox
    return (x2 - x1) * (y2 - y1)


def _emb(engine, path):
    import cv2

    img = cv2.imread(path)
    if img is None:
        return None
    faces = engine.analyze(img)
    if not faces:
        return None
    faces.sort(key=_area, reverse=True)
    return faces[0].embedding


def collect_similarities(n_ident=15, enroll_k=3, test_k=5):
    lfw = os.path.join(get_data_home(), "lfw_home", "lfw_funneled")
    people = []
    for name in sorted(os.listdir(lfw)):
        d = os.path.join(lfw, name)
        if os.path.isdir(d):
            imgs = sorted(glob.glob(os.path.join(d, "*.jpg")))
            if enroll_k + 2 <= len(imgs) <= 40:
                people.append((name, imgs))
        if len(people) >= n_ident:
            break

    engine = FaceEngine()
    db, test = {}, []
    for name, imgs in people:
        embs = [e for e in (_emb(engine, p) for p in imgs[:enroll_k]) if e is not None]
        if not embs:
            continue
        db[name] = np.vstack(embs)
        for p in imgs[enroll_k:enroll_k + test_k]:
            e = _emb(engine, p)
            if e is not None:
                test.append((name, e))

    genuine, impostor = [], []
    for true, emb in test:
        e = emb / (np.linalg.norm(emb) + 1e-8)
        genuine.append(float(np.max(db[true] @ e)))
        for other, embs in db.items():
            if other != true:
                impostor.append(float(np.max(embs @ e)))
    return np.array(genuine), np.array(impostor)


def fig_similarities(genuine, impostor):
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    bins = np.linspace(-0.2, 1.0, 40)
    ax.hist(impostor, bins=bins, density=True, color=ORANGE, alpha=0.65,
            label="Personnes différentes")
    ax.hist(genuine, bins=bins, density=True, color=BLUE, alpha=0.65,
            label="Même personne")
    ax.axvline(THRESHOLD, color=GRAY, ls="--", lw=1.5)
    ax.text(THRESHOLD + 0.01, ax.get_ylim()[1] * 0.9, f"seuil = {THRESHOLD}",
            color=GRAY, fontsize=9)
    ax.set_xlabel("Similarité cosinus")
    ax.set_ylabel("Densité")
    ax.set_title("Distributions des similarités : même personne vs différentes")
    ax.legend(frameon=False)
    ax.grid(True, color="#e5e7eb", lw=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_similarites.png")
    plt.close(fig)


def fig_far_frr(genuine, impostor):
    thr = np.linspace(0.0, 1.0, 101)
    frr = np.array([np.mean(genuine < t) for t in thr]) * 100
    far = np.array([np.mean(impostor >= t) for t in thr]) * 100

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    ax.plot(thr, frr, color=BLUE, lw=2, label="FRR — faux rejets")
    ax.plot(thr, far, color=ORANGE, lw=2, label="FAR — fausses acceptations")
    # Zone de seuils sûrs (FAR=FRR=0)
    safe = thr[(far == 0) & (frr == 0)]
    if len(safe):
        ax.axvspan(safe.min(), safe.max(), color="#dbeafe", alpha=0.5,
                   label="Plage de seuils sûrs")
    ax.axvline(THRESHOLD, color=GRAY, ls="--", lw=1.5)
    ax.set_xlabel("Seuil de similarité")
    ax.set_ylabel("Taux (%)")
    ax.set_title("FAR et FRR en fonction du seuil de décision")
    ax.legend(frameon=False)
    ax.grid(True, color="#e5e7eb", lw=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_far_frr.png")
    plt.close(fig)


def main():
    genuine, impostor = collect_similarities()
    print(f"genuine={len(genuine)}  impostor={len(impostor)}")
    fig_similarities(genuine, impostor)
    fig_far_frr(genuine, impostor)
    print("Figures écrites dans", OUT)


if __name__ == "__main__":
    main()
