"""Routes des étudiants et de leur enrôlement."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import face_service, models, schemas
from ..database import get_db

router = APIRouter(prefix="/students", tags=["étudiants"])


@router.post("", response_model=schemas.EtudiantOut)
def create_student(payload: schemas.EtudiantCreate, db: Session = Depends(get_db)):
    etu = models.Etudiant(**payload.model_dump())
    db.add(etu)
    db.commit()
    db.refresh(etu)
    return etu


@router.get("", response_model=list[schemas.EtudiantOut])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Etudiant).all()


@router.get("/{student_id}", response_model=schemas.EtudiantOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    etu = db.get(models.Etudiant, student_id)
    if not etu:
        raise HTTPException(404, "Étudiant introuvable")
    return etu


@router.post("/{student_id}/enroll")
def enroll_student(
    student_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Calcule et enregistre les empreintes de référence à partir de photos."""
    etu = db.get(models.Etudiant, student_id)
    if not etu:
        raise HTTPException(404, "Étudiant introuvable")
    added, skipped = 0, 0
    for f in files:
        emb = face_service.main_face_embedding(f.file.read())
        if emb is None:
            skipped += 1
            continue
        db.add(
            models.EmpreinteReference(
                etudiant_id=student_id,
                vecteur=emb.astype("float32").tobytes(),
                dim=int(emb.shape[0]),
            )
        )
        added += 1
    db.commit()
    return {
        "etudiant_id": student_id,
        "empreintes_ajoutees": added,
        "photos_sans_visage": skipped,
    }
