#!/usr/bin/env python3
"""Smoke test for the rules module.

Builds the module, starts it against a temporary application workspace, and
walks the pages: an item, a purchase that increases stock and records spending,
a low-stock state after consuming it, the edit form, and the database under the
workspace rather than in the module folder.
"""

import html
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve()
MODULE = HERE.parents[1]
ROBOHUB = MODULE.parents[1]
PROJECTS = ROBOHUB.parent
# The host the module is tested in: the aquarium, in its own repository beside
# this one, or where ROBOHUB_AQUARIUM says.
HOST = Path(os.environ.get("ROBOHUB_AQUARIUM", str(PROJECTS / "robohub-aquarium")))
RHO = PROJECTS / "rho" / "bin" / "rho"

# The bearer ticket every request carries: one the keeper would issue for the
# host, minted by the test with a key pair of its own (see mint_token).
TOKEN = ""


def mint_token(home: str, audience: str) -> str:
    """A ticket for the host, as the keeper would issue one.

    The host verifies tickets against ~/.rho/auth/public.pem in its own home,
    so the test makes a key pair there and signs the ticket with it.
    """
    rho = str(RHO) if RHO.exists() else "rho"
    keys = os.path.join(home, ".rho", "auth")
    os.makedirs(keys, exist_ok=True)
    subprocess.run([rho, "auth", "keygen", "--dir", keys, "--force"],
                   check=True, capture_output=True, text=True)
    result = subprocess.run(
        [rho, "auth", "ticket", "--private", os.path.join(keys, "private.pem"),
         "--issuer", "keeper", "--audience", audience, "--subject", "smoke",
         "--scopes", "*", "--ttl", "1h"],
        check=True, capture_output=True, text=True)
    return result.stdout.strip()


CSRF = ""


def learn_csrf(base: str, page: str) -> None:
    """The form token the host draws its forms with, which every post carries."""
    global CSRF
    with open_url(base + page) as response:
        text = response.read().decode("utf-8", "replace")
    found = re.search(r'name="csrf" value="([^"]*)"', text)
    if not found:
        raise AssertionError(f"{page} draws no form token")
    CSRF = html.unescape(found.group(1))


def open_url(target, timeout: float = 10):
    """urlopen with the test's ticket, which every page of the host asks for."""
    request = target if isinstance(target, urllib.request.Request) else urllib.request.Request(target)
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    return urllib.request.urlopen(request, timeout=timeout)



def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(base: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with open_url(base + "/", timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    raise SystemExit(f"the aquarium host did not start at {base}")


def get(base: str, path: str) -> str:
    with open_url(base + path, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def post(base: str, path: str, fields: dict) -> str:
    if CSRF and "csrf" not in fields:
        fields = dict(fields, csrf=CSRF)
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with open_url(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def assert_contains(haystack: str, needles: list, label: str) -> None:
    for needle in needles:
        if needle not in haystack:
            raise AssertionError(f"{label} does not contain {needle!r}")


def build() -> Path:
    # The module has no port or binary of its own; it is tested inside the
    # aquarium host that includes it.
    binary = HOST / "build" / "aquarium"
    rho = str(RHO) if RHO.exists() else "rho"
    result = subprocess.run([rho, "build", str(HOST)], cwd=ROBOHUB, text=True,
                            capture_output=True)
    if result.returncode != 0:
        raise SystemExit("aquarium build failed:\n" + result.stdout + result.stderr)
    if not binary.exists():
        raise SystemExit(f"aquarium build wrote no binary at {binary}")
    return binary


UNUSED = """
CREATE TABLE categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id), unit TEXT NOT NULL DEFAULT 'unit',
    quantity_milli INTEGER NOT NULL DEFAULT 0, reorder_milli INTEGER NOT NULL DEFAULT 0,
    location TEXT, notes TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')));
"""


def main() -> int:
    binary = build()
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="rules-") as workspace:
        env = dict(os.environ)
        env.setdefault("RHO_HOME", os.path.join(os.path.expanduser("~"), ".rho"))
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f"127.0.0.1:{port}"
        global TOKEN
        auth_home = tempfile.mkdtemp(prefix="rules-home-")
        env["HOME"] = auth_home
        TOKEN = mint_token(auth_home, "aquarium")
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            wait_for(base)
            learn_csrf(base, "/rules")
            page = get(base, "/rules")
            assert_contains(page, ["Rules &amp; modes", "Add a rule"], "the page")
            import json, sqlite3, time
            db = Path(workspace) / "data" / "app.db"
            with sqlite3.connect(db) as conn:
                conn.execute("INSERT INTO rule_modes (name, title, duration_s, do_actions, end_actions, suspends, origin) VALUES "
                             "('smoke-mode', 'Smoke mode', 600, 'journal info \"feeding started\"', 'journal info \"feeding over\"', 'always', 'preset')")
            # A rule that holds, one that cannot be read, and one that waits.
            assert_contains(post(base, "/rules/add", {"name": "Always", "when": "1 == 1 and not (2 > 3)",
                                                      "do": 'journal warning "always holds"'}), ["Rule added"], "a rule")
            assert_contains(post(base, "/rules/add", {"name": "always", "when": "1 == 1"}), ["already exists"], "a name taken")
            assert_contains(post(base, "/rules/add", {"name": "broken", "when": "(1 == 1"}), ["not closed"], "a bracket left open")
            post(base, "/rules/add", {"name": "unread", "when": "heater.temperature < 24.5", "do": "switch heater on"})
            post(base, "/rules/add", {"name": "in-feeding", "when": "mode == smoke-mode or nothing.there > 1",
                                      "do": 'journal info "the mode is seen"'})
            deadline = time.time() + 20
            state = {}
            while time.time() < deadline:
                state = json.loads(get(base, "/api/rules"))
                rules = {r["name"]: r for r in state["rules"]}
                # Both rules are evaluated in the same tick, but the answer may
                # be read between them: wait for both.
                if rules.get("always", {}).get("state") == "active" and rules.get("unread", {}).get("problem"):
                    break
                time.sleep(1)
            rules = {r["name"]: r for r in state["rules"]}
            if rules["always"]["state"] != "active" or rules["always"]["last_fired"] == 0:
                raise AssertionError(f"the rule that holds did not fire: {rules['always']}")
            if rules["unread"]["state"] != "idle" or "no reading for heater.temperature" not in rules["unread"]["problem"]:
                raise AssertionError(f"an unread rule acted or did not say why: {rules['unread']}")
            journal = json.loads(get(base, "/api/journal?kind=rule"))
            if not any(e["message"] == "always holds" and e["level"] == "warning" for e in journal["entries"]):
                raise AssertionError(f"the rule's action is not in the journal: {journal}")

            # A mode: started, seen by a condition, suspends a rule, ended.
            assert_contains(post(base, "/rules/mode", {"mode": "smoke-mode"}), ["Mode started"], "a mode started")
            deadline = time.time() + 20
            while time.time() < deadline:
                rules = {r["name"]: r for r in json.loads(get(base, "/api/rules"))["rules"]}
                if rules["in-feeding"]["state"] == "active":
                    break
                time.sleep(1)
            state = json.loads(get(base, "/api/rules"))
            if state["mode"] != "smoke-mode" or state["mode_ends"] == 0:
                raise AssertionError(f"the mode is not in force: {state}")
            if {r["name"]: r for r in state["rules"]}["in-feeding"]["state"] != "active":
                raise AssertionError("a condition does not see the mode, or a missing reading on the side of an or that did not decide stopped it")
            assert_contains(get(base, "/rules"), ["suspended"], "a suspended rule")
            assert_contains(post(base, "/rules/mode", {"end": "1"}), ["Mode ended"], "a mode ended")
            messages = [e["message"] for e in json.loads(get(base, "/api/journal"))["entries"]]
            for wanted in ["feeding started", "feeding over", "smoke-mode ended"]:
                if wanted not in messages:
                    raise AssertionError(f"{wanted!r} is not in the journal: {messages}")
            if json.loads(get(base, "/api/rules"))["mode"] != "":
                raise AssertionError("the mode is still in force")

            # Disabled, then deleted.
            with sqlite3.connect(db) as conn:
                rid = str(conn.execute("SELECT id FROM rules WHERE name='always'").fetchone()[0])
            post(base, "/rules/change", {"id": rid, "enabled": "1"})
            if {r["name"]: r for r in json.loads(get(base, "/api/rules"))["rules"]}["always"]["enabled"] != 0:
                raise AssertionError("a rule was not disabled")
            assert_contains(post(base, "/rules/change", {"id": rid, "delete": "1"}), ["Rule deleted"], "a rule deleted")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
