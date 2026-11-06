#!/usr/bin/env bash
# deploy-app.sh — build and restart a robohub application managed by the keeper
# Usage: ./scripts/deploy-app.sh mesh
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROBOHUB="$(dirname "$HERE")"
NAME="${1:?application name required}"
APP="$ROBOHUB/applications/$NAME"
RHO="${RHO:-$HOME/.rho/bin/rho}"
UNIT="$HOME/.config/systemd/user/$NAME.service"

if [[ ! -d "$APP" ]]; then
    echo "Application '$NAME' not found under $ROBOHUB/applications" >&2
    exit 1
fi

echo "Building $NAME …"
cd "$APP"
"$RHO" build . || { echo "BUILD FAILED"; exit 1; }

echo "Restarting $NAME …"
systemctl --user restart "$NAME" 2>/dev/null || {
    echo "No systemd unit $NAME.service — start it from the keeper Applications page."
    exit 0
}
echo "Done: $NAME is restarting."
