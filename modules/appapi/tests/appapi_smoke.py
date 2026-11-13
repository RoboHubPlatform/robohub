#!/usr/bin/env python3
"""Smoke test for the application API module.

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
    with tempfile.TemporaryDirectory(prefix="appapi-") as workspace:
        env = dict(os.environ)
        env.setdefault("RHO_HOME", os.path.join(os.path.expanduser("~"), ".rho"))
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f"127.0.0.1:{port}"
        global TOKEN
        auth_home = tempfile.mkdtemp(prefix="appapi-home-")
        env["HOME"] = auth_home
        TOKEN = mint_token(auth_home, "aquarium")
        # The values are seeded before the application starts: a journal entry
        # a derived value counts the days since, a published value with its
        # history, and the derived definition itself.
        import json, sqlite3, time
        now = int(time.time())
        os.makedirs(os.path.join(workspace, "data"), exist_ok=True)
        db = os.path.join(workspace, "data", "app.db")
        with sqlite3.connect(db) as conn:
            conn.executescript((MODULE / "db" / "schema.sql").read_text())
            conn.executescript((MODULE.parent / "journal" / "db" / "schema.sql").read_text())
            conn.execute("INSERT INTO journal_entries (at, level, kind, subject, actor, message) VALUES (?, 'info', 'water_change', 'aquarium', 'person:ana', '30 %')", (now - 86400 * 2,))
            conn.execute("INSERT INTO appapi_derived (id, source, fn, window_s, unit, label) VALUES ('days_since_water_change', 'water_change', 'since', 0, 'd', 'Days since water change')")
            conn.execute("INSERT INTO appapi_derived (id, source, fn, window_s, unit, label) VALUES ('nothing_bound', 'heater.temperature', 'avg', 86400, '°C', '')")
            conn.execute("INSERT INTO appapi_values (id, value, unit, label, kind, updated_at) VALUES ('stocking', '0.8', 'cm/L', 'Stocking level', 'published', ?)", (now,))
            conn.executemany("INSERT INTO appapi_history (id, at, value) VALUES ('stocking', ?, ?)", [(now - 7200, 0.6), (now - 3600, 0.7), (now - 40 * 86400, 0.1)])
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            wait_for(base)
            values = {}
            deadline = time.time() + 30
            while time.time() < deadline:
                values = {v["id"]: v for v in json.loads(get(base, "/api/v1/values"))["values"]}
                if "days_since_water_change" in values:
                    break
                time.sleep(1)
            if "days_since_water_change" not in values:
                raise AssertionError(f"the derived value was not computed: {values}")
            days = float(values["days_since_water_change"]["value"])
            if not 1.99 <= days <= 2.01 or values["days_since_water_change"]["kind"] != "derived":
                raise AssertionError(f"days since the water change: {values['days_since_water_change']}")
            if "nothing_bound" in values:
                raise AssertionError("a value with nothing to read from was invented")
            one = json.loads(get(base, "/api/v1/values/stocking"))
            if one["value"] != "0.8" or one["unit"] != "cm/L":
                raise AssertionError(f"one value: {one}")
            try:
                get(base, "/api/v1/values/missing")
                raise AssertionError("a missing value was answered")
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
            history = json.loads(get(base, "/api/v1/values/stocking/history"))
            if [p["v"] for p in history["points"]] != [0.6, 0.7] or not history["ok"]:
                raise AssertionError(f"the last day's history: {history}")
            if history["points"][0]["t"] != (now - 7200) * 1000:
                raise AssertionError("a point's time is not in milliseconds")
            wide = json.loads(get(base, f"/api/v1/values/stocking/history?from={(now - 50 * 86400) * 1000}&to={now * 1000}"))
            if len(wide["points"]) != 2:
                raise AssertionError(f"history older than 30 days was kept: {wide}")
            events = json.loads(get(base, "/api/v1/events?kind=water_change"))
            if [e["message"] for e in events["entries"]] != ["30 %"]:
                raise AssertionError(f"events: {events}")
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
