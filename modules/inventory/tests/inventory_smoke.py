#!/usr/bin/env python3
"""Smoke test for the inventory and expenses module.

Builds the module, starts it against a temporary application workspace, and
walks the pages: an item, a purchase that increases stock and records spending,
a low-stock state after consuming it, the edit form, and the database under the
workspace rather than in the module folder.
"""

import os
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
HOST = ROBOHUB / "applications" / "aquarium"
PROJECTS = ROBOHUB.parent
RHO = PROJECTS / "rho" / "bin" / "rho"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(base: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/", timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    raise SystemExit(f"the aquarium host did not start at {base}")


def get(base: str, path: str) -> str:
    with urllib.request.urlopen(base + path, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def post(base: str, path: str, fields: dict) -> str:
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=20) as response:
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


def main() -> int:
    binary = build()
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="inventory-") as workspace:
        env = dict(os.environ)
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f":{port}"
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        try:
            wait_for(base)
            asset = urllib.request.urlopen(base + "/static/aquarium-background.jpg", timeout=10)
            if asset.status != 200 or asset.headers.get_content_type() != "image/jpeg":
                raise AssertionError("the aquarium background asset is not served")

            page = get(base, "/expenses")
            assert_contains(page, ["Inventory & expenses", "No items in the inventory",
                                   "No purchases recorded", "Add an item", "RON"],
                            "empty inventory page")

            assert_contains(post(base, "/expenses/categories/add", {"category": "Consumables"}),
                            ["Category added"], "category")
            assert_contains(post(base, "/expenses/items/add", {
                "name": "Salt mix",
                "category_id": "1",
                "unit": "kg",
                "quantity": "5",
                "reorder": "1",
                "location": "Cabinet",
            }), ["Item added"], "item")

            assert_contains(post(base, "/expenses/purchases/add", {
                "item_id": "1",
                "quantity": "2.5",
                "unit_price": "12.34",
                "category_id": "1",
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

            db = Path(workspace) / "modules" / "inventory" / "inventory.db"
            if not db.exists():
                raise AssertionError("the module database is not in the application workspace")

            assert_contains(post(base, "/expenses/purchases/delete", {"id": "1"}),
                            ["Purchase removed"], "delete purchase")
            assert "0.00" in get(base, "/expenses")
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
