#!/bin/sh
# The host-test runner every module of the RoboHub ecosystem uses.
#
# A module's host tests are ordinary portable C, built against the interfaces
# in robohub-common and run on the machine doing the building. The build is the
# same for every module — the same compiler, the same warnings, the same
# include paths, the same generated namespace — and only the module's own
# sources differ.
#
# That part is here, once, because two repositories carried a copy of it and
# had already begun to differ. The part that is the module's own — which
# headers it publishes into the generated namespace, which suites it builds
# and runs — is in the module, in `tests/host-tests.plan`, which this sources.
#
# The sibling checkouts are named by the environment, because a path into
# another repository belongs to the machine and not to this one:
#
#     ROBOHUB_COMMON_DIR=/path/to/robohub-common \
#     ROBOHUB_ORCHESTRATOR_DIR=/path/to/robohub \
#         tests/run.sh
#
# SPDX-License-Identifier: MIT
set -eu

: "${ROBOHUB_COMMON_DIR:?set ROBOHUB_COMMON_DIR to the robohub-common checkout}"

HERE=$(cd "$(dirname "$0")" && pwd)
MODULE_ROOT=${1:?name the module whose host tests are to be run}
MODULE_NAME=$(basename "$MODULE_ROOT")

OUT="${TMPDIR:-/tmp}/robohub-${MODULE_NAME}-tests"
mkdir -p "$OUT"

# The generated namespace a build produces for cross-module includes
# (robohub/protocols/*, robohub/drivers/*). A build makes these copies; the
# test does the same so the sources compile as they are written.
GEN="$OUT/include"
mkdir -p "$GEN"

CC=${CC:-cc}

# The include paths every module in the ecosystem compiles against: the
# interfaces, the HAL, the drivers and the devices.
BASE="-I$ROBOHUB_COMMON_DIR/include -I$ROBOHUB_COMMON_DIR/include/robohub \
      -I$ROBOHUB_COMMON_DIR/include/robohub/hal -I$ROBOHUB_COMMON_DIR/include/robohub/drivers \
      -I$ROBOHUB_COMMON_DIR/include/robohub/devices"

export CC BASE GEN OUT MODULE_ROOT MODULE_NAME

run() { printf '\n== %s ==\n' "$1"; shift; "$@"; }

# The module's own plan: what it publishes, what it builds and what it runs.
PLAN="$MODULE_ROOT/tests/host-tests.plan"
if [ ! -f "$PLAN" ]; then
    printf 'no host-test plan at %s\n' "$PLAN" >&2
    exit 1
fi
. "$PLAN"

printf '\nall %s host tests passed\n' "$MODULE_NAME"
