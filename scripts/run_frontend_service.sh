#!/bin/zsh
set -euo pipefail

PROJECT_ROOT="/Users/claw/GuitarPlatform_v2"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
FRONTEND_HOST="127.0.0.1"
FRONTEND_PORT="3000"

cd "$PROJECT_ROOT"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  npm install --prefix "$FRONTEND_DIR" --no-package-lock
fi

npm run build --prefix "$FRONTEND_DIR"
exec npm run preview --prefix "$FRONTEND_DIR" -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
