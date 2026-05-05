#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist/share"
STAGING_DIR="$DIST_DIR/GuitarPlatform_Mac_No_Resources"
ZIP_PATH="$DIST_DIR/GuitarPlatform_Mac_No_Resources.zip"

mkdir -p "$DIST_DIR"
rm -rf "$STAGING_DIR" "$ZIP_PATH"
mkdir -p "$STAGING_DIR"

rsync -a "$PROJECT_ROOT/" "$STAGING_DIR/" \
  --exclude ".git" \
  --exclude ".DS_Store" \
  --exclude "__pycache__" \
  --exclude "*.pyc" \
  --exclude "frontend/node_modules" \
  --exclude "frontend/dist" \
  --exclude "backend/.venv" \
  --exclude "backend/.env" \
  --exclude "library" \
  --exclude "backend/data/index.json" \
  --exclude "backend/data/coach_sessions.json" \
  --exclude "backend/data/coach_recordings" \
  --exclude "coach_node.zip" \
  --exclude "scripts/com.claw.guitar-platform.backend.plist" \
  --exclude "scripts/com.claw.guitar-platform.frontend.plist" \
  --exclude "dist/share"

mkdir -p \
  "$STAGING_DIR/library/courses" \
  "$STAGING_DIR/library/collected" \
  "$STAGING_DIR/library/songs" \
  "$STAGING_DIR/backend/data"

printf '{\n  "courses": [],\n  "songs": [],\n  "videos": []\n}\n' > "$STAGING_DIR/backend/data/index.json"

chmod +x \
  "$STAGING_DIR/scripts/start_guitar_platform.command" \
  "$STAGING_DIR/scripts/control_guitar_platform.command" \
  "$STAGING_DIR/scripts/run_backend_service.sh" \
  "$STAGING_DIR/scripts/run_frontend_service.sh" \
  "$STAGING_DIR/scripts/install_local_services.command" \
  "$STAGING_DIR/scripts/uninstall_local_services.command"

cd "$DIST_DIR"
zip -r "$ZIP_PATH" "GuitarPlatform_Mac_No_Resources" >/dev/null
echo "$ZIP_PATH"
