#!/bin/sh
# The manifest of tests, and what the orchestrator does with it.
#
# A manifest is a list of what a module has: the tests, which kind each is, and
# whether each is run. The orchestrator reads it to say what there is, to run
# one of them, and to say whether a test is run at all.
#
# It runs against a real module, because the manifest of a module is the
# module's own. The one thing that writes is put back the way it was, whatever
# happens.
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
ROBOHUB="$ROOT/build/robohub"
MODULE=robohub-avr
TEST_NAME="the platform's own tests"

if [ ! -x "$ROBOHUB" ]; then
    echo "the orchestrator is not built: rho build . first" >&2
    exit 1
fi

# Whatever happens, the test is enabled again.
restore() {
    "$ROBOHUB" test enable "$MODULE" "$TEST_NAME" >/dev/null 2>&1 || true
}
trap restore EXIT

# The listing says what there is, and which of it is run.
listing=$("$ROBOHUB" test list "$MODULE" 2>&1)
if ! echo "$listing" | grep -q "$TEST_NAME"; then
    echo "the listing did not say what the module has" >&2
    echo "$listing" >&2
    exit 1
fi

# A test that is not run is not run, and the listing says so.
"$ROBOHUB" test disable "$MODULE" "$TEST_NAME" >/dev/null

# A run of one kind is the tests of that kind that are run: a test that is
# not run is skipped, and the report says so.
run=$("$ROBOHUB" test "$MODULE" --unit 2>&1 || true)
report="/home/miraur/projects/$MODULE/build/test-reports/report-1.txt"
if ! grep -q "skipped" "$report" 2>/dev/null; then
    echo "a run did not leave out the test that is not run" >&2
    echo "$run" >&2
    cat "$report" >&2 2>/dev/null
    exit 1
fi

# And it is run again once it is enabled.
"$ROBOHUB" test enable "$MODULE" "$TEST_NAME" >/dev/null
run=$("$ROBOHUB" test "$MODULE" --unit 2>&1 || true)
report="/home/miraur/projects/$MODULE/build/test-reports/report-1.txt"
if ! grep -q "<testcase" "$report" 2>/dev/null; then
    echo "a run did not count the test that is run" >&2
    echo "$run" >&2
    cat "$report" >&2 2>/dev/null
    exit 1
fi

echo "the manifest says what the module has, and the run follows it"
