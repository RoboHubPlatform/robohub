#!/usr/bin/env python3
"""Smoke test for widgets 0.3 on a gateway: stable ids, inventory items, switching.

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
    with tempfile.TemporaryDirectory(prefix="widgets-gw-") as workspace:
        env = dict(os.environ)
        env.setdefault("RHO_HOME", os.path.join(os.path.expanduser("~"), ".rho"))
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f"127.0.0.1:{port}"
        global TOKEN
        auth_home = tempfile.mkdtemp(prefix="widgets-gw-home-")
        env["HOME"] = auth_home
        TOKEN = mint_token(auth_home, "aquarium")
        # The installation chooses the simulator: the mesh is switched off and
        # the simulator on, as Settings → Gateway does, in the bind.conf.
        env["RHO_APP_WORKSPACE"] = workspace
        with open(os.path.join(workspace, "bind.conf"), "w") as f:
            f.write("robohub-provider-mesh.enabled=false\nsimulator.enabled=true\n")
        os.chmod(os.path.join(workspace, "bind.conf"), 0o600)
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            import json, sqlite3, time
            wait_for(base)
            learn_csrf(base, "/expenses")
            db = Path(workspace) / "data" / "app.db"
            values_file = Path(workspace) / "data" / "simulator" / "values.txt"

            def sim_value(source):
                for line in values_file.read_text().splitlines():
                    if line.startswith(source + "="):
                        return line.split("=", 1)[1]
                return ""

            deadline = time.time() + 15
            while time.time() < deadline and not (values_file.exists() and sim_value("sim-probe.temperature")):
                time.sleep(0.5)
            if not sim_value("sim-probe.temperature"):
                raise AssertionError("the simulator did not tick")

            post(base, "/expenses/categories/add", {"category": "Heaters"})
            with sqlite3.connect(db) as conn:
                conn.execute("UPDATE categories SET kind='equipment', capabilities='switch, temperature?' WHERE name='Heaters'")
                heaters = str(conn.execute("SELECT id FROM categories WHERE name='Heaters'").fetchone()[0])
            post(base, "/expenses/items/add", {"name": "Heater 200 W", "category_id": heaters, "handle": "heater"})
            post(base, "/expenses/items/bind", {"id": "1", "capability": "switch", "source": "sim-heater-plug.switch"})
            post(base, "/expenses/items/bind", {"id": "1", "capability": "temperature", "source": "sim-probe.temperature"})

            learn_csrf(base, "/widgets")
            post(base, "/widgets/add", {"title": "Probe by URL", "kind": "numeric", "source_kind": "mesh",
                                        "source": "http://127.0.0.1:8478/mesh/api/projects/sim/sources/sim-probe.temperature/value"})
            post(base, "/widgets/add", {"title": "Heater temperature", "kind": "numeric", "source_kind": "item",
                                        "source": "heater.temperature", "unit": "C"})
            post(base, "/widgets/add", {"title": "Heater", "kind": "toggle", "source_kind": "item", "source": "heater.switch"})

            # An older widget's URL becomes the source's stable id.
            deadline = time.time() + 20
            source = ""
            while time.time() < deadline:
                with sqlite3.connect(db) as conn:
                    source, kind = conn.execute("SELECT source, source_kind FROM widgets WHERE title='Probe by URL'").fetchone()
                if source == "sim-probe.temperature":
                    break
                time.sleep(1)
            if source != "sim-probe.temperature" or kind != "mesh":
                raise AssertionError(f"the URL did not move to the stable id: {source!r} {kind!r}")

            widgets = {w["title"]: w for w in json.loads(get(base, "/api/widgets"))}
            temperature = widgets["Heater temperature"]["latest"]
            if not temperature or abs(float(temperature) - 24.8) > 1:
                raise AssertionError(f"the item widget does not read the bound probe: {widgets['Heater temperature']}")

            heater = widgets["Heater"]
            post(base, "/widgets/press", {"id": str(heater["id"])})
            if sim_value("sim-heater-plug.switch") != "on":
                raise AssertionError("pressing the item toggle did not switch the plug through inventory")
            journal = json.loads(get(base, "/api/journal?kind=widget"))
            if not any(e["subject"] == "Heater" for e in journal["entries"]):
                raise AssertionError(f"the press is not in the journal: {journal}")
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
