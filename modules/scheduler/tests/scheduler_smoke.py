#!/usr/bin/env python3
"""Smoke test for the scheduler module inside the aquarium host.

Creates an interval chore, completes it, snoozes it, and drives a usage-based
chore to due. The database path is checked as well: modules share the host's
main SQL database under the application workspace.
"""

import html
import json
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
HOST = ROBOHUB / "applications" / "aquarium"
PROJECTS = ROBOHUB.parent
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


def wait_for(base: str) -> None:
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with open_url(base + "/scheduler", timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    raise SystemExit(f"aquarium did not start at {base}")


def get(base: str, path: str) -> str:
    with open_url(base + path, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def post(base: str, path: str, fields: dict) -> dict:
    if CSRF and "csrf" not in fields:
        fields = dict(fields, csrf=CSRF)
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with open_url(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


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
    with tempfile.TemporaryDirectory(prefix="scheduler-") as workspace:
        env = dict(os.environ)
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f":{port}"
        global TOKEN
        auth_home = env.get("HOME") if env.get("HOME", "").startswith(tempfile.gettempdir()) else tempfile.mkdtemp(prefix="aquarium-home-")
        env["HOME"] = auth_home
        TOKEN = mint_token(auth_home, "aquarium")
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        try:
            wait_for(base)
            learn_csrf(base, "/scheduler")
            page = get(base, "/scheduler")
            assert_contains(page, ["Maintenance schedule", "No chores scheduled",
                                   "Add a chore"], "empty scheduler")

            assert post(base, "/api/scheduler/chores", {
                "title": "Change filter sock",
                "kind": "interval",
                "interval_hours": "72",
                "grace_hours": "12",
                "priority": "high",
            })["ok"]
            chores = json.loads(get(base, "/api/scheduler/chores"))
            if len(chores) != 1 or chores[0]["status"] != "pending":
                raise AssertionError(f"unexpected chores: {chores}")

            assert post(base, "/api/scheduler/chores/1/complete", {"note": "Cleaned"})["ok"]
            completed = get(base, "/scheduler")
            assert_contains(completed, ["Cleaned", "Change filter sock"], "completion log")

            assert post(base, "/api/scheduler/chores/1/snooze", {"hours": "24"})["ok"]

            assert post(base, "/api/scheduler/chores", {
                "title": "UV bulb",
                "kind": "usage",
                "usage_hours": "4000",
                "priority": "critical",
            })["ok"]
            assert post(base, "/api/scheduler/chores/2/usage", {"hours": "4000"})["ok"]
            chores = json.loads(get(base, "/api/scheduler/chores"))
            uv = [chore for chore in chores if chore["title"] == "UV bulb"][0]
            if uv["status"] != "due":
                raise AssertionError(f"usage chore should be due: {uv}")

            db = Path(workspace) / "data" / "app.db"
            if not db.exists():
                raise AssertionError("the scheduler records are not in the host's main database")
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
