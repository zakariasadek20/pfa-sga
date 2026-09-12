#!/usr/bin/env bash
# ============================================================
#  Remet la DÉMO à zéro (à lancer entre deux essais en soutenance)
#
#  Supprime : les étudiants, leurs empreintes, les présences et
#             les comptes étudiants.
#  Garde    : le cours (classe / module / séance) et les comptes
#             admin@isga.ma et prof@isga.ma.
#
#  Après avoir lancé ce script, rafraîchis la page du navigateur (F5).
# ============================================================
cd "$(dirname "$0")"

.venv/bin/python - <<'PY'
from face_attendance.api import models
from face_attendance.api.database import SessionLocal, init_db

init_db()
db = SessionLocal()
db.query(models.Presence).delete()
db.query(models.EmpreinteReference).delete()
db.query(models.Etudiant).delete()
db.query(models.Utilisateur).filter(models.Utilisateur.role == "etudiant").delete()
db.commit()
print("Demo remise a zero :",
      db.query(models.Etudiant).count(), "etudiant(s),",
      db.query(models.Presence).count(), "presence(s).")
print("Comptes de connexion restants :",
      [u.email for u in db.query(models.Utilisateur).all()])
db.close()
PY

echo ""
echo "==> Termine. Rafraichis la page du navigateur (F5) pour repartir de zero."
