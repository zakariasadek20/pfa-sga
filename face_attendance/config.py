"""Configuration centrale du projet : chemins, modèle et seuil de reconnaissance."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ENROLL_DIR = DATA_DIR / "enrollment"
TEST_DIR = DATA_DIR / "test"
DB_PATH = DATA_DIR / "enrollment_db.npz"

# Modèle InsightFace : détection RetinaFace + empreinte ArcFace (512-d).
MODEL_NAME = "buffalo_l"
DET_SIZE = 640

# Seuil de similarité cosinus au-dessus duquel une identité est retenue.
# Valeur de départ — à calibrer lors de l'évaluation (étape 7).
MATCH_THRESHOLD = 0.35

# Anti-spoofing (détection du vivant) — MiniFASNet-V2 ONNX.
# Si le fichier du modèle est absent, la détection du vivant est désactivée.
ANTISPOOF_MODEL_PATH = DATA_DIR / "models" / "minifasnet_v2.onnx"
ANTISPOOF_SCALE = 2.7
ANTISPOOF_THRESHOLD = 0.5
