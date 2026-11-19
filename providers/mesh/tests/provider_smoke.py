#!/usr/bin/env python3
"""The Mesh provider's test: how it switches an output through Mesh.

The harness (`harness/`) is a program that binds robohub.gateway to this provider
and switches one source when it is asked to. The test runs a stand-in for Mesh
and for the token issuer on one loopback port, and reads what the provider sent:

- a switch is a POST to the source's action with `state=on` or `off` and no body,
  carrying a bearer ticket the issuer gave for the audience `mesh` and the scope
  `mesh:<project>` — the grant Mesh asks for to change a mesh, never a GET;
- Mesh's 200 (confirmed) is true; its 202 (pending), a 4xx or a 5xx is false;
- a state other than on or off is refused with nothing sent;
- a source stored as Mesh's action URL is switched by its id.

Usage: provider_smoke.py
"""

import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARNESS = HERE / "harness"
ROBOHUB = HERE.parents[2]
PROJECTS = ROBOHUB.parent
RHO = str(PROJECTS / "rho" / "bin" / "rho") if (PROJECTS / "rho" / "bin" / "rho").exists() else "rho"
TOKEN = "stand-in-ticket-for-mesh"
failures = []


def check(ok: bool, what: str) -> None:
    print(("[PASS] " if ok else "[FAIL] ") + what)
    if not ok:
        failures.append(what)


class Stand:
    """What the stand-in Mesh and issuer were asked, and what Mesh answers."""
    requests = []
    issued = []
    status = 200


class Handler(http.server.BaseHTTPRequestHandler):
    def _body(self) -> str:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length).decode("utf-8", "replace") if length else ""

    def _answer(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = self._body()
        if self.path == "/auth/service-token":
            Stand.issued.append(dict(urllib.parse.parse_qsl(body)))
            self._answer(200, {"token": TOKEN, "expires_in": 300})
            return
        self._record("POST", body)

    def do_GET(self):
        self._record("GET", "")

    def _record(self, method: str, body: str) -> None:
        Stand.requests.append({"method": method, "path": self.path, "body": body,
                               "authorization": self.headers.get("Authorization", "")})
        if Stand.status == 200:
            self._answer(200, {"ok": True, "confirmed": True, "outcome": "confirmed"})
        elif Stand.status == 202:
            self._answer(202, {"ok": True, "confirmed": False, "outcome": "pending"})
        else:
            self._answer(Stand.status, {"ok": False})

    def log_message(self, *args):
        pass


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def build() -> Path:
    env = dict(os.environ)
    env.setdefault("ROBOHUB_WORKSPACE", str(PROJECTS))
    result = subprocess.run([RHO, "build", str(HARNESS)], cwd=ROBOHUB, text=True,
                            capture_output=True, env=env)
    lock = HARNESS / "rho.lock"
    if lock.exists():
        lock.unlink()
    if result.returncode != 0:
        raise SystemExit("the harness did not build:\n" + result.stdout + result.stderr)
    return HARNESS / "build" / "robohub-provider-mesh-harness"


def main() -> int:
    binary = build()
    stand = http.server.ThreadingHTTPServer(("127.0.0.1", free_port()), Handler)
    threading.Thread(target=stand.serve_forever, daemon=True).start()
    mesh = f"http://127.0.0.1:{stand.server_address[1]}"
    root = tempfile.mkdtemp(prefix="provider-mesh-")
    workspace = os.path.join(root, "workspace")
    os.makedirs(workspace)
    secret = os.path.join(root, "client.secret")
    with open(secret, "w", encoding="utf-8") as handle:
        handle.write("harness-secret\n")
    os.chmod(secret, 0o600)
    with open(os.path.join(workspace, "bind.conf"), "w", encoding="utf-8") as handle:
        handle.write("robohub-provider-mesh.project=Bench\nrobohub-provider-mesh.transport=http\n")
    port = free_port()
    env = dict(os.environ)
    env.update({
        "HOME": root,
        "RHO_APP_WORKSPACE": workspace,
        "ROBOHUB_APP_WORKSPACE": workspace,
        "RHO_HTTP_ADDR": f"127.0.0.1:{port}",
        "RHO_SERVICE_MESH_URL": mesh,
        "RHO_CLIENT_ID": "robohub-aquarium",
        "RHO_CLIENT_SECRET_FILE": secret,
        "RHO_AUTH_URL": mesh,
    })
    env.pop("ROBOHUB_BUS_URL", None)
    env.pop("ROBOHUB_BUS_USER", None)
    process = subprocess.Popen([str(binary)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                socket.create_connection(("127.0.0.1", port), timeout=1).close()
                break
            except OSError:
                time.sleep(0.1)

        def switch(source: str, state: str) -> str:
            query = urllib.parse.urlencode({"source": source, "state": state})
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/switch?{query}", timeout=30) as response:
                return response.read().decode().strip()

        # @verifies PMESH-0005, PMESH-0002
        Stand.requests.clear()
        Stand.status = 200
        answer = switch("ba06f37ca34ba32c.state", "on")
        sent = Stand.requests[-1] if Stand.requests else {}
        check(answer == "true", f"Mesh's 200 (confirmed) is a switch done ({answer})")
        check(sent.get("method") == "POST", f"the switch is a POST, never a GET ({sent})")
        check(sent.get("path") == "/mesh/api/projects/Bench/sources/ba06f37ca34ba32c.state/action?state=on",
              f"to the source's action, with the state said ({sent.get('path')})")
        check(sent.get("body") == "", "with no body: nothing a form token would be needed for")
        check(sent.get("authorization") == "Bearer " + TOKEN, "carrying the issuer's ticket as a bearer")
        issued = Stand.issued[-1] if Stand.issued else {}
        check(issued.get("audience") == "mesh" and issued.get("scopes") == "mesh:Bench",
              f"a ticket for Mesh with the grant to change that mesh, mesh:Bench ({issued})")

        Stand.status = 202
        answer = switch("ba06f37ca34ba32c.state", "off")
        check(answer == "false" and Stand.requests[-1]["path"].endswith("/action?state=off"),
              f"a 202 (pending) is not reported as switched ({answer})")
        for status in (400, 403, 405, 502):
            Stand.status = status
            check(switch("ba06f37ca34ba32c.state", "on") == "false", f"a {status} is a switch not done")

        # @verifies PMESH-0005
        Stand.status = 200
        count = len(Stand.requests)
        for state in ("", "banana", "ON"):
            check(switch("ba06f37ca34ba32c.state", state) == "false", f"the state {state!r} is refused")
        check(len(Stand.requests) == count, "and nothing is sent to Mesh for it")

        # @verifies PMESH-0006
        stored = mesh + "/mesh/api/projects/Bench/sources/ba06f37ca34ba32c.state/action"
        check(switch(stored, "on") == "true" and
              Stand.requests[-1]["path"] == "/mesh/api/projects/Bench/sources/ba06f37ca34ba32c.state/action?state=on"
              and Stand.requests[-1]["method"] == "POST",
              "a source stored as Mesh's action URL is posted to by its id")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        stand.shutdown()
        import shutil
        shutil.rmtree(root, ignore_errors=True)
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("provider-mesh smoke ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
