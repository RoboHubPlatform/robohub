"""What a forged post looks like to a RoboHub application, for the smoke tests.

A page on another site can make a person's browser post to an application, and
the browser sends the application's session cookie with it. What such a page
cannot do is read the form token out of the application's own page, or make the
browser send an `Authorization` header. So a forged post is one that rides on the
cookie alone, with no token or the wrong one, and every state-changing route has
to refuse it.

The smoke tests sign in with a bearer ticket. `cookie_session` turns a second
ticket into the session cookie a browser would hold, through the application's
own `/auth/callback`, so a test can post the way a browser does; `post` sends one
post with whichever of the two it is given and follows no redirect.
"""

import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401 - urllib's hook
        return None


def mint_ticket(rho: str, home: str, audience: str) -> str:
    """Another ticket signed with the key pair the test made in `home`.

    The key pair is not made again: the application already holds its public key.
    """
    keys = os.path.join(home, ".rho", "auth")
    result = subprocess.run(
        [rho, "auth", "ticket", "--private", os.path.join(keys, "private.pem"),
         "--issuer", "keeper", "--audience", audience, "--subject", "browser",
         "--scopes", "*", "--ttl", "1h"],
        check=True, capture_output=True, text=True)
    return result.stdout.strip()


def cookie_session(rho: str, home: str, base: str, audience: str) -> str:
    """The `Cookie` header of a browser signed in to the application."""
    ticket = mint_ticket(rho, home, audience)
    request = urllib.request.Request(
        base + "/auth/callback?" + urllib.parse.urlencode({"ticket": ticket, "next": "/"}))
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=10) as response:
            headers = response.headers
    except urllib.error.HTTPError as error:
        headers = error.headers
    for value in headers.get_all("Set-Cookie") or []:
        pair = value.split(";", 1)[0].strip()
        if pair.startswith("rho_session_"):
            return pair
    raise AssertionError("the application set no session cookie from /auth/callback")


def post(base: str, path: str, fields: dict, bearer: str = "", cookie: str = "",
         headers: dict = None):
    """One form post, following no redirect: (status, body)."""
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(base + path, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    if bearer:
        request.add_header("Authorization", f"Bearer {bearer}")
    if cookie:
        request.add_header("Cookie", cookie)
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=20) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def refused(status: int, body: str, message: str = "") -> bool:
    """Whether an answer is a refusal: 403, or a page that says it refused."""
    if status == 403:
        return True
    return bool(message) and message in body


def rho_binary(projects) -> str:
    """The toolchain the tests run: the checkout's own when it is built."""
    local = os.path.join(str(projects), "rho", "bin", "rho")
    return local if os.path.exists(local) else "rho"


def workspace_state(workspace: str) -> dict:
    """What an application keeps, to see that a refused post changed none of it.

    The database is compared by its rows (a dump), every other file by its
    contents; logs, live feeds and sessions change on every request and are left
    out.
    """
    import sqlite3
    state = {}
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in ("auth", "logs", "log")]
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, workspace)
            if name.endswith((".log", ".events", "-wal", "-shm", "-journal", ".txt", ".snapshot")):
                continue
            if name.endswith(".db"):
                with sqlite3.connect(path) as conn:
                    state[rel] = "\n".join(conn.iterdump())
                continue
            with open(path, "rb") as handle:
                state[rel] = handle.read()
    return state


def state_diff(before: dict, after: dict) -> str:
    """The names of what differs between two workspace states."""
    names = sorted(set(before) | set(after))
    return ", ".join(n for n in names if before.get(n) != after.get(n))
