"""Enrôlement des étudiants.

Place les photos dans ``data/enrollment/<Nom_Etudiant>/`` puis lance :

    python -m face_attendance.cli.enroll
"""

from .. import config
from ..face.engine import FaceEngine
from ..face.enrollment import build_enrollment_db, save_db


def main() -> None:
    engine = FaceEngine(config.MODEL_NAME, config.DET_SIZE)
    db = build_enrollment_db(engine, config.ENROLL_DIR)
    if not db:
        print(
            "Aucun étudiant enrôlé. Ajoutez des photos dans",
            config.ENROLL_DIR,
        )
        return
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_db(db, config.DB_PATH)
    total = sum(embs.shape[0] for embs in db.values())
    print(f"Enrôlement terminé : {len(db)} étudiant(s), {total} empreinte(s).")
    for name, embs in db.items():
        print(f"  - {name} : {embs.shape[0]} photo(s)")
    print("Base sauvegardée :", config.DB_PATH)


if __name__ == "__main__":
    main()
