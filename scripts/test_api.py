"""Test de bout en bout de l'API (sans serveur, via TestClient).

Utilise quelques identités du jeu LFW pour simuler des étudiants : on les crée,
on les enrôle, on lance la reconnaissance sur une photo mise de côté, on valide
la présence, puis on consulte le rapport du module.

    python scripts/test_api.py
"""

import glob
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from sklearn.datasets import get_data_home  # noqa: E402

from face_attendance import config  # noqa: E402
from face_attendance.api.database import init_db  # noqa: E402
from face_attendance.api.main import app  # noqa: E402


def pick_people(n=3, min_imgs=4):
    lfw = os.path.join(get_data_home(), "lfw_home", "lfw_funneled")
    people = []
    for name in sorted(os.listdir(lfw)):
        d = os.path.join(lfw, name)
        if not os.path.isdir(d):
            continue
        imgs = sorted(glob.glob(os.path.join(d, "*.jpg")))
        if len(imgs) >= min_imgs:
            people.append((name, imgs))
        if len(people) >= n:
            break
    return people


def main():
    # Base de données neuve
    db_file = config.DATA_DIR / "attendance.db"
    if db_file.exists():
        db_file.unlink()
    init_db()

    client = TestClient(app)
    people = pick_people()
    print(f"{len(people)} identités de test :", [p[0] for p in people])

    classe_id = client.post(
        "/classes", json={"libelle": "4A-IIR", "filiere": "Ingénierie", "niveau": "2CI"}
    ).json()["id"]
    ens_id = client.post(
        "/enseignants", json={"nom": "SAMAKE", "email": "encadrant@isga.ma"}
    ).json()["id"]
    mod_id = client.post(
        "/modules",
        json={"libelle": "Machine Learning", "enseignant_id": ens_id, "classe_id": classe_id},
    ).json()["id"]
    seance_id = client.post(
        "/seances", json={"module_id": mod_id, "salle": "B12"}
    ).json()["id"]

    ids = {}
    for name, imgs in people:
        sid = client.post("/students", json={"nom": name, "classe_id": classe_id}).json()["id"]
        ids[name] = sid
        files = [("files", (os.path.basename(p), open(p, "rb"), "image/jpeg")) for p in imgs[:3]]
        res = client.post(f"/students/{sid}/enroll", files=files).json()
        print(f"  enrôlé {name} (id={sid}) :", res)

    # Reconnaissance sur une photo mise de côté de la 1re personne
    test_name, test_imgs = people[0]
    test_img = test_imgs[3]
    with open(test_img, "rb") as fh:
        rec = client.post(
            f"/seances/{seance_id}/recognize",
            files={"photo": (os.path.basename(test_img), fh, "image/jpeg")},
        ).json()
    print("\nReconnaissance :", rec)
    ok = ids[test_name] in rec.get("present_ids", [])
    print(f"  -> {test_name} (id={ids[test_name]}) reconnu : {'OUI' if ok else 'NON'}")

    # Validation de la présence
    presences = [
        {"etudiant_id": f["etudiant_id"], "statut": "present",
         "score_confiance": f["score"], "methode": "auto"}
        for f in rec["faces"] if f["etudiant_id"]
    ]
    conf = client.post(f"/seances/{seance_id}/attendance", json={"presences": presences}).json()
    print("Présences enregistrées :", len(conf))

    # Rapport du module
    report = client.get(f"/modules/{mod_id}/report").json()
    print("\nRapport du module :")
    for row in report:
        print("  ", row)

    # Exports Excel / PDF
    xlsx = client.get(f"/modules/{mod_id}/report.xlsx")
    pdf = client.get(f"/modules/{mod_id}/report.pdf")
    (config.DATA_DIR / "rapport_demo.xlsx").write_bytes(xlsx.content)
    (config.DATA_DIR / "rapport_demo.pdf").write_bytes(pdf.content)
    print(f"\nExport Excel : {xlsx.status_code}  {xlsx.headers.get('content-type')}  {len(xlsx.content)} o")
    print(f"Export PDF   : {pdf.status_code}  {pdf.headers.get('content-type')}  {len(pdf.content)} o")
    exports_ok = (
        xlsx.status_code == 200 and pdf.status_code == 200
        and len(xlsx.content) > 0 and len(pdf.content) > 0
    )

    # Alertes d'absentéisme (seuil 80 % : les deux étudiants à 0 % sont alertés)
    al = client.get(f"/modules/{mod_id}/alerts?threshold=80").json()
    print(f"\nAlertes (<80%) : {len(al['alertes'])} étudiant(s)")
    for a in al["alertes"]:
        print(f"  - {a['nom']} : {a['taux']}%")
    alerts_ok = len(al["alertes"]) == 2

    print("\nTEST OK" if ok and conf and exports_ok and alerts_ok else "\nTEST INCOMPLET")


if __name__ == "__main__":
    main()
