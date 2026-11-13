#!/usr/bin/env python3
"""Smoke test for the inventory and expenses module.

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


OLD_SCHEMA = """
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
    with tempfile.TemporaryDirectory(prefix="inventory-") as workspace:
        env = dict(os.environ)
        # The application finds the toolchain (the documentation generator, the
        # components) by its home; the test gives the application a HOME of its own,
        # so the toolchain's home is named before that happens.
        env.setdefault("RHO_HOME", os.path.join(os.path.expanduser("~"), ".rho"))
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f"127.0.0.1:{port}"
        global TOKEN
        auth_home = env.get("HOME") if env.get("HOME", "").startswith(tempfile.gettempdir()) else tempfile.mkdtemp(prefix="aquarium-home-")
        env["HOME"] = auth_home
        TOKEN = mint_token(auth_home, "aquarium")
        # A database an older inventory made: the new columns come from the
        # module's ALTER statements, and its rows survive.
        import sqlite3
        os.makedirs(os.path.join(workspace, "data"), exist_ok=True)
        with sqlite3.connect(os.path.join(workspace, "data", "app.db")) as conn:
            conn.executescript(OLD_SCHEMA)
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        try:
            wait_for(base)
            learn_csrf(base, "/expenses")
            asset = open_url(base + "/static/aquarium-background.jpg", timeout=10)
            if asset.status != 200 or asset.headers.get_content_type() != "image/jpeg":
                raise AssertionError("the aquarium background asset is not served")

            page = get(base, "/expenses")
            assert_contains(page, ["Inventory & expenses", "No items in the inventory",
                                   "No purchases recorded", "Add an item", "RON"],
                            "empty inventory page")

            assert_contains(post(base, "/expenses/categories/add", {"category": "Consumables"}),
                            ["Category added"], "category")
            import sqlite3
            db_path = Path(workspace) / "data" / "app.db"

            def category_id(name: str) -> str:
                with sqlite3.connect(db_path) as conn:
                    return str(conn.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()[0])

            consumables = category_id("Consumables")
            assert_contains(post(base, "/expenses/items/add", {
                "name": "Salt mix",
                "category_id": consumables,
                "unit": "kg",
                "quantity": "5",
                "reorder": "1",
                "location": "Cabinet",
            }), ["Item added"], "item")

            assert_contains(post(base, "/expenses/purchases/add", {
                "item_id": "1",
                "quantity": "2.5",
                "unit_price": "12.34",
                "category_id": consumables,
                "source": "Shop",
                "purchased_at": "2026-11-02",
                "comment": "Restock",
            }), ["Purchase recorded and stock increased"], "purchase")

            page = get(base, "/expenses")
            assert_contains(page, ["Salt mix", "Consumables", "7.5", "30.85",
                                   "Shop", "Restock"], "purchase in inventory")

            assert_contains(post(base, "/expenses/items/consume", {
                "item_id": "1", "quantity": "7", "comment": "Used",
            }), ["Stock removed"], "consume")
            page = get(base, "/expenses")
            assert_contains(page, ["0.5", "reorder", "Need reorder"], "low stock")

            edit = get(base, "/expenses/items/edit?id=1")
            assert_contains(edit, ["Edit item", 'value="Salt mix"', 'value="Cabinet"'],
                            "item edit")

            db = Path(workspace) / "data" / "app.db"
            if not db.exists():
                raise AssertionError("the module database is not in the application workspace")

            assert_contains(post(base, "/expenses/purchases/delete", {"id": "1"}),
                            ["Purchase removed"], "delete purchase")
            assert "0.00" in get(base, "/expenses")

            # Equipment: an item of kind equipment, named by a handle written
            # loosely and kept clean, whose category has capabilities.
            post(base, "/expenses/categories/add", {"category": "Filters"})
            filters = category_id("Filters")
            with sqlite3.connect(db) as conn:
                conn.execute("UPDATE categories SET kind='equipment', capabilities='switch, power?' WHERE name='Filters'")
            assert_contains(post(base, "/expenses/items/add", {
                "name": "Eheim 2217", "category_id": filters, "unit": "unit", "quantity": "1",
                "kind": "", "handle": "Filter Main",
            }), ["Item added"], "equipment item")
            assert_contains(post(base, "/expenses/items/add", {
                "name": "Light", "category_id": filters, "handle": "light",
            }), ["Item added"], "second equipment item")
            refused = post(base, "/expenses/items/add", {"name": "Twin", "category_id": filters, "handle": "light"})
            assert_contains(refused, ["Another item already has that handle"], "a handle taken twice")
            with sqlite3.connect(db) as conn:
                kind, handle = conn.execute("SELECT kind, handle FROM items WHERE name='Eheim 2217'").fetchone()
            if (kind, handle) != ("equipment", "filter-main"):
                raise AssertionError(f"the item is {kind!r} {handle!r}, want equipment filter-main")
            page = get(base, "/expenses")
            assert_contains(page, ["Equipment", "not connected", "/expenses/items/automation?id=2"],
                            "an unconnected equipment row")

            automation = get(base, "/expenses/items/automation?id=2")
            assert_contains(automation, ["Eheim 2217", "filter-main", "switch", "power", "optional"],
                            "the automation tab")
            assert_contains(post(base, "/expenses/items/bind", {
                "id": "2", "capability": "switch", "source": "plug-a1.switch"}),
                ["Capability bound"], "a switch bound")
            taken = post(base, "/expenses/items/bind", {
                "id": "3", "capability": "switch", "source": "plug-a1.switch"})
            assert_contains(taken, ["already controlled by", "Eheim 2217"], "one relay, two items")
            post(base, "/expenses/items/bind", {"id": "2", "capability": "power", "source": "plug-a1.power"})
            with sqlite3.connect(db) as conn:
                rows = conn.execute("SELECT capability, source, access FROM item_bindings ORDER BY capability").fetchall()
            if rows != [("power", "plug-a1.power", "read"), ("switch", "plug-a1.switch", "control")]:
                raise AssertionError(f"bindings {rows}")
            assert_contains(get(base, "/expenses"), ["connected"], "a connected equipment row")
            assert_contains(post(base, "/expenses/items/bind", {"id": "2", "capability": "power", "source": ""}),
                            ["Capability unbound"], "an optional capability unbound")
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
