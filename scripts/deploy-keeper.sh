#!/usr/bin/env bash
# deploy-keeper.sh — the keeper lives in its own repository, robohub-keeper, and
# deploys itself from there. This forwards to it, so a machine that runs this
# script from habit still gets the keeper beside this orchestrator.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROBOHUB="$(dirname "$HERE")"
KEEPER="${ROBOHUB_KEEPER:-$(dirname "$ROBOHUB")/robohub-keeper}"
if [ ! -x "$KEEPER/scripts/deploy-keeper.sh" ]; then
    echo "deploy-keeper: the keeper is not at $KEEPER" >&2
    echo "  git clone https://github.com/RoboHubPlatform/robohub-keeper \"$KEEPER\"" >&2
    echo "  or set ROBOHUB_KEEPER to where it is." >&2
    exit 1
fi
ROBOHUB_ROOT="$ROBOHUB" exec "$KEEPER/scripts/deploy-keeper.sh" "$@"
