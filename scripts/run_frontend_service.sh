#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
FRONTEND_HOST="0.0.0.0"
FRONTEND_PORT="3000"
NPM_BIN="$(command -v npm || true)"

if [[ -z "$NPM_BIN" ]]; then
  echo "npm 未安装，无法启动前端。" >&2
  exit 1
fi

cd "$PROJECT_ROOT"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  "$NPM_BIN" install --prefix "$FRONTEND_DIR" --no-package-lock
fi

"$NPM_BIN" run build --prefix "$FRONTEND_DIR"
exec "$NPM_BIN" run preview --prefix "$FRONTEND_DIR" -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
