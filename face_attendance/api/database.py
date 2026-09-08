"""Connexion à la base de données et session SQLAlchemy (SQLite)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .. import config

DB_URL = f"sqlite:///{config.DATA_DIR / 'attendance.db'}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dépendance FastAPI : fournit une session et la referme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crée le dossier de données et les tables si nécessaire."""
    from . import models  # noqa: F401  (enregistre les modèles)

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
