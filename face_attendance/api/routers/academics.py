"""Routes des entités académiques : enseignants, classes, modules, séances."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(tags=["académique"])


@router.post("/enseignants", response_model=schemas.EnseignantOut)
def create_enseignant(payload: schemas.EnseignantCreate, db: Session = Depends(get_db)):
    obj = models.Enseignant(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/enseignants", response_model=list[schemas.EnseignantOut])
def list_enseignants(db: Session = Depends(get_db)):
    return db.query(models.Enseignant).all()


@router.post("/classes", response_model=schemas.ClasseOut)
def create_classe(payload: schemas.ClasseCreate, db: Session = Depends(get_db)):
    obj = models.Classe(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/classes", response_model=list[schemas.ClasseOut])
def list_classes(db: Session = Depends(get_db)):
    return db.query(models.Classe).all()


@router.post("/modules", response_model=schemas.ModuleOut)
def create_module(payload: schemas.ModuleCreate, db: Session = Depends(get_db)):
    obj = models.Module(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/modules", response_model=list[schemas.ModuleOut])
def list_modules(db: Session = Depends(get_db)):
    return db.query(models.Module).all()


@router.post("/seances", response_model=schemas.SeanceOut)
def create_seance(payload: schemas.SeanceCreate, db: Session = Depends(get_db)):
    obj = models.Seance(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/seances", response_model=list[schemas.SeanceOut])
def list_seances(db: Session = Depends(get_db)):
    return db.query(models.Seance).all()
