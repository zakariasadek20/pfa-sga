"""Démonstration bout-en-bout dans un vrai navigateur, base vidée (« depuis 0 »).

Vide la base, prépare le cours (enseignant / classe / module / séance), lance le
serveur FastAPI, puis pilote l'application dans Chromium : ajout des étudiants,
enrôlement des visages, prise de présence sur une photo de classe, validation,
tableau de bord, rapports et portail. Une capture est prise à chaque étape et la
session est enregistrée en vidéo.

    python scripts/e2e_demo.py <dossier_sortie>
"""
import subprocess
import sys
import time
from datetime import date, time as dtime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright     # noqa: E402
from face_attendance import config                  # noqa: E402
from face_attendance.api import models              # noqa: E402
from face_attendance.api.database import SessionLocal, init_db  # noqa: E402
from demo_seed import STUDENTS                       # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FACES = config.DATA_DIR / "demo_faces"
CLASS_PHOTO = config.DATA_DIR / "test" / "classe_demo.jpg"
BASE = "http://127.0.0.1:8011"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/e2e")
OUT.mkdir(parents=True, exist_ok=True)
VID = OUT / "video"


def seed_course():
    init_db()
    db = SessionLocal()
    for M in (models.Presence, models.EmpreinteReference, models.Etudiant,
              models.Seance, models.Module, models.Classe, models.Enseignant):
        db.query(M).delete()
    db.commit()
    ens = models.Enseignant(nom="Adama SAMAKE", email="a.samake@isga.ma")
    cls = models.Classe(libelle="2A Cycle Ingénieur", filiere="Génie Informatique",
                        niveau="2ᵉ année")
    db.add_all([ens, cls]); db.commit()
    mod = models.Module(libelle="Intelligence Artificielle",
                        enseignant_id=ens.id, classe_id=cls.id)
    db.add(mod); db.commit()
    sea = models.Seance(module_id=mod.id, date=date(2026, 9, 8),
                        heure_debut=dtime(8, 30), heure_fin=dtime(10, 30), salle="B12")
    db.add(sea); db.commit()
    ids = (cls.id, mod.id)
    db.close()
    return ids


def wait_server():
    for _ in range(60):
        try:
            if httpx.get(f"{BASE}/health", timeout=2).status_code == 200:
                return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    # anti-spoofing désactivé pour la démo (photos ≠ personne réelle devant la caméra)
    model = config.ANTISPOOF_MODEL_PATH
    bak = model.with_suffix(".onnx.bak")
    if model.exists():
        model.rename(bak)

    cls_id, mod_id = seed_course()
    srv = subprocess.Popen(
        [str(REPO / ".venv/bin/python"), "-m", "uvicorn",
         "face_attendance.api.main:app", "--port", "8011", "--log-level", "warning"],
        cwd=str(REPO),
    )
    shots = []

    def shot(page, name, full=False):
        page.wait_for_timeout(500)
        p = OUT / f"{len(shots)+1:02d}-{name}.png"
        page.screenshot(path=str(p), full_page=full)
        shots.append(p)
        print("  capture:", p.name)

    try:
        if not wait_server():
            print("serveur non démarré"); return
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1280, "height": 860},
                                 device_scale_factor=2,
                                 record_video_dir=str(VID),
                                 record_video_size={"width": 1280, "height": 860})
            pg = ctx.new_page()
            pg.set_default_timeout(60000)

            pg.goto(f"{BASE}/"); shot(pg, "tableau-de-bord-vide")
            pg.goto(f"{BASE}/ui/students"); shot(pg, "liste-etudiants-vide")

            # ── ajout des 6 étudiants via le formulaire ──
            for i, (nom, prenom, code, _f) in enumerate(STUDENTS):
                pg.goto(f"{BASE}/ui/students")
                pg.fill("input[name=nom]", nom)
                pg.fill("input[name=prenom]", prenom)
                pg.fill("input[name=code]", code)
                pg.select_option("select[name=classe_id]", value=str(cls_id))
                if i == 0:
                    shot(pg, "ajout-etudiant-formulaire")
                pg.click("button:has-text('Ajouter')")
                pg.wait_for_load_state("networkidle")
            shot(pg, "liste-6-etudiants-non-enroles")

            # ── enrôlement (upload d'une photo par étudiant) ──
            studs = httpx.get(f"{BASE}/students", timeout=10).json()
            for j, s in enumerate(studs):
                photo = FACES / dict((f"{p} {n}", f) for n, p, c, f in STUDENTS)[
                    f"{s['prenom']} {s['nom']}"]
                pg.goto(f"{BASE}/ui/students/{s['id']}/enroll")
                pg.set_input_files("input[name=files]", str(photo))
                if j == 0:
                    shot(pg, "enrolement-photo-choisie")
                pg.click("button:has-text('Enregistrer')")
                pg.wait_for_load_state("networkidle")
            pg.goto(f"{BASE}/ui/students"); shot(pg, "liste-6-etudiants-enroles")

            # ── prise de présence sur la photo de classe ──
            pg.goto(f"{BASE}/ui/attendance")
            pg.select_option("select[name=seance_id]", index=0)
            pg.set_input_files("input[name=photo]", str(CLASS_PHOTO))
            shot(pg, "prise-de-presence-photo-choisie")
            pg.click("button:has-text('Reconnaître')")
            pg.wait_for_selector("img.result")
            shot(pg, "resultat-reconnaissance", full=True)

            # ── validation ──
            pg.click("button:has-text('Valider les présences')")
            pg.wait_for_load_state("networkidle")
            shot(pg, "tableau-de-bord-rempli")

            # ── rapports & portail ──
            pg.goto(f"{BASE}/ui/reports?module_id={mod_id}")
            shot(pg, "rapport-assiduite", full=True)
            pg.goto(f"{BASE}/ui/portail?student_id={studs[0]['id']}")
            shot(pg, "portail-etudiant", full=True)

            ctx.close()   # écrit la vidéo
            br.close()
        print(f"\n{len(shots)} captures dans {OUT}")
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=5)
        except Exception:
            srv.kill()
        if bak.exists():
            bak.rename(model)   # restaure l'anti-spoofing
        print("serveur arrêté, anti-spoofing restauré")


if __name__ == "__main__":
    main()
