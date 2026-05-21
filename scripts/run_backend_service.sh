#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
BACKEND_VENV="$BACKEND_DIR/.venv"
BACKEND_HOST="0.0.0.0"
BACKEND_PORT="8000"
PYTHON_BIN=""

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x /opt/homebrew/opt/python@3.14/bin/python3.14 ]]; then
    PYTHON_BIN="/opt/homebrew/opt/python@3.14/bin/python3.14"
  elif [[ -x /opt/homebrew/bin/python3 ]]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif [[ -x /usr/local/bin/python3 ]]; then
    PYTHON_BIN="/usr/local/bin/python3"
  else
    echo "python3 未安装，无法启动后端。" >&2
    exit 1
  fi
fi

cd "$BACKEND_DIR"

if [[ ! -d "$BACKEND_VENV" ]]; then
  "$PYTHON_BIN" -m venv "$BACKEND_VENV"
fi

if [[ ! -x "$BACKEND_VENV/bin/uvicorn" ]]; then
  "$BACKEND_VENV/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

exec "$BACKEND_VENV/bin/uvicorn" main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
