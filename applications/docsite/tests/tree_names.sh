#!/bin/sh
# @file tree_names.sh
# @brief The assembled tree, read by `rho req`: every requirement once, every
#        part under the name `rho req` gives it in the repositories.
#
# Assembles the site into a scratch folder (build/site is left alone), runs
# `rho req check --workspace` on the tree, and compares the parts it finds with
# the parts it finds in the repositories themselves.
#
# @verifies SITE-0008
# SPDX-License-Identifier: MIT
set -eu

here=$(cd "$(dirname "$0")/.." && pwd)
root=$(cd "$here/../.." && pwd)
workspace=$(cd "$root/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
fail() { echo "FAIL: $*"; exit 1; }

cd "$root"
# A build may rewrite the lock file; the test puts it back as it found it.
cp applications/docsite/rho.lock "$scratch/rho.lock"
rho build applications/docsite >"$scratch/build.txt" 2>&1 || { cp "$scratch/rho.lock" applications/docsite/rho.lock; cat "$scratch/build.txt"; fail "the docsite did not build"; }
cp "$scratch/rho.lock" applications/docsite/rho.lock
./applications/docsite/build/docsite "$scratch/tree" "$scratch/site" >"$scratch/assemble.txt" 2>&1 || fail "the tree was not assembled"

# The tree is the workspace here: robohub/ is the root part, the rest beside it.
check=$(cd "$scratch/tree/robohub" && ROBOHUB_WORKSPACE= rho req check --workspace 2>&1) || { echo "$check"; fail "rho req check on the tree found errors"; }
echo "$check" | tail -1
case "$check" in
    *" 0 errors, 0 warnings"*) ;;
    *) echo "$check"; fail "rho req check on the tree is not clean" ;;
esac

# Every part rho req names in the repositories is in the tree by the same name,
# except the docsite itself, which is not a page of the site.
names() { awk -F'\t' '$1=="repo"{print $2}' | sort; }
(cd "$root" && ROBOHUB_WORKSPACE="$workspace" rho req list --workspace --tsv 2>/dev/null) | names | grep -vx docsite >"$scratch/repos.txt"
(cd "$scratch/tree/robohub" && ROBOHUB_WORKSPACE= rho req list --workspace --tsv 2>/dev/null) | names >"$scratch/tree.txt"
if ! diff "$scratch/repos.txt" "$scratch/tree.txt" >"$scratch/diff.txt"; then
    cat "$scratch/diff.txt"
    fail "the tree names parts differently from rho req (< the repositories, > the tree)"
fi
# And a part is copied once: one folder for the gateway contract.
[ ! -d "$scratch/tree/gateway" ] || fail "the gateway contract is also copied as gateway/"
echo "ok: $(wc -l <"$scratch/tree.txt") parts, named as rho req names them"
