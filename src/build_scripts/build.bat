@echo off
REM -------- Build OsciFootswitch --------
REM 1. Version generieren
python generate_version.py
if ERRORLEVEL 1 (
    echo Fehler beim Generieren von version.txt
    pause
    exit /b 1
)

REM 2. PyInstaller Build
pyinstaller OsciFootswitch.spec
if ERRORLEVEL 1 (
    echo PyInstaller Build fehlgeschlagen
    pause
    exit /b 1
)

echo Build abgeschlossen! Ergebnisse in ../dist/OsciFootswitch
pause