# AI Class Attendance for Students

Système intelligent de gestion des présences par reconnaissance faciale.
PFA — ISGA, Cycle d'ingénieur 2ᵉ année, 2025–2026.
Équipe : BENDADI Mohamed · SADEK Zakaria · BELHASSAN Amine — Encadrant : M. Adama SAMAKE.

> Documentation projet : `docs/analyse-conception.md` (contexte, conception).
> Rapport : `rapport/rapport-pfa.md`. Diagrammes : `rapport/diagrammes/`.

## Architecture du code

```
face_attendance/          Paquet Python (cœur applicatif)
  config.py               Chemins, nom du modèle, seuil de reconnaissance
  face/
    engine.py             FaceEngine : détection (RetinaFace) + empreinte (ArcFace)
    enrollment.py         Construction / sauvegarde de la base d'empreintes
  cli/
    enroll.py             Enrôlement des étudiants (CLI)
    recognize.py          Reconnaissance sur une photo de classe (CLI)
scripts/
  smoke_test.py           Vérifie que le moteur IA se charge et s'exécute
data/
  enrollment/<étudiant>/  Photos de référence (3–5 par étudiant)  [NON versionné]
  test/                   Photos de classe pour les essais         [NON versionné]
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel setuptools
pip install -r requirements.txt
```

Au premier lancement, InsightFace télécharge automatiquement le modèle `buffalo_l`
(RetinaFace + ArcFace).

## Utilisation (cœur IA)

1. **Vérifier l'installation :**
   ```bash
   python scripts/smoke_test.py                 # chargement du moteur
   python scripts/smoke_test.py data/test/photo.jpg   # + détection sur une image
   ```
2. **Enrôler les étudiants** — placer les photos dans `data/enrollment/Nom_Etudiant/` puis :
   ```bash
   python -m face_attendance.cli.enroll
   ```
3. **Prendre la présence** sur une photo de classe :
   ```bash
   python -m face_attendance.cli.recognize data/test/classe.jpg
   ```

## Données personnelles

Les visages sont des **données biométriques** (loi 09-08 / CNDP). Les photos et la
base d'empreintes ne sont **jamais versionnées** (voir `.gitignore`) et l'enrôlement
suppose le **consentement écrit** des personnes concernées.
