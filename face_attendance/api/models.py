"""Modèle de données (entités ORM), reflet du diagramme de classes."""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from .database import Base


class Enseignant(Base):
    __tablename__ = "enseignants"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True)
    modules = relationship("Module", back_populates="enseignant")


class Classe(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    libelle = Column(String, nullable=False)
    filiere = Column(String)
    niveau = Column(String)
    etudiants = relationship("Etudiant", back_populates="classe")
    modules = relationship("Module", back_populates="classe")


class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True)
    libelle = Column(String, nullable=False)
    enseignant_id = Column(Integer, ForeignKey("enseignants.id"))
    classe_id = Column(Integer, ForeignKey("classes.id"))
    enseignant = relationship("Enseignant", back_populates="modules")
    classe = relationship("Classe", back_populates="modules")
    seances = relationship("Seance", back_populates="module")


class Etudiant(Base):
    __tablename__ = "etudiants"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    prenom = Column(String)
    code = Column(String, unique=True)  # CNE / code Apogée
    email = Column(String)
    classe_id = Column(Integer, ForeignKey("classes.id"))
    classe = relationship("Classe", back_populates="etudiants")
    empreintes = relationship(
        "EmpreinteReference", back_populates="etudiant",
        cascade="all, delete-orphan",
    )
    presences = relationship("Presence", back_populates="etudiant")


class EmpreinteReference(Base):
    __tablename__ = "empreintes"
    id = Column(Integer, primary_key=True)
    etudiant_id = Column(Integer, ForeignKey("etudiants.id"))
    vecteur = Column(LargeBinary, nullable=False)  # float32 (512-d) sérialisé
    dim = Column(Integer, default=512)
    etudiant = relationship("Etudiant", back_populates="empreintes")


class Seance(Base):
    __tablename__ = "seances"
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    date = Column(Date)
    heure_debut = Column(Time)
    heure_fin = Column(Time)
    salle = Column(String)
    module = relationship("Module", back_populates="seances")
    presences = relationship("Presence", back_populates="seance")


class Presence(Base):
    __tablename__ = "presences"
    id = Column(Integer, primary_key=True)
    seance_id = Column(Integer, ForeignKey("seances.id"))
    etudiant_id = Column(Integer, ForeignKey("etudiants.id"))
    statut = Column(String, default="present")  # present / absent / retard
    horodatage = Column(DateTime)
    score_confiance = Column(Float)
    methode = Column(String, default="auto")  # auto / manuel
    seance = relationship("Seance", back_populates="presences")
    etudiant = relationship("Etudiant", back_populates="presences")


class Utilisateur(Base):
    """Compte de connexion. Rôle : admin / enseignant / etudiant."""

    __tablename__ = "utilisateurs"
    id = Column(Integer, primary_key=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)   # identifiant de connexion
    mot_de_passe_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="etudiant")
    etudiant_id = Column(Integer, ForeignKey("etudiants.id"), nullable=True)
    etudiant = relationship("Etudiant")
