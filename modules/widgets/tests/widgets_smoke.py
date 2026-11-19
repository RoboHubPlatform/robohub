#!/usr/bin/env python3
"""Smoke test for the widgets module inside the aquarium host."""

import html
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "tests"))
import csrf_probe  # noqa: E402

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


def wait_for(base: str) -> None:
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            with open_url(base + "/widgets", timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    raise SystemExit(f"aquarium did not start at {base}")


def get(base: str, path: str) -> str:
    with open_url(base + path, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def post_form(base: str, path: str, fields: dict) -> str:
    if CSRF and "csrf" not in fields:
        fields = dict(fields, csrf=CSRF)
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with open_url(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def post_json(base: str, path: str, fields: dict) -> dict:
    return json.loads(post_form(base, path, fields))


def assert_contains(haystack: str, needles: list, label: str) -> None:
    for needle in needles:
        if needle not in haystack:
            raise AssertionError(f"{label} does not contain {needle!r}")


REFUSED = "Refused: the form token did not match."


# @verifies WIDG-0013
def forged_posts_are_refused(base: str, home: str) -> None:
    """Every widgets post that changes something refuses a post without the token.

    A form route takes the form token and nothing else: a bearer ticket does not
    stand in for it. A route code calls (the API, the refresh) takes a bearer
    ticket or the token, and refuses a post that has only the browser's cookie.
    """
    before = get(base, "/api/widgets")
    cookie = csrf_probe.cookie_session(str(RHO) if RHO.exists() else "rho", home, base, "aquarium")
    form_posts = [
        ("/widgets/add", {"title": "Forged", "kind": "numeric", "source_kind": "manual"}),
        ("/widgets/edit", {"id": "1", "title": "Forged", "kind": "numeric", "source_kind": "manual"}),
        ("/widgets/delete", {"id": "1"}),
        ("/widgets/move", {"id": "1", "delta": "1"}),
        ("/widgets/resize", {"id": "1", "delta": "inc"}),
        ("/widgets/pin", {"id": "1", "pinned": "1"}),
        ("/widgets/value", {"id": "1", "value": "99"}),
        ("/widgets/press", {"id": "2"}),
        ("/widgets/press", {"id": "2", "return": "dashboard"}),
    ]
    for path, fields in form_posts:
        for label, extra in (("no token", {}), ("a wrong token", {"csrf": "0" * 64})):
            for how, auth in (("a cookie", {"cookie": cookie}), ("a bearer ticket", {"bearer": TOKEN})):
                status, body = csrf_probe.post(base, path, dict(fields, **extra), **auth)
                if not csrf_probe.refused(status, body, REFUSED):
                    raise AssertionError(f"{path} with {label} and {how} was answered {status}")
            status, body = csrf_probe.post(base, path, dict(fields, **extra),
                                           cookie=cookie, headers={"HX-Request": "true"})
            if status != 403:
                raise AssertionError(f"{path} from htmx with {label} was answered {status}")
    machine_posts = [
        ("/api/widgets/1/value", {"value": "99"}),
        ("/api/widgets/2/press", {}),
        ("/widgets/refresh", {}),
    ]
    for path, fields in machine_posts:
        for label, extra in (("no token", {}), ("a wrong token", {"csrf": "0" * 64})):
            status, body = csrf_probe.post(base, path, dict(fields, **extra), cookie=cookie)
            if status != 403:
                raise AssertionError(f"{path} with only a cookie and {label} was answered {status}")
    after = get(base, "/api/widgets")
    if after != before:
        raise AssertionError(f"a refused post changed the widgets:\n{before}\n{after}")
    # The same posts with the token, and the code's with a ticket, are answered.
    status, _ = csrf_probe.post(base, "/widgets/pin", {"id": "1", "pinned": "1", "csrf": CSRF},
                                cookie=cookie, headers={"HX-Request": "true"})
    if status != 200:
        raise AssertionError(f"a pin with the token was answered {status}")
    status, _ = csrf_probe.post(base, "/widgets/refresh", {"csrf": CSRF}, cookie=cookie)
    if status != 200:
        raise AssertionError(f"a refresh with the token was answered {status}")
    status, _ = csrf_probe.post(base, "/api/widgets/1/value", {"value": "25.5"}, bearer=TOKEN)
    if status != 200:
        raise AssertionError(f"the API with a bearer ticket was answered {status}")
    # Every form the pages draw carries the token, so a person's own posts work.
    # The language switch is the one form without: it sets the browser's own
    # language cookie and changes nothing the application keeps.
    for page in ("/widgets", "/widgets/edit?id=1", "/widgets/cards"):
        forms = re.findall(r"<form\b.*?</form>", get(base, page), re.S)
        missing = [f[:120] for f in forms
                   if 'name="csrf"' not in f and 'action="/i18n/locale"' not in f]
        if not forms or missing:
            raise AssertionError(f"{page} draws forms without the token: {missing}")


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
        # curl, as the application finds it, records what it was run with and
        # then runs: a hook's address never appears among its arguments.
        wrapper = Path(auth_home) / "curl-wrapper"
        wrapper.mkdir(exist_ok=True)
        real_curl = shutil.which("curl")
        argv_log = Path(auth_home) / "curl-argv.log"
        (wrapper / "curl").write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$@\" >> " + shlex.quote(str(argv_log)) +
            "\nexec " + shlex.quote(real_curl) + " \"$@\"\n")
        (wrapper / "curl").chmod(0o755)
        env["PATH"] = str(wrapper) + os.pathsep + env.get("PATH", "")
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        try:
            wait_for(base)
            learn_csrf(base, "/widgets")
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
            assert_contains(get(base, "/widgets/cards"), ["Water temperature", "25.4"],
                            "dashboard number")

            post_form(base, "/widgets/add", {
                "title": "Return pump", "kind": "toggle", "source_kind": "url",
                "source": base + "/scheduler?state={state}&key=widget-hook-secret", "method": "GET",
            })
            post_form(base, "/widgets/press", {"id": "2"})
            widgets = json.loads(get(base, "/api/widgets"))
            toggle = [w for w in widgets if w["title"] == "Return pump"][0]
            if toggle["latest"] != "on":
                raise AssertionError(f"toggle should be on: {toggle}")
            assert_contains(get(base, "/widgets/cards"), ["Return pump", "On"], "dashboard switch")
            # @verifies WIDG-0014
            argv = argv_log.read_text() if argv_log.exists() else ""
            if "-K" not in argv:
                raise AssertionError("the press did not run curl with a configuration file")
            if "widget-hook-secret" in argv or "/scheduler" in argv:
                raise AssertionError(f"a hook's address is on curl's command line:\n{argv}")
            leftovers = [p.name for p in (Path(workspace) / "data").glob("widget-*.curl")]
            if leftovers:
                raise AssertionError(f"curl configuration files were left behind: {leftovers}")

            post_form(base, "/widgets/add", {
                "title": "pH", "kind": "chart", "source_kind": "manual", "unit": "pH",
            })
            for value in ["8.1", "8.2", "8.0"]:
                post_form(base, "/widgets/value", {"id": "3", "value": value})
            assert "<svg class=\"spark\"" in get(base, "/widgets/cards"), "chart sparkline"

            forged_posts_are_refused(base, auth_home)

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
