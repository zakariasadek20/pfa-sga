"""Schémas Pydantic (validation des entrées / sorties de l'API)."""

import datetime as dt

from pydantic import BaseModel

_ORM = {"from_attributes": True}


# --- Enseignant ---
class EnseignantCreate(BaseModel):
    nom: str
    email: str | None = None


class EnseignantOut(EnseignantCreate):
    id: int
    model_config = _ORM


# --- Classe ---
class ClasseCreate(BaseModel):
    libelle: str
    filiere: str | None = None
    niveau: str | None = None


class ClasseOut(ClasseCreate):
    id: int
    model_config = _ORM


# --- Module ---
class ModuleCreate(BaseModel):
    libelle: str
    enseignant_id: int | None = None
    classe_id: int | None = None


class ModuleOut(ModuleCreate):
    id: int
    model_config = _ORM


# --- Étudiant ---
class EtudiantCreate(BaseModel):
    nom: str
    prenom: str | None = None
    code: str | None = None
    email: str | None = None
    classe_id: int | None = None


class EtudiantOut(EtudiantCreate):
    id: int
    model_config = _ORM


# --- Séance ---
class SeanceCreate(BaseModel):
    module_id: int
    date: dt.date | None = None
    heure_debut: dt.time | None = None
    heure_fin: dt.time | None = None
    salle: str | None = None


class SeanceOut(SeanceCreate):
    id: int
    model_config = _ORM


# --- Reconnaissance / présence ---
class RecognizedFace(BaseModel):
    etudiant_id: int | None
    nom: str | None
    score: float
    bbox: list[int]


class RecognizeResponse(BaseModel):
    seance_id: int
    faces: list[RecognizedFace]
    present_ids: list[int]


class PresenceIn(BaseModel):
    etudiant_id: int
    statut: str = "present"
    score_confiance: float | None = None
    methode: str = "manuel"


class ConfirmRequest(BaseModel):
    presences: list[PresenceIn]


class PresenceOut(BaseModel):
    id: int
    etudiant_id: int
    statut: str
    horodatage: dt.datetime | None
    score_confiance: float | None
    methode: str
    model_config = _ORM


# --- Rapports ---
class ReportRow(BaseModel):
    etudiant_id: int
    nom: str
    total_seances: int
    presences: int
    taux: float
