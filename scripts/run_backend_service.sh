#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/claw/GuitarPlatform_v2"
BACKEND_DIR="$PROJECT_ROOT/backend"
BACKEND_VENV="$BACKEND_DIR/.venv"
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"

cd "$BACKEND_DIR"

if [[ ! -d "$BACKEND_VENV" ]]; then
  /opt/homebrew/bin/python3 -m venv "$BACKEND_VENV"
fi

if [[ ! -x "$BACKEND_VENV/bin/uvicorn" ]]; then
  "$BACKEND_VENV/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

exec "$BACKEND_VENV/bin/uvicorn" main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
