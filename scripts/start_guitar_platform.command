#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/claw/GuitarPlatform_v2"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_VENV="$BACKEND_DIR/.venv"
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
FRONTEND_HOST="127.0.0.1"
FRONTEND_PORT="3000"
APP_URL="http://$FRONTEND_HOST:$FRONTEND_PORT"

ensure_backend_deps() {
  if [[ ! -d "$BACKEND_VENV" ]]; then
    python3 -m venv "$BACKEND_VENV"
  fi

  if [[ ! -x "$BACKEND_VENV/bin/uvicorn" ]]; then
    "$BACKEND_VENV/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
  fi
}

ensure_frontend_deps() {
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    npm install --prefix "$FRONTEND_DIR" --no-package-lock
  fi
}

port_busy() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

open_terminal_window() {
  local title="$1"
  local command="$2"
  osascript <<APPLESCRIPT
    tell application "Terminal"
      activate
      do script "printf '\\\\e]1;$title\\\\a'; $command"
    end tell
APPLESCRIPT
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-40}"
  local delay="${3:-0.5}"

  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

ensure_backend_deps
ensure_frontend_deps

if ! port_busy "$BACKEND_PORT"; then
  open_terminal_window \
    "GuitarPlatform Backend" \
    "cd '$BACKEND_DIR' && source '$BACKEND_VENV/bin/activate' && uvicorn main:app --reload --host $BACKEND_HOST --port $BACKEND_PORT"
fi

if ! port_busy "$FRONTEND_PORT"; then
  open_terminal_window \
    "GuitarPlatform Frontend" \
    "cd '$PROJECT_ROOT' && npm run dev --prefix frontend -- --host $FRONTEND_HOST --port $FRONTEND_PORT"
fi

if wait_for_url "$APP_URL"; then
  open "$APP_URL"
else
  osascript -e 'display alert "吉他学习平台启动中" message "服务还没有完全启动，请稍后手动打开 http://127.0.0.1:3000"'
fi
