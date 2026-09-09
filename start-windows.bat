@echo off
REM ============================================================
REM   AI Class Attendance  -  DEMARRAGE (Windows)
REM   Double-cliquez pour lancer l'application et ouvrir le
REM   navigateur sur http://127.0.0.1:8000
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
  echo.
  echo [ERREUR] Le projet n'est pas encore installe.
  echo Lancez d'abord :  install-windows.bat
  echo.
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat

echo Demarrage du serveur (premier lancement : telechargement du modele IA)...
start "AI Class Attendance - serveur" cmd /k python -m uvicorn face_attendance.api.main:app --host 127.0.0.1 --port 8000

echo Ouverture du navigateur dans quelques secondes...
timeout /t 6 /nobreak >nul
start "" http://127.0.0.1:8000

echo.
echo ============================================================
echo   Application ouverte :  http://127.0.0.1:8000
echo   Pour ARRETER : fermez la fenetre "AI Class Attendance - serveur".
echo ============================================================
