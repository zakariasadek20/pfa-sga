#!/usr/bin/env bash
# ============================================================
#   AI Class Attendance  -  DEMARRAGE (macOS / Linux)
#   Lance l'application et ouvre http://127.0.0.1:8000
#   Usage :  ./start-mac-linux.sh      (Ctrl+C pour arreter)
# ============================================================
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/activate" ]; then
  echo "[ERREUR] Le projet n'est pas installe. Lancez d'abord : ./install-mac-linux.sh"
  exit 1
fi

source .venv/bin/activate
URL="http://127.0.0.1:8000"

# ouvre le navigateur une fois le serveur pret (en tache de fond)
( sleep 5
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; fi ) &

echo "============================================================"
echo "  Application :  $URL     (Ctrl+C pour arreter)"
echo "============================================================"
python -m uvicorn face_attendance.api.main:app --host 127.0.0.1 --port 8000
