#!/usr/bin/env bash
# deploy-app.sh — build and run a robohub application as a user service.
# Usage: ./scripts/deploy-app.sh <name> [application-dir]
#
# The first install writes ~/.config/systemd/user/<name>.service and enables
# it. Later runs rebuild and restart the same unit, so the Keeper start/stop
# controls and the shell script act on one service.
set -euo pipefail

export PATH=$HOME/.local/bin:/usr/local/go/bin:$HOME/.rho/bin:$PATH

HERE="$(cd "$(dirname "$0")" && pwd)"
ROBOHUB="$(dirname "$HERE")"
NAME="${1:?application name required}"
APP="${2:-$ROBOHUB/applications/$NAME}"
RHO="${RHO:-$HOME/.rho/bin/rho}"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT="$UNIT_DIR/$NAME.service"

if [[ ! -d "$APP" ]]; then
    echo "Application '$NAME' not found at $APP" >&2
    exit 1
fi
if [[ ! -f "$APP/module.yml" ]]; then
    echo "$APP/module.yml is missing" >&2
    exit 1
fi

META=$(python3 - "$APP/module.yml" "$NAME" <<'PY'
import sys, yaml
path, name = sys.argv[1], sys.argv[2]
with open(path) as fh:
    data = yaml.safe_load(fh) or {}
def pick(*keys):
    for key in keys:
        value = data
        for part in key.split("."):
            value = value.get(part, {}) if isinstance(value, dict) else {}
        if value not in ("", None, {}):
            return value
    return ""
port = pick("application.port", "module.port", "deploy.port")
command = pick("application.command", "module.command") or name
print(f"{port}\t{command}")
PY
)
PORT="${META%%$'\t'*}"
COMMAND="${META#*$'\t'}"

echo "Building $NAME …"
cd "$APP"
# A generated project can outlive the toolchain that wrote it; start from the
# sources so a new template or locale feature is really in the build.
rm -rf "$APP/build/generated"
"$RHO" build . || { echo "BUILD FAILED"; exit 1; }

if [[ -z "$PORT" || -z "$COMMAND" || ! -x "$APP/build/$COMMAND" ]]; then
    echo "$NAME has no serveable application block; no service was installed."
    exit 0
fi

# An application that calls other services was registered as a client by the
# keeper before this ran, which wrote the environment it reads into its
# workspace: its client id, where its secret is (never the secret), the issuer and
# the services it calls.
CLIENT_ENV_FILE="$HOME/.rho/keeper/workspaces/$NAME/auth/client.env"
CLIENT_ENV=""
if [[ -f "$CLIENT_ENV_FILE" ]]; then
    CLIENT_ENV="EnvironmentFile=$CLIENT_ENV_FILE"
fi

echo "Writing $UNIT …"
mkdir -p "$UNIT_DIR"
cat > "$UNIT" <<UNIT
[Unit]
Description=RoboHub $NAME
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP
Environment=HOME=$HOME
Environment=PATH=$PATH
Environment=ROBOHUB_ROOT=$ROBOHUB
Environment=ROBOHUB_WORKSPACE=$(dirname "$ROBOHUB")
Environment=ROBOHUB_APP_WORKSPACE=$HOME/.rho/keeper/workspaces/$NAME
Environment=ROBOHUB_APP_MANIFEST=$APP/module.yml
Environment=RHO_KEEPER_PORT=${RHO_KEEPER_PORT:-19090}
Environment=RHO_HTTP_ADDR=:$PORT
$CLIENT_ENVExecStart=$APP/build/$COMMAND
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT

loginctl enable-linger "$(whoami)" 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable "$NAME" >/dev/null
systemctl --user restart "$NAME"
echo "Done: $NAME is running on port $PORT."
