#!/bin/sh
# The validator must catch what it is for.
#
# A validator that says everything is fine is a validator nobody can trust, and
# the only way to know it catches something is to show it something broken. So a
# registry with a mistake in it is written out, and the validator is run over it.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/modules"
# An entry that says no role: a registry entry without one says nothing about
# what the module is for.
cat > "$WORK/modules/robohub-avr.yml" <<'ENTRY'
name: robohub-avr
path: ../robohub-avr
git: https://github.com/RoboHubPlatform/robohub-avr
summary: The 8-bit AVR platform.
ENTRY

if "$ROOT/build/robohub" validate "$WORK/modules" >/dev/null 2>&1; then
    echo "the validator accepted an entry with no role" >&2
    exit 1
fi

# And one that names another module: the entry and the file must agree.
cat > "$WORK/modules/robohub-avr.yml" <<'ENTRY'
name: robohub-something-else
role: platform
path: ../robohub-avr
ENTRY

if "$ROOT/build/robohub" validate "$WORK/modules" >/dev/null 2>&1; then
    echo "the validator accepted an entry that names another module" >&2
    exit 1
fi

echo "the validator catches what it is for"
