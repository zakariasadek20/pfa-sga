# AI Class Attendance for Students

**Système intelligent de gestion des présences par reconnaissance faciale.**
Projet de Fin d'Année (PFA) — ISGA, Cycle d'ingénieur 2ᵉ année, 2025–2026.

- **Équipe :** BENDADI Mohamed · SADEK Zakaria · BELHASSAN Amine
- **Encadrant :** M. Adama SAMAKE

---

## Aperçu

L'application identifie les étudiants présents à partir d'une **photo de la classe**,
enregistre les présences et les restitue à l'enseignant via un **tableau de bord**
(statistiques, rapports, exports Excel/PDF) et un **portail étudiant**.

Le cœur repose sur des modèles pré-entraînés de l'état de l'art :
**RetinaFace** (détection des visages) + **ArcFace** (empreinte 512-d), avec un
module **anti-spoofing** (détection du vivant). Principe clé : la reconnaissance
**propose**, l'enseignant **valide**, puis les présences sont **enregistrées**.

---

## Démarrage rapide

> Prérequis : **Python 3.10 ou plus** installé (https://www.python.org/downloads/ —
> sous Windows, cochez « Add Python to PATH »).

### Windows
1. **Installer** (une seule fois) : double-cliquez sur **`install-windows.bat`**
2. **Lancer** : double-cliquez sur **`start-windows.bat`**
   → le navigateur s'ouvre automatiquement sur **http://127.0.0.1:8000**

### macOS / Linux
```bash
./install-mac-linux.sh     # une seule fois
./start-mac-linux.sh       # lance l'application + ouvre http://127.0.0.1:8000
```

Le **premier** lancement télécharge le modèle IA (`buffalo_l`) — patientez une minute.
Pour **arrêter** : fermez la fenêtre du serveur (Windows) ou faites **Ctrl+C** (macOS/Linux).

---

## Structure du projet

```
isga-pfa/
├── README.md                    Ce fichier
├── requirements.txt             Dépendances Python
├── install-windows.bat          ▶ Installer le projet (Windows, une seule fois)
├── start-windows.bat            ▶ Lancer l'application (Windows)
├── install-mac-linux.sh         ▶ Installer le projet (macOS/Linux, une seule fois)
├── start-mac-linux.sh           ▶ Lancer l'application (macOS/Linux)
│
├── face_attendance/             ▶ L'APPLICATION (paquet Python)
│   ├── config.py                Chemins, nom du modèle, seuil de reconnaissance
│   ├── face/                    Moteur IA
│   │   ├── engine.py            Détection (RetinaFace) + empreinte (ArcFace)
│   │   ├── enrollment.py        Calcul et stockage des empreintes de référence
│   │   └── antispoofing.py      Détection du vivant (MiniFASNet)
│   ├── api/                     Backend & interface web
│   │   ├── main.py              Point d'entrée FastAPI
│   │   ├── models.py            Modèle de données (SQLAlchemy)
│   │   ├── database.py          Connexion SQLite
│   │   ├── face_service.py      Pont API ↔ moteur IA
│   │   ├── web.py               Tableau de bord (pages web)
│   │   ├── routers/             Points d'accès REST (étudiants, séances, rapports…)
│   │   └── templates/           Gabarits HTML du tableau de bord
│   └── cli/                     Commandes en ligne (enrôlement, reconnaissance)
│
├── scripts/                     ▶ SCRIPTS (évaluation, tests, démonstration)
│   ├── smoke_test.py            Vérifie le chargement du moteur IA
│   ├── demo_seed.py             Prépare une démo (6 étudiants + photo de classe)
│   ├── evaluate_lfw.py          Évaluation sur le jeu public LFW
│   ├── realtime_attendance.py   Reconnaissance en temps réel (webcam)
│   └── test_api.py / test_dashboard.py   Tests de l'API et du tableau de bord
│
├── docs/                        ▶ ANALYSE & CONCEPTION (document de référence)
│
├── rapport/                     ▶ LIVRABLES
│   ├── rapport-pfa.docx         Rapport (éditable)
│   ├── rapport-pfa.pdf          Rapport (PDF)
│   ├── presentation-pfa.pptx    Présentation de soutenance
│   ├── diagrammes/              Figures et diagrammes
│   └── annexes/                 Formulaire de consentement
│
└── data/                        Données (photos, base) — NON versionné (voir .gitignore)
```

---

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -r requirements.txt
```

> Au premier lancement, InsightFace télécharge automatiquement le pack
> `buffalo_l` (RetinaFace + ArcFace).

---

## Lancer l'application

```bash
python -m uvicorn face_attendance.api.main:app --reload
```

Puis ouvrir **http://127.0.0.1:8000** dans un navigateur.

Pour préparer rapidement une démonstration (6 étudiants + une photo de classe
prête à reconnaître) :

```bash
python scripts/demo_seed.py
```

Puis, dans le tableau de bord : **Prise de présence** → importer
`data/test/classe_demo.jpg` → **Reconnaître** → **Valider les présences**.

---

## Scripts utiles

| Script | Rôle |
|---|---|
| `scripts/smoke_test.py` | Vérifie que le moteur IA se charge et s'exécute |
| `scripts/demo_seed.py` | Prépare une démo (étudiants + photo de classe) |
| `scripts/evaluate_lfw.py` | Évaluation quantitative sur le jeu public LFW |
| `scripts/realtime_attendance.py` | Reconnaissance en temps réel via webcam |
| `scripts/test_api.py`, `scripts/test_dashboard.py` | Tests de l'API et du tableau de bord |

---

## Données personnelles (loi 09-08 / CNDP)

Les visages sont des **données biométriques sensibles**. Les photos, les
empreintes et la base de données ne sont **jamais versionnées** (voir
`.gitignore`), et tout enrôlement suppose le **consentement écrit** des personnes
concernées (formulaire fourni dans `rapport/annexes/`).
