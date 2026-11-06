#!/usr/bin/env bash
# deploy-keeper.sh  —  build robohub-keeper and install it as a user service
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROBOHUB="$(dirname "$HERE")"
KEEPER="$ROBOHUB/applications/keeper"
KEEPER_PORT=$(python3 -c "import yaml,sys; print(yaml.safe_load(open('$KEEPER/module.yml'))['deploy']['port'])")
SERVICE_NAME="robohub-keeper"
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_FILE="$SERVICE_DIR/$SERVICE_NAME.service"
DEPLOY_LOG="$HOME/.rho/keeper/deploy.log"
RHO="${RHO:-$HOME/.rho/bin/rho}"

mkdir -p "$(dirname "$DEPLOY_LOG")"

# If the service already exists, just report and exit.
if systemctl --user is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
    echo "[$(date)] $SERVICE_NAME is already deployed."
    echo "  Status: $(systemctl --user is-active "$SERVICE_NAME" 2>/dev/null || echo 'inactive')"
    echo "  Use 'systemctl --user restart $SERVICE_NAME' to restart."
    exit 0
fi

echo "[$(date)] Building keeper …" | tee -a "$DEPLOY_LOG"
cd "$KEEPER"
"$RHO" build . >> "$DEPLOY_LOG" 2>&1 || {
    echo "BUILD FAILED"; exit 1
}

echo "[$(date)] Writing systemd unit …" | tee -a "$DEPLOY_LOG"
mkdir -p "$SERVICE_DIR"
cat > "$SERVICE_FILE" <<UNIT
[Unit]
Description=RoboHub Keeper – web dashboard and application manager
After=network-online.target

[Service]
ExecStart=$KEEPER/build/keeper
Restart=on-failure
RestartSec=3
WorkingDirectory=$ROBOHUB
Environment=HOME=$HOME
Environment=ROBOHUB_WORKSPACE=$ROBOHUB
Environment=RHO_HTTP_ADDR=:$KEEPER_PORT

[Install]
WantedBy=default.target
UNIT

loginctl enable-linger "$(whoami)" 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME" >> "$DEPLOY_LOG" 2>&1 || {
    echo "SERVICE START FAILED (user service may need user lingering)"; exit 1
}

echo "[$(date)] Keeper is running on http://127.0.0.1:$KEEPER_PORT" | tee -a "$DEPLOY_LOG"