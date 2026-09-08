"""Alertes d'absentéisme : repérage des étudiants sous un seuil et envoi d'emails.

L'envoi n'a lieu que si un serveur SMTP est configuré via les variables
d'environnement (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM).
Sans configuration, la fonction reste en « simulation » et n'envoie rien — ce qui
permet de prévisualiser les alertes en toute sécurité.
"""

import os
import smtplib
from email.message import EmailMessage

from . import models, reporting

DEFAULT_THRESHOLD = 50.0


def build_absence_alerts(db, module, threshold: float = DEFAULT_THRESHOLD) -> list:
    """Construit la liste des alertes pour les étudiants sous le seuil de présence."""
    alerts = []
    for r in reporting.module_report_rows(db, module):
        if r["taux"] < threshold:
            etu = db.get(models.Etudiant, r["etudiant_id"])
            message = (
                f"Bonjour {r['nom']},\n\n"
                f"Votre taux de présence dans le module « {module.libelle} » est "
                f"actuellement de {r['taux']} % ({r['presences']}/{r['total']} séances), "
                f"en dessous du seuil de {threshold:.0f} %. Nous vous invitons à "
                f"régulariser votre assiduité.\n\n"
                f"Cordialement,\nService de scolarité — ISGA"
            )
            alerts.append(
                {
                    "etudiant_id": r["etudiant_id"],
                    "nom": r["nom"],
                    "email": etu.email if etu else None,
                    "taux": r["taux"],
                    "message": message,
                }
            )
    return alerts


def send_alerts(alerts: list) -> dict:
    """Envoie les alertes par email si SMTP est configuré ; sinon simulation."""
    host = os.environ.get("SMTP_HOST")
    if not host:
        return {
            "mode": "simulation",
            "envoyes": 0,
            "note": "SMTP non configuré — aucun email envoyé.",
        }

    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", user or "no-reply@isga.ma")

    sent = 0
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        if user:
            server.login(user, password)
        for a in alerts:
            if not a["email"]:
                continue
            msg = EmailMessage()
            msg["Subject"] = "Alerte d'assiduité"
            msg["From"] = sender
            msg["To"] = a["email"]
            msg.set_content(a["message"])
            server.send_message(msg)
            sent += 1
    return {"mode": "smtp", "envoyes": sent}
