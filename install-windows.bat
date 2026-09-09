@echo off
REM ============================================================
REM   AI Class Attendance  -  INSTALLATION (Windows)
REM   A lancer UNE SEULE FOIS (double-cliquez sur ce fichier)
REM ============================================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERREUR] Python est introuvable.
  echo Installez Python 3.10 ou plus recent depuis :
  echo     https://www.python.org/downloads/
  echo IMPORTANT : cochez "Add Python to PATH" pendant l'installation.
  echo.
  pause
  exit /b 1
)

echo.
echo [1/2] Creation de l'environnement virtuel (.venv)...
python -m venv .venv
call .venv\Scripts\activate.bat

echo.
echo [2/2] Installation des dependances (quelques minutes)...
python -m pip install --upgrade pip wheel
pip install -r requirements.txt

echo.
echo ============================================================
echo   Installation terminee !
echo   Lancez maintenant :  start-windows.bat
echo ============================================================
pause
