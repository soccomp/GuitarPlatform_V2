#!/bin/zsh
set -euo pipefail

USER_ID="$(id -u)"
BACKEND_LABEL="com.claw.guitar-platform.backend"
FRONTEND_LABEL="com.claw.guitar-platform.frontend"
APP_URL="http://127.0.0.1:3000/"

kickstart_service() {
  local label="$1"
  launchctl kickstart -k "gui/${USER_ID}/${label}" >/dev/null 2>&1 || true
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-30}"
  local delay="${3:-0.5}"

  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done
  return 1
}

kickstart_service "$BACKEND_LABEL"
kickstart_service "$FRONTEND_LABEL"

if wait_for_url "$APP_URL"; then
  open "$APP_URL"
else
  osascript -e 'display alert "吉他学习平台暂时未响应" message "后台服务正在唤醒，请稍后再打开 http://127.0.0.1:3000"'
fi
