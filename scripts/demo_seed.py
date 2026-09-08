"""Prépare une démonstration réaliste : promotion d'étudiants + photo de classe.

Réinitialise la base, crée un enseignant / une classe / un module / une séance,
enrôle six étudiants (noms réalistes) à partir de portraits libres de droits
(Pexels, modèles consentants — utilisés uniquement pour la démonstration), puis
compose une « photo de classe » que le système saura reconnaître.

    python scripts/demo_seed.py
"""
import sys
from datetime import date, time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from face_attendance import config                       # noqa: E402
from face_attendance.api import face_service, models     # noqa: E402
from face_attendance.api.database import SessionLocal, engine, init_db  # noqa: E402

FACES = config.DATA_DIR / "demo_faces"
CLASS_PHOTO = config.DATA_DIR / "test" / "classe_demo.jpg"

# (nom, prénom, CNE, fichier photo) — genre du portrait respecté
STUDENTS = [
    ("El Amrani", "Yassine", "R138024501", "38165826.jpg"),
    ("Berrada", "Anas", "R137082204", "12311572.jpg"),
    ("Ouazzani", "Mehdi", "R139011238", "3474629.jpg"),
    ("Bennani", "Salma", "R135098742", "36215318.jpg"),
    ("Alaoui", "Khadija", "R134063390", "3754430.jpg"),
    ("Tazi", "Imane", "R136045519", "5941459.jpg"),
]


def reset_db(db):
    for M in (models.Presence, models.EmpreinteReference, models.Etudiant,
              models.Seance, models.Module, models.Classe, models.Enseignant):
        db.query(M).delete()
    db.commit()


def augment(img):
    """Trois vues d'un même portrait (comme plusieurs photos d'enrôlement)."""
    yield img
    yield cv2.convertScaleAbs(img, alpha=1.12, beta=8)          # + lumineux
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 6, 1.03)         # légère rotation
    yield cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def face_crop(engine_, img, margin=0.55, size=360):
    faces = engine_.analyze(img)
    if not faces:
        return None
    f = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    x1, y1, x2, y2 = f.bbox
    w, h = x2 - x1, y2 - y1
    cx, cy = x1 + w / 2, y1 + h / 2
    half = int(max(w, h) * (1 + margin) / 2)
    H, W = img.shape[:2]
    l, t = max(0, int(cx - half)), max(0, int(cy - half))
    r, b = min(W, int(cx + half)), min(H, int(cy + half))
    crop = img[t:b, l:r]
    return cv2.resize(crop, (size, size))


def build_class_photo(engine_, imgs):
    cols, cell, gap, pad = 3, 360, 16, 28
    rows = (len(imgs) + cols - 1) // cols
    W = pad * 2 + cols * cell + (cols - 1) * gap
    top = 88
    H = top + pad + rows * cell + (rows - 1) * gap + pad
    canvas = np.full((H, W, 3), 238, np.uint8)
    cv2.rectangle(canvas, (0, 0), (W, 60), (93, 58, 23), -1)     # bandeau navy (BGR)
    cv2.putText(canvas, "Seance IA - 2e annee Cycle Ingenieur", (pad, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    for i, crop in enumerate(imgs):
        r, c = divmod(i, cols)
        x = pad + c * (cell + gap)
        y = top + pad + r * (cell + gap)
        canvas[y:y + cell, x:x + cell] = crop
    CLASS_PHOTO.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(CLASS_PHOTO), canvas)


def main():
    init_db()
    eng = face_service.get_engine()
    db = SessionLocal()
    reset_db(db)

    ens = models.Enseignant(nom="Adama SAMAKE", email="a.samake@isga.ma")
    cls = models.Classe(libelle="2A Cycle Ingénieur", filiere="Génie Informatique",
                        niveau="2ᵉ année")
    db.add_all([ens, cls]); db.commit()
    mod = models.Module(libelle="Intelligence Artificielle",
                        enseignant_id=ens.id, classe_id=cls.id)
    db.add(mod); db.commit()
    sea = models.Seance(module_id=mod.id, date=date(2026, 9, 8),
                        heure_debut=time(8, 30), heure_fin=time(10, 30), salle="B12")
    db.add(sea); db.commit()

    crops = []
    for nom, prenom, code, fname in STUDENTS:
        img = cv2.imread(str(FACES / fname))
        etu = models.Etudiant(nom=nom, prenom=prenom, code=code,
                              email=f"{prenom.lower()}.{nom.lower().replace(' ', '')}@isga.ma",
                              classe_id=cls.id)
        db.add(etu); db.commit()
        for view in augment(img):
            ok, buf = cv2.imencode(".jpg", view)
            emb = face_service.main_face_embedding(buf.tobytes())
            if emb is not None:
                db.add(models.EmpreinteReference(
                    etudiant_id=etu.id, vecteur=emb.astype("float32").tobytes(),
                    dim=int(emb.shape[0])))
        db.commit()
        crop = face_crop(eng, img)
        if crop is not None:
            crops.append(crop)
        print(f"  enrôlé : {prenom} {nom} ({code}) — {len(etu.empreintes)} empreintes")

    build_class_photo(eng, crops)
    n_emp = db.query(models.EmpreinteReference).count()
    print(f"\n{len(STUDENTS)} étudiants, {n_emp} empreintes.")
    print(f"Photo de classe -> {CLASS_PHOTO}")
    db.close()


if __name__ == "__main__":
    main()
