#!/bin/zsh
set -euo pipefail

USER_ID="$(id -u)"
BACKEND_LABEL="com.claw.guitar-platform.backend"
FRONTEND_LABEL="com.claw.guitar-platform.frontend"
APP_URL="http://127.0.0.1:3000/"

choose_action() {
  osascript <<'APPLESCRIPT'
    set actionChoice to button returned of (display dialog "吉他学习平台服务控制" message "请选择要执行的操作" buttons {"停止服务", "重启服务", "取消"} default button "重启服务" cancel button "取消")
    return actionChoice
APPLESCRIPT
}

restart_services() {
  launchctl kickstart -k "gui/${USER_ID}/${BACKEND_LABEL}"
  launchctl kickstart -k "gui/${USER_ID}/${FRONTEND_LABEL}"
  open "$APP_URL"
  osascript -e 'display notification "前后端服务已重启" with title "吉他学习平台"'
}

stop_services() {
  launchctl bootout "gui/${USER_ID}" "/Users/claw/Library/LaunchAgents/${BACKEND_LABEL}.plist" >/dev/null 2>&1 || true
  launchctl bootout "gui/${USER_ID}" "/Users/claw/Library/LaunchAgents/${FRONTEND_LABEL}.plist" >/dev/null 2>&1 || true
  osascript -e 'display notification "前后端服务已停止" with title "吉他学习平台"'
}

ACTION="$(choose_action)"

case "$ACTION" in
  "重启服务")
    restart_services
    ;;
  "停止服务")
    stop_services
    ;;
esac
