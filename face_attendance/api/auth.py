"""Authentification et gestion des rôles.

Rôles : ``admin`` (gère les étudiants), ``enseignant`` (prise de présence,
rapports), ``etudiant`` (portail personnel). La session est stockée dans un
cookie signé (SessionMiddleware). Les mots de passe sont hachés avec PBKDF2
(bibliothèque standard, aucune dépendance externe).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os

from fastapi import Request
from sqlalchemy.orm import Session

from . import models

ROLES = ("admin", "enseignant", "etudiant")


# ── Mots de passe (PBKDF2-HMAC-SHA256) ──
def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000)
    return "pbkdf2$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, salt_b64, hash_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ── Session / contrôle d'accès ──
class NotAuthenticated(Exception):
    """Aucun utilisateur connecté → redirection vers /login."""


class Forbidden(Exception):
    """Rôle insuffisant → redirection vers l'accueil."""


def current_user(request: Request, db: Session):
    uid = request.session.get("uid")
    return db.get(models.Utilisateur, uid) if uid else None


def require(request: Request, db: Session, roles=None):
    """Renvoie l'utilisateur connecté ; lève une exception sinon."""
    user = current_user(request, db)
    if user is None:
        raise NotAuthenticated()
    if roles and user.role not in roles:
        raise Forbidden()
    return user


# ── Comptes par défaut (créés au premier démarrage) ──
def ensure_default_users(db: Session) -> None:
    if db.query(models.Utilisateur).count() > 0:
        return
    db.add_all([
        models.Utilisateur(nom="Administrateur", email="admin@isga.ma",
                           mot_de_passe_hash=hash_password("admin"), role="admin"),
        models.Utilisateur(nom="Adama SAMAKE", email="prof@isga.ma",
                           mot_de_passe_hash=hash_password("prof"), role="enseignant"),
    ])
    db.commit()


def create_student_login(db: Session, etu) -> None:
    """Crée un compte étudiant (connexion) pour un étudiant enrôlé."""
    email = (etu.email or f"{etu.code or ('etu%d' % etu.id)}@isga.ma").lower()
    if db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first():
        return
    db.add(models.Utilisateur(
        nom=f"{etu.prenom or ''} {etu.nom}".strip(),
        email=email,
        mot_de_passe_hash=hash_password(etu.code or "etudiant"),
        role="etudiant",
        etudiant_id=etu.id,
    ))
    db.commit()
