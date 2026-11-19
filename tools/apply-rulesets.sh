#!/usr/bin/env bash
#
# @file apply-rulesets.sh
# @brief Protect main in every RoboHub repository, and in rho, with one ruleset.
#
# The ruleset is .github/rulesets/main.json: no deletion and no force-push of
# main; changes arrive by pull request, with one approval from a code owner and
# CI green; repository administrators — the maintainer — bypass it, so they can
# still push and merge their own work. docs/doc/process/governance.md explains it.
#
#   GITHUB_TOKEN=... tools/apply-rulesets.sh            # show what would be done
#   GITHUB_TOKEN=... tools/apply-rulesets.sh --apply    # do it
#
# The token needs Administration: read and write on the repositories (a
# fine-grained token for the RoboHubPlatform and rho-language owners, or a
# classic token with the repo scope). It is read from the environment and sent
# only to api.github.com.
#
# SPDX-License-Identifier: MIT
#
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
# @req HUB-0017
ruleset="$here/.github/rulesets/main.json"
apply=false
[ "${1:-}" = "--apply" ] && apply=true
: "${GITHUB_TOKEN:?set GITHUB_TOKEN to a token that may administer the repositories}"

# owner/repository and the status check that must pass on it.
targets=(
  "rho-language/rho|build-and-test"
)
for repo in robohub robohub-aquarium robohub-avr robohub-common robohub-core \
            robohub-devices robohub-drivers robohub-energy robohub-esp32 \
            robohub-freertos robohub-gateway robohub-keeper robohub-linux \
            robohub-mesh robohub-pico robohub-stm32 robohub-telemetry robohub-transport; do
  targets+=("RoboHubPlatform/${repo}|ci / build-and-test")
done

api() {
  curl -sS -H "Authorization: Bearer ${GITHUB_TOKEN}" \
       -H "Accept: application/vnd.github+json" \
       -H "X-GitHub-Api-Version: 2022-11-28" "$@"
}

# send runs one request and says what happened: curl succeeds on a refused
# request, so the status is what tells.
send() {
  local repo="$1" done="$2"; shift 2
  local answer status
  answer="$(api -w '\n%{http_code}' "$@")"
  status="${answer##*$'\n'}"
  if [ "${status}" = "200" ] || [ "${status}" = "201" ]; then
    echo "${repo}: ${done}"
  else
    echo "${repo}: refused (${status}): $(printf '%s' "${answer%$'\n'*}" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("message", ""))
except Exception: print("")')"
    failed=1
  fi
}

failed=0
for target in "${targets[@]}"; do
  repo="${target%%|*}"
  check="${target#*|}"
  body="$(python3 - "$ruleset" "$check" <<'PY'
import json, sys
rules = json.load(open(sys.argv[1]))
for rule in rules["rules"]:
    if rule["type"] == "required_status_checks":
        rule["parameters"]["required_status_checks"] = [{"context": sys.argv[2]}]
print(json.dumps(rules))
PY
)"
  existing="$(api "https://api.github.com/repos/${repo}/rulesets" |
    python3 -c 'import json,sys
data = json.load(sys.stdin)
print(next((str(r["id"]) for r in data if isinstance(r, dict) and r.get("name") == "main"), "") if isinstance(data, list) else "ERROR " + str(data.get("message")))')"
  case "$existing" in
    ERROR*) echo "${repo}: cannot read its rulesets: ${existing#ERROR }"; continue ;;
  esac
  if ! $apply; then
    if [ -n "$existing" ]; then echo "${repo}: would update ruleset ${existing} (required check: ${check})"
    else echo "${repo}: would create ruleset main (required check: ${check})"; fi
    continue
  fi
  if [ -n "$existing" ]; then
    send "$repo" updated -X PUT "https://api.github.com/repos/${repo}/rulesets/${existing}" -d "$body"
  else
    send "$repo" created -X POST "https://api.github.com/repos/${repo}/rulesets" -d "$body"
  fi
done
$apply || echo "nothing was changed; run again with --apply"
exit "${failed}"
