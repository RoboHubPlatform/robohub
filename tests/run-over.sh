#!/bin/sh
# A run over the ecosystem answers with its exit status, and the linter and the
# documentation run over every module, tests or not.
#
# The run is made over a registry of its own, in a scratch folder: one module
# whose test fails, and one that declares no tests. `robohub test` must exit
# non-zero and say which failed; `robohub docs` and `robohub lint` must run over
# the module with no tests rather than skip it as having "no tests".
#
# @verifies HUB-0010, HUB-0022
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
ROBOHUB="$ROOT/build/robohub"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

if [ ! -x "$ROBOHUB" ]; then
    echo "the orchestrator is not built: rho build . first" >&2
    exit 1
fi

mkdir -p "$WORK/registry/modules" "$WORK/failing/tests" "$WORK/untested/docs"
cat > "$WORK/registry/modules/failing.yml" <<ENTRY
name: failing
role: runtime
path: $WORK/failing
summary: A module whose one test fails.
ENTRY
cat > "$WORK/registry/modules/untested.yml" <<ENTRY
name: untested
role: runtime
path: $WORK/untested
summary: A module that declares no tests.
ENTRY
cat > "$WORK/failing/module.yml" <<'MANIFEST'
module:
  name: failing
  id: robohub.test.failing
  type: rho
  version: 0.1.0
MANIFEST
cat > "$WORK/failing/tests/tests.yml" <<'SUITES'
name: failing
suites:
  - name: it fails
    kind: command
    command: ["false"]
    tags: [unit]
SUITES
cat > "$WORK/untested/module.yml" <<'MANIFEST'
module:
  name: untested
  id: robohub.test.untested
  type: rho
  version: 0.1.0
MANIFEST
printf '# Untested\n\nA page.\n' > "$WORK/untested/docs/index.md"

cd "$WORK"
if out=$("$ROBOHUB" test 2>&1); then
    echo "robohub test exited 0 when a module's tests failed:" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -q "failing failed" || { echo "the run did not say which module failed:" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q "untested declares no tests" || { echo "a module with no tests was not said to have none:" >&2; echo "$out" >&2; exit 1; }

for tool in docs lint; do
    out=$("$ROBOHUB" "$tool" untested 2>&1 || true)
    if echo "$out" | grep -q "declares no tests"; then
        echo "robohub $tool skipped a module because it declares no tests:" >&2
        echo "$out" >&2
        exit 1
    fi
    echo "$out" | grep -q "$tool: untested" || { echo "robohub $tool did not run over the module:" >&2; echo "$out" >&2; exit 1; }
done

echo "a failed run exits non-zero, and docs and lint run over every module"
