#!/usr/bin/env python3
"""Smoke test for the notifications module, inside the aquarium host.

`POST /notifications/push` and `POST /notifications/dismiss` are routes for code:
no form draws them. They take a bearer ticket, or the form token from a page
script that has one, and refuse a post that rides only on the browser's session
cookie, which is what a page on another site can make a browser send.
"""

import json
import os
import re
import shutil
import html
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
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
RHO = csrf_probe.rho_binary(PROJECTS)


def mint_token(home: str, audience: str) -> str:
    """A key pair in the host's home, and a ticket signed with it."""
    keys = os.path.join(home, ".rho", "auth")
    os.makedirs(keys, exist_ok=True)
    subprocess.run([RHO, "auth", "keygen", "--dir", keys, "--force"],
                   check=True, capture_output=True, text=True)
    return csrf_probe.mint_ticket(RHO, home, audience)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def get(base: str, path: str, token: str) -> str:
    request = urllib.request.Request(base + path)
    request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def wait_for(base: str, token: str) -> None:
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            get(base, "/notifications/list", token)
            return
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    raise SystemExit(f"aquarium did not start at {base}")


def build() -> Path:
    binary = HOST / "build" / "aquarium"
    result = subprocess.run([RHO, "build", str(HOST)], cwd=ROBOHUB, text=True,
                            capture_output=True)
    if result.returncode != 0:
        raise SystemExit("aquarium build failed:\n" + result.stdout + result.stderr)
    return binary


def messages(base: str, token: str) -> list:
    return [m["message"] for m in json.loads(get(base, "/notifications/list", token))]


# @verifies NOTIF-0007
def forged_posts_are_refused(base: str, token: str, cookie: str, csrf: str) -> None:
    for label, extra in (("no token", {}), ("a wrong token", {"csrf": "b" * 64})):
        status, _ = csrf_probe.post(base, "/notifications/push",
                                    dict({"message": "Forged"}, **extra), cookie=cookie)
        if status != 403:
            raise AssertionError(f"a push with only a cookie and {label} was answered {status}")
    if "Forged" in messages(base, token):
        raise AssertionError("a refused push was stored")

    # A program with a ticket pushes; a page with the token pushes too.
    status, _ = csrf_probe.post(base, "/notifications/push", {"message": "From code"}, bearer=token)
    if status != 200:
        raise AssertionError(f"a push with a bearer ticket was answered {status}")
    status, _ = csrf_probe.post(base, "/notifications/push",
                                {"message": "From the page", "csrf": csrf}, cookie=cookie)
    if status != 200:
        raise AssertionError(f"a push with the form token was answered {status}")
    if not {"From code", "From the page"} <= set(messages(base, token)):
        raise AssertionError(f"the pushes were not stored: {messages(base, token)}")

    listed = json.loads(get(base, "/notifications/list", token))
    target = str([m for m in listed if m["message"] == "From code"][0]["id"])
    for label, extra in (("no token", {}), ("a wrong token", {"csrf": "b" * 64})):
        status, _ = csrf_probe.post(base, "/notifications/dismiss",
                                    dict({"id": target}, **extra), cookie=cookie)
        if status != 403:
            raise AssertionError(f"a dismiss with only a cookie and {label} was answered {status}")
    if "From code" not in messages(base, token):
        raise AssertionError("a refused dismiss dismissed the message")
    status, _ = csrf_probe.post(base, "/notifications/dismiss", {"id": target}, bearer=token)
    if status != 200 or "From code" in messages(base, token):
        raise AssertionError(f"a dismiss with a bearer ticket did not dismiss ({status})")


# The keeper's app proxy rewrites a page's root-relative links onto
# /app/<name>/; this is the attribute list it rewrites, as rho's
# src/codegen/emit_go_appproxy.go has it (appProxyAttrs). A script literal is
# not among them.
PROXY_ATTRS = re.compile(r"""(\s(?:href|src|action|formaction|poster|hx-get|hx-post|hx-put|hx-patch|hx-delete|hx-push-url|sse-connect|data-href|data-url)=)(["'])/""")


def proxied(page: str, base: str) -> str:
    """The page as the keeper's proxy hands it on under base (/app/<name>)."""
    return PROXY_ATTRS.sub(lambda m: m.group(1) + m.group(2) + base + "/", page)


# The embed's script, run with a stand-in page: which stream it opens, and how
# long its toast stays up for an event with a timeout, one without, and a page
# script's own call.
EMBED_RUNNER = r"""
const html = require("fs").readFileSync(0, "utf8");
const url = (html.match(/<div id="toast"[^>]*data-url="([^"]*)"/) || [])[1] || null;
const script = html.match(/<script>(\(function\(\)\{var t=document\.getElementById\("toast"\)[\s\S]*?)<\/script>/)[1];
const kp = (html.match(/<div id="toast"[^>]*data-keeper-port="([^"]*)"/) || [])[1] || null;
const toast = {className: "", textContent: "", getAttribute: (n) => (n === "data-url" ? url : (n === "data-keeper-port" ? kp : null))};
const delays = []; let opened = null; let source = null; let keeper = null;
global.location = {protocol: "http:", hostname: "127.0.0.1", port: process.env.PAGE_PORT || "8480"};
global.document = {getElementById: () => toast, documentElement: {lang: "en"}};
global.window = {dispatchEvent: () => {}};
global.CustomEvent = function () {};
global.setTimeout = (f, ms) => { delays.push(ms); return delays.length; };
global.clearTimeout = () => {};
global.EventSource = function (u, o) {
  if (opened === null) { opened = u; source = this; } else { keeper = {url: u, credentials: !!(o && o.withCredentials)}; }
};
eval(script);
source.onmessage({data: JSON.stringify({kind: "info", message: "seven", timeout: 7})});
source.onmessage({data: JSON.stringify({kind: "refresh", message: "no timeout"})});
window.rhoToast("from a page", "warning");
console.log(JSON.stringify({opened, delays, keeper}));
"""


def main() -> int:
    binary = build()
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="notifications-") as workspace:
        env = dict(os.environ)
        env.setdefault("RHO_HOME", os.path.join(os.path.expanduser("~"), ".rho"))
        env["ROBOHUB_WORKSPACE"] = str(ROBOHUB)
        env["ROBOHUB_APP_WORKSPACE"] = workspace
        env["ROBOHUB_APP_MANIFEST"] = str(HOST / "module.yml")
        env["RHO_HTTP_ADDR"] = f"127.0.0.1:{port}"
        # Started by the keeper, the application is told where it is.
        env["ROBOHUB_KEEPER_URL"] = "http://127.0.0.1:19090"
        home = tempfile.mkdtemp(prefix="notifications-home-")
        env["HOME"] = home
        token = mint_token(home, "aquarium")
        process = subprocess.Popen([str(binary)], cwd=HOST, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            wait_for(base, token)
            # The 400s the routes have always answered still come first for a
            # post that is allowed.
            status, _ = csrf_probe.post(base, "/notifications/push", {}, bearer=token)
            if status != 400:
                raise AssertionError(f"a push without a message was answered {status}")
            found = re.search(r'name="csrf" value="([^"]*)"', get(base, "/widgets", token))
            if not found:
                raise AssertionError("the host draws no form token")
            cookie = csrf_probe.cookie_session(RHO, home, base, "aquarium")
            forged_posts_are_refused(base, token, cookie, html.unescape(found.group(1)))

            # A toast stays up as long as its message is kept: the event carries
            # the message's timeout (5 when none is given), and the store keeps
            # the message for the same time.
            # @verifies NOTIF-0001, NOTIF-0009
            live = Path(workspace) / "data" / "live.events"
            for fields, wanted in (({"message": "Seven seconds", "timeout": "7"}, 7), ({"message": "The default"}, 5)):
                status, _ = csrf_probe.post(base, "/notifications/push", fields, bearer=token)
                if status != 200:
                    raise AssertionError(f"a push was answered {status}")
                event = json.loads(live.read_text().splitlines()[-1])
                if event.get("message") != fields["message"] or event.get("timeout") != wanted:
                    raise AssertionError(f"the live event for {fields}: {event}, wanted timeout {wanted}")
                stored = [m for m in json.loads(get(base, "/notifications/list", token)) if m["message"] == fields["message"]][0]
                if stored["expires_at"] - stored["created_at"] != wanted:
                    raise AssertionError(f"the stored message for {fields}: {stored}")

            # The stream is named where the keeper's proxy rewrites it: a page
            # reached at /app/aquarium/ follows /app/aquarium/notifications/stream,
            # which the proxy hands to the application as /notifications/stream.
            # @verifies NOTIF-0003, NOTIF-0009, NOTIF-0010
            page = proxied(get(base, "/widgets", token), "/app/aquarium")
            if 'EventSource("/' in page:
                raise AssertionError("the embed opens its stream at an absolute path in a script, which the proxy does not rewrite")
            named = re.search(r'<div id="toast"[^>]*data-url="([^"]*)"', page)
            if not named or named.group(1) != "/app/aquarium/notifications/stream":
                raise AssertionError(f"the stream behind the keeper's prefix is {named and named.group(1)!r}")
            request = urllib.request.Request(base + named.group(1)[len("/app/aquarium"):])
            request.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(request, timeout=10) as response:
                if not response.headers.get("Content-Type", "").startswith("text/event-stream"):
                    raise AssertionError(f"the stream answered {response.headers.get('Content-Type')}")
            node = shutil.which("node")
            if node:
                ran = subprocess.run([node, "-e", EMBED_RUNNER], input=page, capture_output=True, text=True, timeout=30)
                if ran.returncode != 0:
                    raise AssertionError(f"the embed's script did not run: {ran.stderr}")
                seen = json.loads(ran.stdout)
                if seen.get("opened") != "/app/aquarium/notifications/stream" or seen.get("delays") != [7000, 5000, 5000]:
                    raise AssertionError(f"the embed opened {seen['opened']!r} and held its toasts for {seen['delays']} ms")
                # @verifies NOTIF-0011
                # A page on the application's own port also follows the keeper's
                # feed, at the page's host and the keeper's port, with credentials.
                if seen.get("keeper") != {"url": "http://127.0.0.1:19090/api/v1/notifications/stream", "credentials": True}:
                    raise AssertionError(f"the embed's keeper stream is {seen.get('keeper')!r}")
                same = subprocess.run([node, "-e", EMBED_RUNNER], input=page, capture_output=True, text=True, timeout=30,
                                      env=dict(os.environ, PAGE_PORT="19090"))
                if json.loads(same.stdout).get("keeper") is not None:
                    raise AssertionError("a page on the keeper's own port opened the keeper's feed twice")
            else:
                print("node is not installed: the embed's script was checked by its text only")

            # The live feed is bounded: it starts over after 500 events rather
            # than growing for as long as the application runs.
            # @verifies NOTIF-0008
            for i in range(520):
                status, _ = csrf_probe.post(base, "/notifications/push", {"message": f"Bulk {i}", "timeout": "1"}, bearer=token)
                if status != 200:
                    raise AssertionError(f"push {i} was answered {status}")
            lines = live.read_text().splitlines()
            if not 0 < len(lines) <= 500 or json.loads(lines[-1])["message"] != "Bulk 519":
                raise AssertionError(f"the live feed holds {len(lines)} events, the last {lines[-1] if lines else None}")
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
