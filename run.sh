#!/usr/bin/env bash
# One-command bootstrap for the SGTech Member Community Assistant.
# Creates a virtualenv, installs Flask, and starts the web app.
#
#   bash run.sh            # start on http://localhost:5000
#   PORT=8080 bash run.sh  # start on a different port
#   DEBUG=1 bash run.sh    # dev mode with auto-reload
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "Creating virtualenv (.venv)..."
  python3 -m venv .venv
fi

echo "Installing dependencies..."
./.venv/bin/python -m pip install -q --upgrade pip
./.venv/bin/python -m pip install -q -r requirements.txt

echo "Starting server..."
exec ./.venv/bin/python app.py
