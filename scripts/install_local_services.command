#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
USER_ID="$(id -u)"
BACKEND_LABEL="com.claw.guitar-platform.backend"
FRONTEND_LABEL="com.claw.guitar-platform.frontend"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs/GuitarPlatform"

mkdir -p "$LAUNCH_AGENTS_DIR" "$LOG_DIR" \
  "$PROJECT_ROOT/library/courses" \
  "$PROJECT_ROOT/library/collected" \
  "$PROJECT_ROOT/library/songs" \
  "$PROJECT_ROOT/backend/data"

if [[ ! -f "$PROJECT_ROOT/backend/data/index.json" ]]; then
  printf '{\n  "courses": [],\n  "songs": [],\n  "videos": []\n}\n' > "$PROJECT_ROOT/backend/data/index.json"
fi

write_plist() {
  local label="$1"
  local script_path="$2"
  local stdout_path="$3"
  local stderr_path="$4"
  local plist_path="$LAUNCH_AGENTS_DIR/${label}.plist"

  cat > "$plist_path" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${label}</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>${script_path}</string>
  </array>

  <key>WorkingDirectory</key>
  <string>${PROJECT_ROOT}</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>${stdout_path}</string>

  <key>StandardErrorPath</key>
  <string>${stderr_path}</string>
</dict>
</plist>
PLIST
}

write_plist \
  "$BACKEND_LABEL" \
  "$PROJECT_ROOT/scripts/run_backend_service.sh" \
  "$LOG_DIR/backend.log" \
  "$LOG_DIR/backend.error.log"

write_plist \
  "$FRONTEND_LABEL" \
  "$PROJECT_ROOT/scripts/run_frontend_service.sh" \
  "$LOG_DIR/frontend.log" \
  "$LOG_DIR/frontend.error.log"

launchctl bootout "gui/${USER_ID}" "$LAUNCH_AGENTS_DIR/${BACKEND_LABEL}.plist" >/dev/null 2>&1 || true
launchctl bootout "gui/${USER_ID}" "$LAUNCH_AGENTS_DIR/${FRONTEND_LABEL}.plist" >/dev/null 2>&1 || true

launchctl bootstrap "gui/${USER_ID}" "$LAUNCH_AGENTS_DIR/${BACKEND_LABEL}.plist"
launchctl bootstrap "gui/${USER_ID}" "$LAUNCH_AGENTS_DIR/${FRONTEND_LABEL}.plist"

launchctl enable "gui/${USER_ID}/${BACKEND_LABEL}" >/dev/null 2>&1 || true
launchctl enable "gui/${USER_ID}/${FRONTEND_LABEL}" >/dev/null 2>&1 || true

launchctl kickstart -k "gui/${USER_ID}/${BACKEND_LABEL}" >/dev/null 2>&1 || true
launchctl kickstart -k "gui/${USER_ID}/${FRONTEND_LABEL}" >/dev/null 2>&1 || true

osascript -e 'display notification "本地服务已安装并启动" with title "吉他学习平台"'
echo "安装完成。现在可访问: http://127.0.0.1:3000/"
