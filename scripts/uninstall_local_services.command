#!/bin/zsh
set -euo pipefail

USER_ID="$(id -u)"
BACKEND_LABEL="com.claw.guitar-platform.backend"
FRONTEND_LABEL="com.claw.guitar-platform.frontend"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

launchctl bootout "gui/${USER_ID}" "$LAUNCH_AGENTS_DIR/${BACKEND_LABEL}.plist" >/dev/null 2>&1 || true
launchctl bootout "gui/${USER_ID}" "$LAUNCH_AGENTS_DIR/${FRONTEND_LABEL}.plist" >/dev/null 2>&1 || true

rm -f \
  "$LAUNCH_AGENTS_DIR/${BACKEND_LABEL}.plist" \
  "$LAUNCH_AGENTS_DIR/${FRONTEND_LABEL}.plist"

osascript -e 'display notification "本地服务已卸载" with title "吉他学习平台"'
echo "卸载完成。"
