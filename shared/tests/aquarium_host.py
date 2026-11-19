"""The aquarium, built and started for a module's smoke test.

A module that registers routes is tested inside the application that includes
it: the aquarium, in its own repository beside this one, or where
ROBOHUB_AQUARIUM says. `running()` builds it, starts it on a free port with a
workspace and a home of its own, makes the key pair it verifies tickets with,
and hands the test its address and a bearer ticket.
"""

import contextlib
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROBOHUB = Path(__file__).resolve().parents[2]
PROJECTS = ROBOHUB.parent
HOST = Path(os.environ.get("ROBOHUB_AQUARIUM", str(PROJECTS / "robohub-aquarium")))
_LOCAL_RHO = PROJECTS / "rho" / "bin" / "rho"
RHO = str(_LOCAL_RHO) if _LOCAL_RHO.exists() else "rho"


class Host:
    def __init__(self, base: str, token: str, home: str, workspace: str):
        self.base = base
        self.token = token
        self.home = home
        self.workspace = workspace

    def request(self, path: str, headers: dict = None, bearer: bool = True,
                timeout: float = 10, follow: bool = True):
        """A GET: (status, headers, body). Redirects are not followed unless asked."""
        request = urllib.request.Request(self.base + path)
        if bearer:
            request.add_header("Authorization", f"Bearer {self.token}")
        for name, value in (headers or {}).items():
            request.add_header(name, value)
        opener = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(request, timeout=timeout) as response:
                return response.status, response.headers, response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            return error.code, error.headers, error.read().decode("utf-8", "replace")

    def get(self, path: str) -> str:
        status, _, body = self.request(path, follow=True)
        if status != 200:
            raise AssertionError(f"GET {path} answered {status}")
        return body


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _ticket(home: str) -> str:
    keys = os.path.join(home, ".rho", "auth")
    os.makedirs(keys, exist_ok=True)
    subprocess.run([RHO, "auth", "keygen", "--dir", keys, "--force"],
                   check=True, capture_output=True, text=True)
    result = subprocess.run(
        [RHO, "auth", "ticket", "--private", os.path.join(keys, "private.pem"),
         "--issuer", "keeper", "--audience", "aquarium", "--subject", "smoke",
         "--scopes", "*", "--ttl", "1h"],
        check=True, capture_output=True, text=True)
    return result.stdout.strip()


@contextlib.contextmanager
def running():
    result = subprocess.run([RHO, "build", str(HOST)], cwd=ROBOHUB, text=True, capture_output=True)
    if result.returncode != 0:
        raise SystemExit("aquarium build failed:\n" + result.stdout + result.stderr)
    binary = HOST / "build" / "aquarium"
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="aquarium-ws-") as workspace, \
            tempfile.TemporaryDirectory(prefix="aquarium-home-") as home:
        env = dict(os.environ)
        env.setdefault("RHO_HOME", os.path.join(os.path.expanduser("~"), ".rho"))
        env.update({"ROBOHUB_WORKSPACE": str(ROBOHUB), "ROBOHUB_APP_WORKSPACE": workspace,
                    "ROBOHUB_APP_MANIFEST": str(HOST / "module.yml"),
                    "RHO_HTTP_ADDR": f"127.0.0.1:{port}", "HOME": home})
        token = _ticket(home)
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        try:
            host = Host(base, token, home, workspace)
            deadline = time.time() + 60
            while True:
                try:
                    status, _, _ = host.request("/healthz", timeout=1)
                    if status < 500:
                        break
                except (urllib.error.URLError, OSError):
                    pass
                if time.time() > deadline:
                    raise SystemExit(f"aquarium did not start at {base}")
                time.sleep(0.2)
            yield host
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
