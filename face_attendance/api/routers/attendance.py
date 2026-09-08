"""Routes de prise de présence : reconnaissance, validation, consultation."""

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ... import config
from .. import face_service, models, schemas
from ..database import get_db

router = APIRouter(prefix="/seances/{seance_id}", tags=["présence"])


def _nom(etu) -> str:
    return f"{etu.prenom or ''} {etu.nom}".strip()


@router.post("/recognize", response_model=schemas.RecognizeResponse)
def recognize(
    seance_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Reconnaît les étudiants sur une photo. Propose une liste, sans l'enregistrer."""
    if not db.get(models.Seance, seance_id):
        raise HTTPException(404, "Séance introuvable")

    enroll_map = face_service.build_enroll_map(db)
    raw = face_service.recognize(photo.file.read(), enroll_map, config.MATCH_THRESHOLD)

    faces, present_ids = [], []
    for r in raw:
        sid = r["etudiant_id"]
        nom = None
        if sid is not None:
            etu = db.get(models.Etudiant, sid)
            nom = _nom(etu) if etu else None
            present_ids.append(sid)
        faces.append(
            schemas.RecognizedFace(
                etudiant_id=sid, nom=nom, score=r["score"], bbox=r["bbox"]
            )
        )
    return schemas.RecognizeResponse(
        seance_id=seance_id, faces=faces, present_ids=sorted(set(present_ids))
    )


@router.post("/attendance", response_model=list[schemas.PresenceOut])
def confirm_attendance(
    seance_id: int,
    payload: schemas.ConfirmRequest,
    db: Session = Depends(get_db),
):
    """Enregistre les présences validées par l'enseignant (remplace l'existant)."""
    if not db.get(models.Seance, seance_id):
        raise HTTPException(404, "Séance introuvable")

    db.query(models.Presence).filter(
        models.Presence.seance_id == seance_id
    ).delete()

    saved = []
    for p in payload.presences:
        rec = models.Presence(
            seance_id=seance_id,
            etudiant_id=p.etudiant_id,
            statut=p.statut,
            horodatage=datetime.now(),
            score_confiance=p.score_confiance,
            methode=p.methode,
        )
        db.add(rec)
        saved.append(rec)
    db.commit()
    for rec in saved:
        db.refresh(rec)
    return saved


@router.get("/attendance", response_model=list[schemas.PresenceOut])
def list_attendance(seance_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Presence)
        .filter(models.Presence.seance_id == seance_id)
        .all()
    )
