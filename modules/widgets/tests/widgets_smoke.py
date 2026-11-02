#!/usr/bin/env python3
"""Smoke test for the widgets module inside the aquarium host."""

import json
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


def wait_for(base: str) -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(base + "/widgets", timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    raise SystemExit(f"aquarium did not start at {base}")


def get(base: str, path: str) -> str:
    with urllib.request.urlopen(base + path, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def post_form(base: str, path: str, fields: dict) -> str:
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def post_json(base: str, path: str, fields: dict) -> dict:
    return json.loads(post_form(base, path, fields))


def assert_contains(haystack: str, needles: list, label: str) -> None:
    for needle in needles:
        if needle not in haystack:
            raise AssertionError(f"{label} does not contain {needle!r}")


def build() -> Path:
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
    with tempfile.TemporaryDirectory(prefix="widgets-") as workspace:
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
            page = get(base, "/widgets")
            assert_contains(page, ["Widgets", "No widgets yet", "Add a widget"],
                            "empty widget manager")

            post_form(base, "/widgets/add", {
                "title": "Water temperature", "kind": "numeric",
                "source_kind": "manual", "unit": "C",
            })
            post_form(base, "/widgets/value", {"id": "1", "value": "25.4"})
            widgets = json.loads(get(base, "/api/widgets"))
            if widgets[0]["latest"] != "25.4":
                raise AssertionError(f"unexpected widgets: {widgets}")
            assert_contains(get(base, "/"), ["Water temperature", "25.4"],
                            "dashboard number")

            post_form(base, "/widgets/add", {
                "title": "Return pump", "kind": "toggle", "source_kind": "url",
                "source": base + "/scheduler?state={state}", "method": "GET",
            })
            post_form(base, "/widgets/press", {"id": "2"})
            widgets = json.loads(get(base, "/api/widgets"))
            toggle = [w for w in widgets if w["title"] == "Return pump"][0]
            if toggle["latest"] != "on":
                raise AssertionError(f"toggle should be on: {toggle}")
            assert_contains(get(base, "/"), ["Return pump", "On"], "dashboard switch")

            post_form(base, "/widgets/add", {
                "title": "pH", "kind": "chart", "source_kind": "manual", "unit": "pH",
            })
            for value in ["8.1", "8.2", "8.0"]:
                post_form(base, "/widgets/value", {"id": "3", "value": value})
            assert "<svg class=\"spark\"" in get(base, "/"), "chart sparkline"

            db = Path(workspace) / "data" / "app.db"
            if not db.exists():
                raise AssertionError("widgets are not in the host's main database")
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
