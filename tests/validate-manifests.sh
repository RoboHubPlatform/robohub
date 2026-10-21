#!/bin/sh
# Every manifest of the ecosystem, checked against the toolchain's own schema.
#
# The toolchain is the authority on what a manifest may say: a manifest that
# does not match is not read, and a board whose manifest is not read is a board
# that does not exist — a build that asks for it is told that no such target is
# there, which says nothing about why.
#
# So every module and every board of one is validated. A module's own boards
# live in its `boards` folder, each with a manifest of its own.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")

for module in "$ROOT"/../robohub-*/; do
    name=$(basename "$module")
    if [ -f "$module/module.yml" ]; then
        rho module validate "$module" >/dev/null || {
            echo "$name: its manifest does not match the schema" >&2
            exit 1
        }
    fi
    for board in "$module"boards/*/; do
        if [ -f "$board/module.yml" ]; then
            rho module validate "$board" >/dev/null || {
                echo "$name: the board $(basename "$board") does not match the schema" >&2
                exit 1
            }
        fi
    done
done

echo "every manifest matches the toolchain's schema"
