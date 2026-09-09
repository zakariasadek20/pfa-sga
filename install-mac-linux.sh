#!/usr/bin/env bash
# ============================================================
#   AI Class Attendance  -  INSTALLATION (macOS / Linux)
#   A lancer UNE SEULE FOIS :  ./install-mac-linux.sh
# ============================================================
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERREUR] Python 3 introuvable. Installez Python 3.10+ puis relancez."
  exit 1
fi

echo "[1/2] Creation de l'environnement virtuel (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

echo "[2/2] Installation des dependances (quelques minutes)..."
python -m pip install --upgrade pip wheel
pip install -r requirements.txt

echo ""
echo "============================================================"
echo "  Installation terminee !"
echo "  Lancez maintenant :  ./start-mac-linux.sh"
echo "============================================================"
