@echo off
REM One-command bootstrap for Windows (double-click or run in cmd/PowerShell).
REM Creates a virtualenv, installs Flask, and starts the web app.
REM   run.bat            -> start on http://localhost:5000
REM   set PORT=8080 && run.bat   -> start on a different port

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtualenv (.venv)...
  python -m venv .venv
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo Starting server on http://localhost:%PORT%5000 ...
".venv\Scripts\python.exe" app.py
